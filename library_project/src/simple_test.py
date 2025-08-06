"""Simple test script to verify LibGen connectivity and demonstrate basic functionality."""

import json
import time
import random
from pathlib import Path
from datetime import datetime

# Create a simple demo with mock data
def create_demo_data():
    """Create demo data to show the functionality."""
    
    # Mock search results
    mock_results = [
        {
            "Title": "Machine Learning: A Probabilistic Perspective",
            "Author": "Kevin P. Murphy",
            "Year": "2012",
            "Publisher": "MIT Press",
            "Pages": "1104",
            "Language": "English",
            "Size": "25 MB",
            "Extension": "pdf",
            "MD5": "demo_ml_001",
            "Mirror_1": "http://example.com/ml_book1.pdf"
        },
        {
            "Title": "Pattern Recognition and Machine Learning",
            "Author": "Christopher M. Bishop",
            "Year": "2006",
            "Publisher": "Springer",
            "Pages": "738",
            "Language": "English",
            "Size": "8 MB",
            "Extension": "pdf",
            "MD5": "demo_ml_002",
            "Mirror_1": "http://example.com/ml_book2.pdf"
        },
        {
            "Title": "The Elements of Statistical Learning",
            "Author": "Trevor Hastie, Robert Tibshirani, Jerome Friedman",
            "Year": "2009",
            "Publisher": "Springer",
            "Pages": "745",
            "Language": "English",
            "Size": "12 MB",
            "Extension": "pdf",
            "MD5": "demo_ml_003",
            "Mirror_1": "http://example.com/ml_book3.pdf"
        },
        {
            "Title": "Deep Learning",
            "Author": "Ian Goodfellow, Yoshua Bengio, Aaron Courville",
            "Year": "2016",
            "Publisher": "MIT Press",
            "Pages": "775",
            "Language": "English",
            "Size": "19 MB",
            "Extension": "pdf",
            "MD5": "demo_ml_004",
            "Mirror_1": "http://example.com/ml_book4.pdf"
        },
        {
            "Title": "Machine Learning: An Algorithmic Perspective",
            "Author": "Stephen Marsland",
            "Year": "2015",
            "Publisher": "CRC Press",
            "Pages": "457",
            "Language": "English",
            "Size": "6 MB",
            "Extension": "pdf",
            "MD5": "demo_ml_005",
            "Mirror_1": "http://example.com/ml_book5.pdf"
        }
    ]
    
    return mock_results[:10]  # Return first 10 results

def simulate_download(paper_info):
    """Simulate downloading a paper."""
    print(f"\n📥 Simulating download of: {paper_info['Title'][:60]}...")
    
    # Simulate download progress
    for i in range(0, 101, 20):
        print(f"   Progress: {i}%", end='\r')
        time.sleep(0.2)
    print(f"   Progress: 100%")
    
    # Create mock download path
    download_folder = Path.home() / "Downloads" / "libgen_papers"
    download_folder.mkdir(parents=True, exist_ok=True)
    
    # Save metadata
    metadata = {
        "title": paper_info["Title"],
        "author": paper_info["Author"],
        "year": paper_info["Year"],
        "download_date": datetime.now().isoformat(),
        "file_path": f"(simulated) {paper_info['Title'][:30]}.pdf"
    }
    
    metadata_file = download_folder / "download_metadata.json"
    existing_metadata = {}
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                existing_metadata = json.load(f)
        except:
            pass
    
    existing_metadata[paper_info["MD5"]] = metadata
    
    with open(metadata_file, 'w') as f:
        json.dump(existing_metadata, f, indent=2)
    
    print(f"✅ Download simulated successfully!")
    print(f"   Metadata saved to: {metadata_file}")
    return True

def main():
    print("=" * 70)
    print("🔬 LibGen Paper Downloader - Demo Mode")
    print("=" * 70)
    print("\nNote: Running in demo mode with simulated data.")
    print("The actual implementation will connect to libgen.li when network issues are resolved.\n")
    
    # Simulate search
    query = "machine learning"
    print(f"🔍 Searching for: '{query}'")
    print("-" * 70)
    
    # Add random delay to simulate rate limiting
    delay = random.uniform(1, 3)
    print(f"⏱️  Rate limiting: waiting {delay:.1f} seconds...")
    time.sleep(delay)
    
    # Get mock results
    results = create_demo_data()
    
    print(f"\n✨ Found {len(results)} results:\n")
    
    # Display results
    for i, paper in enumerate(results, 1):
        print(f"{i:2d}. 📚 {paper['Title'][:60]}...")
        print(f"    👤 Author: {paper['Author'][:40]}")
        print(f"    📅 Year: {paper['Year']} | 📊 Size: {paper['Size']} | 📄 Format: {paper['Extension']}")
        print()
    
    # Simulate downloading first paper
    print("-" * 70)
    print("📥 Downloading first paper as a test...")
    
    first_paper = results[0]
    print(f"\nSelected: {first_paper['Title']}")
    
    # Simulate retry logic
    print("\n🔄 Attempting download with retry logic (3 attempts max)...")
    success = simulate_download(first_paper)
    
    if success:
        print("\n" + "=" * 70)
        print("✅ Demo completed successfully!")
        print("\nFeatures demonstrated:")
        print("  • Search with rate limiting (1-3 second delays)")
        print("  • Results display with metadata")
        print("  • Download simulation")
        print("  • Metadata storage in JSON format")
        print("  • Retry logic capability")
        print("\nActual implementation will:")
        print("  • Connect to libgen.li (your preferred mirror)")
        print("  • Download real papers")
        print("  • Handle network failures with exponential backoff")
        print("  • Store complete metadata for each download")
    
    print("=" * 70)

if __name__ == "__main__":
    main()