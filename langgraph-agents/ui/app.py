import os
import asyncio
from typing import List, Dict, Any
from datetime import datetime

import streamlit as st
import pandas as pd

# Ensure src is on path when running in container
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.logging import configure_logging, get_recent_logs
from src.agents.book_agent import build_book_graph
from src.models.book import BookInfo, SearchIntent
from src.scrapers.anna_archive import AnnaArchiveScraper
from src.storage.database import Database

configure_logging()
st.set_page_config(page_title="LangGraph Book Agent", layout="wide", page_icon="📚")
st.title("📚 LangGraph Book Discovery")
st.caption("Search, discover, and manage your book collection")

# Initialize resources
@st.cache_resource(show_spinner=False)
def get_graph():
    return build_book_graph()

@st.cache_resource(show_spinner=False)
def get_database():
    return Database()

@st.cache_resource(show_spinner=False)
def get_scraper():
    return AnnaArchiveScraper()

def render_book_table(books: List[Any], show_actions: bool = False):
    if not books:
        st.info("No results to display.")
        return

    rows: List[Dict[str, Any]] = []
    for b in books:
        if isinstance(b, dict):
            rows.append({
                "Title": b.get("title", ""),
                "Author": b.get("author") or "Unknown",
                "Year": b.get("year") or "",
                "Format": b.get("format") or b.get("file_format") or "",
                "Size": b.get("size") or b.get("filesize") or "",
                "MD5": b.get("md5", ""),
            })
        else:
            rows.append({
                "Title": b.title,
                "Author": b.author or "Unknown",
                "Year": b.year or "",
                "Format": b.file_format or "",
                "Size": b.filesize or "",
                "MD5": b.md5,
            })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True, height=400)
    return df

# Sidebar configuration
with st.sidebar:
    st.subheader("⚙️ Configuration")

    api_set = bool(os.getenv("ANTHROPIC_API_KEY"))
    if api_set:
        st.success("✅ Anthropic API Key configured")
    else:
        st.error("❌ Missing ANTHROPIC_API_KEY in .env")

    st.divider()

    st.subheader("📊 Database Stats")
    db = get_database()
    book_count = len(db.get_books(limit=10000))
    st.metric("Total Books Saved", book_count)

# Main interface with tabs
tab1, tab2, tab3, tab4 = st.tabs(["🤖 AI Agent Search", "🔍 Direct Search", "📚 Saved Books", "💾 Export"])
with st.expander("🧰 Live Logs (last 200 lines)", expanded=False):
    refresh_logs = st.button("Refresh Logs", key="refresh_logs")
    if refresh_logs:
        st.session_state.get("_noop", 0)
        st.rerun()
    logs = get_recent_logs(limit=200)
    if logs:
        st.code("\n".join(logs))
    else:
        st.caption("No logs captured yet. Initiate a search or agent run.")

# Tab 1: AI Agent Search
with tab1:
    st.subheader("AI-Powered Book Discovery")
    st.write("Use natural language to find books. The agent will parse your intent and search intelligently.")

    col1, col2 = st.columns([3, 1])
    with col1:
        agent_query = st.text_input(
            "Natural language query",
            placeholder="e.g., 'Find Python programming books from 2020+ in PDF format'",
            key="agent_query"
        )
    with col2:
        save_agent_results = st.checkbox("Auto-save results", value=True, key="agent_save")

    if st.button("🚀 Run AI Agent", type="primary", key="agent_run"):
        if agent_query.strip():
            async def run_agent():
                graph = get_graph()
                state = {
                    "user_query": agent_query.strip(),
                    "search_results": [],
                    "ranked_books": [],
                    "selected_books": [],
                    "messages": [],
                }
                result = await graph.ainvoke(state)
                return result

            with st.spinner("🤖 Agent processing..."):
                result_state = asyncio.run(run_agent())

                # Display agent messages
                messages = result_state.get("messages", [])
                if messages:
                    with st.expander("Agent Processing Log", expanded=True):
                        for msg in messages:
                            st.code(msg)

                # Display results
                selected = result_state.get("selected_books", [])
                if selected:
                    st.success(f"Found {len(selected)} books!")
                    df = render_book_table(selected)

                    # Save if requested
                    if save_agent_results:
                        db = get_database()
                        saved = db.save_books(selected)
                        db.save_session(query=agent_query.strip(), result_count=len(selected))
                        st.info(f"✅ Saved {saved} new books to database")
                else:
                    st.warning("No books found matching your query.")
        else:
            st.error("Please enter a search query")

# Tab 2: Direct Search
with tab2:
    st.subheader("Direct Anna's Archive Search")
    st.write("Search directly with specific parameters")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        direct_query = st.text_input("Search query", key="direct_query")
    with col2:
        enable_min_year = st.checkbox("Set Min. Year", value=False, key="enable_min_year")
        default_year = 2000
        min_year = st.number_input("Min. Year", min_value=1900, max_value=2025, value=default_year, key="min_year") if enable_min_year else None
    with col3:
        max_results = st.slider("Max Results", 5, 100, 25, key="max_results")

    formats = st.multiselect(
        "File Formats",
        ["PDF", "EPUB", "MOBI", "AZW3", "DJVU"],
        key="formats"
    )

    if st.button("🔍 Search", type="primary", key="direct_search"):
        if direct_query.strip():
            async def run_search():
                scraper = get_scraper()
                intent = SearchIntent(
                    query=direct_query.strip(),
                    min_year=min_year if min_year else None,
                    formats=formats if formats else None,
                    max_results=max_results
                )
                return await scraper.search(intent)

            with st.spinner(f"Searching for '{direct_query}'..."):
                results = asyncio.run(run_search())

                if results:
                    st.success(f"Found {len(results)} books!")
                    df = render_book_table(results)

                    # Save button
                    if st.button("💾 Save Results to Database", key="save_direct"):
                        db = get_database()
                        saved = db.save_books(results)
                        db.save_session(query=direct_query.strip(), result_count=len(results))
                        st.success(f"✅ Saved {saved} new books to database")
                else:
                    st.warning("No books found.")
        else:
            st.error("Please enter a search query")

# Tab 3: Saved Books
with tab3:
    st.subheader("Browse Saved Books")

    col1, col2 = st.columns([3, 1])
    with col1:
        limit = st.slider("Number of books to display", 10, 500, 50, key="saved_limit")
    with col2:
        if st.button("🔄 Refresh", key="refresh_saved"):
            st.rerun()

    db = get_database()
    saved_books = db.get_books(limit=limit)

    if saved_books:
        st.info(f"Showing {len(saved_books)} most recently added books")
        df = render_book_table(saved_books)
    else:
        st.warning("No books saved yet. Use the search tabs to find and save books.")

# Tab 4: Export
with tab4:
    st.subheader("Export Book Collection")
    st.write("Export your saved books to CSV format")

    export_format = st.selectbox("Export Format", ["CSV", "JSON"], key="export_format")

    col1, col2 = st.columns([2, 1])
    with col1:
        export_path = st.text_input(
            "Export filename",
            value=f"books_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            key="export_path"
        )
    with col2:
        export_limit = st.number_input("Max books to export", min_value=1, max_value=10000, value=1000, key="export_limit")

    if st.button("📥 Export Books", type="primary", key="export_books"):
        db = get_database()
        books = db.get_books(limit=export_limit)

        if books:
            df = pd.DataFrame(books)

            if export_format == "CSV":
                csv = df.to_csv(index=False)
                st.download_button(
                    label=f"⬇️ Download {len(books)} books as CSV",
                    data=csv,
                    file_name=export_path,
                    mime="text/csv"
                )
            else:  # JSON
                json_str = df.to_json(orient="records", indent=2)
                st.download_button(
                    label=f"⬇️ Download {len(books)} books as JSON",
                    data=json_str,
                    file_name=export_path.replace(".csv", ".json"),
                    mime="application/json"
                )

            st.success(f"✅ Prepared {len(books)} books for download")
        else:
            st.warning("No books to export. Save some books first!")

    # Show export preview
    if st.checkbox("Preview export data", key="preview_export"):
        db = get_database()
        preview_books = db.get_books(limit=10)
        if preview_books:
            st.write("Preview (first 10 books):")
            render_book_table(preview_books)
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

from src.utils.logging import configure_logging
from src.agents.book_agent import build_book_graph
from src.models.book import BookInfo


configure_logging()
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


