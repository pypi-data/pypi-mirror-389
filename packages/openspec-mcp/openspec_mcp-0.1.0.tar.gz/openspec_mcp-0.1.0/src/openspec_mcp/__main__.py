"""Main entry point for OpenSpec MCP server."""

import sys
from .server import OpenSpecMCPServer
from .utils import logger


def main() -> None:
    """Main entry point."""
    try:
        logger.info("Starting OpenSpec MCP Server...")
        server = OpenSpecMCPServer()
        server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
