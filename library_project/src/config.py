"""Configuration settings for LibGen downloader."""

import os
from pathlib import Path

# Fixed [CRITICAL-002]: Add path validation to prevent traversal attacks
def validate_path(path_str: str, base_dir: str) -> Path:
    """Validate and sanitize file paths to prevent traversal attacks."""
    base = Path(base_dir).resolve()
    target = (base / path_str).resolve()
    
    # Ensure the target is within the base directory
    if not str(target).startswith(str(base)):
        raise ValueError(f"Path traversal attempt detected: {path_str}")
    
    return target

# Configuration dictionary
CONFIG = {
    # Rate limiting settings
    "rate_limit": {
        "requests_per_minute": 25,  # 20-30 requests per minute
        "delay_between_requests": 2.4,  # seconds (60/25)
    },
    
    # Download settings
    "download": {
        "folder_path": str(validate_path("downloads", Path(__file__).parent.parent)),
        "max_concurrent_downloads": 5,
        "chunk_size": 8192,  # bytes for streaming downloads
        "timeout": 30,  # seconds
    },
    
    # Search settings
    "search": {
        "results_per_page": 25,
        "max_results": 100,
    },
    
    # Logging settings
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "date_format": "%Y-%m-%d %H:%M:%S",
        "log_file": "libgen_downloader.log",
    },
    
    # User agent settings
    "user_agent": {
        "browsers": ["chrome", "firefox", "safari"],
        "os": ["windows", "macos", "linux"],
        "use_random": True,
    }
}

# Ensure download directory exists (path already validated)
Path(CONFIG["download"]["folder_path"]).mkdir(parents=True, exist_ok=True)