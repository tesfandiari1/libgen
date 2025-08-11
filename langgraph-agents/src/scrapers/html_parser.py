from selectolax.parser import HTMLParser as SelectoHTML
from bs4 import BeautifulSoup


class HTMLParser:
    """HTML parser with selectolax primary and BeautifulSoup fallback."""

    def __init__(self, html: str) -> None:
        self._html = html
        self._sel = SelectoHTML(html)
        self._bs: BeautifulSoup = None  # type: ignore[assignment]

    def _ensure_bs(self) -> BeautifulSoup:
        if self._bs is None:
            self._bs = BeautifulSoup(self._html, "lxml")
        return self._bs

    def extract_text(self) -> str:
        try:
            return self._sel.body.text(separator=" ").strip()
        except Exception:
            return self._ensure_bs().get_text(" ").strip()

    def extract_links(self) -> list[str]:
        links: list[str] = []
        try:
            for node in self._sel.css("a[href]"):
                href = node.attributes.get("href")
                if href:
                    links.append(href)
            return links
        except Exception:
            soup = self._ensure_bs()
            for a in soup.find_all("a", href=True):
                links.append(a.get("href"))
            return links

    def extract_by_css(self, selector: str) -> list[str]:
        results: list[str] = []
        try:
            for node in self._sel.css(selector):
                results.append(node.text(separator=" ").strip())
            return results
        except Exception:
            soup = self._ensure_bs()
            for el in soup.select(selector):
                results.append(el.get_text(" ").strip())
            return results


