import pytest
from src.scrapers.anna_archive import AnnaArchiveScraper
from src.models.book import SearchIntent

class DummyClient:
    def __init__(self, pages):
        self.pages = pages
        self.calls = 0

    async def get(self, url: str) -> str:
        # emulate sequential pagination responses
        idx = min(self.calls, len(self.pages) - 1)
        self.calls += 1
        return self.pages[idx]

HTML_PAGE = """
<div class="h-[125]">
  <a href="/md5/0123456789abcdef0123456789abcdef">
    <h3>Book Title</h3>
    <div class="truncate italic">Author Name</div>
    <div class="text-xs">2023, 450 pages, PDF, 12.5 MB</div>
  </a>
</div>
"""

def test_md5_extraction():
    scraper = AnnaArchiveScraper()
    md5 = scraper._extract_md5("/md5/0123456789abcdef0123456789abcdef")
    assert md5 == "0123456789abcdef0123456789abcdef"

@pytest.mark.asyncio
async def test_search_parsing_basic():
    client = DummyClient([HTML_PAGE])
    scraper = AnnaArchiveScraper(http_client=client)
    intent = SearchIntent(query="test", max_results=5)
    results = await scraper.search(intent)
    assert len(results) == 1
    b = results[0]
    assert b.title == "Book Title"
    assert b.author == "Author Name"
    assert b.year == 2023
    assert b.pages == 450
    assert b.file_format == "PDF"
    assert b.filesize == "12.5 MB"

@pytest.mark.asyncio
async def test_error_handling_returns_partial():
    class ErrorClient(DummyClient):
        async def get(self, url: str) -> str:
            raise RuntimeError("network fail")

    scraper = AnnaArchiveScraper(http_client=ErrorClient([""]))
    intent = SearchIntent(query="x", max_results=10)
    # Should not raise, should return empty list
    results = await scraper.search(intent)
    assert results == []