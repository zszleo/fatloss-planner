"""枚举类型定义

集中管理应用程序中使用的所有枚举类型。
"""

from enum import Enum


class Gender(str, Enum):
    """性别"""

    MALE = "男"
    FEMALE = "女"


class ActivityLevel(str, Enum):
    """活动水平"""

    SEDENTARY = "久坐"  # 久坐
    LIGHT = "轻度活动"  # 轻度活动
    MODERATE = "中度活动"  # 中度活动
    ACTIVE = "活跃"  # 活跃
    VERY_ACTIVE = "非常活跃"  # 非常活跃


class UnitSystem(str, Enum):
    """单位制"""

    METRIC = "metric"  # 公制（千克，厘米）
    IMPERIAL = "imperial"  # 英制（磅，英尺）


class Theme(str, Enum):
    """主题"""

    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


def get_enum_from_string(enum_cls: type[Enum], value: str, case_sensitive: bool = False) -> Enum:
    """将字符串转换为枚举值，支持不区分大小写。
    
    Args:
        enum_cls: 枚举类
        value: 字符串值
        case_sensitive: 是否区分大小写，默认为False（不区分大小写）
        
    Returns:
        对应的枚举成员
        
    Raises:
        ValueError: 如果找不到匹配的枚举值
    """
    if case_sensitive:
        return enum_cls(value)
    
    # 不区分大小写匹配
    value_lower = value.lower()
    for member in enum_cls:
        if member.value.lower() == value_lower:
            return member
    
    raise ValueError(f"无效的值 '{value}'，有效值: {[e.value for e in enum_cls]}")


def get_enum_values(enum_cls: type[Enum]) -> list[str]:
    """获取枚举的所有值列表。
    
    Args:
        enum_cls: 枚举类
        
    Returns:
        枚举值字符串列表
    """
    return [e.value for e in enum_cls]


def validate_enum_value(enum_cls: type[Enum], value: str, case_sensitive: bool = False) -> bool:
    """验证字符串是否是有效的枚举值。
    
    Args:
        enum_cls: 枚举类
        value: 要验证的字符串值
        case_sensitive: 是否区分大小写
        
    Returns:
        如果有效返回True，否则返回False
    """
    try:
        get_enum_from_string(enum_cls, value, case_sensitive)
        return True
    except ValueError:
        return False