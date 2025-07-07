#!/usr/bin/env python3
"""
Image downloader for pope photos and coat of arms from Vatican website.
"""

import os
import aiohttp
import asyncio
import logging
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urljoin, urlparse
import re

logger = logging.getLogger(__name__)

class VaticanImageDownloader:
    """Downloads and manages pope images from Vatican website."""

    def __init__(self, output_dir: str = "api/popes"):
        # Handle relative paths from different locations
        if not os.path.isabs(output_dir):
            # Try to find the api directory
            current_dir = Path.cwd()
            if (current_dir / "api").exists():
                self.output_dir = current_dir / output_dir
            elif (current_dir.parent / "api").exists():
                self.output_dir = current_dir.parent / output_dir
            else:
                self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(output_dir)
   
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session: Optional[aiohttp.ClientSession] = None
   
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def get_image_filename(self, pope_id: str, image_type: str = "photo") -> str:
        """Generate local filename for pope image."""
        if image_type == "coat_of_arms":
            return f"{pope_id}-arms.jpg"
        return f"{pope_id}.jpg"

    async def find_pope_image_url(self, pope_id: str, vatican_url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Find pope image and coat of arms URLs from Vatican page.
        Returns (image_url, coat_of_arms_url).
        """
        try:
            logger.info(f"Searching for images for {pope_id} at {vatican_url}")
       
            async with self.session.get(vatican_url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch {vatican_url}: {response.status}")
                    return None, None
           
                html = await response.text()
           
                # Common image patterns on Vatican website
                image_url = None
                coat_of_arms_url = None
           
                # Look for main pope image
                # Pattern 1: Profile photo in content area
                img_patterns = [
                    rf'https://www\.vatican\.va/content/{pope_id}/[^"]*\.(?:jpg|jpeg|png)',
                    rf'/content/{pope_id}/[^"]*\.(?:jpg|jpeg|png)',
                    rf'https://www\.vatican\.va/content/dam/{pope_id}/[^"]*\.(?:jpg|jpeg|png)',
                    rf'/content/dam/{pope_id}/[^"]*\.(?:jpg|jpeg|png)'
                ]
           
                for pattern in img_patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    if matches:
                        # Filter for likely profile photos (not coat of arms)
                        for match in matches:
                            if not any(keyword in match.lower() for keyword in ['arms', 'coat', 'stemma', 'logo']):
                                if match.startswith('/'):
                                    image_url = urljoin('https://www.vatican.va', match)
                                else:
                                    image_url = match
                                break
                        if image_url:
                            break
           
                # Look for coat of arms
                arms_patterns = [
                    rf'https://www\.vatican\.va/content/{pope_id}/[^"]*(?:arms|coat|stemma)[^"]*\.(?:jpg|jpeg|png)',
                    rf'/content/{pope_id}/[^"]*(?:arms|coat|stemma)[^"]*\.(?:jpg|jpeg|png)',
                    rf'https://www\.vatican\.va/content/dam/{pope_id}/[^"]*(?:arms|coat|stemma)[^"]*\.(?:jpg|jpeg|png)',
                    rf'/content/dam/{pope_id}/[^"]*(?:arms|coat|stemma)[^"]*\.(?:jpg|jpeg|png)'
                ]
           
                for pattern in arms_patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    if matches:
                        match = matches[0]
                        if match.startswith('/'):
                            coat_of_arms_url = urljoin('https://www.vatican.va', match)
                        else:
                            coat_of_arms_url = match
                        break
           
                # Fallback: Try to find generic image patterns
                if not image_url:
                    generic_patterns = [
                        r'<img[^>]+src="([^"]+)"[^>]*class="[^"]*(?:pope|pontiff|photo)[^"]*"',
                        r'<img[^>]+class="[^"]*(?:pope|pontiff|photo)[^"]*"[^>]+src="([^"]+)"'
                    ]
               
                    for pattern in generic_patterns:
                        matches = re.findall(pattern, html, re.IGNORECASE)
                        if matches:
                            match = matches[0]
                            if match.startswith('/'):
                                image_url = urljoin('https://www.vatican.va', match)
                            else:
                                image_url = match
                            break
           
                logger.info(f"Found images for {pope_id}: photo={image_url}, arms={coat_of_arms_url}")
                return image_url, coat_of_arms_url
           
        except Exception as e:
            logger.error(f"Error finding images for {pope_id}: {e}")
            return None, None

    async def download_image(self, url: str, output_path: Path) -> bool:
        """Download image from URL to local path."""
        try:
            logger.info(f"Downloading image from {url} to {output_path}")
       
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to download {url}: {response.status}")
                    return False
           
                # Check content type
                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    logger.warning(f"Invalid content type for {url}: {content_type}")
                    return False
           
                # Download and save
                content = await response.read()
           
                # Ensure directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)
           
                with open(output_path, 'wb') as f:
                    f.write(content)
           
                logger.info(f"Successfully downloaded image to {output_path}")
                return True
           
        except Exception as e:
            logger.error(f"Error downloading image from {url}: {e}")
            return False

    async def download_pope_images(self, pope_id: str, vatican_url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Download pope images and return local paths.
        Returns (image_path, coat_of_arms_path).
        """
        # Find image URLs
        image_url, coat_of_arms_url = await self.find_pope_image_url(pope_id, vatican_url)
   
        image_path = None
        coat_of_arms_path = None
   
        # Download main image
        if image_url:
            filename = self.get_image_filename(pope_id, "photo")
            local_path = self.output_dir / filename
            if await self.download_image(image_url, local_path):
                image_path = f"/api/popes/{filename}"
   
        # Download coat of arms
        if coat_of_arms_url:
            filename = self.get_image_filename(pope_id, "coat_of_arms")
            local_path = self.output_dir / filename
            if await self.download_image(coat_of_arms_url, local_path):
                coat_of_arms_path = f"/api/popes/{filename}"
   
        return image_path, coat_of_arms_path

    async def process_multiple_popes(self, pope_data_list: list) -> list:
        """Process multiple popes and download their images."""
        updated_popes = []
   
        for pope_data in pope_data_list:
            pope_id = pope_data.get('id')
            vatican_urls = pope_data.get('metadata', {}).get('vatican_urls', {})
       
            # Try English URL first, then any available language
            vatican_url = vatican_urls.get('en') or next(iter(vatican_urls.values()), None)
       
            if not vatican_url:
                logger.warning(f"No Vatican URL found for pope {pope_id}")
                updated_popes.append(pope_data)
                continue
       
            # Download images
            image_path, coat_of_arms_path = await self.download_pope_images(pope_id, vatican_url)
       
            # Update pope data
            if image_path:
                pope_data['local_image_path'] = image_path
            if coat_of_arms_path:
                pope_data['local_coat_of_arms_path'] = coat_of_arms_path
       
            updated_popes.append(pope_data)
       
            # Small delay to be respectful to Vatican servers
            await asyncio.sleep(1)
   
        return updated_popes

async def download_all_pope_images():
    """Standalone function to download all pope images."""
    import json

    # Load existing pope data - try multiple paths
    current_dir = Path.cwd()
    possible_paths = [
        current_dir / "api/popes.json",
        current_dir.parent / "api/popes.json",
        Path("api/popes.json"),
        Path("../api/popes.json")
    ]

    popes_file = None
    for path in possible_paths:
        if path.exists():
            popes_file = path
            break

    if not popes_file:
        logger.error("Pope data file not found in any of the expected locations")
        return

    with open(popes_file, 'r', encoding='utf-8') as f:
        popes_data = json.load(f)

    # Download images
    async with VaticanImageDownloader() as downloader:
        updated_popes = await downloader.process_multiple_popes(popes_data)

    # Save updated data
    with open(popes_file, 'w', encoding='utf-8') as f:
        json.dump(updated_popes, f, indent=2, ensure_ascii=False)

    logger.info("Finished downloading pope images")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(download_all_pope_images())