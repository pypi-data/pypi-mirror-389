from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class Paper:
    """
    A class to represent a scientific paper with standardized fields.

    Attributes:
        title (str): Title of the paper.
        authors (List[str]): List of author names.
        abstract (Optional[str]): Abstract of the paper.
        doi (Optional[str]): DOI of the paper.
        publication_date (Optional[str]): Publication date (format: YYYY-MM-DD).
        provider_id (Optional[str]): Provider-specific ID (e.g., arXiv ID, Scopus ID).
        keywords (Optional[List[str]]): List of keywords.
        url (Optional[str]): URL to the paper.
        journal (Optional[str]): Journal or conference name.
        metadata (Optional[Dict[str, Any]]): Additional provider-specific metadata.
    """
    # --- Core bibliographic fields ---
    title: str
    authors: List[str] = field(default_factory=list)
    publication_date: Optional[int] = None
    provider_id: Optional[str] =None
    url: Optional[str] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    source: Optional[str] = None  # e.g. 'Scopus', 'Elsevier'
    keywords: List[str] = field(default_factory=list)

    # --- Extended metadata ---
    paper_id: Optional[str] = None  # surrogate PK (e.g., Scopus EID)
    doc_type: Optional[str] = None  # Article, Conference, Review…
    peer_reviewed: Optional[bool] = None
    cited_by: int = 0
    open_access: Optional[bool] = None

    # --- Screening / annotation fields ---
    screen_flag: Optional[str] = None  # include / exclude / pending
    screen_date: Optional[datetime] = None
    domain_id: Optional[int] = None  # FK → Domains
    pop_note: Optional[str] = None  # free-text notes

    
    def add_keyword(self, keyword: str) -> None:
        """Safely add a keyword if not already present."""
        if keyword not in self.keywords:
            self.keywords.append(keyword)



    @classmethod
    def is_recent(self, years: int = 5) -> bool:
        """Check if the paper was published within the last `years` years."""
        if not self.publication_year:
            return False
        current_year = datetime.now().year
        return (current_year - self.publication_year) <= years

    def to_dict(self) -> dict:
        """Serialize the paper metadata to a dictionary."""
        return {
            'title': self.title,
            'authors': self.authors,
            'publication_date': self.publication_date,
            'journal': self.journal,
            'doi': self.doi,
            'abstract': self.abstract,
            'source': self.source, 
            'keywords': self.keywords,
            'paper_id': self.paper_id,
            'doc_type': self.doc_type,
            'peer_reviewed': self.peer_reviewed,
            'cited_by': self.cited_by,
            'open_access': self.open_access,
            'screen_flag': self.screen_flag,
            'screen_date': self.screen_date.isoformat() if self.screen_date else None,
            'domain_id': self.domain_id,
            'pop_note': self.pop_note
        }


    def __str__(self) -> str:
        return f"Paper(title={self.title}, authors={self.authors}, doi={self.doi})"


