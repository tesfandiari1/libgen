#!/usr/bin/env python
"""Run the demo version of LibGen Paper Downloader."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from simple_test import main

if __name__ == "__main__":
    main()