#!/usr/bin/env python
"""Main entry point for LibGen Paper Downloader."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import without relative imports since we're adding to path
import main

if __name__ == "__main__":
    main.main()