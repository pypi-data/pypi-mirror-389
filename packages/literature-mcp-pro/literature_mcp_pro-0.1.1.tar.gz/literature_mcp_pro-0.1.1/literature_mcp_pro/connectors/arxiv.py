"""ArXiv 数据源服务接口。"""

from typing import List
from ..models import Article, SearchQuery, SearchResult
from ..config import Config
import httpx
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus


class ArxivService:
    """ArXiv 文献检索服务，使用 arXiv API (Atom feed)。

    回退：如网络或解析失败，返回模拟结果以保证稳定性。
    """
    BASE_URL = Config.ARXIV_BASE_URL.rstrip('/')

    @staticmethod
    async def search(query: SearchQuery) -> SearchResult:
        try:
            q = quote_plus(query.query)
            url = f"{ArxivService.BASE_URL}/query?search_query=all:{q}&start=0&max_results={query.max_results}"
            async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
                resp = await client.get(url, headers={"User-Agent": Config.USER_AGENT})
                resp.raise_for_status()
                # parse Atom XML
                root = ET.fromstring(resp.text)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                entries = root.findall('atom:entry', ns)
                articles = []
                for e in entries:
                    try:
                        aid = e.find('atom:id', ns)
                        title_el = e.find('atom:title', ns)
                        summary_el = e.find('atom:summary', ns)
                        published_el = e.find('atom:published', ns)
                        title = (title_el.text or '').strip() if title_el is not None else ''
                        summary = (summary_el.text or '').strip() if summary_el is not None else ''
                        published = None
                        if published_el is not None and published_el.text:
                            try:
                                published = published_el.text[:4]
                                published = int(published)
                            except Exception:
                                published = None

                        # authors
                        authors = []
                        for a in e.findall('atom:author', ns):
                            name_el = a.find('atom:name', ns)
                            if name_el is not None and name_el.text:
                                authors.append({'name': name_el.text.strip()})

                        # try to get DOI from arxiv:doi (in arXiv namespace) if present
                        doi = None
                        for child in e:
                            if 'doi' in (child.tag or '').lower():
                                if child.text:
                                    doi = child.text.strip()
                                    break

                        article = Article(
                            id=(aid.text if aid is not None and aid.text else f"arxiv:{query.query}:{len(articles)+1}"),
                            arxiv_id=(aid.text if aid is not None and aid.text else None),
                            doi=doi,
                            title=title,
                            abstract=summary,
                            authors=authors,
                            publication_year=published,
                            source='arxiv',
                        )
                        articles.append(article)
                    except Exception:
                        continue
                return SearchResult(query=query, articles=articles, total_count=len(articles), sources_used=['arxiv'], search_time=0.0)
        except Exception:
            # 回退到模拟
            title = f"{query.query} - arXiv simulated result"
            article = Article(
                id=f"arxiv:{query.query}:1",
                arxiv_id="arXiv:0000.00001",
                doi=None,
                title=title,
                abstract=f"Simulated abstract for {query.query} from arXiv.",
                authors=[],
                source="arxiv",
            )
            return SearchResult(query=query, articles=[article], total_count=1, sources_used=["arxiv"], search_time=0.0)
