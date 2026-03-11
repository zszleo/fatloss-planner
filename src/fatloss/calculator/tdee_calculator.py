"""每日总能量消耗计算模块。

计算基于基础代谢率和训练消耗的总能量消耗。
"""

from fatloss.utils.validation import validate_range, validate_positive


class TDEEConstants:
    """TDEE计算相关常量"""
    
    CALORIES_PER_MINUTE_EXERCISE = 10.0  # 每分钟运动消耗10大卡
    
    # 输入验证范围
    EXERCISE_MINUTES_RANGE_MIN = 0
    EXERCISE_MINUTES_RANGE_MAX = 300


def calculate_tdee(bmr: float, exercise_minutes: float) -> float:
    """计算每日总能量消耗（TDEE）。

    Args:
        bmr: 基础代谢率（大卡/天）
        exercise_minutes: 训练时间（分钟/天）

    Returns:
        每日总能量消耗（大卡/天）

    Raises:
        ValueError: 如果输入参数超出合理范围
    """
    validate_positive(bmr, "BMR")
    validate_range(exercise_minutes, TDEEConstants.EXERCISE_MINUTES_RANGE_MIN, TDEEConstants.EXERCISE_MINUTES_RANGE_MAX, "训练时间", "分钟")

    exercise_calories = exercise_minutes * TDEEConstants.CALORIES_PER_MINUTE_EXERCISE
    tdee = bmr + exercise_calories

    return round(tdee, 2)
