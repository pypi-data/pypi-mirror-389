"""
logx - A Python logging library compatible with NETSTARS log specification v1.3

This package provides structured logging capabilities compatible with the NETSTARS log specification.
It outputs logs in JSON format with all required fields like compliance, log_app_id, log_level, etc.
"""

from .logx import (
    init as Init,
    log as Log,
    fatal as Fatal,
    fatalf as Fatalf,
    fatalln as Fatalln,
    error as Error,
    errorf as Errorf,
    errorln as Errorln,
    warn as Warn,
    warnf as Warnf,
    warnln as Warnln,
    info as Info,
    infof as Infof,
    infoln as Infoln,
    print as Print,
    printf as Printf,
    println as Println,
    debug as Debug,
    debugf as Debugf,
    debugln as Debugln,
    trace as Trace,
    tracef as Tracef,
    traceln as Traceln,
    new as New,
    set_max_level as SetMaxLevel,
    get_max_level as GetMaxLevel,
)

__version__ = "0.0.2"
__all__ = [
    "Init",
    "Log",
    "Fatal", "Fatalf", "Fatalln",
    "Error", "Errorf", "Errorln",
    "Warn", "Warnf", "Warnln",
    "Info", "Infof", "Infoln",
    "Print", "Printf", "Println",
    "Debug", "Debugf", "Debugln",
    "Trace", "Tracef", "Traceln",
    "New",
    "SetMaxLevel",
    "GetMaxLevel",
]

# Also export the lowercase versions
from .logx import *
from . import constant as _

# Export constants
from .constant import (
    DisabledLvl,
    FatalLvl,
    ErrorLvl,
    WarnLvl,
    InfoLvl,
    DebugLvl,
    TraceLvl,
    LEVEL_NAMES,
    LEVEL_ABBREV,
)

# Export functions from opt
from .opt import custom_item as CustomItem
