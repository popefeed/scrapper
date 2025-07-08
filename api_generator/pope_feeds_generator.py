"""
Generate pope-specific feeds for the API.
Creates api/feed/pope-{pope_id}.json for each pope with their documents.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Set
from pathlib import Path
from collections import defaultdict

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

def get_document_type_display(doc_type: str) -> str:
    """Convert document type to display format."""
    type_mapping = {
        'encyclicals': 'Encyclical',
        'angelus': 'Angelus',
        'homilies': 'Homily',
        'audiences': 'Audience',
        'speeches': 'Speech',
        'letters': 'Letter',
        'messages': 'Message',
        'apostolic_exhortations': 'Apostolic Exhortation',
        'apostolic_letters': 'Apostolic Letter',
        'motu_proprio': 'Motu Proprio',
        'bulls': 'Bull',
        'constitutions': 'Constitution'
    }
    return type_mapping.get(doc_type, doc_type.replace('_', ' ').title())

def group_documents_by_pope(documents: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group documents by pope ID."""
    pope_documents = defaultdict(list)
    
    for doc in documents:
        pope_id = doc.get('pope_id', 'unknown')
        pope_documents[pope_id].append(doc)
    
    return dict(pope_documents)

def group_documents_by_type(documents: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group documents by type for a specific pope."""
    type_documents = defaultdict(list)
    
    for doc in documents:
        doc_type = doc.get('type', 'unknown')
        type_documents[doc_type].append(doc)
    
    return dict(type_documents)

def create_document_summary(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Create a summary of a document for the feed."""
    # Get title
    title = doc.get('title', 'Untitled Document')
    
    # Get excerpt
    excerpts = doc.get('excerpt', {})
    excerpt = ""
    if excerpts:
        # Prefer English, then any available language
        for lang in ['en', 'es', 'pt', 'it', 'fr', 'la']:
            if lang in excerpts and excerpts[lang].strip():
                excerpt = excerpts[lang]
                break
        # If no preferred language, get any available excerpt
        if not excerpt:
            for exc in excerpts.values():
                if exc and exc.strip():
                    excerpt = exc
                    break
    
    # Get available languages
    vatican_urls = doc.get('metadata', {}).get('vatican_urls', {})
    available_languages = list(vatican_urls.keys())
    
    return {
        'id': doc['id'],
        'title': title,
        'type': get_document_type_display(doc.get('type', 'document')),
        'date': doc.get('date', ''),
        'excerpt': excerpt,
        'languages': available_languages,
        'vatican_url': vatican_urls.get('en') if vatican_urls else None
    }

def generate_pope_feed(pope_id: str, pope_data: Dict[str, Any], pope_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate feed data for a specific pope."""
    # Sort documents by date descending
    pope_documents.sort(key=lambda x: parse_date(x.get('date', '')), reverse=True)
    
    # Group documents by type
    documents_by_type = group_documents_by_type(pope_documents)
    
    # Create document summaries grouped by type
    feed_documents = {}
    total_documents = 0
    
    for doc_type, docs in documents_by_type.items():
        # Sort documents within each type by date
        docs.sort(key=lambda x: parse_date(x.get('date', '')), reverse=True)
        
        feed_documents[doc_type] = [create_document_summary(doc) for doc in docs]
        total_documents += len(docs)
    
    # Get pope information
    pope_name = pope_data.get('names', {}).get('en', pope_id.replace('-', ' ').title())
    
    # Create pope avatar URL
    pope_avatar = f"https://via.placeholder.com/128x128/9CA3AF/ffffff?text={pope_id[:2].upper()}"
    if pope_data.get('local_image_path'):
        # Convert to API URL
        image_path = pope_data['local_image_path'].replace('/api/', '/')
        pope_avatar = f"http://localhost:8000{image_path}"
    
    # Generate feed
    feed = {
        'pope': {
            'id': pope_id,
            'name': pope_name,
            'full_name': pope_data.get('full_name', ''),
            'avatar': pope_avatar,
            'reign_start': pope_data.get('reign_start', ''),
            'reign_end': pope_data.get('reign_end'),
            'biography': pope_data.get('biographies', {}).get('en', '')
        },
        'statistics': {
            'total_documents': total_documents,
            'document_types': len(documents_by_type),
            'latest_document_date': pope_documents[0].get('date', '') if pope_documents else '',
            'earliest_document_date': pope_documents[-1].get('date', '') if pope_documents else ''
        },
        'documents': feed_documents,
        'meta': {
            'generated_at': datetime.now().isoformat(),
            'document_count_by_type': {doc_type: len(docs) for doc_type, docs in documents_by_type.items()}
        }
    }
    
    return feed

def create_pope_feeds_api(api_dir: Path):
    """Create pope-specific feeds."""
    print("Loading popes data...")
    popes_data = load_popes_data(api_dir)
    
    print("Loading documents...")
    documents = load_all_documents(api_dir)
    print(f"Found {len(documents)} documents")
    
    # Group documents by pope
    print("Grouping documents by pope...")
    pope_documents = group_documents_by_pope(documents)
    
    # Create feed directory if it doesn't exist
    feed_dir = api_dir / 'feed'
    feed_dir.mkdir(exist_ok=True)
    
    # Generate feeds for each pope that has documents
    total_feeds = 0
    
    for pope_id, pope_docs in pope_documents.items():
        if pope_id == 'unknown':
            print(f"Skipping unknown pope documents: {len(pope_docs)} documents")
            continue
            
        if pope_id not in popes_data:
            print(f"Warning: Pope {pope_id} not found in popes data, skipping...")
            continue
        
        print(f"Generating feed for {pope_id} ({len(pope_docs)} documents)...")
        
        pope_data = popes_data[pope_id]
        feed = generate_pope_feed(pope_id, pope_data, pope_docs)
        
        # Save feed file
        feed_file = feed_dir / f'pope-{pope_id}.json'
        with open(feed_file, 'w', encoding='utf-8') as f:
            json.dump(feed, f, indent=2, ensure_ascii=False)
        
        print(f"Created {feed_file}")
        total_feeds += 1
    
    # Create index of all pope feeds
    pope_feeds_index = {
        'feeds': [],
        'meta': {
            'total_feeds': total_feeds,
            'generated_at': datetime.now().isoformat()
        }
    }
    
    for pope_id in pope_documents.keys():
        if pope_id != 'unknown' and pope_id in popes_data:
            pope_data = popes_data[pope_id]
            pope_name = pope_data.get('names', {}).get('en', pope_id.replace('-', ' ').title())
            doc_count = len(pope_documents[pope_id])
            
            pope_feeds_index['feeds'].append({
                'pope_id': pope_id,
                'pope_name': pope_name,
                'document_count': doc_count,
                'feed_url': f'/feed/pope-{pope_id}.json'
            })
    
    # Sort by document count descending
    pope_feeds_index['feeds'].sort(key=lambda x: x['document_count'], reverse=True)
    
    # Save index file
    index_file = feed_dir / 'index.json'
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(pope_feeds_index, f, indent=2, ensure_ascii=False)
    
    print(f"Created {index_file}")
    print(f"Generated {total_feeds} pope feeds")

def update_popes_with_document_counts(api_dir: Path):
    """Update popes.json with document counts and organized document structure."""
    print("Updating popes data with document information...")
    
    # Load current popes data
    popes_data = load_popes_data(api_dir)
    documents = load_all_documents(api_dir)
    
    # Group documents by pope
    pope_documents = group_documents_by_pope(documents)
    
    # Update each pope with their documents
    updated_popes = []
    
    for pope in popes_data.values():
        pope_id = pope['id']
        pope_docs = pope_documents.get(pope_id, [])
        
        # Group documents by type
        documents_by_type = group_documents_by_type(pope_docs)
        
        # Create organized document structure
        organized_documents = {}
        for doc_type, docs in documents_by_type.items():
            # Sort by date descending
            docs.sort(key=lambda x: parse_date(x.get('date', '')), reverse=True)
            organized_documents[doc_type] = [create_document_summary(doc) for doc in docs]
        
        # Update pope data
        pope['documents'] = organized_documents
        pope['document_count'] = len(pope_docs)
        pope['document_types'] = list(documents_by_type.keys())
        
        updated_popes.append(pope)
    
    # Sort popes by document count (descending) and then by reign start
    updated_popes.sort(key=lambda p: (
        -p.get('document_count', 0),  # Negative for descending
        parse_date(p.get('reign_start', ''))
    ))
    
    # Save updated popes data
    popes_file = api_dir / 'popes.json'
    with open(popes_file, 'w', encoding='utf-8') as f:
        json.dump(updated_popes, f, indent=2, ensure_ascii=False)
    
    print(f"Updated {popes_file} with document information")

if __name__ == '__main__':
    # Default API directory (relative to project root)
    api_dir = Path(__file__).parent.parent.parent / 'api'
    
    print("Creating pope-specific feeds...")
    create_pope_feeds_api(api_dir)
    
    print("\nUpdating popes data with document information...")
    update_popes_with_document_counts(api_dir)
    
    print("\nPope feeds generation complete!")