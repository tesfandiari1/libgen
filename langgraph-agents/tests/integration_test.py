from __future__ import annotations

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
import pandas as pd

from src.scrapers.anna_archive import AnnaArchiveScraper
from src.models.book import SearchIntent
from src.storage.database import Database


def main() -> None:
    load_dotenv()

    query = "Python programming"
    db = Database()
    scraper = AnnaArchiveScraper()

    # 1. Search
    results = asyncio.run(scraper.search(SearchIntent(query=query, max_results=10)))
    assert results and len(results) > 0, "Search returned no results"

    # 2-3. Save to DB
    saved = db.save_books(results)
    assert saved > 0, "No results saved to database"

    # 4. Retrieve from DB
    books = db.get_books(limit=5)
    assert books, "No books retrieved from database"

    # 5. Export to CSV
    export_path = os.getenv("INTEGRATION_EXPORT_PATH", "/app/data/integration_export.csv")
    Path(export_path).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(books).to_csv(export_path, index=False)
    assert Path(export_path).exists(), "CSV export failed"

    print(f"OK: results={len(results)} saved={saved} export={export_path}")


if __name__ == "__main__":
    main()


