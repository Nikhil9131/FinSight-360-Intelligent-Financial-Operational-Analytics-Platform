"""
FinSight 360 - Logging Utility
================================
Provides a pre-configured logger for every module in the project.
Uses loguru for structured, readable logs with automatic file rotation.

Usage:
    from src.utils.logger import get_logger
    logger = get_logger("ingestion")
    logger.info("Pipeline started")
    logger.error("Validation failed: {}", error_msg)
"""

import sys
from pathlib import Path
from loguru import logger as _loguru_logger

from config.settings import PROJECT_ROOT


# ─── Default log directory ────────────────────────────────────
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_logger(module_name: str, log_level: str = "INFO"):
    """
    Return a configured loguru logger for a specific module.

    Each module gets:
      - Console output (colored, human-readable)
      - File output   (JSON-structured, auto-rotated at 10 MB, kept 30 days)

    Args:
        module_name: Name to tag log messages with (e.g., "ingestion", "cleaning").
        log_level:   Minimum severity to log. Default: INFO.

    Returns:
        A loguru logger instance bound to the module name.
    """
    # Remove default handler on first call to avoid duplicates
    _loguru_logger.remove()

    # ── Console handler ────────────────────────────────────────
    _loguru_logger.add(
        sys.stderr,
        level=log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{extra[module]}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # ── File handler (one combined log + one per module) ──────
    # Combined log
    _loguru_logger.add(
        LOG_DIR / "finsight360.log",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[module]} | {message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,  # thread-safe
    )

    # Per-module log
    _loguru_logger.add(
        LOG_DIR / f"{module_name}.log",
        level="DEBUG",  # capture everything for the module file
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
        rotation="5 MB",
        retention="14 days",
        compression="zip",
        filter=lambda record: record["extra"].get("module") == module_name,
        enqueue=True,
    )

    # Return a logger bound to this module name
    return _loguru_logger.bind(module=module_name)

