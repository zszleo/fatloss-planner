"""每日总能量消耗计算模块测试"""

import pytest

from src.fatloss.calculator.tdee_calculator import calculate_tdee


class TestTDEECalculator:
    """TDEE计算器测试类"""

    def test_calculate_tdee_basic(self):
        """测试基本TDEE计算"""
        result = calculate_tdee(bmr=2100, exercise_minutes=60)
        expected = 2100 + 60 * 10
        assert result == expected

    def test_calculate_tdee_zero_exercise(self):
        """测试零训练时间"""
        result = calculate_tdee(bmr=1800, exercise_minutes=0)
        assert result == 1800

    def test_calculate_tdee_max_exercise(self):
        """测试最大训练时间"""
        result = calculate_tdee(bmr=2000, exercise_minutes=300)
        assert result == 2000 + 300 * 10

    def test_calculate_tdee_float_input(self):
        """测试浮点数输入"""
        result = calculate_tdee(bmr=2100.5, exercise_minutes=45.5)
        expected = 2100.5 + 45.5 * 10
        expected = round(expected, 2)
        assert result == expected

    @pytest.mark.parametrize(
        "bmr,exercise_minutes,expected_error",
        [
            (0, 60, "BMR必须为正数"),  # BMR为零
            (-100, 60, "BMR必须为正数"),  # BMR为负数
            (2100, -10, "训练时间必须在0-300分钟之间"),  # 训练时间为负
            (2100, 301, "训练时间必须在0-300分钟之间"),  # 训练时间超过上限
        ],
    )
    def test_calculate_tdee_invalid_input(self, bmr, exercise_minutes, expected_error):
        """测试无效输入"""
        with pytest.raises(ValueError) as exc_info:
            calculate_tdee(bmr=bmr, exercise_minutes=exercise_minutes)
        assert expected_error in str(exc_info.value)

    def test_calculate_tdee_rounding(self):
        """测试结果舍入"""
        result = calculate_tdee(bmr=2100.123, exercise_minutes=60.789)
        # 验证结果保留两位小数
        assert result == round(2100.123 + 60.789 * 10, 2)
