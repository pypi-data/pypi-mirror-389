from literature_mcp_pro.connectors.pubmed import PubMedService
from literature_mcp_pro.models import SearchQuery


async def test_pubmed_search_returns_article():
    q = SearchQuery(query="machine learning")
    res = await PubMedService.search(q)
    # 真实接口或回退均可能返回 >=1 条；不强制为 1 条
    assert len(res.articles) >= 1
    assert res.total_count >= 1
