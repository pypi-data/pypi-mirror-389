"""Connectors package: data source implementations (PubMed, arXiv, CrossRef)."""

from .pubmed import PubMedService
from .arxiv import ArxivService
from .crossref import CrossRefService

__all__ = ["PubMedService", "ArxivService", "CrossRefService"]
