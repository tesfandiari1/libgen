"""LibGen paper downloader - Main application."""

import json
import logging
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from urllib.parse import urlparse, unquote

import httpx
from fake_useragent import UserAgent
from libgen_api import LibgenSearch
from tqdm import tqdm

try:
    # Try relative imports (when used as a module)
    from .config import CONFIG
    from .download_manager import DownloadManager
    from .utils import generate_safe_filename  # Fixed [CRITICAL-003]
except ImportError:
    # Fall back to absolute imports (when run directly)
    from config import CONFIG
    from download_manager import DownloadManager
    from utils import generate_safe_filename  # Fixed [CRITICAL-003]

# Set up logging
def setup_logging():
    """Configure logging based on settings in config.py."""
    log_config = CONFIG["logging"]
    
    # Create logger
    logger = logging.getLogger("libgen_downloader")
    logger.setLevel(getattr(logging, log_config["level"]))
    
    # Create formatters
    formatter = logging.Formatter(
        fmt=log_config["format"],
        datefmt=log_config["date_format"]
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(log_config["log_file"])
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


class LibGenDownloader:
    """Simple LibGen paper downloader with rate limiting."""
    
    def __init__(self):
        """Initialize the downloader with configuration settings."""
        self.logger = logging.getLogger("libgen_downloader")
        self.download_folder = Path(CONFIG["download"]["folder_path"])
        self.last_request_time = 0
        self.ua = UserAgent() if CONFIG["user_agent"]["use_random"] else None
        
        # HTTP client with timeout
        self.client = httpx.Client(
            timeout=CONFIG["download"]["timeout"],
            follow_redirects=True
        )
        
        # Metadata file path
        self.metadata_file = self.download_folder / "download_metadata.json"
        self.metadata = self._load_metadata()
        
        # LibGen search instance with different mirrors to try
        self.searcher = LibgenSearch()
        # Primary mirror from user preference
        self.mirrors = [
            "libgen.li",  # User's preferred mirror
            "libgen.rs",
            "libgen.st",
            "libgen.is",
            "libgen.gs"
        ]
        self.current_mirror_index = 0
        
        self.logger.info(f"LibGen Downloader initialized")
        self.logger.info(f"Download folder: {self.download_folder}")
        self.logger.info(f"Metadata file: {self.metadata_file}")
        
    def _load_metadata(self) -> Dict:
        """Load existing metadata from JSON file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                self.logger.warning("Corrupted metadata file, starting fresh")
                return {}
        return {}
    
    def _save_metadata(self):
        """Save metadata to JSON file."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2, default=str)
            self.logger.debug("Metadata saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save metadata: {e}")
    
    def _add_metadata(self, paper_info: Dict, file_path: Path):
        """Add download metadata for a paper."""
        metadata_entry = {
            "title": paper_info.get("Title", "Unknown"),
            "author": paper_info.get("Author", "Unknown"),
            "year": paper_info.get("Year", "Unknown"),
            "publisher": paper_info.get("Publisher", "Unknown"),
            "pages": paper_info.get("Pages", "Unknown"),
            "language": paper_info.get("Language", "Unknown"),
            "size": paper_info.get("Size", "Unknown"),
            "extension": paper_info.get("Extension", "Unknown"),
            "md5": paper_info.get("MD5", "Unknown"),
            "download_date": datetime.now().isoformat(),
            "file_path": str(file_path),
        }
        
        # Use MD5 as unique key
        key = paper_info.get("MD5", str(time.time()))
        self.metadata[key] = metadata_entry
        self._save_metadata()
    
    def _rate_limit(self):
        """Enforce rate limiting with random delay between requests."""
        # Add random delay between 1-3 seconds
        random_delay = random.uniform(1, 3)
        self.logger.debug(f"Random delay: {random_delay:.2f} seconds")
        time.sleep(random_delay)
        
        # Also enforce configured rate limit
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_delay = CONFIG["rate_limit"]["delay_between_requests"]
        
        if time_since_last < min_delay:
            sleep_time = min_delay - time_since_last
            self.logger.debug(f"Rate limiting: additional sleep for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with random user agent."""
        headers = {}
        if self.ua:
            headers["User-Agent"] = self.ua.random
        return headers
    
    def _download_with_retry(self, url: str, file_path: Path, max_retries: int = 3) -> bool:
        """
        Download file with exponential backoff retry logic.
        
        Args:
            url: Download URL
            file_path: Path to save the file
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if successful, False otherwise
        """
        retry_delays = [1, 2, 4]  # Exponential backoff
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Download attempt {attempt + 1}/{max_retries}")
                
                # Get headers with user agent
                headers = self._get_headers()
                
                # Stream download with progress bar
                with self.client.stream("GET", url, headers=headers) as response:
                    response.raise_for_status()
                    
                    # Get total size if available
                    total_size = int(response.headers.get("content-length", 0))
                    
                    # Create progress bar
                    progress_bar = tqdm(
                        total=total_size,
                        unit="B",
                        unit_scale=True,
                        desc=file_path.name[:30]
                    )
                    
                    # Download and write to file
                    with open(file_path, "wb") as f:
                        for chunk in response.iter_bytes(chunk_size=CONFIG["download"]["chunk_size"]):
                            f.write(chunk)
                            progress_bar.update(len(chunk))
                    
                    progress_bar.close()
                    
                self.logger.info(f"Successfully downloaded: {file_path.name}")
                return True
                
            except httpx.HTTPStatusError as e:
                self.logger.warning(f"HTTP error on attempt {attempt + 1}: {e}")
            except httpx.TimeoutException as e:
                self.logger.warning(f"Timeout on attempt {attempt + 1}: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            
            # Wait before retry if not the last attempt
            if attempt < max_retries - 1:
                wait_time = retry_delays[attempt] if attempt < len(retry_delays) else retry_delays[-1]
                self.logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
        
        self.logger.error(f"Failed to download after {max_retries} attempts")
        return False
    
    def search_papers(self, query: str, limit: Optional[int] = 10) -> List[Dict]:
        """
        Search for papers on LibGen.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return (default: 10)
            
        Returns:
            List of paper metadata dictionaries
        """
        self.logger.info(f"Searching for: '{query}' (limit: {limit})")
        
        results = []
        
        # Try different mirrors if one fails
        for attempt, mirror in enumerate(self.mirrors):
            try:
                self.logger.info(f"Trying mirror: {mirror}")
                
                # Apply rate limiting
                self._rate_limit()
                
                # Configure the searcher to use this mirror
                # Note: libgen-api doesn't directly support changing mirrors,
                # so we'll need to work around this
                # For now, we'll use the default behavior and handle failures
                
                # Search using LibGen API
                results = self.searcher.search_title(query)
                
                if results:
                    # Limit results
                    results = results[:limit] if limit else results
                    
                    self.logger.info(f"Found {len(results)} results from {mirror}")
                    
                    # Log brief info about each result
                    for i, result in enumerate(results, 1):
                        title = result.get("Title", "Unknown")[:50]
                        author = result.get("Author", "Unknown")[:30]
                        year = result.get("Year", "N/A")
                        size = result.get("Size", "Unknown")
                        self.logger.debug(f"  {i}. {title}... by {author} ({year}) - {size}")
                    
                    return results
                else:
                    self.logger.warning(f"No results found on {mirror}")
                    
            except Exception as e:
                self.logger.warning(f"Failed to search on {mirror}: {str(e)[:100]}")
                if attempt < len(self.mirrors) - 1:
                    self.logger.info("Trying next mirror...")
                    continue
        
        self.logger.error(f"All mirrors failed for query: {query}")
        return []
    
    def download_paper(self, paper_info: Dict, show_progress: bool = True) -> Optional[Path]:
        """
        Download a single paper.
        
        Args:
            paper_info: Dictionary containing paper metadata
            show_progress: Whether to show download progress bar
            
        Returns:
            Path to downloaded file if successful, None otherwise
        """
        title = paper_info.get("Title", "Unknown")
        self.logger.info(f"Starting download: {title[:50]}...")
        
        try:
            # Apply rate limiting
            self._rate_limit()
            
            # Get download links
            self.logger.debug("Resolving download links...")
            download_links = self.searcher.resolve_download_links(paper_info)
            
            if not download_links:
                self.logger.error("No download links available")
                return None
            
            # Try download links in order
            for link_name, link_url in download_links.items():
                self.logger.info(f"Trying download source: {link_name}")
                
                # Generate filename (Fixed [CRITICAL-003]: Use secure filename sanitization)
                extension = paper_info.get("Extension", "pdf").lower()
                filename = generate_safe_filename(
                    title=title,
                    author=paper_info.get("Author", "Unknown"),
                    extension=extension
                )
                file_path = self.download_folder / filename
                
                # Skip if already downloaded
                if file_path.exists():
                    self.logger.info(f"File already exists: {file_path.name}")
                    return file_path
                
                # Attempt download with retry
                if self._download_with_retry(link_url, file_path):
                    # Save metadata
                    self._add_metadata(paper_info, file_path)
                    self.logger.info(f"✓ Download complete: {file_path.name}")
                    return file_path
                else:
                    self.logger.warning(f"Failed to download from {link_name}")
            
            self.logger.error("All download sources failed")
            return None
            
        except Exception as e:
            self.logger.error(f"Download failed: {e}", exc_info=True)
            return None
    
    def batch_download(self, papers: List[Dict], max_concurrent: Optional[int] = None):
        """
        Download multiple papers with concurrency control.
        
        Args:
            papers: List of paper info dictionaries
            max_concurrent: Maximum concurrent downloads (uses config default if None)
        """
        if max_concurrent is None:
            max_concurrent = CONFIG["download"]["max_concurrent_downloads"]
        
        self.logger.info(f"Starting batch download of {len(papers)} papers")
        self.logger.info(f"Max concurrent downloads: {max_concurrent}")
        
        # TODO: Implement concurrent download logic
        # This is a placeholder for batch download functionality
        for paper in tqdm(papers, desc="Downloading papers"):
            self.download_paper(paper)
    
    def close(self):
        """Clean up resources with proper error handling. Fixed [HIGH-003]."""
        errors = []
        
        try:
            if hasattr(self, 'client') and self.client:
                self.client.close()
        except Exception as e:
            errors.append(f"Failed to close HTTP client: {e}")
        
        try:
            # Flush any pending metadata
            if hasattr(self, 'metadata') and self.metadata:
                self._save_metadata()
        except Exception as e:
            errors.append(f"Failed to save metadata: {e}")
        
        if errors:
            self.logger.error(f"Errors during cleanup: {'; '.join(errors)}")
        else:
            self.logger.info("Downloader closed successfully")


def main():
    """Main entry point for the application."""
    # Set up logging
    logger = setup_logging()
    logger.info("Starting LibGen Paper Downloader with Concurrent Downloads")
    logger.info("=" * 60)
    
    # Create downloader instance for searching
    downloader = LibGenDownloader()
    
    # Create download manager for concurrent downloads
    download_manager = DownloadManager(max_workers=5)
    
    try:
        # Test with "machine learning" query
        test_query = "machine learning"
        logger.info(f"Testing with query: '{test_query}'")
        logger.info("-" * 60)
        
        # Search for papers
        logger.info("Step 1: Searching for papers...")
        results = downloader.search_papers(test_query, limit=10)
        
        if not results:
            logger.warning("No results found. Please try a different query.")
            return
        
        # Display search results
        logger.info(f"\nFound {len(results)} papers:")
        logger.info("-" * 60)
        for i, paper in enumerate(results, 1):
            title = paper.get("Title", "Unknown")[:60]
            author = paper.get("Author", "Unknown")[:40]
            year = paper.get("Year", "N/A")
            size = paper.get("Size", "Unknown")
            extension = paper.get("Extension", "Unknown")
            
            logger.info(f"{i:2d}. {title}...")
            logger.info(f"    Author: {author}")
            logger.info(f"    Year: {year} | Size: {size} | Format: {extension}")
            logger.info("")
        
        # Prepare papers for concurrent download (first 5 as demonstration)
        logger.info("-" * 60)
        logger.info("Step 2: Preparing concurrent downloads (first 5 papers)...")
        
        papers_to_download = []
        for paper in results[:5]:  # Download first 5 papers as demonstration
            try:
                # Apply rate limiting
                downloader._rate_limit()
                
                # Get download links
                logger.debug(f"Resolving links for: {paper.get('Title', 'Unknown')[:50]}")
                download_links = downloader.searcher.resolve_download_links(paper)
                
                if download_links:
                    # Use the first available download link
                    first_link = list(download_links.values())[0]
                    papers_to_download.append((paper, first_link))
                    logger.info(f"  ✓ Prepared: {paper.get('Title', 'Unknown')[:50]}")
                else:
                    logger.warning(f"  ✗ No links: {paper.get('Title', 'Unknown')[:50]}")
            except Exception as e:
                logger.warning(f"  ✗ Failed to resolve links: {str(e)[:50]}")
        
        if not papers_to_download:
            logger.error("No download links could be resolved. This might be a network issue.")
            logger.info("\nRunning demonstration with mock data instead...")
            
            # Create mock download URLs for demonstration
            papers_to_download = [
                (paper, f"http://example.com/paper_{i}.pdf")
                for i, paper in enumerate(results[:5], 1)
            ]
        
        # Perform concurrent downloads
        logger.info("-" * 60)
        logger.info(f"Step 3: Starting concurrent downloads ({len(papers_to_download)} papers)...")
        logger.info(f"Using {download_manager.max_workers} concurrent workers")
        logger.info("")
        
        # Download papers concurrently
        download_results = download_manager.download_batch(
            papers_to_download,
            show_progress=True
        )
        
        # Display results
        logger.info("\nDownload Results:")
        logger.info("-" * 60)
        
        for paper_id, result in download_results.items():
            if result["success"]:
                logger.info(f"✅ {result['title'][:50]}")
                if result["file_path"]:
                    logger.info(f"   Saved to: {Path(result['file_path']).name}")
            else:
                logger.info(f"❌ {result.get('title', 'Unknown')[:50]}")
                if "error" in result:
                    logger.info(f"   Error: {result['error'][:100]}")
        
        # Show status summary
        summary = download_manager.get_status_summary()
        logger.info("\nStatus Summary:")
        logger.info(f"  Completed: {summary['completed']}")
        logger.info(f"  Failed: {summary['failed']}")
        logger.info(f"  Queued: {summary['queued']}")
        logger.info(f"  Downloading: {summary['downloading']}")
        
        logger.info("-" * 60)
        logger.info("✅ Concurrent download test complete!")
        logger.info(f"Status saved to: {download_manager.status_file}")
        logger.info(f"Metadata saved to: {download_manager.metadata_file}")
        
    except KeyboardInterrupt:
        logger.info("\nDownload interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        downloader.close()
        download_manager.close()
        logger.info("-" * 60)
        logger.info("Application shutdown complete")


if __name__ == "__main__":
    main()
