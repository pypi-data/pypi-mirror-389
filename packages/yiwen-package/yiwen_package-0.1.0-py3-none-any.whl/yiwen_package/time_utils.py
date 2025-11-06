"""时间日期工具函数"""
from datetime import datetime, timedelta
from typing import Optional


def now_timestamp() -> int:
    """获取当前时间戳（秒）"""
    return int(datetime.now().timestamp())


def now_timestamp_ms() -> int:
    """获取当前时间戳（毫秒）"""
    return int(datetime.now().timestamp() * 1000)


def format_datetime(dt: Optional[datetime] = None, fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
    """格式化日期时间"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime(fmt)


def parse_datetime(date_str: str, fmt: str = '%Y-%m-%d %H:%M:%S') -> datetime:
    """解析日期时间字符串"""
    return datetime.strptime(date_str, fmt)


def time_ago(dt: datetime) -> str:
    """返回相对时间描述（例如：3小时前）"""
    now = datetime.now()
    diff = now - dt

    seconds = diff.total_seconds()

    if seconds < 60:
        return f"{int(seconds)}秒前"
    elif seconds < 3600:
        return f"{int(seconds / 60)}分钟前"
    elif seconds < 86400:
        return f"{int(seconds / 3600)}小时前"
    elif seconds < 2592000:
        return f"{int(seconds / 86400)}天前"
    elif seconds < 31536000:
        return f"{int(seconds / 2592000)}个月前"
    else:
        return f"{int(seconds / 31536000)}年前"


def add_days(dt: datetime, days: int) -> datetime:
    """增加或减少天数"""
    return dt + timedelta(days=days)
