"""Launcher kept for anyone used to double-clicking Save_Christmas.py.
The game itself lives in main.py (pygbag, the browser builder, needs that name)."""

import asyncio
import sys

from main import main

if __name__ == "__main__":
    asyncio.run(main(fullscreen="--fullscreen" in sys.argv))
