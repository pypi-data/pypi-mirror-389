"""Logging configuration for OpenSpec MCP."""

import logging
import sys
import os


def setup_logger(name: str = "openspec_mcp") -> logging.Logger:
    """Setup logger with appropriate configuration.
    
    Logs to stderr to avoid interfering with stdio MCP communication.
    """
    debug = os.getenv("OPENSPEC_DEBUG", "false").lower() == "true"
    log_level = os.getenv("OPENSPEC_LOG_LEVEL", "DEBUG" if debug else "INFO")
    
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create stderr handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger


# Global logger instance
logger = setup_logger()
