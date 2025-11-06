"""研究趋势分析模块（AI）。"""

from typing import List
from ..models import Article

class TrendAnalyzer:
    """AI驱动的研究趋势分析器（最小实现）。"""
    @staticmethod
    async def analyze_trends(articles: List[Article]) -> dict:
        # 简单实现：统计出现频率最高的词（来自标题和摘要），作为趋势关键词
        from collections import Counter
        import re

        counter = Counter()
        for a in articles:
            text = "".join(filter(None, [a.title or "", " ", a.abstract or ""]))
            # 小写并移除非字母数字字符
            tokens = re.findall(r"\b[a-zA-Z0-9]{3,}\b", text.lower())
            counter.update(tokens)

        common = [w for w, _ in counter.most_common(10)]
        return {"trend_keywords": common, "total_articles": len(articles)}
