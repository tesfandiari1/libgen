# LibGen Paper Downloader - Streamlit Interface

## Quick Start

### Run with UV (Recommended)
```bash
cd library_project
uv run streamlit run app.py
```

### Alternative: Run with Python directly
```bash
cd library_project
streamlit run app.py
```

### Or use the provided script
```bash
cd library_project
./run_streamlit.sh
```

## Features

### 1. Search Interface
- Text input field for search queries
- Search button to execute searches
- Supports queries like "machine learning", "python", "data science"

### 2. Results Table
- Displays search results in a clean table format
- Shows: Title, Author, Year, Size, and File Type
- Checkbox selection for each paper

### 3. Download Management
- Select multiple papers using checkboxes
- "Download Selected" button to queue papers
- Concurrent downloads (up to 3 simultaneous by default)

### 4. Progress Tracking
- Individual progress bars for each download
- Overall progress indicator
- Download status persists across page refreshes using st.session_state

### 5. Settings (Sidebar)
- Toggle between Mock Data and Real LibGen searches
- Adjust maximum number of search results (5-50)
- View recent download history

## Usage

1. **Start the app** using one of the commands above
2. **Enter a search query** (e.g., "machine learning")
3. **Click Search** to find papers
4. **Select papers** using the checkboxes in the results table
5. **Click "Download Selected"** to start downloading
6. **Monitor progress** with the progress bars

## Notes

- **Mock Data Mode** (default): Uses simulated data for safe testing
- **Real Mode**: Connects to actual LibGen (use responsibly)
- Downloads are saved to the `downloads/` folder
- The app maintains state across page refreshes
- Download status is saved in `downloads/download_status.json`

## Configuration

Edit `src/config.py` to adjust:
- Maximum concurrent downloads
- Download folder location
- Request rate limiting
- Logging settings

## Troubleshooting

If the app doesn't start:
1. Ensure all dependencies are installed: `uv pip install -r requirements.txt`
2. Check if port 8501 is available
3. Try running with: `uv run streamlit run app.py --server.port 8502`

## Dependencies

- streamlit: Web interface
- stqdm: Streamlit-compatible progress bars
- httpx: HTTP client
- beautifulsoup4: HTML parsing
- fake-useragent: User agent rotation
- tqdm: Terminal progress bars (fallback)