"""Download Manager for concurrent paper downloads using ThreadPoolExecutor."""

import json
import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional, Tuple

import httpx
from fake_useragent import UserAgent
from tqdm import tqdm

try:
    from .config import CONFIG
    from .utils import generate_safe_filename  # Fixed [CRITICAL-003]
except ImportError:
    from config import CONFIG
    from utils import generate_safe_filename  # Fixed [CRITICAL-003]


class DownloadManager:
    """Manages concurrent downloads with ThreadPoolExecutor."""
    
    # Download status constants
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    
    def __init__(self, max_workers: int = None):
        """
        Initialize the DownloadManager.
        
        Args:
            max_workers: Maximum concurrent downloads (default from config)
        """
        self.logger = logging.getLogger("libgen_downloader")
        self.max_workers = max_workers or CONFIG["download"]["max_concurrent_downloads"]
        self.download_folder = Path(CONFIG["download"]["folder_path"])
        self.download_folder.mkdir(parents=True, exist_ok=True)
        
        # User agent for requests
        self.ua = UserAgent()
        
        # Thread-safe lock for status updates
        self.status_lock = Lock()
        
        # Status tracking
        self.status_file = self.download_folder / "download_status.json"
        self.download_status = self._load_status()
        
        # Metadata tracking
        self.metadata_file = self.download_folder / "download_metadata.json"
        self.metadata = self._load_metadata()
        
        # HTTP client (thread-safe)
        # Fixed [CRITICAL-001]: Enable SSL verification for security
        self.client = httpx.Client(
            timeout=CONFIG["download"]["timeout"],
            follow_redirects=True,
            verify=True  # Always verify SSL certificates
        )
        
        self.logger.info(f"DownloadManager initialized (max workers: {self.max_workers})")
    
    def _load_status(self) -> Dict:
        """Load download status from JSON file."""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                self.logger.warning("Corrupted status file, starting fresh")
        return {}
    
    def _save_status(self):
        """Save download status to JSON file (thread-safe). Fixed [HIGH-002]."""
        # Create a copy to avoid holding lock during I/O
        with self.status_lock:
            status_copy = self.download_status.copy()
        
        try:
            # Atomic write using temporary file
            temp_file = self.status_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(status_copy, f, indent=2, default=str)
            temp_file.replace(self.status_file)  # Atomic on POSIX
        except Exception as e:
            self.logger.error(f"Failed to save status: {e}")
    
    def _load_metadata(self) -> Dict:
        """Load metadata from JSON file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                self.logger.warning("Corrupted metadata file, starting fresh")
        return {}
    
    def _save_metadata(self):
        """Save metadata to JSON file (thread-safe). Fixed [HIGH-002]."""
        # Create a copy to avoid holding lock during I/O
        with self.status_lock:
            metadata_copy = self.metadata.copy()
        
        try:
            # Atomic write using temporary file
            temp_file = self.metadata_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(metadata_copy, f, indent=2, default=str)
            temp_file.replace(self.metadata_file)  # Atomic on POSIX
        except Exception as e:
            self.logger.error(f"Failed to save metadata: {e}")
    
    def _update_status(self, paper_id: str, status: str, details: Dict = None):
        """Update download status for a paper (thread-safe). Fixed [HIGH-002]."""
        with self.status_lock:
            if paper_id not in self.download_status:
                self.download_status[paper_id] = {}
            
            self.download_status[paper_id].update({
                "status": status,
                "last_updated": datetime.now().isoformat(),
                "details": details or {}
            })
        
        # Save outside the lock to reduce contention
        self._save_status()
    
    def _rate_limit(self):
        """Apply rate limiting with random delay."""
        # Random delay between 1-3 seconds
        delay = random.uniform(1, 3)
        time.sleep(delay)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with random user agent."""
        return {
            "User-Agent": self.ua.random,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
    
    def _generate_filename(self, paper_info: Dict) -> Path:
        """Generate a safe filename for the paper (Fixed [CRITICAL-003])."""
        title = paper_info.get("title", paper_info.get("Title", "Unknown"))
        author = paper_info.get("author", paper_info.get("Author", "Unknown"))
        extension = paper_info.get("extension", paper_info.get("Extension", "pdf")).lower()
        
        # Use secure filename generation
        filename = generate_safe_filename(title, author, extension)
        return self.download_folder / filename
    
    def _download_single(self, paper_info: Dict, download_url: str, 
                        progress_position: int = 0) -> Tuple[str, bool, Optional[Path]]:
        """
        Download a single paper.
        
        Args:
            paper_info: Paper metadata
            download_url: URL to download from
            progress_position: Position for tqdm progress bar
            
        Returns:
            Tuple of (paper_id, success, file_path)
        """
        paper_id = paper_info.get("md5", paper_info.get("MD5", str(time.time())))
        title = paper_info.get("title", paper_info.get("Title", "Unknown"))[:50]
        
        try:
            # Update status to downloading
            self._update_status(paper_id, self.DOWNLOADING, {"title": title})
            
            # Apply rate limiting
            self._rate_limit()
            
            # Generate filename
            file_path = self._generate_filename(paper_info)
            
            # Skip if already exists
            if file_path.exists():
                self.logger.info(f"File already exists: {file_path.name}")
                self._update_status(paper_id, self.COMPLETED, {
                    "title": title,
                    "file_path": str(file_path),
                    "skipped": True
                })
                return paper_id, True, file_path
            
            # Download with retry logic
            retry_delays = [1, 2, 4]  # Exponential backoff
            
            for attempt in range(3):
                try:
                    headers = self._get_headers()
                    
                    # Stream download with progress bar
                    with self.client.stream("GET", download_url, headers=headers) as response:
                        response.raise_for_status()
                        
                        # Get total size
                        total_size = int(response.headers.get("content-length", 0))
                        
                        # Create progress bar for this download
                        progress_bar = tqdm(
                            total=total_size,
                            unit="B",
                            unit_scale=True,
                            desc=f"[{progress_position}] {title[:30]}",
                            position=progress_position,
                            leave=False
                        )
                        
                        # Download and write
                        with open(file_path, "wb") as f:
                            for chunk in response.iter_bytes(chunk_size=CONFIG["download"]["chunk_size"]):
                                f.write(chunk)
                                progress_bar.update(len(chunk))
                        
                        progress_bar.close()
                    
                    # Success - save metadata
                    self.metadata[paper_id] = {
                        "title": paper_info.get("title", paper_info.get("Title", "Unknown")),
                        "author": paper_info.get("author", paper_info.get("Author", "Unknown")),
                        "year": paper_info.get("year", paper_info.get("Year", "Unknown")),
                        "size": paper_info.get("size", paper_info.get("Size", "Unknown")),
                        "extension": paper_info.get("extension", paper_info.get("Extension", "Unknown")),
                        "download_date": datetime.now().isoformat(),
                        "file_path": str(file_path),
                    }
                    self._save_metadata()
                    
                    # Update status
                    self._update_status(paper_id, self.COMPLETED, {
                        "title": title,
                        "file_path": str(file_path),
                        "attempts": attempt + 1
                    })
                    
                    self.logger.info(f"✓ Downloaded: {file_path.name}")
                    return paper_id, True, file_path
                    
                except Exception as e:
                    if attempt < 2:  # Not last attempt
                        wait_time = retry_delays[attempt]
                        self.logger.warning(f"Attempt {attempt + 1} failed for '{title}': {str(e)[:50]}")
                        time.sleep(wait_time)
                    else:
                        raise
            
        except Exception as e:
            self.logger.error(f"Failed to download '{title}': {e}")
            self._update_status(paper_id, self.FAILED, {
                "title": title,
                "error": str(e)[:200]
            })
            return paper_id, False, None
    
    def download_batch(self, papers_with_urls: List[Tuple[Dict, str]], 
                      show_progress: bool = True) -> Dict[str, Dict]:
        """
        Download multiple papers concurrently.
        
        Args:
            papers_with_urls: List of (paper_info, download_url) tuples
            show_progress: Whether to show progress bars
            
        Returns:
            Dictionary of results {paper_id: {"success": bool, "file_path": str}}
        """
        results = {}
        total_papers = len(papers_with_urls)
        
        if total_papers == 0:
            self.logger.warning("No papers to download")
            return results
        
        self.logger.info(f"Starting batch download of {total_papers} papers")
        self.logger.info(f"Using {self.max_workers} concurrent workers")
        
        # Initialize status for all papers
        for paper_info, _ in papers_with_urls:
            paper_id = paper_info.get("md5", paper_info.get("MD5", str(time.time())))
            self._update_status(paper_id, self.QUEUED, {
                "title": paper_info.get("title", paper_info.get("Title", "Unknown"))[:50]
            })
        
        # Overall progress bar
        if show_progress:
            overall_progress = tqdm(
                total=total_papers,
                desc="Overall Progress",
                position=0,
                bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} papers"
            )
        
        # Use ThreadPoolExecutor for concurrent downloads
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all download tasks
            future_to_paper = {}
            for idx, (paper_info, download_url) in enumerate(papers_with_urls):
                # Position for individual progress bars (offset by 1 for overall bar)
                position = (idx % self.max_workers) + 1 if show_progress else 0
                
                future = executor.submit(
                    self._download_single,
                    paper_info,
                    download_url,
                    position
                )
                future_to_paper[future] = paper_info
            
            # Process completed downloads
            for future in as_completed(future_to_paper):
                paper_info = future_to_paper[future]
                
                try:
                    paper_id, success, file_path = future.result()
                    results[paper_id] = {
                        "success": success,
                        "file_path": str(file_path) if file_path else None,
                        "title": paper_info.get("title", paper_info.get("Title", "Unknown"))
                    }
                    
                    if show_progress:
                        overall_progress.update(1)
                        
                except Exception as e:
                    paper_id = paper_info.get("md5", paper_info.get("MD5", str(time.time())))
                    self.logger.error(f"Unexpected error for paper {paper_id}: {e}")
                    results[paper_id] = {
                        "success": False,
                        "file_path": None,
                        "error": str(e)
                    }
                    
                    if show_progress:
                        overall_progress.update(1)
        
        if show_progress:
            overall_progress.close()
        
        # Print summary
        successful = sum(1 for r in results.values() if r["success"])
        failed = len(results) - successful
        
        self.logger.info("=" * 60)
        self.logger.info(f"Batch download complete:")
        self.logger.info(f"  ✓ Successful: {successful}")
        self.logger.info(f"  ✗ Failed: {failed}")
        self.logger.info(f"  Total: {len(results)}")
        self.logger.info("=" * 60)
        
        return results
    
    def get_status_summary(self) -> Dict[str, int]:
        """Get a summary of download statuses."""
        summary = {
            self.QUEUED: 0,
            self.DOWNLOADING: 0,
            self.COMPLETED: 0,
            self.FAILED: 0
        }
        
        for paper_status in self.download_status.values():
            status = paper_status.get("status", self.QUEUED)
            if status in summary:
                summary[status] += 1
        
        return summary
    
    def close(self):
        """Clean up resources with proper error handling. Fixed [HIGH-003]."""
        errors = []
        
        try:
            if hasattr(self, 'client') and self.client:
                self.client.close()
        except Exception as e:
            errors.append(f"Failed to close HTTP client: {e}")
        
        try:
            # Flush any pending metadata/status
            if hasattr(self, 'metadata') and self.metadata:
                self._save_metadata()
            if hasattr(self, 'download_status') and self.download_status:
                self._save_status()
        except Exception as e:
            errors.append(f"Failed to save data: {e}")
        
        if errors:
            self.logger.error(f"Errors during cleanup: {'; '.join(errors)}")
        else:
            self.logger.info("DownloadManager closed successfully")