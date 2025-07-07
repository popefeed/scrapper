"""
Command line argument parsing
"""

import argparse
from pathlib import Path


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="PopeFeed Vatican Document Scraper")
    parser.add_argument(
        "--resume", action="store_true", help="Resume interrupted scraping session"
    )
    parser.add_argument(
        "--skip-documents-with-exists", action="store_true", help="Resume interrupted scraping session"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("../api"),
        help="Output directory for API files (default: ../api)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    return parser.parse_args()