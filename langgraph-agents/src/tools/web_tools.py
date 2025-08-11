from langchain_core.tools import tool

from ..scrapers.base_scraper import BaseHttpClient
from ..scrapers.html_parser import HTMLParser
from ..scrapers.anna_archive import AnnaArchiveScraper
from ..models.book import SearchIntent, BookInfo


_client = BaseHttpClient()


@tool("fetch_web_page", return_direct=False)
async def fetch_web_page(url: str, css: str | None = None) -> dict[str, object]:
    """Fetch a web page and return parsed content.

    Args:
        url: The URL to fetch.
        css: Optional CSS selector to extract elements' text.
    Returns:
        dict with keys: url, text, links, css_results
    """
    html = await _client.get(url)
    parser = HTMLParser(html)
    data: dict[str, object] = {
        "url": url,
        "text": parser.extract_text(),
        "links": parser.extract_links(),
    }
    if css:
        data["css_results"] = parser.extract_by_css(css)
    return data


@tool("anna_search_tool", return_direct=False)
async def anna_search_tool(query: str, min_year: int | None = None, formats: list[str] | None = None, max_results: int = 25) -> list[dict]:
    """Search Anna's Archive for books.

    Returns a list of BookInfo dictionaries compatible with LangGraph tools.
    """
    scraper = AnnaArchiveScraper(http_client=_client)
    intent = SearchIntent(query=query, min_year=min_year, formats=formats, max_results=max_results)
    results = await scraper.search(intent)
    # Return as list of dicts for tool serialization
    return [BookInfo.model_validate(r).model_dump() for r in results]

