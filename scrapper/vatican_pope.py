"""
Vatican Pope scraper - specialized for scraping pope information
"""

import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Optional
from datetime import datetime

from models.pope import Pope


def parse_vatican_date(date_str: str) -> Optional[str]:
    """Parses Vatican date strings (e.g., '19.IV.2005') into YYYY-MM-DD format."""
    if not date_str:
        return None

    # Handle cases like '28.II.2013' or '8.V.2025'
    parts = date_str.replace(".", " ").split()
    if len(parts) == 3:
        day, month_roman, year = parts
        roman_to_int = {
            "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6,
            "VII": 7, "VIII": 8, "IX": 9, "X": 10, "XI": 11, "XII": 12,
        }
        month = roman_to_int.get(month_roman.upper())
        if month:
            try:
                return datetime(int(year), month, int(day)).strftime("%Y-%m-%d")
            except ValueError:
                pass
    return None


class VaticanPopeScraper:
    """Specialized scraper for Vatican pope information"""

    BASE_URL = "https://www.vatican.va"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })

    def scrape_pope_list(self) -> List[Pope]:
        """Scrapes the list of popes from the Vatican's holy_father index page."""
        pope_list_url = "https://www.vatican.va/holy_father/index.htm"
        popes = []
   
        try:
            response = self.session.get(pope_list_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
       
            # Find the main table containing pope links
            main_table = soup.find("table", class_="table_bord")
            if not main_table:
                # Fallback to positional selector
                main_table = soup.select_one(
                    "body > div > table > tbody > tr:nth-of-type(2) > td > table > tbody > tr:nth-of-type(2) > td:nth-of-type(1) > table"
                )
       
            if main_table:
                for link in main_table.find_all("a", href=True):
                    href = link.get("href")
                    if href and "/content/" in href and "/en.html" in href:
                        pope_name_en = link.get_text(strip=True)
                        # Extract pope_id from URL: /content/{pope_id}/en.html
                        match = re.search(r"/content/([^/]+)/en\.html", href)
                        if match:
                            pope_id = match.group(1)
                       
                            # Create Pope object with basic info
                            pope = Pope(
                                id=pope_id,
                                names={"en": pope_name_en},
                                metadata={
                                    "vatican_urls": {"en": urljoin(self.BASE_URL, href)},
                                    "documents_vatican_url_index": {}
                                }
                            )
                       
                            # Get detailed pope information and update the Pope object
                            self._update_pope_details(pope)
                       
                            popes.append(pope)
            else:
                print("Error: Could not find the main table containing pope list.")
           
        except requests.exceptions.RequestException as e:
            print(f"Error fetching pope list page {pope_list_url}: {e}")
        except Exception as e:
            print(f"Error parsing pope list from {pope_list_url}: {e}")
       
        return popes

    def _update_pope_details(self, pope: Pope) -> None:
        """Updates a Pope object with detailed information from their Vatican page."""
        details_url = f"https://www.vatican.va/content/{pope.id}/en.html"
   
        try:
            response = self.session.get(details_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
       
            info_div = soup.find("div", class_="info")
            if info_div:
                # Official Name (H1) - usually Latin
                h1 = info_div.find("h1")
                if h1:
                    latin_name = h1.get_text(strip=True)
                    pope.names["la"] = latin_name
           
                # Birth Name (H2 i)
                h2_i = info_div.find("h2")
                if h2_i and h2_i.find("i"):
                    pope.full_name = h2_i.find("i").get_text(strip=True)
           
                # Reign Dates (H2 b)
                b_tags = info_div.find_all("b")
                if len(b_tags) >= 1:
                    pope.reign_start = parse_vatican_date(
                        b_tags[0].get_text(strip=True)
                    )
                if len(b_tags) >= 2:
                    pope.reign_end = parse_vatican_date(
                        b_tags[1].get_text(strip=True)
                    )
                else:
                    # Handle cases where reign end is in a nested div (e.g., Francis)
                    siv_text_h2_b = info_div.select_one("div.siv-text h2 b")
                    if siv_text_h2_b:
                        pope.reign_end = parse_vatican_date(
                            siv_text_h2_b.get_text(strip=True)
                        )
       
        except requests.exceptions.RequestException as e:
            print(f"Error fetching pope details page {details_url}: {e}")
        except Exception as e:
            print(f"Error parsing pope details from {details_url}: {e}")