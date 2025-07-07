"""
Vatican Website Scraper

Handles scraping papal documents from the Vatican website
"""

import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from models.document import Document

LANGUAGE_CODES = {
    "en": "en",  # English
    "es": "es",  # Spanish
    "pt": "pt",  # Portuguese
    "it": "it",  # Italian
    "fr": "fr",  # French
    "la": "la",  # Latin
    "de": "ge",  # German (optional)
    "pl": "pl",  # Polish (optional)
}


def parse_vatican_date(date_str: str) -> Optional[str]:
    """Parses Vatican date strings (e.g., '19.IV.2005') into YYYY-MM-DD format."""
    if not date_str:
        return None

    # Handle cases like '28.II.2013' or '8.V.2025'
    parts = date_str.replace(".", " ").split()
    if len(parts) == 3:
        day, month_roman, year = parts
        roman_to_int = {
            "I": 1,
            "II": 2,
            "III": 3,
            "IV": 4,
            "V": 5,
            "VI": 6,
            "VII": 7,
            "VIII": 8,
            "IX": 9,
            "X": 10,
            "XI": 11,
            "XII": 12,
        }
        month = roman_to_int.get(month_roman.upper())
        if month:
            try:
                return datetime(int(year), month, int(day)).strftime("%Y-%m-%d")
            except ValueError:
                pass
    return None


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


def build_vatican_url(pope, doc_type, language, year=None):
    if year:
        return f"https://www.vatican.va/content/{pope}/{language}/{doc_type}/{year}.index.html"
    return f"https://www.vatican.va/content/{pope}/{language}/{doc_type}.index.html"


@dataclass
class VaticanURL:
    """Represents a Vatican URL structure"""

    pope_id: str
    language: str
    document_type: str
    full_url: str


class VaticanScraper:
    """Main scraper class for Vatican documents"""

    BASE_URL = "https://www.vatican.va"

    def __init__(self, language: str = "en"):
        """Initialize scraper with target language"""
        self.language = language
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )

    def scrape_pope_list_page(self) -> List[Dict[str, Any]]:
        """Scrapes the list of popes from the Vatican's holy_father index page."""
        pope_list_url = "https://www.vatican.va/holy_father/index.htm"
        popes_data = []
        try:
            response = self.session.get(pope_list_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            # Navigate to the table using CSS selectors based on the provided XPath
            # /html/body/div/table/tbody/tr[2]/td/table/tbody/tr[2]/td[1]/table
            # This translates to: body > div > table > tbody > tr:nth-of-type(2) > td > table > tbody > tr:nth-of-type(2) > td:nth-of-type(1) > table
            # Or more simply, find the table that contains the pope list
            # Given the structure, it's likely a table within a table.
            # Let's try to find the specific table by its content or structure.
            # A common pattern for such lists is a table with <a> tags for popes.

            # Find the main content div, then the table within it
            # This is a more robust way than relying on exact tr/td counts which can change.
            main_table = soup.find(
                "table", class_="table_bord"
            )  # Assuming a class or id might exist, or find by content
            if not main_table:
                # Fallback to a more general search if specific class not found
                # This is a heuristic, might need adjustment based on actual HTML
                main_table = soup.find(
                    "table", summary="List of Popes"
                )  # Another common attribute

            if not main_table:
                # If still not found, try to find the table by its position as per XPath
                # This is a very specific and fragile selector, but matches the XPath
                try:
                    # This is a very specific and fragile selector, but matches the XPath
                    main_table = soup.select_one(
                        "body > div > table > tbody > tr:nth-of-type(2) > td > table > tbody > tr:nth-of-type(2) > td:nth-of-type(1) > table"
                    )
                except Exception as e:
                    print(f"Could not find main table using CSS selector: {e}")
                    main_table = None

            if main_table:
                # Find all links within the table that point to pope pages
                # Pope links usually contain "/content/{pope_id}/en.html"
                for link in main_table.find_all("a", href=True):
                    href = link.get("href")
                    if href and "/content/" in href and "/en.html" in href:
                        pope_name_en = link.get_text(strip=True)
                        # Extract pope_id from URL: /content/{pope_id}/en.html
                        match = re.search(r"/content/([^/]+)/en\.html", href)
                        if match:
                            pope_id = match.group(1)
                            popes_data.append(
                                {
                                    "id": pope_id,
                                    "names": {"en": pope_name_en},
                                    "metadata": {
                                        "vatican_url": urljoin(self.BASE_URL, href),
                                    },
                                }
                            )
            else:
                print("Error: Could not find the main table containing pope list.")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching pope list page {pope_list_url}: {e}")
        except Exception as e:
            print(f"Error parsing pope list from {pope_list_url}: {e}")
        return popes_data

    def scrape_pope_details(self, pope_id: str) -> Dict[str, Any]:
        """Scrapes detailed information for a single pope from their Vatican page."""
        details_url = f"https://www.vatican.va/content/{pope_id}/en.html"
        pope_details = {
            "id": pope_id,
            "names": {},
            "full_names": {},
            "reign_start": None,
            "reign_end": None,
            "documents_index": {
                "homilies": [],
                "motu_proprio": [],
                "apostolic_letters": [],
                "encyclicals": [],
                "audiences": [],
                "speeches": [],
                "messages": [],
            },
        }

        try:
            response = self.session.get(details_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            info_div = soup.find("div", class_="info")
            if info_div:
                # Official Name (H1)
                h1 = info_div.find("h1")
                if h1:
                    pope_details["names"]["la"] = h1.get_text(strip=True)

                # Birth Name (H2 i)
                h2_i = info_div.find("h2")
                if h2_i and h2_i.find("i"):  # Ensure it's the one with <i> tag
                    pope_details["full_names"]["en"] = h2_i.find("i").get_text(
                        strip=True
                    )

                # Reign Dates (H2 b)
                b_tags = info_div.find_all("b")
                if len(b_tags) >= 1:
                    pope_details["reign_start"] = parse_vatican_date(
                        b_tags[0].get_text(strip=True)
                    )
                if len(b_tags) >= 2:
                    pope_details["reign_end"] = parse_vatican_date(
                        b_tags[1].get_text(strip=True)
                    )
                else:
                    # Handle cases where reign end is in a nested div (e.g., Francis)
                    siv_text_h2_b = info_div.select_one("div.siv-text h2 b")
                    if siv_text_h2_b:
                        pope_details["reign_end"] = parse_vatican_date(
                            siv_text_h2_b.get_text(strip=True)
                        )

            # Extract document index URLs
            document_index_urls = {}
            accordion_menu = soup.select_one(
                "div.topnav.holyfatherAccordionSidenav.sidenav_accordion #accordionmenu ul"
            )
            if accordion_menu:
                for li in accordion_menu.find_all("li"):
                    link = li.find("a", href=True)
                    if link:
                        href = link.get("href")
                        # Only consider links that are likely document index pages
                        # and are not just anchors on the same page
                        if (
                            href
                            and "/content/" in href
                            and ".html" in href
                            and "#" not in href
                        ):
                            parts = href.split("/")
                            doc_type = None
                            try:
                                lang_index = parts.index("en")
                                if lang_index + 1 < len(parts):
                                    potential_doc_type = parts[lang_index + 1]
                                    if ".index.html" in potential_doc_type:
                                        doc_type = potential_doc_type.replace(
                                            ".index.html", ""
                                        )
                                    elif potential_doc_type.isdigit():
                                        if lang_index + 2 < len(parts):
                                            doc_type = parts[lang_index + 1]
                                    else:
                                        doc_type = potential_doc_type
                            except ValueError:
                                pass

                            if doc_type:
                                doc_type = doc_type.replace("_", "-")
                                if doc_type not in document_index_urls:
                                    document_index_urls[doc_type] = []
                                document_index_urls[doc_type].append(
                                    urljoin(self.BASE_URL, href)
                                )
            else:
                print(
                    f"Warning: Could not find div.info for {pope_id} at {details_url}"
                )

            pope_details["documents_index"] = document_index_urls

        except requests.exceptions.RequestException as e:
            print(f"Error fetching pope details page {details_url}: {e}")
        except Exception as e:
            print(f"Error parsing pope details from {details_url}: {e}")
        return pope_details

    def get_document_urls_from_index_page(self, doc_index_url, pope_id, doc_type) -> List[Document]:
        """Scrapes document URLs from a pope's document index page."""
        document_urls = []
        try:
            response = self.session.get(doc_index_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            vaticanindex_div = soup.find("div", class_="vaticanindex")
            if not vaticanindex_div:
                print(f"Warning: Could not find .vaticanindex div in {doc_index_url}")
                return document_urls

            ul = vaticanindex_div.find("ul")
            if not ul:
                print(
                    f"Warning: Could not find ul in .vaticanindex div in {doc_index_url}"
                )
                return document_urls

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
                    title = title_and_date_text[: date_match.start()].strip()

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

                example_language_url = languages.get("en", list(languages.keys())[0]).get("metadata").get("url")
                document_id = self._extract_document_id(example_language_url)

                # Build vatican_urls from languages
                vatican_urls = {}
                for lang_code, lang_data in languages.items():
                    if "metadata" in lang_data and "url" in lang_data["metadata"]:
                        vatican_urls[lang_code] = lang_data["metadata"]["url"]

                document_data = Document(
                    id=document_id,
                    pope_id=pope_id,
                    type=doc_type,
                    title=title,
                    date=date_str,
                    excerpt={},  # Will be filled later when parsing document content
                    metadata={
                        "vatican_urls": vatican_urls
                    }
                )

                document_urls.append(document_data)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching document index page {doc_index_url}: {e}")
        except Exception as e:
            print(f"Error parsing document URLs from {doc_index_url}: {e}")
        return document_urls

    def _extract_document_id(self, url):
        """Extract document ID from Vatican URL."""
        if not url:
            return None

        # Remove .html extension and get the last part
        # Example: /content/john-paul-ii/en/encyclicals/documents/hf_jp-ii_enc_20030417_eccl-de-euch.html
        # Should return: hf_jp-ii_enc_20030417_eccl-de-euch
        parts = url.rstrip("/").split("/")
        if parts:
            filename = parts[-1]
            if filename.endswith(".html"):
                return filename[:-5]  # Remove .html
        return None

    def _extract_language_code(self, url):
        """Extract language code from Vatican URL."""
        if not url:
            return None

        # Example: /content/john-paul-ii/en/encyclicals/documents/...
        # Should return: en
        parts = url.split("/")
        try:
            content_idx = parts.index("content")
            if content_idx + 2 < len(parts):
                return parts[content_idx + 2]  # Language code is after pope_id
        except (ValueError, IndexError):
            pass
        return None
