"""营养素分配计算模块。

按照5:3:2比例分配碳水化合物、蛋白质和脂肪。
"""

from dataclasses import dataclass


@dataclass
class NutritionDistribution:
    """营养素分配结果"""

    carbohydrates_g: float  # 碳水化合物（克）
    protein_g: float  # 蛋白质（克）
    fat_g: float  # 脂肪（克）
    total_calories: float  # 总热量（大卡）


def calculate_nutrition(tdee: float) -> NutritionDistribution:
    """计算三大营养素分配（5:3:2比例）。

    Args:
        tdee: 每日总能量消耗（大卡）

    Returns:
        NutritionDistribution对象，包含各营养素克重

    Raises:
        ValueError: 如果TDEE不是正数
    """
    if tdee <= 0:
        raise ValueError(f"TDEE必须为正数，当前值：{tdee}")

    carb_ratio = 0.5  # 50% 碳水化合物
    protein_ratio = 0.3  # 30% 蛋白质
    fat_ratio = 0.2  # 20% 脂肪

    carb_calories = tdee * carb_ratio
    protein_calories = tdee * protein_ratio
    fat_calories = tdee * fat_ratio

    carb_grams = carb_calories / 4  # 4大卡/克
    protein_grams = protein_calories / 4  # 4大卡/克
    fat_grams = fat_calories / 9  # 9大卡/克

    return NutritionDistribution(
        carbohydrates_g=round(carb_grams, 2),
        protein_g=round(protein_grams, 2),
        fat_g=round(fat_grams, 2),
        total_calories=round(tdee, 2),
    )


def adjust_carbohydrates(base_carb_g: float, adjustment_units: int) -> float:
    """调整碳水化合物摄入量。

    Args:
        base_carb_g: 基础碳水化合物克重
        adjustment_units: 调整单位数（正数表示增加，负数表示减少，每个单位30g）

    Returns:
        调整后的碳水化合物克重

    Raises:
        ValueError: 如果调整后结果为负数
    """
    adjustment_g = adjustment_units * 30
    adjusted = base_carb_g + adjustment_g

    if adjusted < 0:
        raise ValueError(f"调整后碳水化合物不能为负数：{adjusted}g")

    return round(adjusted, 2)
