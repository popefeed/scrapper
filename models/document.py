from dataclasses import dataclass, field, asdict
from typing import Dict, Optional
from .vatican_metadata import LanguageNames, DocumentMetadata, DocumentType
from .document_summary import DocumentSummary

@dataclass
class Document:
    """Full document model with proper typing and structure"""
    id: str
    pope_id: str
    type: DocumentType
    date: Optional[str] = None
    title: str = ""
    excerpt: LanguageNames = field(default_factory=dict)
    metadata: DocumentMetadata = field(default_factory=lambda: {"vatican_urls": {}, "raw_html": {}})

    def to_dict(self) -> Dict:
        """Convert Document to dictionary for JSON serialization."""
        return asdict(self)

    def to_summary(self) -> DocumentSummary:
        """Convert to DocumentSummary for inclusion in Pope's documents list."""
        return DocumentSummary(
            id=self.id,
            pope_id=self.pope_id,
            type=self.type,
            date=self.date,
            title=self.title,
            excerpt=self.excerpt
        )
    # titles: Dict[str, str] = field(default_factory=dict)
    # subtitles: Dict[str, str] = field(default_factory=dict)
    # available_languages: List[str] = field(default_factory=list)
    # excerpts: Dict[str, str] = field(default_factory=dict)
    # full_texts: Dict[str, str] = field(default_factory=dict)
    # vatican_urls: Dict[str, str] = field(default_factory=dict)
    # pdf_urls: Dict[str, str] = field(default_factory=dict)
    # local_pdfs: Dict[str, str] = field(default_factory=dict)
    # word_counts: Dict[str, int] = field(default_factory=dict)
    # reading_times: Dict[str, int] = field(default_factory=dict)
    # tags: Dict[str, List[str]] = field(default_factory=dict)
