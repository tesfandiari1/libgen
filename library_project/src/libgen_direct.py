"""Direct LibGen implementation using web scraping for libgen.li mirror."""

import json
import logging
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from urllib.parse import urljoin, quote

import httpx
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from tqdm import tqdm

try:
    from .config import CONFIG
    from .utils import generate_safe_filename  # Fixed [CRITICAL-003]
except ImportError:
    from config import CONFIG
    from utils import generate_safe_filename  # Fixed [CRITICAL-003]


class LibGenDirect:
    """Direct LibGen scraper for libgen.li mirror."""
    
    def __init__(self, base_url: str = "https://libgen.li"):
        """Initialize the direct LibGen scraper."""
        self.logger = logging.getLogger("libgen_downloader")
        self.base_url = base_url
        self.download_folder = Path(CONFIG["download"]["folder_path"])
        self.last_request_time = 0
        self.ua = UserAgent()
        
        # HTTP client with timeout
        # Fixed [CRITICAL-001]: Enable SSL verification for security
        self.client = httpx.Client(
            timeout=CONFIG["download"]["timeout"],
            follow_redirects=True,
            verify=True  # Always verify SSL certificates
        )
        
        # Metadata handling
        self.metadata_file = self.download_folder / "download_metadata.json"
        self.metadata = self._load_metadata()
        
        self.logger.info(f"LibGen Direct initialized with mirror: {base_url}")
    
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
            "title": paper_info.get("title", "Unknown"),
            "author": paper_info.get("author", "Unknown"),
            "year": paper_info.get("year", "Unknown"),
            "publisher": paper_info.get("publisher", "Unknown"),
            "pages": paper_info.get("pages", "Unknown"),
            "language": paper_info.get("language", "Unknown"),
            "size": paper_info.get("size", "Unknown"),
            "extension": paper_info.get("extension", "Unknown"),
            "md5": paper_info.get("md5", "Unknown"),
            "download_date": datetime.now().isoformat(),
            "file_path": str(file_path),
        }
        
        # Use MD5 as unique key
        key = paper_info.get("md5", str(time.time()))
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
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for papers on LibGen.li
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of paper metadata dictionaries
        """
        self.logger.info(f"Searching for: '{query}' on {self.base_url}")
        
        try:
            self._rate_limit()
            
            # Build search URL
            search_url = f"{self.base_url}/index.php"
            params = {
                "req": query,
                "res": str(limit),  # Results per page
                "column": "def",    # Search in default fields
                "sort": "year",
                "sortmode": "DESC"
            }
            
            # Make request
            headers = self._get_headers()
            response = self.client.get(search_url, params=params, headers=headers)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the results table
            tables = soup.find_all('table')
            if len(tables) < 3:
                self.logger.warning("No results table found")
                return []
            
            # The results are usually in the 3rd table
            results_table = tables[2]
            rows = results_table.find_all('tr')[1:]  # Skip header row
            
            results = []
            for row in rows[:limit]:
                cells = row.find_all('td')
                if len(cells) >= 9:
                    # Extract paper info from table cells
                    paper = {
                        "id": cells[0].text.strip(),
                        "author": cells[1].text.strip(),
                        "title": cells[2].text.strip(),
                        "publisher": cells[3].text.strip(),
                        "year": cells[4].text.strip(),
                        "pages": cells[5].text.strip(),
                        "language": cells[6].text.strip(),
                        "size": cells[7].text.strip(),
                        "extension": cells[8].text.strip(),
                    }
                    
                    # Get MD5 from the title link if available
                    title_link = cells[2].find('a')
                    if title_link and 'href' in title_link.attrs:
                        href = title_link['href']
                        md5_match = re.search(r'md5=([a-fA-F0-9]{32})', href)
                        if md5_match:
                            paper['md5'] = md5_match.group(1)
                        paper['details_url'] = urljoin(self.base_url, href)
                    
                    results.append(paper)
                    
                    self.logger.debug(f"Found: {paper['title'][:50]}... by {paper['author'][:30]}")
            
            self.logger.info(f"Found {len(results)} results")
            return results
            
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error during search: {e}")
        except Exception as e:
            self.logger.error(f"Search failed: {e}", exc_info=True)
        
        return []
    
    def get_download_links(self, paper: Dict) -> Dict[str, str]:
        """
        Get download links for a paper.
        
        Args:
            paper: Paper metadata dictionary
            
        Returns:
            Dictionary of mirror names to download URLs
        """
        if 'details_url' not in paper:
            self.logger.error("No details URL in paper info")
            return {}
        
        try:
            self._rate_limit()
            
            # Fetch the details page
            headers = self._get_headers()
            response = self.client.get(paper['details_url'], headers=headers)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find download links (usually in a table)
            download_links = {}
            
            # Look for mirror links
            for link in soup.find_all('a'):
                href = link.get('href', '')
                text = link.text.strip().lower()
                
                # Common download link patterns
                if any(pattern in href for pattern in ['get.php', 'ads.php', 'book/index.php']):
                    if 'libgen' in href or 'library' in href:
                        mirror_name = f"Mirror {len(download_links) + 1}"
                        download_links[mirror_name] = urljoin(self.base_url, href)
                        self.logger.debug(f"Found download link: {mirror_name}")
            
            return download_links
            
        except Exception as e:
            self.logger.error(f"Failed to get download links: {e}")
            return {}
    
    def download_with_retry(self, url: str, file_path: Path, max_retries: int = 3) -> bool:
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
    
    def download_paper(self, paper: Dict) -> Optional[Path]:
        """
        Download a paper.
        
        Args:
            paper: Paper metadata dictionary
            
        Returns:
            Path to downloaded file if successful, None otherwise
        """
        title = paper.get("title", "Unknown")
        self.logger.info(f"Starting download: {title[:50]}...")
        
        try:
            # Get download links
            download_links = self.get_download_links(paper)
            
            if not download_links:
                self.logger.error("No download links available")
                return None
            
            # Generate filename (Fixed [CRITICAL-003]: Use secure filename sanitization)
            extension = paper.get("extension", "pdf").lower()
            filename = generate_safe_filename(
                title=title,
                author=paper.get("author", "Unknown"),
                extension=extension
            )
            file_path = self.download_folder / filename
            
            # Skip if already downloaded
            if file_path.exists():
                self.logger.info(f"File already exists: {file_path.name}")
                return file_path
            
            # Try each download link
            for link_name, link_url in download_links.items():
                self.logger.info(f"Trying download source: {link_name}")
                
                if self.download_with_retry(link_url, file_path):
                    # Save metadata
                    self._add_metadata(paper, file_path)
                    self.logger.info(f"✓ Download complete: {file_path.name}")
                    return file_path
                else:
                    self.logger.warning(f"Failed to download from {link_name}")
            
            self.logger.error("All download sources failed")
            return None
            
        except Exception as e:
            self.logger.error(f"Download failed: {e}", exc_info=True)
            return None
    
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


def setup_logging():
    """Configure logging."""
    log_config = CONFIG["logging"]
    
    logger = logging.getLogger("libgen_downloader")
    logger.setLevel(getattr(logging, log_config["level"]))
    
    formatter = logging.Formatter(
        fmt=log_config["format"],
        datefmt=log_config["date_format"]
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    file_handler = logging.FileHandler(log_config["log_file"])
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def main():
    """Main entry point."""
    logger = setup_logging()
    logger.info("Starting LibGen Direct Downloader")
    logger.info("=" * 60)
    
    # Create downloader
    downloader = LibGenDirect(base_url="https://libgen.li")
    
    try:
        # Test search
        query = "machine learning"
        logger.info(f"Testing with query: '{query}'")
        
        results = downloader.search(query, limit=5)
        
        if not results:
            logger.warning("No results found")
            return
        
        # Display results
        logger.info(f"\nFound {len(results)} papers:")
        for i, paper in enumerate(results, 1):
            logger.info(f"{i}. {paper['title'][:60]}...")
            logger.info(f"   Author: {paper['author'][:40]}")
            logger.info(f"   Year: {paper['year']} | Size: {paper['size']} | Format: {paper['extension']}")
        
        # Download first paper
        logger.info("\nDownloading first paper...")
        first_paper = results[0]
        
        downloaded_file = downloader.download_paper(first_paper)
        
        if downloaded_file:
            logger.info(f"✅ Success! Downloaded to: {downloaded_file}")
        else:
            logger.error("❌ Download failed")
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        downloader.close()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    main()