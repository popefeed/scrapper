"""
Generate paginated posts API from existing documents and popes data.
Creates api/posts/page=1.json, page=2.json, etc. with 50 documents per page.
"""

import json
import os
import glob
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
import math

def load_popes_data(api_dir: Path) -> Dict[str, Any]:
    """Load popes data for pope information lookup."""
    popes_file = api_dir / 'popes.json'
    with open(popes_file, 'r', encoding='utf-8') as f:
        popes_list = json.load(f)

    # Convert list to dict for easy lookup
    popes_dict = {}
    for pope in popes_list:
        popes_dict[pope['id']] = pope

    return popes_dict

def load_all_documents(api_dir: Path) -> List[Dict[str, Any]]:
    """Load all document JSON files from api/documents/."""
    documents = []
    documents_dir = api_dir / 'documents'
    document_files = list(documents_dir.glob('*.json'))

    for file_path in document_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                doc = json.load(f)
                documents.append(doc)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading {file_path}: {e}")
            continue

    return documents

def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime object for sorting."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        # Fallback for other formats or invalid dates
        return datetime.min

def get_pope_display_name(pope_id: str, popes_data: Dict[str, Any]) -> str:
    """Get display name for pope."""
    if pope_id in popes_data:
        names = popes_data[pope_id].get('names', {})
        return names.get('en', pope_id.replace('-', ' ').title())
    return pope_id.replace('-', ' ').title()

def get_pope_handle(pope_id: str) -> str:
    """Generate social media handle for pope."""
    return pope_id.replace('-', '')

def get_excerpt_from_document(doc: Dict[str, Any]) -> str:
    """Extract excerpt from document's existing excerpt or fallback text."""
    # First try to get excerpt from the document's excerpt field
    excerpts = doc.get('excerpt', {})
    if excerpts:
        # Prefer English, then any available language
        for lang in ['en', 'es', 'pt', 'it', 'fr', 'la']:
            if lang in excerpts and excerpts[lang].strip():
                return excerpts[lang]
        # If no preferred language, get any available excerpt
        for excerpt in excerpts.values():
            if excerpt and excerpt.strip():
                return excerpt

    # Fallback to generic text
    doc_type = doc.get('type', 'document')
    return f"Read the full text of this {doc_type} and discover the teachings within..."

def create_post_from_document(doc: Dict[str, Any], popes_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert document to post format."""
    pope_id = doc.get('pope_id', 'unknown')

    # Get pope information
    pope_name = get_pope_display_name(pope_id, popes_data)
    pope_handle = get_pope_handle(pope_id)

    # Get pope avatar - use local image if available, fallback to placeholder
    pope_avatar = f"https://via.placeholder.com/56x56/9CA3AF/ffffff?text={pope_handle if pope_handle else 'P'}"
    if pope_id in popes_data:
        local_image = popes_data[pope_id].get('local_image_path')
        if local_image:
            # Convert to API URL (remove /api prefix since server serves from api directory)
            image_path = local_image.replace('/api/', '/')
            pope_avatar = f"http://localhost:8000{image_path}"

    # Get document title
    title = doc.get('title', 'Untitled Document')

    # Get real excerpt from document content
    excerpt_text = get_excerpt_from_document(doc)

    # Count available languages
    vatican_urls = doc.get('metadata', {}).get('vatican_urls', {})
    language_count = len(vatican_urls)

    # Get document type for display
    doc_type = doc.get('type', 'document').replace('_', ' ').title()
    if doc_type == 'Encyclicals':
        doc_type = 'Encyclical'

    post = {
        'id': doc['id'],
        'pope': {
            'id': pope_id,
            'name': pope_name,
            'handle': pope_handle,
            'avatar': pope_avatar
        },
        'document': {
            'title': title,
            'type': doc_type,
            'date': doc.get('date', ''),
            'excerpt': excerpt_text,
            'language_count': language_count,
            'pdf_available': language_count > 0
        },
        'metadata': {
            'document_id': doc['id'],
            'original_type': doc.get('type', 'document')
        }
    }

    return post

def create_paginated_posts_api(api_dir: Path):
    """Create paginated posts API."""
    print("Loading popes data...")
    popes_data = load_popes_data(api_dir)

    print("Loading documents...")
    documents = load_all_documents(api_dir)
    print(f"Found {len(documents)} documents")

    # Sort documents by date descending
    print("Sorting documents by date...")
    documents.sort(key=lambda x: parse_date(x.get('date', '')), reverse=True)

    # Convert documents to posts
    print("Converting documents to posts...")
    posts = []
    for doc in documents:
        post = create_post_from_document(doc, popes_data)
        posts.append(post)

    # Calculate pagination
    posts_per_page = 50
    total_posts = len(posts)
    total_pages = math.ceil(total_posts / posts_per_page)

    print(f"Creating {total_pages} pages with {posts_per_page} posts per page...")

    # Create posts directory if it doesn't exist
    posts_dir = api_dir / 'posts'
    posts_dir.mkdir(exist_ok=True)

    # Create paginated files
    for page_num in range(1, total_pages + 1):
        start_idx = (page_num - 1) * posts_per_page
        end_idx = min(start_idx + posts_per_page, total_posts)
        page_posts = posts[start_idx:end_idx]
   
        page_data = {
            'meta': {
                'page': page_num,
                'per_page': posts_per_page,
                'total_pages': total_pages,
                'total_posts': total_posts,
                'has_next': page_num < total_pages,
                'has_prev': page_num > 1,
                'next_page': page_num + 1 if page_num < total_pages else None,
                'prev_page': page_num - 1 if page_num > 1 else None
            },
            'posts': page_posts
        }
   
        # Save page file
        page_file = posts_dir / f'page={page_num}.json'
        with open(page_file, 'w', encoding='utf-8') as f:
            json.dump(page_data, f, indent=2, ensure_ascii=False)
   
        print(f"Created {page_file} with {len(page_posts)} posts")

    # Create index file with metadata only
    index_data = {
        'meta': {
            'total_pages': total_pages,
            'total_posts': total_posts,
            'posts_per_page': posts_per_page,
            'latest_page': 1,
            'generated_at': datetime.now().isoformat()
        }
    }

    index_file = posts_dir / 'index.json'
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    print(f"Created {index_file}")
    print(f"Generated {total_pages} pages with {total_posts} total posts")

if __name__ == '__main__':
    # Default API directory (relative to project root)
    api_dir = Path(__file__).parent.parent.parent / 'api'
    create_paginated_posts_api(api_dir)