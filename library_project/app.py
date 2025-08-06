"""Minimal Streamlit interface for LibGen paper downloader."""

import streamlit as st
import pandas as pd
import time
from pathlib import Path
import sys
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple
import random

# Add src to path
sys.path.append('src')

# Import from existing modules
from src.download_manager import DownloadManager
from src.demo_with_concurrent import generate_mock_papers
from src.libgen_direct import LibGenDirect
from src.config import CONFIG
from src.utils import sanitize_filename  # Fixed [CRITICAL-003]

# Import stqdm for Streamlit-compatible progress bars
from stqdm import stqdm

# Set up logging
@st.cache_resource
def setup_logging():
    """Configure logging for the app."""
    logger = logging.getLogger("libgen_downloader")
    logger.setLevel(logging.INFO)
    
    # Only add handler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

# Initialize session state
def init_session_state():
    """Initialize session state variables."""
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'selected_papers' not in st.session_state:
        st.session_state.selected_papers = []
    if 'download_queue' not in st.session_state:
        st.session_state.download_queue = []
    if 'download_status' not in st.session_state:
        st.session_state.download_status = {}
    if 'download_manager' not in st.session_state:
        st.session_state.download_manager = DownloadManager(max_workers=3)
    if 'use_mock_data' not in st.session_state:
        st.session_state.use_mock_data = True  # Default to mock data for safety
    if 'active_downloads' not in st.session_state:
        st.session_state.active_downloads = {}

def search_papers(query: str, use_mock: bool = True, limit: int = 10) -> List[Dict]:
    """
    Search for papers using either mock data or real LibGen.
    
    Args:
        query: Search query
        use_mock: Whether to use mock data
        limit: Maximum number of results
    
    Returns:
        List of paper dictionaries
    """
    logger = setup_logging()
    
    if use_mock:
        logger.info(f"Using mock data for query: {query}")
        return generate_mock_papers(query, count=limit)
    else:
        try:
            logger.info(f"Searching LibGen for: {query}")
            libgen = LibGenDirect()
            results = libgen.search(query, limit=limit)
            # Normalize the keys to match mock data format
            normalized = []
            for r in results:
                normalized.append({
                    "Title": r.get("title", "Unknown"),
                    "Author": r.get("author", "Unknown"),
                    "Year": r.get("year", "N/A"),
                    "Publisher": r.get("publisher", "Unknown"),
                    "Pages": r.get("pages", "Unknown"),
                    "Language": r.get("language", "English"),
                    "Size": r.get("size", "Unknown"),
                    "Extension": r.get("extension", "pdf"),
                    "MD5": r.get("md5", f"md5_{len(normalized)}"),
                    "details_url": r.get("details_url", ""),
                })
            return normalized
        except Exception as e:
            logger.error(f"LibGen search failed: {e}")
            st.error(f"LibGen search failed. Using mock data instead.")
            return generate_mock_papers(query, count=limit)

def download_selected_papers(papers: List[Dict]):
    """Queue selected papers for download."""
    logger = setup_logging()
    download_manager = st.session_state.download_manager
    
    # Prepare papers for download
    papers_to_download = []
    for paper in papers:
        # For mock data, use httpbin.org for demo downloads
        if st.session_state.use_mock_data:
            # Generate a small random file size for demo
            file_size = random.randint(1000, 10000)
            download_url = f"https://httpbin.org/bytes/{file_size}"
        else:
            # For real LibGen, would need to get actual download URL
            # This would require additional scraping of the details page
            download_url = paper.get("Mirror_1", "")
        
        if download_url:
            papers_to_download.append((paper, download_url))
    
    if not papers_to_download:
        st.warning("No valid download URLs found for selected papers.")
        return {}
    
    # Start downloads
    logger.info(f"Starting download of {len(papers_to_download)} papers")
    results = {}
    
    # Create progress container
    progress_container = st.container()
    
    with progress_container:
        # Overall progress
        st.write(f"Downloading {len(papers_to_download)} papers...")
        overall_progress = st.progress(0)
        
        # Individual progress bars
        progress_bars = {}
        for idx, (paper, _) in enumerate(papers_to_download):
            title = paper.get("Title", "Unknown")[:50]
            progress_bars[title] = st.progress(0, text=f"Queued: {title}")
        
        # Use ThreadPoolExecutor for concurrent downloads
        completed = 0
        with ThreadPoolExecutor(max_workers=download_manager.max_workers) as executor:
            # Submit all download tasks
            future_to_paper = {}
            for paper, url in papers_to_download:
                future = executor.submit(
                    simulate_download,  # Using simulation for demo
                    paper,
                    url,
                    progress_bars[paper.get("Title", "Unknown")[:50]]
                )
                future_to_paper[future] = paper
            
            # Process completed downloads
            for future in as_completed(future_to_paper):
                paper = future_to_paper[future]
                paper_id = paper.get("MD5", str(time.time()))
                
                try:
                    success, file_path = future.result()
                    results[paper_id] = {
                        "success": success,
                        "file_path": str(file_path) if file_path else None,
                        "title": paper.get("Title", "Unknown")
                    }
                    
                    if success:
                        st.success(f"✓ Downloaded: {paper.get('Title', 'Unknown')[:50]}")
                except Exception as e:
                    logger.error(f"Download failed: {e}")
                    results[paper_id] = {
                        "success": False,
                        "error": str(e),
                        "title": paper.get("Title", "Unknown")
                    }
                    st.error(f"✗ Failed: {paper.get('Title', 'Unknown')[:50]}")
                
                completed += 1
                overall_progress.progress(completed / len(papers_to_download))
    
    return results

def simulate_download(paper: Dict, url: str, progress_bar) -> Tuple[bool, Path]:
    """
    Simulate a download with progress updates.
    For demo purposes - in production, would use actual download logic.
    """
    title = paper.get("Title", "Unknown")[:50]
    progress_bar.progress(0, text=f"Starting: {title}")
    
    # Simulate download progress
    for i in range(101):
        time.sleep(random.uniform(0.01, 0.03))  # Random delay for realism
        progress_bar.progress(i/100, text=f"Downloading: {title} ({i}%)")
    
    # Save to downloads folder
    download_folder = Path(CONFIG["download"]["folder_path"])
    download_folder.mkdir(exist_ok=True)
    
    # Create a dummy file for demo (Fixed [CRITICAL-003]: Use secure filename)
    safe_filename = sanitize_filename(f"{title}.pdf", max_length=255)
    file_path = download_folder / safe_filename
    file_path.write_text(f"Demo content for: {title}\nDownloaded at: {datetime.now()}")
    
    progress_bar.progress(1.0, text=f"Complete: {title}")
    return True, file_path

# Main Streamlit App
def main():
    st.title("📚 LibGen Paper Downloader")
    
    # Initialize session state
    init_session_state()
    
    # Setup logging
    logger = setup_logging()
    
    # Sidebar settings
    with st.sidebar:
        st.header("Settings")
        st.session_state.use_mock_data = st.checkbox(
            "Use Mock Data",
            value=st.session_state.use_mock_data,
            help="Use mock data for testing (recommended)"
        )
        
        max_results = st.number_input(
            "Max Results",
            min_value=5,
            max_value=50,
            value=10,
            step=5
        )
        
        st.divider()
        
        # Download status
        if st.session_state.download_status:
            st.header("Recent Downloads")
            for paper_id, status in list(st.session_state.download_status.items())[-5:]:
                if status.get("success"):
                    st.success(f"✓ {status.get('title', 'Unknown')[:30]}")
                else:
                    st.error(f"✗ {status.get('title', 'Unknown')[:30]}")
    
    # Main content
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "Search Query",
            placeholder="Enter search terms (e.g., 'machine learning', 'python')",
            key="search_input"
        )
    
    with col2:
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
    
    # Perform search
    if search_button and search_query:
        with st.spinner("Searching..."):
            results = search_papers(
                search_query,
                use_mock=st.session_state.use_mock_data,
                limit=max_results
            )
            st.session_state.search_results = results
            st.session_state.selected_papers = []  # Reset selection
            
            if results:
                st.success(f"Found {len(results)} results")
            else:
                st.warning("No results found")
    
    # Display results
    if st.session_state.search_results:
        st.divider()
        st.subheader("Search Results")
        
        # Create dataframe for display
        df_data = []
        for idx, paper in enumerate(st.session_state.search_results):
            df_data.append({
                "Select": False,
                "Title": paper.get("Title", "Unknown")[:60],
                "Author": paper.get("Author", "Unknown")[:40],
                "Year": paper.get("Year", "N/A"),
                "Size": paper.get("Size", "Unknown"),
                "Type": paper.get("Extension", "pdf"),
                "_index": idx
            })
        
        # Display as editable dataframe with checkboxes
        edited_df = st.data_editor(
            pd.DataFrame(df_data),
            column_config={
                "Select": st.column_config.CheckboxColumn(
                    "Select",
                    help="Select papers to download",
                    default=False,
                ),
                "Title": st.column_config.TextColumn(
                    "Title",
                    width="large",
                ),
                "Author": st.column_config.TextColumn(
                    "Author",
                    width="medium",
                ),
            },
            disabled=["Title", "Author", "Year", "Size", "Type", "_index"],
            hide_index=True,
            use_container_width=True,
            key="results_table"
        )
        
        # Get selected papers
        selected_indices = edited_df[edited_df["Select"] == True]["_index"].tolist()
        selected_papers = [st.session_state.search_results[i] for i in selected_indices]
        
        if selected_papers:
            st.info(f"Selected {len(selected_papers)} paper(s) for download")
            
            if st.button(f"⬇️ Download Selected ({len(selected_papers)} papers)", type="primary"):
                st.divider()
                st.subheader("Download Progress")
                
                # Start downloads
                download_results = download_selected_papers(selected_papers)
                
                # Update session state
                st.session_state.download_status.update(download_results)
                
                # Summary
                successful = sum(1 for r in download_results.values() if r.get("success"))
                failed = len(download_results) - successful
                
                st.divider()
                if successful > 0:
                    st.success(f"✓ Successfully downloaded {successful} paper(s)")
                if failed > 0:
                    st.error(f"✗ Failed to download {failed} paper(s)")

if __name__ == "__main__":
    main()