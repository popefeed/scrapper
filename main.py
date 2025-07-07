"""
Legacy main.py - now redirects to CLI module
"""

import asyncio
from cli.main import main as cli_main


async def main():
    """Main entry point - redirects to CLI module"""
    await cli_main()


if __name__ == "__main__":
    asyncio.run(main())