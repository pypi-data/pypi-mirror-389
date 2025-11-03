import asyncio
from .server import main

def main_entry():
    """Entry point for the bluesky-mcp command."""
    asyncio.run(main())

__all__ = ["main", "main_entry"]