"""Demo script for concurrent downloads with simulated data."""

import json
import logging
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Dict, List, Tuple

from tqdm import tqdm


def setup_logging():
    """Set up basic logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    return logging.getLogger("concurrent_demo")


class SimulatedDownloadManager:
    """Simulated download manager for demonstration."""
    
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    
    def __init__(self, max_workers: int = 5):
        """Initialize the simulated download manager."""
        self.logger = logging.getLogger("concurrent_demo")
        self.max_workers = max_workers
        self.status_lock = Lock()
        self.download_status = {}
        
        # Create downloads folder
        self.download_folder = Path(__file__).parent.parent / "downloads"
        self.download_folder.mkdir(parents=True, exist_ok=True)
        
        self.status_file = self.download_folder / "demo_status.json"
        
    def _update_status(self, paper_id: str, status: str, details: Dict = None):
        """Update status for a paper."""
        with self.status_lock:
            self.download_status[paper_id] = {
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "details": details or {}
            }
    
    def _simulate_download(self, paper_info: Dict, position: int) -> Tuple[str, bool]:
        """Simulate downloading a single paper."""
        paper_id = paper_info["id"]
        title = paper_info["title"][:40]
        size_mb = paper_info["size_mb"]
        
        try:
            # Update status to downloading
            self._update_status(paper_id, self.DOWNLOADING, {"title": title})
            
            # Random delay to simulate rate limiting
            time.sleep(random.uniform(0.5, 1.5))
            
            # Simulate download with progress bar
            # Simulate different speeds for different papers
            speed_mbps = random.uniform(1, 10)  # MB per second
            download_time = size_mb / speed_mbps
            
            # Create progress bar
            progress = tqdm(
                total=100,
                desc=f"[{position}] {title}",
                position=position,
                leave=False,
                bar_format="{desc}: {percentage:3.0f}%|{bar}| {elapsed}<{remaining}"
            )
            
            # Simulate download progress
            steps = 20
            for i in range(steps):
                # Simulate potential failure (5% chance)
                if random.random() < 0.05:
                    progress.close()
                    raise Exception("Simulated network error")
                
                time.sleep(download_time / steps)
                progress.update(100 / steps)
            
            progress.close()
            
            # Update status to completed
            self._update_status(paper_id, self.COMPLETED, {
                "title": title,
                "size_mb": size_mb,
                "download_time": f"{download_time:.1f}s"
            })
            
            return paper_id, True
            
        except Exception as e:
            # Update status to failed
            self._update_status(paper_id, self.FAILED, {
                "title": title,
                "error": str(e)
            })
            return paper_id, False
    
    def download_batch(self, papers: List[Dict]) -> Dict[str, bool]:
        """Download multiple papers concurrently."""
        results = {}
        total = len(papers)
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Starting concurrent download simulation")
        self.logger.info(f"Papers to download: {total}")
        self.logger.info(f"Max concurrent workers: {self.max_workers}")
        self.logger.info(f"{'='*60}\n")
        
        # Initialize all as queued
        for paper in papers:
            self._update_status(paper["id"], self.QUEUED, {"title": paper["title"][:40]})
        
        # Overall progress bar
        overall_progress = tqdm(
            total=total,
            desc="Overall Progress",
            position=0,
            bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} papers [{elapsed}<{remaining}]",
            colour="green"
        )
        
        # Use ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_paper = {}
            for idx, paper in enumerate(papers):
                # Position for individual progress bars
                position = (idx % self.max_workers) + 1
                
                future = executor.submit(self._simulate_download, paper, position)
                future_to_paper[future] = paper
            
            # Process completed downloads
            for future in as_completed(future_to_paper):
                paper = future_to_paper[future]
                
                try:
                    paper_id, success = future.result()
                    results[paper_id] = success
                    
                    if success:
                        self.logger.debug(f"✓ Completed: {paper['title'][:40]}")
                    else:
                        self.logger.debug(f"✗ Failed: {paper['title'][:40]}")
                    
                    overall_progress.update(1)
                    
                except Exception as e:
                    results[paper["id"]] = False
                    self.logger.error(f"Unexpected error: {e}")
                    overall_progress.update(1)
        
        overall_progress.close()
        
        # Clear progress bars area
        print("\n" * (self.max_workers + 2))
        
        # Save status to file
        with open(self.status_file, 'w') as f:
            json.dump(self.download_status, f, indent=2)
        
        return results


def main():
    """Main demo function."""
    logger = setup_logging()
    
    # Generate mock papers
    papers = []
    topics = ["Machine Learning", "Deep Learning", "Neural Networks", 
              "Computer Vision", "Natural Language Processing", "Robotics",
              "Data Science", "Artificial Intelligence", "Statistics",
              "Quantum Computing", "Blockchain", "Cybersecurity"]
    
    for i in range(12):  # Create 12 mock papers
        paper = {
            "id": f"paper_{i+1:03d}",
            "title": f"{random.choice(topics)}: Advanced Techniques and Applications (2024 Edition)",
            "author": f"Author {i+1}",
            "size_mb": random.randint(1, 50),  # Random size 1-50 MB
        }
        papers.append(paper)
    
    # Create download manager
    manager = SimulatedDownloadManager(max_workers=5)
    
    # Display papers to download
    logger.info("Papers to download:")
    for i, paper in enumerate(papers, 1):
        logger.info(f"  {i:2d}. {paper['title'][:50]}... ({paper['size_mb']} MB)")
    
    # Start concurrent downloads
    input("\nPress Enter to start concurrent downloads...")
    
    start_time = time.time()
    results = manager.download_batch(papers)
    elapsed_time = time.time() - start_time
    
    # Display results
    successful = sum(1 for success in results.values() if success)
    failed = len(results) - successful
    
    logger.info(f"\n{'='*60}")
    logger.info("Download Results:")
    logger.info(f"  ✅ Successful: {successful}/{len(results)}")
    logger.info(f"  ❌ Failed: {failed}/{len(results)}")
    logger.info(f"  ⏱️  Total time: {elapsed_time:.1f} seconds")
    logger.info(f"  📊 Average speed: {len(results)/elapsed_time:.1f} papers/second")
    logger.info(f"{'='*60}")
    
    # Show individual results
    logger.info("\nDetailed Status:")
    for paper_id, status_info in manager.download_status.items():
        status = status_info["status"]
        title = status_info["details"].get("title", "Unknown")
        
        if status == manager.COMPLETED:
            time_taken = status_info["details"].get("download_time", "N/A")
            logger.info(f"  ✅ {title} - Completed in {time_taken}")
        elif status == manager.FAILED:
            error = status_info["details"].get("error", "Unknown error")
            logger.info(f"  ❌ {title} - Failed: {error}")
    
    logger.info(f"\nStatus saved to: {manager.status_file}")
    logger.info("\n✨ Demo complete! This demonstrates concurrent downloading with:")
    logger.info("  • ThreadPoolExecutor for parallel downloads")
    logger.info("  • Individual progress bars for each download")
    logger.info("  • Overall progress tracking")
    logger.info("  • Status tracking (queued → downloading → completed/failed)")
    logger.info("  • JSON status persistence")


if __name__ == "__main__":
    main()