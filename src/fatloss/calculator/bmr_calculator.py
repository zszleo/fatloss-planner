"""基础代谢率计算模块。

提供基于Mifflin-St Jeor公式的基础代谢率计算功能。
"""

from fatloss.models.enums import Gender
from fatloss.utils.validation import validate_range, validate_positive


class BMRConstants:
    """BMR计算相关常量（基于Mifflin-St Jeor公式）"""
    
    WEIGHT_COEFFICIENT = 10.0
    HEIGHT_COEFFICIENT = 6.25
    AGE_COEFFICIENT = 5.0
    
    # 性别常数
    MALE_CONSTANT = 5.0
    FEMALE_CONSTANT = -161.0
    
    # 输入验证范围
    WEIGHT_RANGE_MIN = 30
    WEIGHT_RANGE_MAX = 200
    
    HEIGHT_RANGE_MIN = 100
    HEIGHT_RANGE_MAX = 250
    
    AGE_RANGE_MIN = 18
    AGE_RANGE_MAX = 80


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
    validate_range(weight_kg, BMRConstants.WEIGHT_RANGE_MIN, BMRConstants.WEIGHT_RANGE_MAX, "体重", "kg")
    validate_range(height_cm, BMRConstants.HEIGHT_RANGE_MIN, BMRConstants.HEIGHT_RANGE_MAX, "身高", "cm")
    validate_range(age_years, BMRConstants.AGE_RANGE_MIN, BMRConstants.AGE_RANGE_MAX, "年龄", "岁")

    if gender == Gender.MALE:
        bmr = (
            BMRConstants.WEIGHT_COEFFICIENT * weight_kg +
            BMRConstants.HEIGHT_COEFFICIENT * height_cm -
            BMRConstants.AGE_COEFFICIENT * age_years +
            BMRConstants.MALE_CONSTANT
        )
    else:  # Gender.FEMALE
        bmr = (
            BMRConstants.WEIGHT_COEFFICIENT * weight_kg +
            BMRConstants.HEIGHT_COEFFICIENT * height_cm -
            BMRConstants.AGE_COEFFICIENT * age_years +
            BMRConstants.FEMALE_CONSTANT
        )

    return round(bmr, 2)
