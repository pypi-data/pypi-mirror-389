"""CrossRef 数据源服务接口。"""

from typing import List
from ..models import Article, SearchQuery, SearchResult
from ..config import Config
import httpx


class CrossRefService:
    """CrossRef 文献检索服务，使用 CrossRef REST API。回退到模拟实现以保持稳定性。"""
    BASE_URL = Config.CROSSREF_BASE_URL.rstrip('/')

    @staticmethod
    async def search(query: SearchQuery) -> SearchResult:
        try:
            params = {
                'query': query.query,
                'rows': query.max_results,
            }
            url = f"{CrossRefService.BASE_URL}/works"
            async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
                resp = await client.get(url, params=params, headers={"User-Agent": Config.USER_AGENT})
                resp.raise_for_status()
                data = resp.json()
                items = data.get('message', {}).get('items', [])
                articles = []
                for it in items:
                    try:
                        doi = it.get('DOI')
                        title_list = it.get('title', [])
                        title = title_list[0] if title_list else ''
                        abstract = it.get('abstract') or ''
                        # CrossRef abstract may be in HTML-like format; strip tags if present
                        if abstract and abstract.startswith('<'):
                            import re
                            abstract = re.sub(r'<[^>]+>', '', abstract)

                        authors = []
                        for a in it.get('author', []):
                            name = ''
                            if a.get('given') and a.get('family'):
                                name = f"{a.get('given')} {a.get('family')}"
                            elif a.get('name'):
                                name = a.get('name')
                            if name:
                                authors.append({'name': name})

                        pub_year = None
                        if 'issued' in it and it['issued'].get('date-parts'):
                            try:
                                pub_year = int(it['issued']['date-parts'][0][0])
                            except Exception:
                                pub_year = None

                        journal = None
                        container = it.get('container-title') or []
                        if container:
                            journal = {'name': container[0]}

                        art = Article(
                            id=(f"crossref:{doi}" if doi else f"crossref:{query.query}:{len(articles)+1}"),
                            doi=doi,
                            title=title,
                            abstract=abstract,
                            authors=authors,
                            journal=journal,
                            publication_year=pub_year,
                            source='crossref',
                        )
                        articles.append(art)
                    except Exception:
                        continue
                return SearchResult(query=query, articles=articles, total_count=len(articles), sources_used=['crossref'], search_time=0.0)
        except Exception:
            # 回退模拟
            title = f"{query.query} - CrossRef simulated result"
            article = Article(
                id=f"crossref:{query.query}:1",
                doi=f"10.0000/sim.{query.query}",
                title=title,
                abstract=f"Simulated abstract for {query.query} from CrossRef.",
                authors=[],
                source="crossref",
            )
            return SearchResult(query=query, articles=[article], total_count=1, sources_used=["crossref"], search_time=0.0)
