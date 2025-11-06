"""字符串处理工具函数"""


def is_empty(s: str) -> bool:
    """检查字符串是否为空或只包含空白字符"""
    return not s or s.isspace()


def truncate(s: str, length: int, suffix: str = '...') -> str:
    """截断字符串到指定长度，并添加后缀"""
    if len(s) <= length:
        return s
    return s[:length - len(suffix)] + suffix


def remove_prefix(s: str, prefix: str) -> str:
    """移除字符串的前缀（兼容 Python 3.9+）"""
    if s.startswith(prefix):
        return s[len(prefix):]
    return s


def remove_suffix(s: str, suffix: str) -> str:
    """移除字符串的后缀（兼容 Python 3.9+）"""
    if suffix and s.endswith(suffix):
        return s[:-len(suffix)]
    return s


def camel_to_snake(s: str) -> str:
    """将驼峰命名转换为下划线命名"""
    import re
    s = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s).lower()


def snake_to_camel(s: str, capitalize_first: bool = False) -> str:
    """将下划线命名转换为驼峰命名"""
    components = s.split('_')
    if capitalize_first:
        return ''.join(x.capitalize() for x in components)
    return components[0] + ''.join(x.capitalize() for x in components[1:])
