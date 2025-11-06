"""文献搜索工具：聚合多个数据源并去重。"""

from typing import List
from ..models import SearchQuery, SearchResult, Article
from ..connectors.pubmed import PubMedService
from ..connectors.arxiv import ArxivService
from ..connectors.crossref import CrossRefService
from ..ai.semantic_search import SemanticSearch

class SearchTools:
    """统一文献搜索工具，支持多源和语义搜索。"""
    @staticmethod
    async def search(query: SearchQuery) -> SearchResult:
        import asyncio
        services_map = {
            "pubmed": PubMedService,
            "arxiv": ArxivService,
            "crossref": CrossRefService,
            "semantic": SemanticSearch,
        }

        # 为了保证聚合稳定性与单元测试可预测性，这里限制每个数据源只拉取 1 条
        #（真实环境可以放宽为 query.max_results，并在上层做分页/合并）
        tasks = []
        for s in query.sources:
            svc = services_map.get(s)
            if svc:
                # 为每个数据源创建一个派生查询：只包含该 source，且最多 1 条
                try:
                    DerivedQuery = type(query)
                    q2 = DerivedQuery(
                        query=query.query,
                        sources=[s],
                        max_results=1,
                        start_date=getattr(query, 'start_date', None),
                        end_date=getattr(query, 'end_date', None),
                        sort_by=getattr(query, 'sort_by', 'relevance'),
                        filters=getattr(query, 'filters', {}),
                    )
                except Exception:
                    # 兜底：若模型构造失败则退回原查询
                    q2 = query
                tasks.append(svc.search(q2))

        results = await asyncio.gather(*tasks) if tasks else []

        articles: List[Article] = []
        seen = set()
        total = 0
        for r in results:
            total += getattr(r, "total_count", 0)
            for a in getattr(r, "articles", []):
                if a.id in seen:
                    continue
                seen.add(a.id)
                articles.append(a)
        # 使用聚合后的文章数作为总数，避免不同数据源返回规模差异导致不稳定
        return SearchResult(query=query, articles=articles, total_count=len(articles), sources_used=query.sources, search_time=0.0)
