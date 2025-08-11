from __future__ import annotations

import asyncio
import typer
import pandas as pd

from ..storage import Database
from ..scrapers.anna_archive import AnnaArchiveScraper
from ..models.book import SearchIntent
from ..agents.book_agent import build_book_graph


app = typer.Typer(help="Anna Agent CLI")


@app.command("search")
def cmd_search(query: str, limit: int = typer.Option(25, "--limit", "-n", min=1, max=200)) -> None:
    """Search books from Anna's Archive and store results."""
    db = Database()
    scraper = AnnaArchiveScraper()
    results = asyncio.run(scraper.search(SearchIntent(query=query, max_results=limit)))
    saved = db.save_books(results)
    db.save_session(query=query, result_count=len(results))
    typer.echo(f"Found {len(results)}, saved {saved}.")
    for i, b in enumerate(results[:10], 1):
        title = b.get("title")
        author = b.get("author") or "Unknown"
        year = b.get("year") or "N/A"
        fmt = b.get("file_format") or "?"
        size = b.get("filesize") or "?"
        typer.echo(f"{i}. {title} — {author} ({year}) [{fmt} | {size}]")


@app.command("list")
def cmd_list(limit: int = typer.Option(20, "--limit", "-n", min=1)) -> None:
    """List saved books."""
    db = Database()
    books = db.get_books(limit=limit)
    for i, b in enumerate(books, 1):
        year = b.get("year") or "N/A"
        fmt = b.get("format") or "?"
        size = b.get("size") or "?"
        typer.echo(f"{i}. {b['title']} — {b.get('author') or 'Unknown'} ({year}) [{fmt} | {size}] md5:{b['md5']}")


@app.command("export")
def cmd_export(path: str) -> None:
    """Export saved books to CSV."""
    db = Database()
    books = db.get_books(limit=10000)
    df = pd.DataFrame(books)
    if not df.empty:
        df.to_csv(path, index=False)
        typer.echo(f"Exported {len(df)} books to {path}")
    else:
        typer.echo("No books to export.")


@app.command("agent")
def cmd_agent(query: str, save: bool = typer.Option(False, "--save/--no-save")) -> None:
    """Run the LangGraph book discovery agent with a natural-language query.

    Example:
      anna agent "Find Python programming books from 2020+" --save
    """
    graph = build_book_graph()
    initial_state = {
        "user_query": query,
        "search_results": [],
        "ranked_books": [],
        "selected_books": [],
        "messages": [],
    }
    result = asyncio.run(graph.ainvoke(initial_state))
    output = (result.get("messages") or [""])[-1]
    typer.echo(output)

    if save:
        db = Database()
        selected = result.get("selected_books") or []
        saved = db.save_books(selected)
        db.save_session(query=query, result_count=len(selected))
        typer.echo(f"Saved {saved} selected books to database.")

