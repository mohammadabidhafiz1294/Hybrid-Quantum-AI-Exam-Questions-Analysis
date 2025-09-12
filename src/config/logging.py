"""Logging configuration for VQE Exam Topic Prediction System."""

from pathlib import Path
from typing import Any

from loguru import logger
import structlog
from rich.console import Console

# Configure Rich console for better output
console = Console()

# Remove default logger
logger.remove()

# Add console logger with rich formatting
logger.add(
    console.print,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>",
    level="INFO",
    colorize=True,
)

# Add file logger for persistent logging
log_file = Path("logs/vqe_predictor.log")
log_file.parent.mkdir(exist_ok=True)

logger.add(
    log_file,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - "
    "{message}",
    level="DEBUG",
    rotation="10 MB",
    retention="1 week",
    encoding="utf-8",
)

# Configure structlog for structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(min_level=0),
    context_class=dict,
    logger_factory=structlog.WriteLoggerFactory(),
    cache_logger_on_first_use=True,
)


def get_logger(name: str) -> Any:
    """Get a configured logger instance."""
    return logger.bind(name=name)


def get_struct_logger(name: str) -> Any:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Global logger instances
app_logger = get_logger("vqe_predictor")
api_logger = get_logger("vqe_predictor.api")
cli_logger = get_logger("vqe_predictor.cli")
service_logger = get_logger("vqe_predictor.service")
