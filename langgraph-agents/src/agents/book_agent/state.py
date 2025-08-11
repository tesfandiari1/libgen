from __future__ import annotations

from typing import List, TypedDict

from ...models.book import BookInfo


class BookState(TypedDict):
    user_query: str
    search_results: List[BookInfo]
    ranked_books: List[BookInfo]
    selected_books: List[BookInfo]
    messages: List[str]


