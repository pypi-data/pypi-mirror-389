"""文件操作工具函数"""
import json
from pathlib import Path
from typing import Any, Union


def read_json(file_path: Union[str, Path]) -> Any:
    """读取 JSON 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json(file_path: Union[str, Path], data: Any, indent: int = 2) -> None:
    """写入 JSON 文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def ensure_dir(dir_path: Union[str, Path]) -> Path:
    """确保目录存在，如果不存在则创建"""
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size(file_path: Union[str, Path]) -> int:
    """获取文件大小（字节）"""
    return Path(file_path).stat().st_size


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小为人类可读格式"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"
