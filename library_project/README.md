# LibGen Paper Downloader

A simple Python tool for downloading papers from Library Genesis (LibGen).

## Features
- Search and download papers from LibGen
- Rate limiting to respect server resources (20-30 requests/minute)
- Concurrent downloads support (up to 5 simultaneous downloads)
- Progress tracking with tqdm
- Comprehensive logging
- Random user agent rotation
- Metadata tracking in JSON format
- Retry logic with exponential backoff

## Project Structure

```
library_project/
├── downloads/              # Downloaded papers (git-ignored)
│   └── .gitkeep
├── src/                    # Source code
│   ├── __init__.py
│   ├── config.py          # Configuration settings
│   ├── main.py            # Main implementation
│   ├── libgen_direct.py  # Direct web scraping implementation
│   └── simple_test.py     # Demo version
├── .gitignore             # Git ignore rules
├── .venv/                 # Virtual environment (git-ignored)
├── requirements.txt       # Python dependencies
├── run.py                 # Main entry point
├── run_demo.py           # Demo entry point
└── README.md             # This file
```

## Installation

1. Create and activate a virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
uv pip install -r requirements.txt
```

## Configuration

Edit `src/config.py` to customize:
- **Rate limiting**: 20-30 requests/minute with random delays
- **Download location**: `./downloads/` (within the project)
- **Concurrent downloads**: Maximum 5 simultaneous downloads
- **Logging**: Console and file output

## Usage

### Run the main application:
```bash
python run.py
```

### Run the demo (simulated downloads):
```bash
python run_demo.py
```

### Direct web scraping version:
```bash
python src/libgen_direct.py
```

## Downloaded Files

- Papers are saved to the `downloads/` folder within the project
- Metadata is stored in `downloads/download_metadata.json`
- Each download includes:
  - Title, author, year, publisher
  - File size, format, language
  - Download date and file path
  - MD5 hash for deduplication

## Dependencies

- **libgen-api** - LibGen API interface
- **streamlit** - Web UI framework (for future GUI)
- **httpx** - Modern HTTP client
- **tqdm** - Progress bars
- **fake-useragent** - Random user agent generation
- **beautifulsoup4** - HTML parsing (for direct implementation)
- **lxml** - XML/HTML processing

## Features

### Rate Limiting
- Configurable base rate (default: 25 requests/minute)
- Additional random delay (1-3 seconds) between requests
- Prevents server overload

### Retry Logic
- 3 retry attempts with exponential backoff
- Wait times: 1, 2, 4 seconds between retries
- Handles timeout and connection errors

### Metadata Tracking
- JSON file stores all download history
- Uses MD5 hash as unique identifier
- Prevents duplicate downloads

## Notes

- The project uses libgen.li as the primary mirror
- Alternative mirrors are tried if the primary fails
- All downloads respect rate limits and include error handling
- The downloads folder is git-ignored to prevent committing papers