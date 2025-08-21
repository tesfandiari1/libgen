from __future__ import annotations

from typing import List

import logging
from .state import BookState
from ...models.book import BookInfo, SearchIntent
from ...scrapers.anna_archive import AnnaArchiveScraper
from .ranker import score_book


log = logging.getLogger("book_agent")


async def parse_intent(state: BookState) -> BookState:
    q = state.get("user_query", "").strip()
    min_year = None
    import re
    m = re.search(r"(19\d{2}|20\d{2})\+?", q)
    if m:
        min_year = int(m.group(1))
    formats: List[str] = []
    for f in ["pdf", "epub", "mobi", "azw3"]:
        if f in q.lower():
            formats.append(f.upper())
    log.info("parse_intent: min_year=%s formats=%s", min_year, formats)
    return {
        "messages": [f"Parsed intent: min_year={min_year}, formats={formats}"],
        "selected_books": [],
    }


async def search_books(state: BookState) -> BookState:
    q = state["user_query"]
    min_year = None
    for m in state.get("messages", []):
        if "min_year=" in m:
            try:
                min_year = int(m.split("min_year=")[1].split(",")[0])
            except Exception:
                pass
    formats = []
    if state.get("messages"):
        msg = state["messages"][0]
        if "formats=[" in msg:
            inside = msg.split("formats=")[1].strip()
            inside = inside.strip("[]")
            formats = [s.strip(" ' ").upper() for s in inside.split(",") if s.strip()]
    scraper = AnnaArchiveScraper()
    intent = SearchIntent(query=q, min_year=min_year, formats=formats or None, max_results=25)
    log.info("search_books: query='%s' min_year=%s formats=%s", q, min_year, formats)
    results = await scraper.search(intent)
    log.info("search_books: got %d results", len(results))
    return {"search_results": results}


async def rank_books(state: BookState) -> BookState:
    formats_upper: List[str] = []
    if state.get("messages"):
        msg = state["messages"][0]
        if "formats=[" in msg:
            inside = msg.split("formats=")[1].strip()
            inside = inside.strip("[]")
            if inside:
                formats_upper = [s.strip(" ' ").upper() for s in inside.split(",") if s.strip()]
    books = [BookInfo.model_validate(b) if isinstance(b, dict) else b for b in state.get("search_results", [])]
    scored = []
    for b in books:
        s, _ = score_book(b, preferred_formats=formats_upper)
        scored.append((s, b))
    scored.sort(key=lambda x: x[0], reverse=True)
    log.info("rank_books: ranked %d items", len(scored))
    return {"ranked_books": [b for _, b in scored[:25]]}


async def filter_books(state: BookState) -> BookState:
    # Simple pass-through; could enforce min_year/formats again
    selected = state.get("ranked_books", [])[:10]
    log.info("filter_books: selected %d items", len(selected))
    return {"selected_books": selected}


async def format_results(state: BookState) -> BookState:
    lines: List[str] = []
    for i, b in enumerate(state.get("selected_books", []), 1):
        lines.append(f"{i}. {b.title} — {b.author or 'Unknown'} ({b.year or 'N/A'}) [{b.file_format or '?'} | {b.filesize or '?'}] md5:{b.md5}")
    new_msg = "\n".join(lines) if lines else "No results found."
    log.info("format_results: %d lines", len(lines))
    return {"messages": [*state.get("messages", []), new_msg]}


