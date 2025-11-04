"""
Loggerz - The core logger class
"""

import sys
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Callable, Optional
import json

from . import constant
from .opt import log_level_string, category_of_level


def _format_datetime(dt: datetime) -> str:
    """Format datetime in the required format with timezone"""
    # Get timezone offset
    if dt.tzinfo is None:
        # Use local timezone
        local_offset = dt.utcoffset() or timedelta(0)
        # For Python 3.8+, we can get local timezone
        local_tz = datetime.now(timezone.utc).astimezone().tzinfo
        dt = dt.replace(tzinfo=local_tz)
    
    offset = dt.utcoffset()
    if offset:
        total_seconds = int(offset.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        sign = '+' if total_seconds >= 0 else '-'
        offset_str = f"{sign}{abs(hours):02d}:{abs(minutes):02d}"
    else:
        offset_str = "+00:00"
    
    # Format datetime without microseconds if needed
    formatted = dt.strftime(constant.TimeFormat)
    # Remove trailing zeros from microseconds
    if '.' in formatted:
        formatted = formatted.rstrip('0').rstrip('.')
    
    return f"{formatted}{offset_str}"


class Loggerz:
    """Logger class with customizable options"""
    
    def __init__(self, items: Optional[list] = None):
        """Initialize logger with optional items"""
        self.output = sys.stdout
        self.msg_key = "message"
        self.log_items: Dict[str, Any] = {}
        self.log_hooks: list = []
        self.log_elapsed_time = False
        self.begin_time: Optional[int] = None
        self._lock = threading.Lock()
        
        # Set default items
        self._set_default_items()
        
        # Apply provided items
        if items:
            for item_option in items:
                item_option(self.log_items)
    
    def _set_default_items(self) -> None:
        """Set default log items"""
        from .logx import GlobalConfig
        now = datetime.now()
        
        self.log_items[constant.ItemCompliance] = GlobalConfig.default_compliance
        self.log_items[constant.ItemLogTime] = _format_datetime(now)
        self.log_items[constant.ItemLogEventTime] = _format_datetime(now)
        self.log_items[constant.ItemLogLevel] = log_level_string(constant.InfoLvl)
        self.log_items[constant.ItemLogCategory] = category_of_level(constant.InfoLvl)
        self.log_items[constant.ItemLogAppId] = GlobalConfig.app_id
        self.log_items[constant.ItemLogAppVersion] = GlobalConfig.app_version
        self.log_items[constant.ItemLogEventId] = ""
    
    def enable_log_elapsed_time(self) -> None:
        """Enable elapsed time tracking"""
        with self._lock:
            self.log_elapsed_time = True
            self.begin_time = datetime.now().timestamp()
    
    def get_items(self) -> Dict[str, Any]:
        """Get all log items"""
        with self._lock:
            return self.log_items.copy()
    
    def set_items(self, *item_options) -> None:
        """Update log items"""
        with self._lock:
            for item_option in item_options:
                item_option(self.log_items)
    
    def add_hook(self, hook: Callable[[str], str]) -> None:
        """Add a hook function"""
        with self._lock:
            self.log_hooks.append(hook)
    
    def log(self, lvl: int, message: str, *log_items) -> None:
        """Output custom log"""
        # Check if level exceeds max level
        from .logx import GlobalConfig
        if lvl > GlobalConfig.max_level:
            return
        
        # Get message key
        msg_key = self.msg_key
        if not msg_key:
            msg_key = "message"
        
        # Copy preset log items
        with self._lock:
            items = self.log_items.copy()
            hooks = self.log_hooks.copy()
        
        # Add current log items
        for item_option in log_items:
            item_option(items)
        
        # Check if should ignore hooks
        ignore_hook = items.pop(constant.ItemIgnoreHook, False)
        
        items[constant.ItemLogLevel] = log_level_string(lvl)
        items[constant.ItemLogCategory] = category_of_level(lvl)
        items[msg_key] = message
        
        # Log elapsed time
        if self.log_elapsed_time and self.begin_time is not None:
            now = datetime.now().timestamp()
            elapsed = now - self.begin_time
            items[constant.ItemLogElapsedTime] = f"{elapsed:.3f}"
        
        # Get compliance version
        compliance = items.get(constant.ItemCompliance)
        if not compliance:
            return
        
        # Format log text
        if compliance == constant.Compliance0:
            text = self._format_log0(items)
        elif compliance == constant.Compliance13:
            text = self._format_log13(items)
        else:
            return
        
        # Execute hooks
        if not ignore_hook and hooks:
            for hook in hooks:
                try:
                    text = hook(text)
                except Exception:
                    pass
        
        # Output log
        print(text, file=self.output)
    
    def _format_log0(self, items: Dict[str, Any]) -> str:
        """Format log for compliance 0 (text format)"""
        parts = []
        now = datetime.now().strftime(constant.TimeFormat)
        lvl = items.get(constant.ItemLogLevel, "info")
        
        abbrev = constant.LEVEL_ABBREV.get(
            next((k for k, v in constant.LEVEL_NAMES.items() if v == lvl), constant.InfoLvl),
            "INF"
        )
        
        parts.append(f"{now} [{abbrev}]")
        
        for k, v in items.items():
            if k not in (constant.ItemLogTime, constant.ItemLogLevel):
                parts.append(f"{k}: {v};")
        
        return " ".join(parts).rstrip(";")
    
    def _format_log13(self, items: Dict[str, Any]) -> str:
        """Format log for compliance 13 (JSON format)"""
        return json.dumps(items, ensure_ascii=False)
    
    # Convenience methods for different log levels
    def fatal(self, *args) -> None:
        """Log fatal message"""
        msg = " ".join(str(arg) for arg in args)
        self.log(constant.FatalLvl, msg)
    
    def fatalf(self, format_string: str, *args) -> None:
        """Log fatal message with formatting"""
        msg = format_string % args
        self.log(constant.FatalLvl, msg)
    
    def fatalln(self, *args) -> None:
        """Log fatal message with newline"""
        msg = " ".join(str(arg) for arg in args)
        self.log(constant.FatalLvl, msg)
    
    def error(self, *args) -> None:
        """Log error message"""
        msg = " ".join(str(arg) for arg in args)
        self.log(constant.ErrorLvl, msg)
    
    def errorf(self, format_string: str, *args) -> None:
        """Log error message with formatting"""
        msg = format_string % args
        self.log(constant.ErrorLvl, msg)
    
    def errorln(self, *args) -> None:
        """Log error message with newline"""
        msg = " ".join(str(arg) for arg in args)
        self.log(constant.ErrorLvl, msg)
    
    def warn(self, *args) -> None:
        """Log warning message"""
        msg = " ".join(str(arg) for arg in args)
        self.log(constant.WarnLvl, msg)
    
    def warnf(self, format_string: str, *args) -> None:
        """Log warning message with formatting"""
        msg = format_string % args
        self.log(constant.WarnLvl, msg)
    
    def warnln(self, *args) -> None:
        """Log warning message with newline"""
        msg = " ".join(str(arg) for arg in args)
        self.log(constant.WarnLvl, msg)
    
    def print(self, *args) -> None:
        """Log info message"""
        msg = " ".join(str(arg) for arg in args)
        self.log(constant.InfoLvl, msg)
    
    def printf(self, format_string: str, *args) -> None:
        """Log info message with formatting"""
        msg = format_string % args
        self.log(constant.InfoLvl, msg)
    
    def println(self, *args) -> None:
        """Log info message with newline"""
        msg = " ".join(str(arg) for arg in args)
        self.log(constant.InfoLvl, msg)
    
    def debug(self, *args) -> None:
        """Log debug message"""
        msg = " ".join(str(arg) for arg in args)
        self.log(constant.DebugLvl, msg)
    
    def debugf(self, format_string: str, *args) -> None:
        """Log debug message with formatting"""
        msg = format_string % args
        self.log(constant.DebugLvl, msg)
    
    def debugln(self, *args) -> None:
        """Log debug message with newline"""
        msg = " ".join(str(arg) for arg in args)
        self.log(constant.DebugLvl, msg)
    
    def trace(self, *args) -> None:
        """Log trace message"""
        msg = " ".join(str(arg) for arg in args)
        self.log(constant.TraceLvl, msg)
    
    def tracef(self, format_string: str, *args) -> None:
        """Log trace message with formatting"""
        msg = format_string % args
        self.log(constant.TraceLvl, msg)
    
    def traceln(self, *args) -> None:
        """Log trace message with newline"""
        msg = " ".join(str(arg) for arg in args)
        self.log(constant.TraceLvl, msg)
