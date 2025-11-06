"""相关文献推荐模块（AI）。"""

from typing import List
from ..models import Article

class Recommender:
    """AI驱动的文献推荐系统（最小实现）。"""
    @staticmethod
    async def recommend(articles: List[Article], top_k: int = 5) -> List[Article]:
        # 简单实现：按 citation_count 降序排序，返回 top_k
        def score(a: Article) -> int:
            return int(a.citation_count or 0)

        ranked = sorted(articles, key=score, reverse=True)
        return ranked[:top_k]
