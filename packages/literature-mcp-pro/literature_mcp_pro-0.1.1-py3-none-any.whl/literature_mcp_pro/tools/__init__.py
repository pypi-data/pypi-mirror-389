"""Tools package: AI analysis and search aggregation."""

# AI implementations live under `ai/` but are exposed here for compatibility.
from ..ai.summarizer import Summarizer
from ..ai.analyzer import TrendAnalyzer
from ..ai.recommender import Recommender
from .search import SearchTools

__all__ = ["Summarizer", "TrendAnalyzer", "Recommender", "SearchTools"]
