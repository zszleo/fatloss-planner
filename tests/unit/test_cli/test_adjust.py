#!/usr/bin/env python3
"""调整命令CLI单元测试。"""

from datetime import date
from unittest.mock import Mock, patch
import pytest
from click.testing import CliRunner

from fatloss.cli.main import cli


class TestAdjustCommand:
    """调整命令测试类。"""

    @pytest.fixture
    def runner(self):
        """提供CliRunner实例。"""
        return CliRunner()

    def test_adjust_help(self, runner):
        """测试adjust命令帮助信息。"""
        result = runner.invoke(cli, ["adjust", "--help"])
        assert result.exit_code == 0
        assert "基于体重变化调整营养计划" in result.output

    @patch('fatloss.cli.commands.adjust.PlannerService')
    def test_adjust_manual_positive_without_apply(self, mock_planner_class, runner):
        """测试手动调整（正数）但不应用。"""
        mock_planner = Mock()
        mock_planner_class.return_value = mock_planner

        result = runner.invoke(cli, [
            "adjust",
            "--user-id", "1",
            "--manual-adjustment", "2"
        ])

        assert result.exit_code == 0
        assert "🔧 手动调整模式" in result.output
        assert "调整单位数: 2" in result.output
        assert "调整方向: 增加碳水化合物摄入" in result.output
        assert "使用 --apply 标志将调整应用到今日营养计划" in result.output
        # 确保没有调用生成计划的方法
        assert not mock_planner.generate_daily_nutrition_plan.called

    @patch('fatloss.cli.commands.adjust.PlannerService')
    def test_adjust_manual_negative_without_apply(self, mock_planner_class, runner):
        """测试手动调整（负数）但不应用。"""
        mock_planner = Mock()
        mock_planner_class.return_value = mock_planner

        result = runner.invoke(cli, [
            "adjust",
            "--user-id", "1",
            "--manual-adjustment", "-1"
        ])

        assert result.exit_code == 0
        assert "🔧 手动调整模式" in result.output
        assert "调整单位数: -1" in result.output
        assert "调整方向: 减少碳水化合物摄入" in result.output
        assert "使用 --apply 标志将调整应用到今日营养计划" in result.output

    @patch('fatloss.cli.commands.adjust.PlannerService')
    def test_adjust_manual_zero_without_apply(self, mock_planner_class, runner):
        """测试手动调整（零）但不应用。"""
        mock_planner = Mock()
        mock_planner_class.return_value = mock_planner

        result = runner.invoke(cli, [
            "adjust",
            "--user-id", "1",
            "--manual-adjustment", "0"
        ])

        assert result.exit_code == 0
        assert "🔧 手动调整模式" in result.output
        assert "调整单位数: 0" in result.output
        assert "调整方向: 无碳水化合物摄入" in result.output

    @patch('fatloss.cli.commands.adjust.PlannerService')
    @patch('fatloss.planner.planner_service.NutritionPlanRequest')
    def test_adjust_manual_positive_with_apply_success(self, mock_request_class, mock_planner_class, runner):
        """测试手动调整（正数）并成功应用。"""
        mock_planner = Mock()
        mock_daily_plan = Mock()
        mock_daily_plan.id = 100
        mock_daily_plan.nutrition = Mock(carbohydrates_g=180)
        mock_planner.generate_daily_nutrition_plan.return_value = mock_daily_plan
        mock_planner_class.return_value = mock_planner
        
        mock_request = Mock()
        mock_request_class.return_value = mock_request

        result = runner.invoke(cli, [
            "adjust",
            "--user-id", "1",
            "--manual-adjustment", "2",
            "--apply"
        ])

        assert result.exit_code == 0
        assert "🔧 手动调整模式" in result.output
        assert "调整单位数: 2" in result.output
        assert "调整方向: 增加碳水化合物摄入" in result.output
        assert "✅ 已应用调整到今日营养计划" in result.output
        assert "计划ID: 100" in result.output
        assert "调整后碳水化合物: 180 g" in result.output
        
        # 验证NutritionPlanRequest创建
        mock_request_class.assert_called_once_with(
            user_id=1,
            plan_date=date.today(),
            exercise_minutes=60.0,
            adjustment_units=2,
        )
        
        # 验证生成计划调用
        mock_planner.generate_daily_nutrition_plan.assert_called_once_with(mock_request)

    @patch('fatloss.cli.commands.adjust.PlannerService')
    @patch('fatloss.planner.planner_service.NutritionPlanRequest')
    def test_adjust_manual_negative_with_apply_success(self, mock_request_class, mock_planner_class, runner):
        """测试手动调整（负数）并成功应用。"""
        mock_planner = Mock()
        mock_daily_plan = Mock()
        mock_daily_plan.id = 101
        mock_daily_plan.nutrition = Mock(carbohydrates_g=150)
        mock_planner.generate_daily_nutrition_plan.return_value = mock_daily_plan
        mock_planner_class.return_value = mock_planner
        
        mock_request = Mock()
        mock_request_class.return_value = mock_request

        result = runner.invoke(cli, [
            "adjust",
            "--user-id", "1",
            "--manual-adjustment", "-1",
            "--apply"
        ])

        assert result.exit_code == 0
        assert "🔧 手动调整模式" in result.output
        assert "调整单位数: -1" in result.output
        assert "调整方向: 减少碳水化合物摄入" in result.output
        assert "✅ 已应用调整到今日营养计划" in result.output
        
        # 验证NutritionPlanRequest创建
        mock_request_class.assert_called_once_with(
            user_id=1,
            plan_date=date.today(),
            exercise_minutes=60.0,
            adjustment_units=-1,
        )

    @patch('fatloss.cli.commands.adjust.PlannerService')
    @patch('fatloss.planner.planner_service.NutritionPlanRequest')
    def test_adjust_manual_with_apply_failure(self, mock_request_class, mock_planner_class, runner):
        """测试手动调整应用失败。"""
        mock_planner = Mock()
        mock_planner.generate_daily_nutrition_plan.side_effect = Exception("数据库错误")
        mock_planner_class.return_value = mock_planner
        
        mock_request = Mock()
        mock_request_class.return_value = mock_request

        result = runner.invoke(cli, [
            "adjust",
            "--user-id", "1",
            "--manual-adjustment", "1",
            "--apply"
        ])

        assert result.exit_code != 0
        assert "应用调整失败" in result.output
        assert "数据库错误" in result.output

    @patch('fatloss.cli.commands.adjust.PlannerService')
    def test_adjust_automatic_positive_recommendation(self, mock_planner_class, runner):
        """测试自动调整建议（正数建议）。"""
        mock_planner = Mock()
        mock_planner.get_weekly_adjustment_recommendation.return_value = (2, "体重下降过快，建议增加碳水摄入")
        mock_planner_class.return_value = mock_planner

        result = runner.invoke(cli, [
            "adjust",
            "--user-id", "1"
        ])

        assert result.exit_code == 0
        assert "📊 分析体重变化数据..." in result.output
        assert "💡 每周调整建议" in result.output
        assert "👤 用户ID: 1" in result.output
        assert "📅 分析日期:" in result.output
        assert "✅ 建议: 增加 2 单位碳水化合物摄入" in result.output
        assert "体重下降过快，建议增加碳水摄入" in result.output
        assert "📋 调整单位说明:" in result.output
        assert "🔧 应用建议调整:" in result.output
        assert "fatloss-planner adjust --user-id 1 --manual-adjustment 2 --apply" in result.output
        
        # 验证调用
        mock_planner.get_weekly_adjustment_recommendation.assert_called_once_with(1)

    @patch('fatloss.cli.commands.adjust.PlannerService')
    def test_adjust_automatic_negative_recommendation(self, mock_planner_class, runner):
        """测试自动调整建议（负数建议）。"""
        mock_planner = Mock()
        mock_planner.get_weekly_adjustment_recommendation.return_value = (-1, "体重下降过慢，建议减少碳水摄入")
        mock_planner_class.return_value = mock_planner

        result = runner.invoke(cli, [
            "adjust",
            "--user-id", "1"
        ])

        assert result.exit_code == 0
        assert "✅ 建议: 减少 1 单位碳水化合物摄入" in result.output
        assert "体重下降过慢，建议减少碳水摄入" in result.output
        assert "fatloss-planner adjust --user-id 1 --manual-adjustment -1 --apply" in result.output

    @patch('fatloss.cli.commands.adjust.PlannerService')
    def test_adjust_automatic_zero_recommendation(self, mock_planner_class, runner):
        """测试自动调整建议（零建议）。"""
        mock_planner = Mock()
        mock_planner.get_weekly_adjustment_recommendation.return_value = (0, "体重变化正常，无需调整")
        mock_planner_class.return_value = mock_planner

        result = runner.invoke(cli, [
            "adjust",
            "--user-id", "1"
        ])

        assert result.exit_code == 0
        assert "✅ 建议: 无需调整" in result.output
        assert "体重变化正常，无需调整" in result.output
        # 零调整时不显示应用建议命令
        assert "🔧 应用建议调整:" not in result.output

    @patch('fatloss.cli.commands.adjust.PlannerService')
    def test_adjust_automatic_recommendation_failure(self, mock_planner_class, runner):
        """测试自动调整建议失败。"""
        mock_planner = Mock()
        mock_planner.get_weekly_adjustment_recommendation.side_effect = Exception("数据不足")
        mock_planner_class.return_value = mock_planner

        result = runner.invoke(cli, [
            "adjust",
            "--user-id", "1"
        ])

        assert result.exit_code != 0
        assert "获取调整建议失败" in result.output
        assert "数据不足" in result.output