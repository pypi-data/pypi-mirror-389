"""文献智能摘要模块（AI）。"""

from ..models import Article
from ..config import Config

class Summarizer:
    """AI驱动的文献摘要生成器（最小实现）。"""
    @staticmethod
    async def summarize(article: Article) -> str:
        # 最小实现：如果已有摘要则返回摘要的前200字符，否则返回标题
        if article.abstract:
            text = article.abstract.strip()
            return text if len(text) <= 200 else text[:197] + "..."
        return (article.title or "").strip()
