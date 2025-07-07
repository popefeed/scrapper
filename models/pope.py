from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, List
from .vatican_metadata import LanguageNames, PopeMetadata, DocumentType
from .document_summary import DocumentSummary


@dataclass
class Pope:
    """Pope model with proper typing and structure"""
    id: str
    names: LanguageNames = field(default_factory=dict)
    full_name: Optional[str] = None  # Changed from full_names to single full_name
    reign_start: Optional[str] = None
    reign_end: Optional[str] = None
    image_url: Optional[str] = None  # Vatican website image URL
    local_image_path: Optional[str] = None  # Local saved image path
    coat_of_arms_url: Optional[str] = None  # Coat of arms image URL
    local_coat_of_arms_path: Optional[str] = None  # Local coat of arms path
    metadata: PopeMetadata = field(default_factory=lambda: {
        "vatican_urls": {},
        "documents_vatican_url_index": {}
    })
    documents: Dict[DocumentType, List[DocumentSummary]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert Pope to dictionary for JSON serialization, handling nested DocumentSummary objects."""
        result = asdict(self)
        
        # Handle nested DocumentSummary objects in the documents field
        if self.documents:
            for doc_type, doc_list in self.documents.items():
                if doc_list:
                    converted_docs = []
                    for doc in doc_list:
                        if hasattr(doc, 'to_dict'):
                            # DocumentSummary object - convert to dict
                            converted_docs.append(doc.to_dict())
                        else:
                            # Already a dict or other serializable type
                            converted_docs.append(doc)
                    result['documents'][doc_type] = converted_docs
        
        return result
