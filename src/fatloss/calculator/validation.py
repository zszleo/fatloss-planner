"""输入验证工具模块。

提供通用的输入验证函数，用于验证计算器输入参数。
"""

from typing import Union, Optional


def validate_range(
    value: Union[int, float],
    min_val: Union[int, float],
    max_val: Union[int, float],
    param_name: str,
    unit: Optional[str] = None,
) -> None:
    """验证值是否在指定范围内。
    
    Args:
        value: 要验证的值
        min_val: 最小值（包含）
        max_val: 最大值（包含）
        param_name: 参数名称（用于错误消息）
        unit: 可选单位（如'kg', 'cm'等）
    
    Raises:
        ValueError: 如果值不在范围内
    """
    if not (min_val <= value <= max_val):
        unit_str = f"{unit}" if unit else ""
        raise ValueError(
            f"{param_name}必须在{min_val}-{max_val}{unit_str}之间，当前值：{value}"
        )/


def validate_positive(
    value: Union[int, float],
    param_name: str,
    allow_zero: bool = False,
) -> None:
    """验证值是否为正数。
    
    Args:
        value: 要验证的值
        param_name: 参数名称（用于错误消息）
        allow_zero: 是否允许零值（默认为False）
    
    Raises:
        ValueError: 如果值不是正数（或不允许零时为零）
    """
    if allow_zero:
        if value < 0:
            raise ValueError(f"{param_name}不能为负数，当前值：{value}")
    else:
        if value <= 0:
            raise ValueError(f"{param_name}必须为正数，当前值：{value}")