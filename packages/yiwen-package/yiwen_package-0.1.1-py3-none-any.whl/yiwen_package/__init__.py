"""Yiwen Package - 一个简单实用的 Python 工具包"""

from .hello import hello

# 字符串工具
from .string_utils import (
    is_empty,
    truncate,
    remove_prefix,
    remove_suffix,
    camel_to_snake,
    snake_to_camel,
)

# 列表工具
from .list_utils import (
    chunk,
    flatten,
    unique,
    group_by,
)

# 文件工具
from .file_utils import (
    read_json,
    write_json,
    ensure_dir,
    get_file_size,
    format_file_size,
)

# 时间工具
from .time_utils import (
    now_timestamp,
    now_timestamp_ms,
    format_datetime,
    parse_datetime,
    time_ago,
    add_days,
)

__version__ = "0.1.0"

__all__ = [
    # 基础
    "hello",
    # 字符串工具
    "is_empty",
    "truncate",
    "remove_prefix",
    "remove_suffix",
    "camel_to_snake",
    "snake_to_camel",
    # 列表工具
    "chunk",
    "flatten",
    "unique",
    "group_by",
    # 文件工具
    "read_json",
    "write_json",
    "ensure_dir",
    "get_file_size",
    "format_file_size",
    # 时间工具
    "now_timestamp",
    "now_timestamp_ms",
    "format_datetime",
    "parse_datetime",
    "time_ago",
    "add_days",
]
