"""营养素分配计算模块测试"""

import pytest

from src.fatloss.calculator.nutrition_calculator import (
    NutritionDistribution,
    adjust_carbohydrates,
    calculate_nutrition,
)


class TestNutritionCalculator:
    """营养素计算器测试类"""

    def test_calculate_nutrition_basic(self):
        """测试基本营养素分配"""
        result = calculate_nutrition(tdee=2700)
        expected_carb = 2700 * 0.5 / 4  # 337.5
        expected_protein = 2700 * 0.3 / 4  # 202.5
        expected_fat = 2700 * 0.2 / 9  # 60.0

        assert isinstance(result, NutritionDistribution)
        assert result.carbohydrates_g == pytest.approx(expected_carb, abs=0.01)
        assert result.protein_g == pytest.approx(expected_protein, abs=0.01)
        assert result.fat_g == pytest.approx(expected_fat, abs=0.01)
        assert result.total_calories == 2700

    def test_calculate_nutrition_532_ratio(self):
        """验证5:3:2比例"""
        result = calculate_nutrition(tdee=2000)
        carb_calories = result.carbohydrates_g * 4
        protein_calories = result.protein_g * 4
        fat_calories = result.fat_g * 9

        total = carb_calories + protein_calories + fat_calories
        assert total == pytest.approx(2000, abs=0.05)

        carb_ratio = carb_calories / 2000
        protein_ratio = protein_calories / 2000
        fat_ratio = fat_calories / 2000

        assert carb_ratio == pytest.approx(0.5, abs=0.01)
        assert protein_ratio == pytest.approx(0.3, abs=0.01)
        assert fat_ratio == pytest.approx(0.2, abs=0.01)

    def test_calculate_nutrition_edge_cases(self):
        """测试边界值"""
        # 最小TDEE
        result = calculate_nutrition(tdee=1)
        assert result.carbohydrates_g > 0
        assert result.protein_g > 0
        assert result.fat_g > 0

        # 较大TDEE
        result = calculate_nutrition(tdee=5000)
        assert result.carbohydrates_g > 0

    def test_calculate_nutrition_invalid_input(self):
        """测试无效输入"""
        with pytest.raises(ValueError) as exc_info:
            calculate_nutrition(tdee=0)
        assert "TDEE必须为正数" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            calculate_nutrition(tdee=-100)
        assert "TDEE必须为正数" in str(exc_info.value)

    def test_adjust_carbohydrates_increase(self):
        """测试增加碳水化合物"""
        base_carb = 300
        adjusted = adjust_carbohydrates(base_carb, adjustment_units=2)
        assert adjusted == base_carb + 60  # 2 * 30g

    def test_adjust_carbohydrates_decrease(self):
        """测试减少碳水化合物"""
        base_carb = 300
        adjusted = adjust_carbohydrates(base_carb, adjustment_units=-1)
        assert adjusted == base_carb - 30

    def test_adjust_carbohydrates_no_change(self):
        """测试无调整"""
        base_carb = 300
        adjusted = adjust_carbohydrates(base_carb, adjustment_units=0)
        assert adjusted == base_carb

    def test_adjust_carbohydrates_negative_result(self):
        """测试调整后结果为负数"""
        base_carb = 20
        with pytest.raises(ValueError) as exc_info:
            adjust_carbohydrates(base_carb, adjustment_units=-1)
        assert "调整后碳水化合物不能为负数" in str(exc_info.value)

    def test_adjust_carbohydrates_float_input(self):
        """测试浮点数输入"""
        base_carb = 300.5
        adjusted = adjust_carbohydrates(base_carb, adjustment_units=1)
        assert adjusted == round(base_carb + 30, 2)
