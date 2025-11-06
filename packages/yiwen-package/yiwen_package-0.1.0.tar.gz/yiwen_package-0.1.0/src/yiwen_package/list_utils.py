"""列表和集合处理工具函数"""
from typing import List, TypeVar, Iterable, Any

T = TypeVar('T')


def chunk(lst: List[T], size: int) -> List[List[T]]:
    """将列表分割成指定大小的块"""
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def flatten(nested_list: List[Any]) -> List[Any]:
    """展平嵌套列表"""
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def unique(lst: List[T], key=None) -> List[T]:
    """去重，保持原始顺序"""
    if key is None:
        seen = set()
        result = []
        for item in lst:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result
    else:
        seen = set()
        result = []
        for item in lst:
            k = key(item)
            if k not in seen:
                seen.add(k)
                result.append(item)
        return result


def group_by(items: Iterable[T], key_func) -> dict:
    """按指定函数分组"""
    groups = {}
    for item in items:
        key = key_func(item)
        if key not in groups:
            groups[key] = []
        groups[key].append(item)
    return groups
