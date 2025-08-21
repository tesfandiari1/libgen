from __future__ import annotations

import asyncio
import re
from typing import Iterable, Optional
import logging

from .base_scraper import BaseHttpClient
from .html_parser import HTMLParser
from ..models.book import BookInfo, SearchIntent


class AnnaArchiveScraper:
    """Anna's Archive HTML search scraper (search-only)."""

    BASE_URL = "https://annas-archive.org"
    SEARCH_PATH = "/search"

    def __init__(self, http_client: Optional[BaseHttpClient] = None) -> None:
        self._client = http_client or BaseHttpClient()

    async def search(self, intent: SearchIntent) -> list[dict]:
        log = logging.getLogger(self.__class__.__name__)
        results: list[dict] = []
        page = 1
        max_pages = max(1, min(10, (intent.max_results // 25) + 3))
        while len(results) < intent.max_results and page <= max_pages:
            url = self._compose_search_url(intent.query, page)
            try:
                log.info("scrape page=%d url=%s", page, url)
                html = await self._client.get(url)
            except Exception as e:
                log.warning("scrape error on page=%d: %s", page, e)
                # Continue to next page in case of transient error
                page += 1
                continue
            page_books = self._parse_results_bs(HTMLParser(html))
            page_books = self._filter_results(page_books, intent)
            results.extend([b.model_dump() for b in page_books])
            page += 1
            await asyncio.sleep(0)
        log.info("scrape complete total=%d (limit=%d)", len(results), intent.max_results)
        return results[: intent.max_results]

    def _compose_search_url(self, query: str, page: int) -> str:
        from urllib.parse import urlencode

        params = {"q": query}
        if page > 1:
            params["page"] = str(page)
        return f"{self.BASE_URL}{self.SEARCH_PATH}?{urlencode(params)}"

    def _parse_results_bs(self, parser: HTMLParser) -> list[BookInfo]:
        from bs4 import BeautifulSoup

        soup: BeautifulSoup = parser._ensure_bs()  # type: ignore[attr-defined]
        books: list[BookInfo] = []
        # Some result containers use Tailwind classes like `h-[125px]`, which include brackets.
        # Use an attribute substring selector to avoid needing CSS escapes.
        for c in soup.select('div[class*="h-["]'):
            title_el = c.select_one("h3")
            link_el = c.select_one('a[href*="/md5/"]')
            author_el = c.select_one("div.truncate.italic")
            meta_el = c.select_one("div.text-xs")

            title = title_el.get_text(strip=True) if title_el else None
            md5 = self._extract_md5(link_el.get("href")) if link_el else None
            author = author_el.get_text(strip=True) if author_el else None
            meta = meta_el.get_text(strip=True) if meta_el else ""
            year, pages, file_format, filesize = self._parse_meta(meta)
            if md5 and title:
                books.append(
                    BookInfo(
                        md5=md5,
                        title=title,
                        author=author,
                        year=year,
                        pages=pages,
                        file_format=file_format,
                        filesize=filesize,
                    )
                )
        return books

    def _parse_meta(self, meta: str) -> tuple[Optional[int], Optional[int], Optional[str], Optional[str]]:
        # Expected like: "2023, 450 pages, PDF, 12.5 MB"
        if not meta:
            return None, None, None, None
        year: Optional[int] = None
        pages: Optional[int] = None
        file_format: Optional[str] = None
        filesize: Optional[str] = None

        # Year (first 4-digit number)
        m = re.search(r"\b(1\d{3}|20\d{2})\b", meta)
        if m:
            try:
                year = int(m.group(1))
            except ValueError:
                year = None

        # Pages
        m = re.search(r"(\d+)\s*pages", meta, re.IGNORECASE)
        if m:
            try:
                pages = int(m.group(1))
            except ValueError:
                pages = None

        # Format: token that is not year/pages/size; we try to pick common formats
        known_formats = ["PDF", "EPUB", "MOBI", "AZW3", "DJVU", "CBZ", "CBR"]
        for fmt in known_formats:
            if re.search(rf"\b{re.escape(fmt)}\b", meta, re.IGNORECASE):
                file_format = fmt.upper()
                break

        # Size: like "12.5 MB" or "800 KB"
        m = re.search(r"(\d+(?:\.\d+)?)\s*(KB|MB|GB)", meta, re.IGNORECASE)
        if m:
            filesize = f"{m.group(1)} {m.group(2).upper()}"

        return year, pages, file_format, filesize

    def _extract_md5(self, href: Optional[str]) -> Optional[str]:
        if not href:
            return None
        # href like: "/md5/[MD5_HASH]" possibly with query params
        m = re.search(r"/md5/([a-fA-F0-9]{32})", href)
        return m.group(1).lower() if m else None

    def _filter_results(self, books: Iterable[BookInfo], intent: SearchIntent) -> list[BookInfo]:
        filtered: list[BookInfo] = []
        allowed = {f.upper() for f in (intent.formats or [])}
        for b in books:
            if intent.min_year is not None and b.year is not None and b.year < intent.min_year:
                continue
            if allowed and (b.file_format or "").upper() not in allowed:
                continue
            filtered.append(b)
        return filtered


