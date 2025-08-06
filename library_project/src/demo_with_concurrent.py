"""Working demo with concurrent downloads using mock data."""

import json
import logging
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from download_manager import DownloadManager
from config import CONFIG


def setup_logging():
    """Configure logging based on settings in config.py."""
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


def generate_mock_papers(query: str, count: int = 10) -> List[Dict]:
    """Generate mock paper data for testing."""
    topics = {
        "machine learning": [
            ("Deep Learning", "Ian Goodfellow, Yoshua Bengio, Aaron Courville", "2016", "19 MB"),
            ("Pattern Recognition and Machine Learning", "Christopher M. Bishop", "2006", "8 MB"),
            ("The Elements of Statistical Learning", "Trevor Hastie, Robert Tibshirani", "2009", "12 MB"),
            ("Machine Learning: A Probabilistic Perspective", "Kevin P. Murphy", "2012", "25 MB"),
            ("Understanding Machine Learning", "Shai Shalev-Shwartz, Shai Ben-David", "2014", "5 MB"),
            ("Hands-On Machine Learning", "Aurélien Géron", "2019", "15 MB"),
            ("Machine Learning Yearning", "Andrew Ng", "2018", "2 MB"),
            ("Introduction to Machine Learning", "Ethem Alpaydin", "2020", "10 MB"),
            ("Machine Learning: An Algorithmic Perspective", "Stephen Marsland", "2015", "6 MB"),
            ("Reinforcement Learning: An Introduction", "Richard S. Sutton, Andrew G. Barto", "2018", "7 MB"),
        ],
        "python": [
            ("Learning Python", "Mark Lutz", "2013", "8 MB"),
            ("Python Crash Course", "Eric Matthes", "2019", "4 MB"),
            ("Fluent Python", "Luciano Ramalho", "2015", "6 MB"),
            ("Effective Python", "Brett Slatkin", "2019", "3 MB"),
            ("Python Tricks", "Dan Bader", "2017", "2 MB"),
        ]
    }
    
    # Get papers for the query or use machine learning as default
    paper_list = topics.get(query.lower(), topics["machine learning"])
    
    papers = []
    for i, (title, author, year, size) in enumerate(paper_list[:count]):
        papers.append({
            "Title": title,
            "Author": author,
            "Year": year,
            "Publisher": "Mock Publisher",
            "Pages": str(random.randint(200, 800)),
            "Language": "English",
            "Size": size,
            "Extension": "pdf",
            "MD5": f"mock_md5_{i+1:03d}",
            # Mock download URLs - in real scenario these would be actual LibGen mirrors
            "Mirror_1": f"https://httpbin.org/bytes/{random.randint(1000, 5000)}",  # Returns random bytes
        })
    
    return papers


def main():
    """Main entry point with working concurrent downloads."""
    # Set up logging
    logger = setup_logging()
    logger.info("LibGen Paper Downloader - Demo with Concurrent Downloads")
    logger.info("=" * 60)
    
    # Create download manager
    download_manager = DownloadManager(max_workers=5)
    
    try:
        # Test query
        test_query = "machine learning"
        logger.info(f"Demo Mode: Simulating search for '{test_query}'")
        logger.info("-" * 60)
        
        # Generate mock results
        logger.info("Step 1: Generating mock search results...")
        time.sleep(1)  # Simulate search delay
        
        results = generate_mock_papers(test_query, count=10)
        
        if not results:
            logger.warning("No results found.")
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
        
        # Prepare papers for concurrent download
        logger.info("-" * 60)
        logger.info("Step 2: Preparing concurrent downloads (first 5 papers)...")
        
        # Create download list with mock URLs
        papers_to_download = []
        for paper in results[:5]:
            # Use httpbin.org for demo (returns random bytes)
            # In production, these would be actual LibGen download URLs
            mock_url = f"https://httpbin.org/bytes/{random.randint(1000, 10000)}"
            papers_to_download.append((paper, mock_url))
            logger.info(f"  ✓ Prepared: {paper.get('Title', 'Unknown')[:50]}")
        
        # Perform concurrent downloads
        logger.info("-" * 60)
        logger.info(f"Step 3: Starting concurrent downloads ({len(papers_to_download)} papers)...")
        logger.info(f"Using {download_manager.max_workers} concurrent workers")
        logger.info("")
        logger.info("Note: Using httpbin.org for demo downloads (small test files)")
        logger.info("")
        
        # Download papers concurrently
        download_results = download_manager.download_batch(
            papers_to_download,
            show_progress=True
        )
        
        # Display results
        logger.info("\nDownload Results:")
        logger.info("-" * 60)
        
        successful_count = 0
        failed_count = 0
        
        for paper_id, result in download_results.items():
            if result["success"]:
                successful_count += 1
                logger.info(f"✅ {result['title'][:50]}")
                if result["file_path"]:
                    file_path = Path(result["file_path"])
                    if file_path.exists():
                        file_size = file_path.stat().st_size
                        logger.info(f"   Saved to: {file_path.name} ({file_size:,} bytes)")
            else:
                failed_count += 1
                logger.info(f"❌ {result.get('title', 'Unknown')[:50]}")
                if "error" in result:
                    logger.info(f"   Error: {result['error'][:100]}")
        
        # Show download statistics
        logger.info("\n" + "=" * 60)
        logger.info("Download Statistics:")
        logger.info(f"  ✅ Successful: {successful_count}")
        logger.info(f"  ❌ Failed: {failed_count}")
        logger.info(f"  📁 Download folder: {download_manager.download_folder}")
        
        # Show status summary
        summary = download_manager.get_status_summary()
        logger.info("\nStatus Summary:")
        logger.info(f"  Completed: {summary['completed']}")
        logger.info(f"  Failed: {summary['failed']}")
        logger.info(f"  Queued: {summary['queued']}")
        logger.info(f"  Downloading: {summary['downloading']}")
        
        # List downloaded files
        downloaded_files = list(download_manager.download_folder.glob("*.pdf"))
        if downloaded_files:
            logger.info("\nDownloaded Files:")
            for file in downloaded_files[:5]:  # Show first 5
                logger.info(f"  📄 {file.name} ({file.stat().st_size:,} bytes)")
        
        logger.info("-" * 60)
        logger.info("✅ Concurrent download demo complete!")
        logger.info(f"Status saved to: {download_manager.status_file}")
        logger.info(f"Metadata saved to: {download_manager.metadata_file}")
        
        logger.info("\n" + "=" * 60)
        logger.info("DEMO NOTES:")
        logger.info("• This demo uses httpbin.org for test downloads")
        logger.info("• Real implementation would use actual LibGen mirrors")
        logger.info("• Concurrent downloads with ThreadPoolExecutor are working")
        logger.info("• Progress bars show individual and overall progress")
        logger.info("• Status tracking saves to JSON after each download")
        logger.info("• Rate limiting and retry logic are implemented")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.info("\nDownload interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        download_manager.close()
        logger.info("-" * 60)
        logger.info("Application shutdown complete")


if __name__ == "__main__":
    main()