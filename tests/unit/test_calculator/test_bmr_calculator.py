"""基础代谢率计算模块测试"""

import pytest

from src.fatloss.calculator.bmr_calculator import Gender, calculate_bmr


class TestBMRCalculator:
    """BMR计算器测试类"""

    def test_calculate_bmr_male(self):
        """测试男性BMR计算"""
        result = calculate_bmr(
            weight_kg=70, height_cm=175, age_years=30, gender=Gender.MALE
        )
        expected = 10 * 70 + 6.25 * 175 - 5 * 30 + 5
        expected = round(expected, 2)
        assert result == expected

    def test_calculate_bmr_female(self):
        """测试女性BMR计算"""
        result = calculate_bmr(
            weight_kg=60, height_cm=165, age_years=25, gender=Gender.FEMALE
        )
        expected = 10 * 60 + 6.25 * 165 - 5 * 25 - 161
        expected = round(expected, 2)
        assert result == expected

    def test_calculate_bmr_edge_cases(self):
        """测试边界值"""
        # 最小合理值
        result = calculate_bmr(
            weight_kg=30, height_cm=100, age_years=18, gender=Gender.MALE
        )
        assert result > 0

        # 最大合理值
        result = calculate_bmr(
            weight_kg=200, height_cm=250, age_years=80, gender=Gender.FEMALE
        )
        assert result > 0

    @pytest.mark.parametrize(
        "weight,height,age,gender,expected_error",
        [
            (29, 175, 30, Gender.MALE, "体重必须在30-200kg之间"),  # 体重过低
            (201, 175, 30, Gender.MALE, "体重必须在30-200kg之间"),  # 体重过高
            (70, 99, 30, Gender.MALE, "身高必须在100-250cm之间"),  # 身高过低
            (70, 251, 30, Gender.MALE, "身高必须在100-250cm之间"),  # 身高过高
            (70, 175, 17, Gender.MALE, "年龄必须在18-80岁之间"),  # 年龄过低
            (70, 175, 81, Gender.MALE, "年龄必须在18-80岁之间"),  # 年龄过高
        ],
    )
    def test_calculate_bmr_invalid_input(
        self, weight, height, age, gender, expected_error
    ):
        """测试无效输入"""
        with pytest.raises(ValueError) as exc_info:
            calculate_bmr(
                weight_kg=weight, height_cm=height, age_years=age, gender=gender
            )
        assert expected_error in str(exc_info.value)

    def test_calculate_bmr_precision(self):
        """测试计算精度"""
        result = calculate_bmr(
            weight_kg=70.5, height_cm=175.3, age_years=30, gender=Gender.MALE
        )
        expected = 10 * 70.5 + 6.25 * 175.3 - 5 * 30 + 5
        expected = round(expected, 2)
        assert result == expected
