"""
Vatican Documents Index scraper - specialized for scraping document indexes and individual documents
"""

import re
import requests
import json
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.document import Document
from models.pope import Pope
from .vatican_scraper import VaticanScraper


def parse_document_date(date_str: str) -> Optional[str]:
    """Parses document date strings from Vatican index pages into YYYY-MM-DD format."""
    if not date_str:
        return None

    # Define month names in English
    month_names = {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
    }

    # Handle formats like "17 April 2003", "November 28, 1959", "24 May 2015"
    date_str = date_str.strip().lower()

    # Pattern 1: "17 April 2003" or "24 May 2015"
    match = re.match(r'^(\d{1,2})\s+(\w+)\s+(\d{4})$', date_str)
    if match:
        day, month_name, year = match.groups()
        month = month_names.get(month_name.lower())
        if month:
            try:
                return datetime(int(year), month, int(day)).strftime("%Y-%m-%d")
            except ValueError:
                pass

    # Pattern 2: "November 28, 1959"
    match = re.match(r'^(\w+)\s+(\d{1,2}),?\s+(\d{4})$', date_str)
    if match:
        month_name, day, year = match.groups()
        month = month_names.get(month_name.lower())
        if month:
            try:
                return datetime(int(year), month, int(day)).strftime("%Y-%m-%d")
            except ValueError:
                pass

    # Pattern 3: "December 25, 2005"
    match = re.match(r'^(\w+)\s+(\d{1,2}),\s+(\d{4})$', date_str)
    if match:
        month_name, day, year = match.groups()
        month = month_names.get(month_name.lower())
        if month:
            try:
                return datetime(int(year), month, int(day)).strftime("%Y-%m-%d")
            except ValueError:
                pass

    return None


class VaticanDocumentsIndexScraper:
    """Specialized scraper for Vatican document indexes"""

    BASE_URL = "https://www.vatican.va"

    def __init__(self, output_dir: Path = None, resume: bool = False):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
        self.content_scraper = VaticanScraper()
        self.output_dir = output_dir or Path("../api")
        self.resume = resume

    def _document_has_content(self, document_id: str) -> bool:
        """Check if document file exists and has raw_html content."""
        if not self.resume:
            return False
       
        document_file = self.output_dir / "documents" / f"{document_id}.json"
        if not document_file.exists():
            return False
       
        try:
            with open(document_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
           
            # Check if document has raw_html metadata with content
            raw_html = data.get("metadata", {}).get("raw_html", {})
            return len(raw_html) > 0 and any(content.strip() for content in raw_html.values())
       
        except (json.JSONDecodeError, FileNotFoundError, KeyError):
            return False

    def update_pope_documents_index(self, pope: Pope) -> None:
        """Updates a Pope object with document index URLs from their main page."""
        details_url = f"https://www.vatican.va/content/{pope.id}/en.html"
   
        try:
            response = self.session.get(details_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
       
            # Extract document index URLs from navigation menu
            accordion_menu = soup.select_one(
                "div.topnav.holyfatherAccordionSidenav.sidenav_accordion #accordionmenu ul"
            )
       
            if accordion_menu:
                for li in accordion_menu.find_all("li"):
                    link = li.find("a", href=True)
                    if link:
                        href = link.get("href")
                        if (href and "/content/" in href and ".html" in href and "#" not in href):
                            parts = href.split("/")
                            doc_type = None
                            try:
                                lang_index = parts.index("en")
                                if lang_index + 1 < len(parts):
                                    potential_doc_type = parts[lang_index + 1]
                                    if ".index.html" in potential_doc_type:
                                        doc_type = potential_doc_type.replace(".index.html", "")
                                    elif potential_doc_type.isdigit():
                                        if lang_index + 2 < len(parts):
                                            doc_type = parts[lang_index + 1]
                                    else:
                                        doc_type = potential_doc_type
                            except ValueError:
                                pass
                       
                            if doc_type:
                                doc_type = doc_type.replace("_", "-")
                                if doc_type not in pope.metadata["documents_vatican_url_index"]:
                                    pope.metadata["documents_vatican_url_index"][doc_type] = []
                                pope.metadata["documents_vatican_url_index"][doc_type].append(
                                    urljoin(self.BASE_URL, href)
                                )
                           
        except requests.exceptions.RequestException as e:
            print(f"Error fetching pope page {details_url}: {e}")
        except Exception as e:
            print(f"Error parsing document indexes from {details_url}: {e}")

    def scrape_documents_from_index(self, doc_index_url: str, pope_id: str, doc_type: str) -> List[Document]:
        """Scrapes document URLs from a pope's document index page."""
        documents = []
   
        try:
            response = self.session.get(doc_index_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            vaticanindex_div = soup.find("div", class_="vaticanindex")
            if not vaticanindex_div:
                print(f"Warning: Could not find .vaticanindex div in {doc_index_url}")
                return documents

            ul = vaticanindex_div.find("ul")
            if not ul:
                print(f"Warning: Could not find ul in .vaticanindex div in {doc_index_url}")
                return documents

            for li in ul.find_all("li"):
                item_div = li.find("div", class_="item")
                if not item_div:
                    continue

                h1 = item_div.find("h1")
                if not h1:
                    continue

                title_and_date_text = h1.get_text(strip=True)
                # Clean unwanted characters like \r, \n, extra spaces
                title_and_date_text = re.sub(r'[\r\n\t]+', ' ', title_and_date_text)
                title_and_date_text = re.sub(r'\s+', ' ', title_and_date_text).strip()

                title = title_and_date_text
                date_str = ""

                date_match = re.search(r"\(([^)]+)\)\s*$", title_and_date_text)
                if date_match:
                    raw_date_str = date_match.group(1).strip()
                    date_str = parse_document_date(raw_date_str) or raw_date_str
                    title = title_and_date_text[:date_match.start()].strip()

                # Find all language links in h2
                languages = {}
                h2 = item_div.find("h2")
                if h2:
                    for link in h2.find_all("a", href=True):
                        href = link.get("href")
                        language_name = link.get_text(strip=True)
                        language_code = self._extract_language_code(href)
                        if language_code:
                            languages[language_code] = {
                                "language": language_name,
                                "metadata": {
                                    "url": (
                                        urljoin(self.BASE_URL, href)
                                        if not href.startswith("http")
                                        else href
                                    ),
                                }
                            }

                if not languages:
                    continue
               
                # Extract document ID from any available language URL
                example_language_url = languages.get("en", list(languages.values())[0])["metadata"]["url"]
                document_id = self._extract_document_id(example_language_url)

                if not document_id:
                    continue

                # Build vatican_urls from languages
                vatican_urls = {}
                for lang_code, lang_data in languages.items():
                    if "metadata" in lang_data and "url" in lang_data["metadata"]:
                        vatican_urls[lang_code] = lang_data["metadata"]["url"]

                document = Document(
                    id=document_id,
                    pope_id=pope_id,
                    type=doc_type,
                    title=title,
                    date=date_str,
                    excerpt={},  # Will be filled by content fetching
                    metadata={
                        "vatican_urls": vatican_urls,
                        "raw_html": {}
                    }
                )

                # Check if document already has content when resuming
                if self._document_has_content(document_id):
                    print(f"    Skipping {document_id} (content already exists)")
                    # Load existing document data to preserve existing content
                    document_file = self.output_dir / "documents" / f"{document_id}.json"
                    try:
                        with open(document_file, 'r', encoding='utf-8') as f:
                            existing_data = json.load(f)
                        # Update document with existing content
                        document.excerpt = existing_data.get("excerpt", {})
                        document.metadata["raw_html"] = existing_data.get("metadata", {}).get("raw_html", {})
                    except Exception as e:
                        print(f"    Warning: Could not load existing content for {document_id}: {e}")
                        # Fall back to fetching content
                        print(f"    Fetching content for {document_id}...")
                        document = self.content_scraper.fetch_document_content(document)
                else:
                    # Fetch document content for all languages
                    print(f"    Fetching content for {document_id}...")
                    document = self.content_scraper.fetch_document_content(document)
           
                documents.append(document)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching document index page {doc_index_url}: {e}")
        except Exception as e:
            print(f"Error parsing document URLs from {doc_index_url}: {e}")
       
        return documents

    def scrape_and_add_documents_to_pope(self, pope: Pope, doc_type: str) -> List[Document]:
        """Scrapes documents from all index URLs for a given document type and adds summaries to Pope."""
        all_documents = []
   
        if doc_type not in pope.metadata["documents_vatican_url_index"]:
            return all_documents
       
        for index_url in pope.metadata["documents_vatican_url_index"][doc_type]:
            documents = self.scrape_documents_from_index(index_url, pope.id, doc_type)
            all_documents.extend(documents)
       
            # Add document summaries to pope
            if doc_type not in pope.documents:
                pope.documents[doc_type] = []
           
            for doc in documents:
                pope.documents[doc_type].append(doc.to_summary())
           
        return all_documents

    def _extract_document_id(self, url: str) -> Optional[str]:
        """Extract document ID from Vatican URL."""
        if not url:
            return None
   
        # Remove .html extension and get the last part
        # Example: /content/john-paul-ii/en/encyclicals/documents/hf_jp-ii_enc_20030417_eccl-de-euch.html
        # Should return: hf_jp-ii_enc_20030417_eccl-de-euch
        parts = url.rstrip('/').split('/')
        if parts:
            filename = parts[-1]
            if filename.endswith('.html'):
                return filename[:-5]  # Remove .html
        return None

    def _extract_language_code(self, url: str) -> Optional[str]:
        """Extract language code from Vatican URL."""
        if not url:
            return None
   
        # Example: /content/john-paul-ii/en/encyclicals/documents/...
        # Should return: en
        parts = url.split('/')
        try:
            content_idx = parts.index('content')
            if content_idx + 2 < len(parts):
                return parts[content_idx + 2]  # Language code is after pope_id
        except (ValueError, IndexError):
            pass
        return None