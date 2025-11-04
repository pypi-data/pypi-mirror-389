"""
logx - Main API for structured logging
"""

import sys
import os
from datetime import datetime
from typing import Any

# Import all dependencies
from . import constant
from .loggerz import Loggerz
from .opt import custom_item


class GlobalConfig:
    """Global configuration"""
    default_compliance = constant.Compliance13
    app_id = os.path.basename(sys.argv[0]) if sys.argv else "unknown"
    app_version = "1.0.0"
    max_level = constant.InfoLvl


# Global logger instance
_std_logger: Loggerz = None


def _get_default_logger() -> Loggerz:
    """Get or create default logger"""
    from .loggerz import _format_datetime
    global _std_logger
    if _std_logger is None:
        _std_logger = Loggerz()
    else:
        # Update time
        now = datetime.now()
        formatted_time = _format_datetime(now)
        _std_logger.set_items(
            lambda items: items.update({
                constant.ItemLogTime: formatted_time,
                constant.ItemLogEventTime: formatted_time,
            })
        )
    return _std_logger


def set_max_level(lvl: int) -> None:
    """Set maximum log level"""
    if constant.DisabledLvl <= lvl <= constant.TraceLvl:
        GlobalConfig.max_level = lvl


def get_max_level() -> int:
    """Get maximum log level"""
    return GlobalConfig.max_level


def init(lvl: int, app: str = None, app_ver: str = None, compliance: str = None) -> None:
    """Initialize log configuration"""
    set_max_level(lvl)
    
    if compliance:
        GlobalConfig.default_compliance = compliance
    
    if app_ver:
        GlobalConfig.app_version = app_ver
    
    if app:
        GlobalConfig.app_id = app
    
    if not GlobalConfig.app_id or GlobalConfig.app_id == "unknown":
        GlobalConfig.app_id = os.path.basename(sys.argv[0]) if sys.argv else "unknown"
    
    # Reset the global logger
    global _std_logger
    _std_logger = None


def log(lvl: int, message: str, *log_items) -> None:
    """Log a message with specified level"""
    logger = _get_default_logger()
    logger.log(lvl, message, *log_items)


def new(*items) -> Loggerz:
    """Create a new logger with given items"""
    return Loggerz(items)


# Define and export all convenience functions
def fatal(*args) -> None:
    """Log fatal message"""
    logger = _get_default_logger()
    logger.fatal(*args)


def fatalf(format_string: str, *args) -> None:
    """Log fatal message with formatting"""
    logger = _get_default_logger()
    logger.fatalf(format_string, *args)


def fatalln(*args) -> None:
    """Log fatal message with newline"""
    logger = _get_default_logger()
    logger.fatalln(*args)


def error(*args) -> None:
    """Log error message"""
    logger = _get_default_logger()
    logger.error(*args)


def errorf(format_string: str, *args) -> None:
    """Log error message with formatting"""
    logger = _get_default_logger()
    logger.errorf(format_string, *args)


def errorln(*args) -> None:
    """Log error message with newline"""
    logger = _get_default_logger()
    logger.errorln(*args)


def warn(*args) -> None:
    """Log warning message"""
    logger = _get_default_logger()
    logger.warn(*args)


def warnf(format_string: str, *args) -> None:
    """Log warning message with formatting"""
    logger = _get_default_logger()
    logger.warnf(format_string, *args)


def warnln(*args) -> None:
    """Log warning message with newline"""
    logger = _get_default_logger()
    logger.warnln(*args)


def print(*args) -> None:
    """Log info message"""
    logger = _get_default_logger()
    logger.print(*args)


def printf(format_string: str, *args) -> None:
    """Log info message with formatting"""
    logger = _get_default_logger()
    logger.printf(format_string, *args)


def println(*args) -> None:
    """Log info message with newline"""
    logger = _get_default_logger()
    logger.println(*args)


def info(*args) -> None:
    """Log info message"""
    logger = _get_default_logger()
    logger.print(*args)


def infof(format_string: str, *args) -> None:
    """Log info message with formatting"""
    logger = _get_default_logger()
    logger.printf(format_string, *args)


def infoln(*args) -> None:
    """Log info message with newline"""
    logger = _get_default_logger()
    logger.println(*args)


def debug(*args) -> None:
    """Log debug message"""
    logger = _get_default_logger()
    logger.debug(*args)


def debugf(format_string: str, *args) -> None:
    """Log debug message with formatting"""
    logger = _get_default_logger()
    logger.debugf(format_string, *args)


def debugln(*args) -> None:
    """Log debug message with newline"""
    logger = _get_default_logger()
    logger.debugln(*args)


def trace(*args) -> None:
    """Log trace message"""
    logger = _get_default_logger()
    logger.trace(*args)


def tracef(format_string: str, *args) -> None:
    """Log trace message with formatting"""
    logger = _get_default_logger()
    logger.tracef(format_string, *args)


def traceln(*args) -> None:
    """Log trace message with newline"""
    logger = _get_default_logger()
    logger.traceln(*args)


# Export for convenience
CustomItem = custom_item