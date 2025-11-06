"""MCP stdio tool server entrypoint.

This file attempts to register MCP tools with FastMCP if the package is
available. If not, it falls back to a minimal stdio-based MCP loop so the
tool can still be used locally via pipes.

Registered tools:
 - search_literature
 - summarize_article
 - analyze_trends
 - recommend_articles

Run: python main.py
"""
import asyncio
import json
import sys
from typing import Any

from literature_mcp_pro.tools.search import SearchTools
from literature_mcp_pro.tools.analysis import AnalysisTools
from literature_mcp_pro.models import SearchQuery, Article


async def search_literature(params: dict) -> dict:
    q = SearchQuery(**params)
    res = await SearchTools.search(q)
    return res.model_dump()


async def summarize_article(params: dict) -> dict:
    art = Article(**params)
    s = await AnalysisTools.summarize(art)
    return {"summary": s}


async def analyze_trends(params: dict) -> dict:
    articles = [Article(**a) for a in params.get("articles", [])]
    r = await AnalysisTools.analyze_trends(articles)
    return r


async def recommend_articles(params: dict) -> dict:
    articles = [Article(**a) for a in params.get("articles", [])]
    top_k = params.get("top_k", 5)
    recs = await AnalysisTools.recommend(articles, top_k)
    return {"recommendations": [a.model_dump() for a in recs]}


def register_with_fastmcp(loop):
    try:
        import fastmcp

        # Try several common server APIs on fastmcp to be compatible with
        # different fastmcp implementations.
        server = None
        if hasattr(fastmcp, "FastMCP"):
            server = fastmcp.FastMCP()
        elif hasattr(fastmcp, "MCPServer"):
            server = fastmcp.MCPServer()

        if server is None:
            # Unknown API, bail to stdio mode
            return False

        # Register the async callables; adapt to registration API if necessary
        register = getattr(server, "register", None)
        if callable(register):
            register("search_literature", search_literature)
            register("summarize_article", summarize_article)
            register("analyze_trends", analyze_trends)
            register("recommend_articles", recommend_articles)

            # Run server
            loop.run_until_complete(server.serve())
            return True
        return False
    except Exception:
        return False


async def stdio_loop():
    """A minimal stdio-based MCP-like loop.

    It expects JSON objects (one per line) with the shape:
      {"tool": "search_literature", "params": {...}}

    and prints a JSON response per line: {"ok": true, "result": ...}
    """
    dispatch = {
        "search_literature": search_literature,
        "summarize_article": summarize_article,
        "analyze_trends": analyze_trends,
        "recommend_articles": recommend_articles,
    }

    loop = asyncio.get_event_loop()
    reader = sys.stdin
    writer = sys.stdout

    while True:
        line = reader.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            tool = req.get("tool")
            params = req.get("params", {})
            fn = dispatch.get(tool)
            if not fn:
                resp = {"ok": False, "error": f"Unknown tool: {tool}"}
            else:
                result = loop.run_until_complete(fn(params))
                resp = {"ok": True, "result": result}
        except Exception as e:
            resp = {"ok": False, "error": str(e)}

        writer.write(json.dumps(resp, ensure_ascii=False) + "\n")
        writer.flush()


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Prefer fastmcp when available
    ok = register_with_fastmcp(loop)
    if not ok:
        # Fallback to stdio loop
        try:
            loop.run_until_complete(stdio_loop())
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
