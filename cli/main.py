"""
CLI main entry point
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict

from .args import parse_arguments
from models.pope import Pope
from models.document import Document
from scrapper.vatican_pope import VaticanPopeScraper
from scrapper.vatican_documents_index import VaticanDocumentsIndexScraper
from api_generator.json_builder import save_api_file


def setup_logging(verbose: bool = False):
    """Configure logging for the scraper"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


async def run_scraper(args):
    """Runs the main scraping process."""
    logger = logging.getLogger(__name__)
    
    all_popes: Dict[str, Pope] = {}
    all_documents: Dict[str, Document] = {}
    
    # Define document types to scrape (hardcoded)
    document_types = ["encyclicals"]
    
    logger.info(f"Document types: {document_types}")
        
    # Step 1: Scrape pope list
    pope_scraper = VaticanPopeScraper()
    logger.info("Scraping pope list...")
    popes = pope_scraper.scrape_pope_list()
    
    if not popes:
        logger.error("No popes found. Exiting.")
        return
        
    logger.info(f"Found {len(popes)} popes")
    
    # Add to collection
    for pope in popes:
        all_popes[pope.id] = pope
    
    # Step 2: Scrape document indexes and documents for each pope
    doc_index_scraper = VaticanDocumentsIndexScraper()
    
    for pope_id, pope in all_popes.items():
        logger.info(f"Processing pope: {pope_id}")
        
        # Update pope with document index URLs
        doc_index_scraper.update_pope_documents_index(pope)
        
        # Scrape documents for each document type
        for doc_type in document_types:
            if doc_type not in pope.metadata["documents_vatican_url_index"]:
                logger.warning(f"No {doc_type} index found for {pope_id}")
                continue
                
            logger.info(f"  Scraping {doc_type} documents...")
            
            # Scrape documents and add summaries to pope
            documents = doc_index_scraper.scrape_and_add_documents_to_pope(pope, doc_type)
            
            # Add documents to global collection
            for doc in documents:
                all_documents[doc.id] = doc
                    
            logger.info(f"    Found {len(documents)} {doc_type} documents")
    
    # Step 3: Save to files
    logger.info("Saving files...")
    
    # Create output directories
    args.output_dir.mkdir(exist_ok=True)
    (args.output_dir / "popes").mkdir(exist_ok=True)
    (args.output_dir / "documents").mkdir(exist_ok=True)
    
    # Save individual documents
    for doc_id, doc in all_documents.items():
        file_path = args.output_dir / "documents" / f"{doc_id}.json"
        save_api_file(str(file_path), doc.to_dict())
        logger.info(f"Saved document: {doc_id}")
    
    # Save individual popes
    for pope_id, pope in all_popes.items():
        file_path = args.output_dir / "popes" / f"{pope_id}.json"
        save_api_file(str(file_path), pope.to_dict())
        logger.info(f"Saved pope: {pope_id}")
    
    # Save aggregated popes list
    popes_list = [pope.to_dict() for pope in all_popes.values()]
    save_api_file(str(args.output_dir / "popes.json"), popes_list)
    logger.info(f"Saved aggregated popes list")
    
    logger.info("Scraping completed successfully!")


async def main():
    """CLI main entry point"""
    args = parse_arguments()
    setup_logging(args.verbose)
    
    try:
        await run_scraper(args)
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        logging.error(f"Scraping failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())