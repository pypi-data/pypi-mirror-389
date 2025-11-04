"""
Options and configuration for logx
"""

from datetime import datetime
from typing import Dict, Any, Callable
from . import constant


def _avoid_conflict_with_reserved_key(key: str) -> str:
    """Avoid conflicts with reserved keys by adding a prefix"""
    reserved_keys = {
        constant.ItemCompliance,
        constant.ItemLogEventTime,
        constant.ItemLogTime,
        constant.ItemLogLevel,
        constant.ItemLogCategory,
        constant.ItemLogAppId,
        constant.ItemLogAppVersion,
        constant.ItemLogEventId,
    }
    if key in reserved_keys:
        return f"conflict_{key}"
    return key


def custom_item(key: str, value: Any) -> Callable[[Dict[str, Any]], None]:
    """Create a custom log item option"""
    def update_items(items: Dict[str, Any]) -> None:
        safe_key = _avoid_conflict_with_reserved_key(key)
        items[safe_key] = value
    return update_items


def compliance(ver: str) -> Callable[[Dict[str, Any]], None]:
    """Set compliance version"""
    def update_items(items: Dict[str, Any]) -> None:
        if ver in (constant.Compliance0, constant.Compliance13):
            items[constant.ItemCompliance] = ver
    return update_items


def log_time(log_time: datetime) -> Callable[[Dict[str, Any]], None]:
    """Set log time"""
    def update_items(items: Dict[str, Any]) -> None:
        from .loggerz import _format_datetime
        items[constant.ItemLogTime] = _format_datetime(log_time)
    return update_items


def event_time(ev_time: datetime) -> Callable[[Dict[str, Any]], None]:
    """Set event time"""
    def update_items(items: Dict[str, Any]) -> None:
        from .loggerz import _format_datetime
        items[constant.ItemLogEventTime] = _format_datetime(ev_time)
    return update_items


def level(lvl: int) -> Callable[[Dict[str, Any]], None]:
    """Set log level and category"""
    def update_items(items: Dict[str, Any]) -> None:
        items[constant.ItemLogLevel] = log_level_string(lvl)
        items[constant.ItemLogCategory] = category_of_level(lvl)
    return update_items


def category(category: str) -> Callable[[Dict[str, Any]], None]:
    """Set log category"""
    def update_items(items: Dict[str, Any]) -> None:
        items[constant.ItemLogCategory] = category
    return update_items


def app_id(app_id: str) -> Callable[[Dict[str, Any]], None]:
    """Set application ID"""
    def update_items(items: Dict[str, Any]) -> None:
        items[constant.ItemLogAppId] = app_id
    return update_items


def app_version(ver: str) -> Callable[[Dict[str, Any]], None]:
    """Set application version"""
    def update_items(items: Dict[str, Any]) -> None:
        items[constant.ItemLogAppVersion] = ver
    return update_items


def event_id(ev_id: str) -> Callable[[Dict[str, Any]], None]:
    """Set event ID"""
    def update_items(items: Dict[str, Any]) -> None:
        items[constant.ItemLogEventId] = ev_id
    return update_items


def log_level_string(lvl: int) -> str:
    """Convert log level to string representation"""
    return constant.LEVEL_NAMES.get(lvl, str(lvl))


def category_of_level(lvl: int) -> str:
    """Get category based on log level"""
    if lvl <= constant.WarnLvl:
        return "srv-exception-log"
    return "srv-biz-process-log"
