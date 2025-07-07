"""
DocumentSummary model - lightweight version for Pope documents list
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from .vatican_metadata import LanguageNames


@dataclass
class DocumentSummary:
    """Summary of a document for inclusion in Pope's documents list"""
    id: str
    pope_id: str
    type: str
    date: Optional[str]
    title: str
    excerpt: LanguageNames
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)