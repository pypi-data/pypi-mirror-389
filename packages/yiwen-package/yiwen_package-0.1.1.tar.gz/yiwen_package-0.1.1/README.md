# yiwen-package

一个简单实用的 Python 工具包，提供常用的字符串、列表、文件和时间处理工具函数。

## 安装

```bash
pip install yiwen-package
```

## 功能特性

- **字符串工具** - 命名转换、截断、前缀/后缀处理
- **列表工具** - 分块、扁平化、去重、分组
- **文件工具** - JSON 读写、目录管理、文件大小格式化
- **时间工具** - 时间戳、日期格式化、相对时间

## 快速开始

```python
from yiwen_package import (
    camel_to_snake,
    chunk,
    read_json,
    format_datetime,
    time_ago
)

# 字符串工具
camel_to_snake("MyClassName")  # "my_class_name"

# 列表工具
chunk([1, 2, 3, 4, 5], 2)  # [[1, 2], [3, 4], [5]]

# 文件工具
data = read_json("config.json")

# 时间工具
from datetime import datetime
format_datetime(datetime.now())  # "2023-11-06 14:30:45"
```

## API 文档

### 字符串工具 (string_utils)

#### `is_empty(s: str) -> bool`
检查字符串是否为空或只包含空白字符。

```python
is_empty("")        # True
is_empty("   ")     # True
is_empty("hello")   # False
```

#### `truncate(s: str, length: int, suffix: str = '...') -> str`
截断字符串到指定长度。

```python
truncate("hello world", 8)              # "hello..."
truncate("hello world", 8, suffix=">>") # "hello >>"
```

#### `remove_prefix(s: str, prefix: str) -> str`
移除字符串的前缀。

```python
remove_prefix("hello_world", "hello_")  # "world"
```

#### `remove_suffix(s: str, suffix: str) -> str`
移除字符串的后缀。

```python
remove_suffix("hello_world", "_world")  # "hello"
```

#### `camel_to_snake(s: str) -> str`
将驼峰命名转换为下划线命名。

```python
camel_to_snake("CamelCase")   # "camel_case"
camel_to_snake("myClassName") # "my_class_name"
```

#### `snake_to_camel(s: str, capitalize_first: bool = False) -> str`
将下划线命名转换为驼峰命名。

```python
snake_to_camel("snake_case")                        # "snakeCase"
snake_to_camel("snake_case", capitalize_first=True) # "SnakeCase"
```

### 列表工具 (list_utils)

#### `chunk(lst: List[T], size: int) -> List[List[T]]`
将列表分割成指定大小的块。

```python
chunk([1, 2, 3, 4, 5], 2)  # [[1, 2], [3, 4], [5]]
```

#### `flatten(nested_list: List[Any]) -> List[Any]`
展平嵌套列表。

```python
flatten([[1, 2], [3, [4, 5]]])  # [1, 2, 3, 4, 5]
```

#### `unique(lst: List[T], key=None) -> List[T]`
去重，保持原始顺序。

```python
unique([1, 2, 2, 3, 1])  # [1, 2, 3]

# 使用 key 函数
data = [{'id': 1, 'name': 'a'}, {'id': 2, 'name': 'b'}, {'id': 1, 'name': 'c'}]
unique(data, key=lambda x: x['id'])  # [{'id': 1, 'name': 'a'}, {'id': 2, 'name': 'b'}]
```

#### `group_by(items: Iterable[T], key_func) -> dict`
按指定函数分组。

```python
group_by([1, 2, 3, 4, 5, 6], lambda x: x % 2)
# {0: [2, 4, 6], 1: [1, 3, 5]}
```

### 文件工具 (file_utils)

#### `read_json(file_path: Union[str, Path]) -> Any`
读取 JSON 文件。

```python
data = read_json("config.json")
```

#### `write_json(file_path: Union[str, Path], data: Any, indent: int = 2) -> None`
写入 JSON 文件。

```python
write_json("output.json", {"key": "value"})
```

#### `ensure_dir(dir_path: Union[str, Path]) -> Path`
确保目录存在，如果不存在则创建。

```python
ensure_dir("data/output")  # 创建 data/output 目录
```

#### `get_file_size(file_path: Union[str, Path]) -> int`
获取文件大小（字节）。

```python
get_file_size("file.txt")  # 1024
```

#### `format_file_size(size_bytes: int) -> str`
格式化文件大小为人类可读格式。

```python
format_file_size(1024)           # "1.00 KB"
format_file_size(1024 * 1024)    # "1.00 MB"
```

### 时间工具 (time_utils)

#### `now_timestamp() -> int`
获取当前时间戳（秒）。

```python
now_timestamp()  # 1699200000
```

#### `now_timestamp_ms() -> int`
获取当前时间戳（毫秒）。

```python
now_timestamp_ms()  # 1699200000000
```

#### `format_datetime(dt: Optional[datetime] = None, fmt: str = '%Y-%m-%d %H:%M:%S') -> str`
格式化日期时间。

```python
from datetime import datetime
format_datetime(datetime(2023, 11, 6, 14, 30, 45))  # "2023-11-06 14:30:45"
format_datetime(fmt='%Y/%m/%d')  # "2023/11/06"
```

#### `parse_datetime(date_str: str, fmt: str = '%Y-%m-%d %H:%M:%S') -> datetime`
解析日期时间字符串。

```python
parse_datetime("2023-11-06 14:30:45")  # datetime(2023, 11, 6, 14, 30, 45)
```

#### `time_ago(dt: datetime) -> str`
返回相对时间描述。

```python
from datetime import datetime, timedelta
dt = datetime.now() - timedelta(hours=3)
time_ago(dt)  # "3小时前"
```

#### `add_days(dt: datetime, days: int) -> datetime`
增加或减少天数。

```python
from datetime import datetime
dt = datetime(2023, 11, 6)
add_days(dt, 5)   # datetime(2023, 11, 11)
add_days(dt, -5)  # datetime(2023, 11, 1)
```

## 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest
```

### 查看测试覆盖率

```bash
pytest --cov=yiwen_package --cov-report=html
```

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 作者

yw.hao (yiwenlemo@gmail.com)
