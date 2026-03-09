"""减脂时间预测模块。

基于当前体重和目标体重预测减脂所需时间。
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class WeightLossPrediction:
    """减脂预测结果"""

    total_loss_kg: float  # 总减重量（千克）
    monthly_loss_kg: float  # 每月减重量（千克）
    weekly_loss_kg: float  # 每周减重量（千克）
    estimated_months: float  # 预计月数
    estimated_weeks: float  # 预计周数


def predict_weight_loss_time(
    current_weight_kg: float, target_weight_kg: float
) -> WeightLossPrediction:
    """预测减脂所需时间。

    Args:
        current_weight_kg: 当前体重（千克）
        target_weight_kg: 目标体重（千克）

    Returns:
        WeightLossPrediction对象，包含预测结果

    Raises:
        ValueError: 如果体重参数无效
    """
    if current_weight_kg <= 0:
        raise ValueError(f"当前体重必须为正数，当前值：{current_weight_kg}")
    if target_weight_kg <= 0:
        raise ValueError(f"目标体重必须为正数，当前值：{target_weight_kg}")
    if target_weight_kg >= current_weight_kg:
        raise ValueError(
            f"目标体重必须小于当前体重，当前：{current_weight_kg}，目标：{target_weight_kg}"
        )

    total_loss = current_weight_kg - target_weight_kg
    monthly_loss = current_weight_kg * 0.05  # 每月最大减重5%
    weekly_loss = monthly_loss / 4  # 假设每月4周

    estimated_months = total_loss / monthly_loss
    estimated_weeks = estimated_months * 4

    return WeightLossPrediction(
        total_loss_kg=round(total_loss, 2),
        monthly_loss_kg=round(monthly_loss, 2),
        weekly_loss_kg=round(weekly_loss, 2),
        estimated_months=round(estimated_months, 2),
        estimated_weeks=round(estimated_weeks, 2),
    )


def calculate_weekly_adjustment(
    current_weight_kg: float, previous_weight_kg: float, expected_weekly_loss_kg: float
) -> int:
    """根据体重变化计算碳水化合物调整单位。

    Args:
        current_weight_kg: 当前体重（千克）
        previous_weight_kg: 上周体重（千克）
        expected_weekly_loss_kg: 预期每周减重量（千克）

    Returns:
        调整单位数：
            - 正数：需要增加碳水（体重下降过快）
            - 负数：需要减少碳水（体重下降过慢）
            - 0：无需调整

    Raises:
        ValueError: 如果体重参数无效
    """
    if current_weight_kg <= 0:
        raise ValueError(f"当前体重必须为正数，当前值：{current_weight_kg}")
    if previous_weight_kg <= 0:
        raise ValueError(f"上周体重必须为正数，当前值：{previous_weight_kg}")

    actual_loss = previous_weight_kg - current_weight_kg
    loss_difference = actual_loss - expected_weekly_loss_kg

    # 设置调整阈值：如果差异超过预期值的20%，则进行调整
    threshold = expected_weekly_loss_kg * 0.2

    if loss_difference > threshold:
        # 体重下降过快，需要增加碳水
        return 1
    elif loss_difference < -threshold:
        # 体重下降过慢，需要减少碳水
        return -1
    else:
        # 体重变化在预期范围内
        return 0
