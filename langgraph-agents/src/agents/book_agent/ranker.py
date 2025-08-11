from __future__ import annotations

from datetime import datetime
from typing import Iterable, Tuple

from ...models.book import BookInfo


def _parse_size_mb(size: str | None) -> float | None:
    if not size:
        return None
    try:
        value, unit = size.split()
        n = float(value)
        unit = unit.upper()
        if unit == "KB":
            return n / 1024
        if unit == "MB":
            return n
        if unit == "GB":
            return n * 1024
    except Exception:
        return None
    return None


def score_book(book: BookInfo, preferred_formats: Iterable[str] | None = None) -> Tuple[float, dict]:
    year = book.year or datetime.utcnow().year
    recency = (datetime.utcnow().year - year) / 10.0
    pref = {f.upper() for f in (preferred_formats or [])}
    fmt_score = 1.0 if (book.file_format or "").upper() in pref and pref else 0.5
    size_mb = _parse_size_mb(book.filesize)
    size_score = 1.0 if (size_mb is None or 1 <= size_mb <= 50) else 0.5
    score = (2.0 - recency) + fmt_score + size_score
    return score, {"recency": recency, "format": fmt_score, "size": size_score}


