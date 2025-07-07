"""
Vatican metadata type definitions
"""

from typing import Dict, List, Optional, TypedDict


class LanguageNames(TypedDict, total=False):
    """Language-specific names mapping"""
    en: Optional[str]
    es: Optional[str] 
    pt: Optional[str]
    it: Optional[str]
    fr: Optional[str]
    la: Optional[str]


class VaticanUrls(TypedDict, total=False):
    """Vatican URLs for different languages"""
    en: Optional[str]
    es: Optional[str]
    pt: Optional[str] 
    it: Optional[str]
    fr: Optional[str]
    la: Optional[str]


class DocumentMetadata(TypedDict):
    """Document metadata structure"""
    vatican_urls: VaticanUrls


class PopeMetadata(TypedDict):
    """Pope metadata structure"""
    vatican_urls: VaticanUrls
    documents_vatican_url_index: Dict[str, List[str]]


# Type aliases
DocumentType = str  # "encyclicals", "apostolic-letters", etc.
LanguageCode = str  # "en", "es", "pt", etc.