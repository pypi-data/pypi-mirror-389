#!/usr/bin/env python3
"""
Example usage of logx

This demonstrates how to use the logx library for structured logging.
"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logx import init, errorf, InfoLvl, CustomItem, log, new, DebugLvl, Error, Info, Debug


def main():
    # Initialize logging with debug level to show all logs
    init(DebugLvl, "my_app", "1.0.0", "1.3")  # Set to debug level to show all logs
    
    print("=== Simple Log Output ===")
    # Simple error log
    errorf("用户登录失败: %s", "密码错误")
    
    print("\n=== Custom Log Items ===")
    # Custom log with additional fields
    log(InfoLvl, "用户操作",
        CustomItem("user_id", "12345"),
        CustomItem("action", "login"))
    
    print("\n=== Using Loggerz Object ===")
    # Create a logger with default fields
    logger = new(
        CustomItem("service", "user-service"),
        CustomItem("version", "1.0.0"),
    )
    logger.printf("处理用户请求: GET /api/users")
    
    print("\n=== Different Log Levels ===")
    Error("This is an error message")
    Info("This is an info message")
    Debug("This is a debug message")
    
    print("\n=== With Different Compliance Levels ===")
    # Compliance 0 (text format)
    init(InfoLvl, "my_app", "1.0.0", "0")
    errorf("This is an error in format 0")
    Info("This is an info in format 0")
    
    # Compliance 1.3 (JSON format)
    init(InfoLvl, "my_app", "1.0.0", "1.3")
    print("\n=== Back to JSON format ===")
    errorf("This is an error in JSON format")
    Info("This is an info in JSON format")


if __name__ == "__main__":
    main()