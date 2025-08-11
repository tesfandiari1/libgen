import sys, os, asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.book_agent import build_book_graph


async def main():
    graph = build_book_graph()
    user_query = "Find Python programming books from 2020+"
    state = {
        "user_query": user_query,
        "search_results": [],
        "ranked_books": [],
        "selected_books": [],
        "messages": [],
    }
    result = await graph.ainvoke(state)
    print(result["messages"][-1])


if __name__ == "__main__":
    asyncio.run(main())


