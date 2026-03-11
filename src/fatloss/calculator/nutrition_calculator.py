"""营养素分配计算模块。

按照5:3:2比例分配碳水化合物、蛋白质和脂肪。
"""

from dataclasses import dataclass

from fatloss.utils.validation import validate_positive


class NutritionConstants:
    """营养计算相关常量"""
    
    # 宏量营养素比例
    CARBOHYDRATE_RATIO = 0.5  # 50% 碳水化合物
    PROTEIN_RATIO = 0.3  # 30% 蛋白质
    FAT_RATIO = 0.2  # 20% 脂肪
    
    # 每克营养素的热量值（大卡/克）
    CALORIES_PER_GRAM_CARB = 4.0
    CALORIES_PER_GRAM_PROTEIN = 4.0
    CALORIES_PER_GRAM_FAT = 9.0
    
    # 碳水化合物调整相关
    CARB_ADJUSTMENT_UNIT_G = 30  # 每个调整单位30克


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
    validate_positive(tdee, "TDEE")

    carb_calories = tdee * NutritionConstants.CARBOHYDRATE_RATIO
    protein_calories = tdee * NutritionConstants.PROTEIN_RATIO
    fat_calories = tdee * NutritionConstants.FAT_RATIO

    carb_grams = carb_calories / NutritionConstants.CALORIES_PER_GRAM_CARB
    protein_grams = protein_calories / NutritionConstants.CALORIES_PER_GRAM_PROTEIN
    fat_grams = fat_calories / NutritionConstants.CALORIES_PER_GRAM_FAT

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
    adjustment_g = adjustment_units * NutritionConstants.CARB_ADJUSTMENT_UNIT_G
    adjusted = base_carb_g + adjustment_g

    if adjusted < 0:
        raise ValueError(f"调整后碳水化合物不能为负数：{adjusted}g")

    return round(adjusted, 2)
