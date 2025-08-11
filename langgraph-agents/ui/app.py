import os
import asyncio
from typing import List, Dict, Any

import streamlit as st

# Ensure src is on path when running in container
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Add project root so `import src...` works
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents.book_agent import build_book_graph
from src.models.book import BookInfo


st.set_page_config(page_title="LangGraph Book Agent", layout="wide")
st.title("LangGraph Book Discovery")
st.caption("Enter a query like: 'Python programming 2020+ pdf'")


@st.cache_resource(show_spinner=False)
def get_graph():
    return build_book_graph()


def render_book_table(books: List[BookInfo]):
    if not books:
        st.info("No results yet.")
        return
    rows: List[Dict[str, Any]] = []
    for b in books:
        rows.append(
            {
                "Title": b.title,
                "Author": b.author or "Unknown",
                "Year": b.year or "",
                "Format": b.file_format or "",
                "Size": b.filesize or "",
                "MD5": b.md5,
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)


with st.sidebar:
    st.subheader("Settings")
    save_results = st.checkbox("Save top results to DB (agent default 10)", value=False)
    st.divider()
    api_set = bool(os.getenv("ANTHROPIC_API_KEY"))
    st.write(
        "Anthropic key: " + ("set" if api_set else "missing - set ANTHROPIC_API_KEY in .env")
    )


query = st.text_input("Your query", value="")
go = st.button("Run Agent", type="primary")


if "history" not in st.session_state:
    st.session_state.history = []


placeholder = st.empty()

if go and query.strip():
    async def run():
        graph = get_graph()
        state = {
            "user_query": query.strip(),
            "search_results": [],
            "ranked_books": [],
            "selected_books": [],
            "messages": [],
        }
        result = await graph.ainvoke(state)
        return result

    with st.spinner("Running agent..."):
        result_state = asyncio.run(run())
        st.session_state.history.append({
            "query": query.strip(),
            "result": result_state,
        })

if st.session_state.history:
    last = st.session_state.history[-1]
    messages = last["result"].get("messages", [])
    ranked = last["result"].get("ranked_books", [])
    selected = last["result"].get("selected_books", [])

    st.subheader("Agent Messages")
    for m in messages:
        st.code(m)

    st.subheader("Top Ranked")
    render_book_table(ranked)

    st.subheader("Selected (Top 10)")
    render_book_table(selected)


