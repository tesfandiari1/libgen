from __future__ import annotations

import os
import typer
from dotenv import load_dotenv

from .commands import app as cli


def main() -> None:
    load_dotenv()
    # Allow Typer to run as a function entry point
    cli()


if __name__ == "__main__":
    main()


