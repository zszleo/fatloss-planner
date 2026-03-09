"""每日总能量消耗计算模块。

计算基于基础代谢率和训练消耗的总能量消耗。
"""


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
    if bmr <= 0:
        raise ValueError(f"BMR必须为正数，当前值：{bmr}")
    if not (0 <= exercise_minutes <= 300):
        raise ValueError(f"训练时间必须在0-300分钟之间，当前值：{exercise_minutes}")

    exercise_calories = exercise_minutes * 10
    tdee = bmr + exercise_calories

    return round(tdee, 2)
