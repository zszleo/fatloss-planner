"""基础代谢率计算模块。

提供基于Mifflin-St Jeor公式的基础代谢率计算功能。
"""

from enum import Enum


class Gender(Enum):
    """性别枚举"""

    MALE = "male"
    FEMALE = "female"


def calculate_bmr(
    weight_kg: float, height_cm: float, age_years: int, gender: Gender
) -> float:
    """计算基础代谢率（BMR）。

    Args:
        weight_kg: 体重（千克）
        height_cm: 身高（厘米）
        age_years: 年龄（岁）
        gender: 性别（Gender.MALE或Gender.FEMALE）

    Returns:
        基础代谢率（大卡/天）

    Raises:
        ValueError: 如果输入参数超出合理范围
    """
    if not (30 <= weight_kg <= 200):
        raise ValueError(f"体重必须在30-200kg之间，当前值：{weight_kg}")
    if not (100 <= height_cm <= 250):
        raise ValueError(f"身高必须在100-250cm之间，当前值：{height_cm}")
    if not (18 <= age_years <= 80):
        raise ValueError(f"年龄必须在18-80岁之间，当前值：{age_years}")

    if gender == Gender.MALE:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age_years + 5
    else:  # Gender.FEMALE
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age_years - 161

    return round(bmr, 2)
