from literature_mcp_pro.ai.summarizer import Summarizer
from literature_mcp_pro.ai.analyzer import TrendAnalyzer
from literature_mcp_pro.ai.recommender import Recommender
from literature_mcp_pro.models import Article


async def test_summarizer_truncates_abstract():
    long_abs = "a" * 300
    art = Article(id="a1", title="T1", abstract=long_abs, source="pubmed")
    s = await Summarizer.summarize(art)
    assert len(s) <= 200


async def test_trend_analyzer_counts_keywords():
    a1 = Article(id="1", title="Deep Learning in Medicine", abstract="deep learning applications", source="pubmed")
    a2 = Article(id="2", title="Deep Learning for Images", abstract="deep image deep", source="arxiv")
    result = await TrendAnalyzer.analyze_trends([a1, a2])
    assert "deep" in result.get("trend_keywords", [])
    assert result.get("total_articles") == 2


async def test_recommender_ranks_by_citation():
    a1 = Article(id="1", title="A", citation_count=5, source="pubmed")
    a2 = Article(id="2", title="B", citation_count=20, source="pubmed")
    recs = await Recommender.recommend([a1, a2], top_k=2)
    assert recs[0].id == "2"
