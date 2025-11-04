"""
Constants for logx package
"""

# Item names
ItemLogLevel = "log_level"
ItemLogEventId = "log_event_id"
ItemCompliance = "compliance"
ItemLogEventTime = "log_event_time"
ItemLogTime = "log_time"
ItemLogCategory = "log_category"
ItemLogAppId = "log_app_id"
ItemLogAppVersion = "log_app_version"
ItemLogElapsedTime = "log_elapsed_time"
ItemIgnoreHook = "log_ignore_hook"

# Compliance versions
Compliance0 = "0"   # No compliance, simple text output
Compliance13 = "1.3"  # v1.3 JSON format

# Time format (Python's %z format is not ideal, we'll format manually)
TimeFormat = "%Y-%m-%dT%H:%M:%S.%f"

# Log levels
DisabledLvl = 0
FatalLvl = 1
ErrorLvl = 2
WarnLvl = 3
InfoLvl = 4
DebugLvl = 5
TraceLvl = 6

# Level names
LEVEL_NAMES = {
    DisabledLvl: "disabled",
    FatalLvl: "fatal",
    ErrorLvl: "error",
    WarnLvl: "warn",
    InfoLvl: "info",
    DebugLvl: "debug",
    TraceLvl: "trace",
}

# Compliance level abbreviations for format 0
LEVEL_ABBREV = {
    FatalLvl: "FAT",
    ErrorLvl: "ERR",
    WarnLvl: "WRN",
    InfoLvl: "INF",
    DebugLvl: "DBG",
    TraceLvl: "TRC",
}
