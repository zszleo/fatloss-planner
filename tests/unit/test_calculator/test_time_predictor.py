"""减脂时间预测模块测试"""

import pytest

from src.fatloss.calculator.time_predictor import (
    WeightLossPrediction,
    calculate_weekly_adjustment,
    predict_weight_loss_time,
)


class TestTimePredictor:
    """减脂时间预测测试类"""

    def test_predict_weight_loss_time_basic(self):
        """测试基本减脂时间预测"""
        result = predict_weight_loss_time(current_weight_kg=103, target_weight_kg=75)
        assert isinstance(result, WeightLossPrediction)
        assert result.total_loss_kg == 28  # 103 - 75
        assert result.monthly_loss_kg == pytest.approx(103 * 0.05, abs=0.01)  # 5.15
        assert result.weekly_loss_kg == pytest.approx(
            103 * 0.05 / 4, abs=0.01
        )  # 1.2875
        assert result.estimated_months == pytest.approx(
            28 / (103 * 0.05), abs=0.01
        )  # 约5.44
        assert result.estimated_weeks == pytest.approx(28 / (103 * 0.05) * 4, abs=0.01)

    def test_predict_weight_loss_time_small_loss(self):
        """测试小幅减重"""
        result = predict_weight_loss_time(current_weight_kg=70, target_weight_kg=65)
        assert result.total_loss_kg == 5
        assert result.monthly_loss_kg == pytest.approx(70 * 0.05, abs=0.01)  # 3.5

    def test_predict_weight_loss_time_invalid_input(self):
        """测试无效输入"""
        with pytest.raises(ValueError) as exc_info:
            predict_weight_loss_time(current_weight_kg=0, target_weight_kg=65)
        assert "当前体重必须为正数" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            predict_weight_loss_time(current_weight_kg=70, target_weight_kg=0)
        assert "目标体重必须为正数" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            predict_weight_loss_time(current_weight_kg=70, target_weight_kg=75)
        assert "目标体重必须小于当前体重" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            predict_weight_loss_time(current_weight_kg=70, target_weight_kg=70)
        assert "目标体重必须小于当前体重" in str(exc_info.value)

    def test_calculate_weekly_adjustment_increase(self):
        """测试需要增加碳水的情况（体重下降过快）"""
        # 预期每周减1kg，实际减了2kg（下降过快）
        adjustment = calculate_weekly_adjustment(
            current_weight_kg=98, previous_weight_kg=100, expected_weekly_loss_kg=1
        )
        assert adjustment == 1  # 需要增加碳水

    def test_calculate_weekly_adjustment_decrease(self):
        """测试需要减少碳水的情况（体重下降过慢）"""
        # 预期每周减1kg，实际减了0.1kg（下降过慢）
        adjustment = calculate_weekly_adjustment(
            current_weight_kg=99.9, previous_weight_kg=100, expected_weekly_loss_kg=1
        )
        assert adjustment == -1  # 需要减少碳水

    def test_calculate_weekly_adjustment_no_change(self):
        """测试无需调整的情况（体重变化在预期范围内）"""
        # 预期每周减1kg，实际减了1kg（正好）
        adjustment = calculate_weekly_adjustment(
            current_weight_kg=99, previous_weight_kg=100, expected_weekly_loss_kg=1
        )
        assert adjustment == 0  # 无需调整

        # 预期每周减1kg，实际减了0.9kg（在阈值内）
        adjustment = calculate_weekly_adjustment(
            current_weight_kg=99.1, previous_weight_kg=100, expected_weekly_loss_kg=1
        )
        assert adjustment == 0

    def test_calculate_weekly_adjustment_invalid_input(self):
        """测试无效体重输入"""
        with pytest.raises(ValueError) as exc_info:
            calculate_weekly_adjustment(
                current_weight_kg=0, previous_weight_kg=100, expected_weekly_loss_kg=1
            )
        assert "当前体重必须为正数" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            calculate_weekly_adjustment(
                current_weight_kg=99, previous_weight_kg=0, expected_weekly_loss_kg=1
            )
        assert "上周体重必须为正数" in str(exc_info.value)

    def test_calculate_weekly_adjustment_weight_gain(self):
        """测试体重增加的情况"""
        # 体重增加（负减重）
        adjustment = calculate_weekly_adjustment(
            current_weight_kg=101, previous_weight_kg=100, expected_weekly_loss_kg=1
        )
        # 实际减重为-1kg，与预期-1kg差异为-2kg，应减少碳水
        assert adjustment == -1

    def test_calculate_weekly_adjustment_threshold(self):
        """测试调整阈值"""
        # 阈值 = 1kg * 0.2 = 0.2kg
        # 实际减重0.79kg，与预期1kg差异-0.21kg，超过阈值下限
        adjustment = calculate_weekly_adjustment(
            current_weight_kg=99.21, previous_weight_kg=100, expected_weekly_loss_kg=1
        )
        assert adjustment == -1

        # 实际减重0.81kg，与预期1kg差异-0.19kg，在阈值内
        adjustment = calculate_weekly_adjustment(
            current_weight_kg=99.19, previous_weight_kg=100, expected_weekly_loss_kg=1
        )
        assert adjustment == 0
