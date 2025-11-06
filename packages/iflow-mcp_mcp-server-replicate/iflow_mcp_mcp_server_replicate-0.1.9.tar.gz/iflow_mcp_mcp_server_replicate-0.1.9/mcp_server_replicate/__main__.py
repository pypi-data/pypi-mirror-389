"""Entry point for the MCP server."""

import argparse
import logging
import os
from typing import NoReturn

from .server import create_server


def main() -> NoReturn:
    """Run the MCP server with configured log level."""
    parser = argparse.ArgumentParser(description="Replicate MCP Server")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=os.getenv("LOG_LEVEL", "WARNING"),
        help="Set the logging level (default: WARNING, env: LOG_LEVEL)",
    )
    args = parser.parse_args()

    # Configure log level
    log_level = getattr(logging, args.log_level.upper())
    
    # Create and run server with configured log level
    mcp = create_server(log_level=log_level)
    mcp.run()
    raise SystemExit(0)


if __name__ == "__main__":
    main()
