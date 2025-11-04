# logx

Python implementation of structured logging compatible with NETSTARS log specification v1.3

## Introduction

logx is a universal logging library that conforms to the NETSTARS log specification requirements. By default, it supports [NETSTARS Log Specification v1.3](https://tech-netstars.atlassian.net/wiki/spaces/MSD/pages/301269044/NETSTARS+v1.3). Under specification v1.3, logx outputs logs in JSON format, as shown in the following example:

```json
{"compliance":"1.3","log_app_id":"test_app_id","log_app_version":"0.1","log_category":"srv-exception-log","log_event_id":"","log_event_time":"2022-01-21T10:53:21.774+09:00","log_level":"fatal","log_time":"2022-01-21T10:53:21.774+09:00","message":"this is a test message"}
```

JSON format logs can nest JSON, and newlines and double quotes in key-value content are automatically escaped.

During development and debugging, you can set the compliance level to "0" to output simple semicolon-separated log information:

```
2022-01-21T10:56:43.901+09:00 [INF] item_1: 23; log_event_time: 2022-01-21T10:56:43.901+09:00; message: this is a test message
```

> __Note:__ Specification v1.3 meets SLA requirements and can be parsed by Elasticsearch; specification 0 is only recommended for development and testing phases.

## Log Levels

Log levels in logx are integers conforming to the v1.3 log specification. Valid range is `[0,6]`, where 0 means no log output, and 1-6 correspond to `fatal`, `error`, `warn`, `info`, `debug`, `trace` respectively. Larger values provide richer output information. The maximum output log level can be specified in the `logx.init()` initialization method to control the level of detail. You can also dynamically adjust the maximum log output level using the `logx.set_max_level()` method.

## Usage

### Complete Usage Example

```python
from logx import init, errorf, Log, InfoLvl, New, CustomItem, DebugLvl

# Initialize logging
init(DebugLvl, "my_app", "1.0.0", "1.3")  # Set to debug level to show all logs

# Simple log output
errorf("用户登录失败: %s", "密码错误")

# Custom log items
Log(InfoLvl, "用户操作",
    CustomItem("user_id", "12345"),
    CustomItem("action", "login"))

# Use Loggerz object
logger = New(
    CustomItem("service", "user-service"),
    CustomItem("version", "1.0.0"),
)
logger.printf("处理用户请求: %s", "GET /api/users")
```

### Output

Running the above code will output the following JSON formatted logs:

```json
{"compliance":"1.3","log_app_id":"my_app","log_app_version":"1.0.0","log_category":"srv-exception-log","log_event_id":"","log_event_time":"2025-10-22T19:58:30.785+08:00","log_level":"error","log_time":"2025-10-22T19:58:30.785+08:00","message":"用户登录失败: 密码错误"}
{"compliance":"1.3","log_app_id":"my_app","log_app_version":"1.0.0","log_category":"srv-biz-process-log","log_event_id":"","log_event_time":"2025-10-22T19:58:30.785+08:00","log_level":"info","log_time":"2025-10-22T19:58:30.785+08:00","message":"用户操作","user_id":"12345","action":"login"}
{"compliance":"1.3","log_app_id":"my_app","log_app_version":"1.0.0","log_category":"srv-biz-process-log","log_event_id":"","log_event_time":"2025-10-22T19:58:30.785+08:00","log_level":"info","log_time":"2025-10-22T19:58:30.785+08:00","message":"处理用户请求: GET /api/users","service":"user-service","version":"1.0.0"}
```

### Detailed Description

- __Initialization__: Call the `logx.init()` method at program startup to set the maximum output log level. Usually this method is called in the `main()` function, and the parameter values can be provided through the application's configuration file.

  - `DebugLvl`: Sets the log level to debug, which outputs all level logs
  - `"my_app"`: Application ID
  - `"1.0.0"`: Application version number
  - `"1.3"`: Log specification version number. If "0" is specified, simple information is output, recommended only during debugging

- __Simple log output__: Use methods like `logx.printf()`, `logx.errorf()` to output simple log information:

```python
logx.errorf("用户登录失败: %s", "密码错误")
```

- __Custom log items__: Use `logx.log()` and `logx.CustomItem()` methods to achieve maximum flexibility in log information customization:

```python
logx.Log(InfoLvl, "用户操作",
    CustomItem("user_id", "12345"),
    CustomItem("action", "login"))
```

- __Using Loggerz objects__: Use the `logx.new()` method to create a new Loggerz object and save some common log information, so you don't have to manually pass this information each time:

```python
logger = logx.new(
    CustomItem("service", "user-service"),
    CustomItem("version", "1.0.0"),
)
logger.printf("处理用户请求: %s", "GET /api/users")
```

## Installation

### From PyPI (Recommended)

```bash
pip install 0xnetx-logx
```

### From GitHub

```bash
pip install git+https://github.com/0xNetx/logx.git
```

### From Local Directory

If you've cloned the repository:

```bash
cd logx
pip install -e .
```

Or install directly:

```bash
pip install -e /path/to/logx
```

## Version

- **v0.0.1**: Initial release version with complete log formatting functionality
- Supports NETSTARS v1.3 specification JSON format output
- Supports simple text format output (compliance 0)
- Includes hook mechanism and Loggerz object functionality

## API Reference

### Constants

- `DisabledLvl = 0`: No log output
- `FatalLvl = 1`: Fatal error
- `ErrorLvl = 2`: General error
- `WarnLvl = 3`: Warning
- `InfoLvl = 4`: General info
- `DebugLvl = 5`: Debug information
- `TraceLvl = 6`: Trace information

### Functions

#### Initialization

- `init(level, app_id, app_version, compliance)`: Initialize log configuration
- `set_max_level(level)`: Set maximum log output level
- `get_max_level()`: Get maximum log output level

#### Logging Functions

- `log(level, message, *log_items)`: Log a message with specified level
- `fatal(*args)`: Log fatal message
- `error(*args)`: Log error message
- `warn(*args)`: Log warning message
- `print(*args)`: Log info message
- `debug(*args)`: Log debug message
- `trace(*args)`: Log trace message

Each level also has `*f` (formatted) and `*ln` (with newline) variants.

#### Options

- `CustomItem(key, value)`: Add custom log item
- `Compliance(version)`: Set compliance version
- `LogTime(time)`: Set log time
- `EventTime(time)`: Set event time
- `Level(level)`: Set log level
- `Category(category)`: Set log category
- `AppId(app_id)`: Set application ID
- `AppVersion(version)`: Set application version
- `EventId(event_id)`: Set event ID

#### Objects

- `new(*items)` -> `Loggerz`: Create a new logger object

### Loggerz Class

The `Loggerz` class provides all the functionality of the global functions plus:

- `enable_log_elapsed_time()`: Enable elapsed time tracking
- `get_items()`: Get all log items
- `set_items(*items)`: Update log items
- `add_hook(hook)`: Add a hook function
