from literature_mcp_pro.models import SearchQuery
from literature_mcp_pro.tools.search import SearchTools


async def test_search_tools_aggregates():
    q = SearchQuery(query="covid", sources=["pubmed", "arxiv", "semantic"])
    res = await SearchTools.search(q)
    # total_count should reflect each service returning 1 in our simulated implementations
    assert res.total_count == 3
    # we should have at least 1 aggregated article
    assert len(res.articles) >= 1
    # check sources_used matches requested sources
    assert set(res.sources_used) == set(q.sources)
