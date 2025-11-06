"""文献分析工具：摘要、趋势、推荐包装器。"""

from typing import List
from ..models import Article
from ..ai.analyzer import TrendAnalyzer
from ..ai.summarizer import Summarizer
from ..ai.recommender import Recommender

class AnalysisTools:
    """文献分析相关工具。"""
    @staticmethod
    async def summarize(article: Article) -> str:
        return await Summarizer.summarize(article)

    @staticmethod
    async def analyze_trends(articles: List[Article]) -> dict:
        return await TrendAnalyzer.analyze_trends(articles)

    @staticmethod
    async def recommend(articles: List[Article], top_k: int = 5) -> List[Article]:
        return await Recommender.recommend(articles, top_k)
