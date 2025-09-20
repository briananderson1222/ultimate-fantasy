"""Domain-specific logging utilities."""

import logging
import logging.handlers
from collections.abc import MutableMapping
from contextvars import ContextVar
from typing import Any

from .log_config import get_domain_log_levels, get_log_config, setup_log_directory

# Context variable for tracking request ID across async calls
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# Context variable for tracking current domain
current_domain_var: ContextVar[str | None] = ContextVar("current_domain", default=None)

# Store configured loggers to avoid reconfiguration
_configured_loggers: dict[str, logging.Logger] = {}


class DomainAdapter(logging.LoggerAdapter):
    """Logger adapter that adds domain context to log records."""

    def __init__(self, logger: logging.Logger, domain: str):
        super().__init__(logger, {"domain": domain})
        self.domain = domain

    def process(
        self, msg: Any, kwargs: MutableMapping[str, Any]
    ) -> tuple[Any, MutableMapping[str, Any]]:
        """Process log record to add domain and request context."""
        extra = kwargs.get("extra", {})

        # Add domain context
        extra["domain"] = self.domain

        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            extra["request_id"] = request_id

        kwargs["extra"] = extra
        return msg, kwargs


class DomainFormatter(logging.Formatter):
    """Custom formatter for domain-specific logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with domain context."""
        # Ensure domain is set
        if not hasattr(record, "domain"):
            record.domain = getattr(record, "name", "").split(".")[0] or "unknown"

        # Add request ID if available
        if not hasattr(record, "request_id"):
            record.request_id = request_id_var.get() or ""

        return super().format(record)


def get_domain_logger(domain: str) -> DomainAdapter:
    """Get a domain-specific logger."""
    if domain in _configured_loggers:
        return DomainAdapter(_configured_loggers[domain], domain)

    # Create new logger for this domain
    logger = logging.getLogger(f"ultimate_fantasy.{domain}")

    # Configure logger if not already done
    if not logger.handlers:
        setup_domain_logger(logger, domain)

    _configured_loggers[domain] = logger
    return DomainAdapter(logger, domain)


def setup_domain_logger(logger: logging.Logger, domain: str) -> None:
    """Set up a domain-specific logger with appropriate handlers."""
    config = get_log_config()
    domain_levels = get_domain_log_levels()

    # Set domain-specific log level
    domain_level = domain_levels.get(domain, config.log_level)
    logger.setLevel(getattr(logging, domain_level.upper()))

    # Create formatter
    formatter = DomainFormatter(config.log_format)

    # Console handler
    if config.enable_console_logging:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, domain_level.upper()))
        logger.addHandler(console_handler)

    # File handler with rotation
    if config.enable_file_logging:
        setup_log_directory()

        # Create domain-specific log file if domain separation is enabled
        if config.enable_domain_separation:
            log_file = config.log_file_path.replace(".log", f"_{domain}.log")
        else:
            log_file = config.log_file_path

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=_parse_size(config.log_rotation_size),
            backupCount=config.log_backup_count,
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, domain_level.upper()))
        logger.addHandler(file_handler)


def setup_domain_logging() -> None:
    """Initialize domain logging for all domains."""
    domains = [
        "leagues",
        "users",
        "lineups",
        "trading",
        "scoring",
        "waitlist",
        "shared",
    ]

    for domain in domains:
        get_domain_logger(domain)


def set_request_context(request_id: str, domain: str) -> None:
    """Set request context for logging."""
    request_id_var.set(request_id)
    current_domain_var.set(domain)


def clear_request_context() -> None:
    """Clear request context."""
    request_id_var.set(None)
    current_domain_var.set(None)


def _parse_size(size_str: str) -> int:
    """Parse size string (e.g., '10MB') to bytes."""
    size_str = size_str.upper()

    if size_str.endswith("KB"):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith("MB"):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith("GB"):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        # Assume bytes
        return int(size_str)


# Create domain-specific logger instances for easy import
leagues_logger = get_domain_logger("leagues")
users_logger = get_domain_logger("users")
lineups_logger = get_domain_logger("lineups")
trading_logger = get_domain_logger("trading")
scoring_logger = get_domain_logger("scoring")
waitlist_logger = get_domain_logger("waitlist")
shared_logger = get_domain_logger("shared")
