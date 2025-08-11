from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from .state import BookState
from .nodes import parse_intent, search_books, rank_books, filter_books, format_results


def build_book_graph():
    graph = StateGraph(BookState)
    graph.add_node("parse_intent", parse_intent)
    graph.add_node("search_books", search_books)
    graph.add_node("rank_books", rank_books)
    graph.add_node("filter_books", filter_books)
    graph.add_node("format_results", format_results)

    graph.add_edge(START, "parse_intent")
    graph.add_edge("parse_intent", "search_books")
    graph.add_edge("search_books", "rank_books")
    graph.add_edge("rank_books", "filter_books")
    graph.add_edge("filter_books", "format_results")
    graph.add_edge("format_results", END)
    return graph.compile()


