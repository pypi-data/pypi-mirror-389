"""Data models for literature management."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl


class Author(BaseModel):
    """Author model."""
    
    name: str = Field(..., description="Full name of the author")
    affiliation: Optional[str] = Field(None, description="Author's affiliation")
    email: Optional[str] = Field(None, description="Author's email")
    orcid: Optional[str] = Field(None, description="ORCID identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "affiliation": "MIT",
                "email": "john@mit.edu",
                "orcid": "0000-0001-2345-6789"
            }
        }


class Journal(BaseModel):
    """Journal model."""
    
    name: str = Field(..., description="Journal name")
    issn: Optional[str] = Field(None, description="ISSN")
    e_issn: Optional[str] = Field(None, description="Electronic ISSN")
    impact_factor: Optional[float] = Field(None, description="Impact factor")
    publisher: Optional[str] = Field(None, description="Publisher name")
    quartile: Optional[str] = Field(None, description="Journal quartile (Q1-Q4)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Nature",
                "issn": "0028-0836",
                "e_issn": "1476-4687",
                "impact_factor": 49.962,
                "publisher": "Springer Nature",
                "quartile": "Q1"
            }
        }


class Article(BaseModel):
    """Article model representing a research paper."""
    
    # Identifiers
    id: str = Field(..., description="Unique identifier")
    pmid: Optional[str] = Field(None, description="PubMed ID")
    pmcid: Optional[str] = Field(None, description="PubMed Central ID")
    doi: Optional[str] = Field(None, description="Digital Object Identifier")
    arxiv_id: Optional[str] = Field(None, description="ArXiv ID")
    
    # Basic information
    title: str = Field(..., description="Article title")
    abstract: Optional[str] = Field(None, description="Article abstract")
    authors: List[Author] = Field(default_factory=list, description="List of authors")
    
    # Publication details
    journal: Optional[Journal] = Field(None, description="Journal information")
    publication_date: Optional[datetime] = Field(None, description="Publication date")
    publication_year: Optional[int] = Field(None, description="Publication year")
    volume: Optional[str] = Field(None, description="Journal volume")
    issue: Optional[str] = Field(None, description="Journal issue")
    pages: Optional[str] = Field(None, description="Page numbers")
    
    # Content
    keywords: List[str] = Field(default_factory=list, description="Keywords")
    mesh_terms: List[str] = Field(default_factory=list, description="MeSH terms")
    
    # Metrics
    citation_count: Optional[int] = Field(None, description="Number of citations")
    reference_count: Optional[int] = Field(None, description="Number of references")
    
    # URLs
    url: Optional[HttpUrl] = Field(None, description="Article URL")
    pdf_url: Optional[HttpUrl] = Field(None, description="PDF URL")
    
    # Source information
    source: str = Field(..., description="Data source (pubmed, arxiv, etc.)")
    
    # Local management
    added_date: Optional[datetime] = Field(None, description="Date added to library")
    tags: List[str] = Field(default_factory=list, description="User-defined tags")
    notes: Optional[str] = Field(None, description="User notes")
    read_status: Optional[str] = Field("unread", description="Reading status")
    
    # AI-generated fields
    ai_summary: Optional[str] = Field(None, description="AI-generated summary")
    quality_score: Optional[float] = Field(None, description="Quality score (0-100)")
    relevance_score: Optional[float] = Field(None, description="Relevance score")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "PMC12345678",
                "pmid": "12345678",
                "doi": "10.1038/s41586-021-03819-2",
                "title": "Advances in Machine Learning for Medical Imaging",
                "abstract": "This paper presents...",
                "authors": [
                    {
                        "name": "John Doe",
                        "affiliation": "MIT"
                    }
                ],
                "publication_year": 2023,
                "citation_count": 150,
                "source": "pubmed",
                "keywords": ["machine learning", "medical imaging"],
                "quality_score": 85.5
            }
        }


class CitationNetwork(BaseModel):
    """Citation network model."""
    
    nodes: List[dict] = Field(..., description="Network nodes (articles)")
    edges: List[dict] = Field(..., description="Network edges (citations)")
    metrics: dict = Field(default_factory=dict, description="Network metrics")


class SearchQuery(BaseModel):
    """Search query model."""
    
    query: str = Field(..., description="Search query string")
    sources: List[str] = Field(
        default=["pubmed", "arxiv", "europepmc"],
        description="Data sources to search"
    )
    max_results: int = Field(20, description="Maximum number of results")
    start_date: Optional[datetime] = Field(None, description="Start date filter")
    end_date: Optional[datetime] = Field(None, description="End date filter")
    sort_by: str = Field("relevance", description="Sort order")
    filters: dict = Field(default_factory=dict, description="Additional filters")


class SearchResult(BaseModel):
    """Search result model."""
    
    query: SearchQuery = Field(..., description="Original query")
    articles: List[Article] = Field(..., description="List of articles")
    total_count: int = Field(..., description="Total number of results")
    sources_used: List[str] = Field(..., description="Data sources queried")
    search_time: float = Field(..., description="Search duration in seconds")
