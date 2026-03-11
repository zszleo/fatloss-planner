#!/usr/bin/env python3
"""计划命令CLI单元测试。"""

from datetime import date
from unittest.mock import Mock, patch
import pytest
from click.testing import CliRunner

from fatloss.cli.main import cli


class TestPlanCommand:
    """计划命令测试类。"""

    @pytest.fixture
    def runner(self):
        """提供CliRunner实例。"""
        return CliRunner()

    def test_plan_help(self, runner):
        """测试plan命令帮助信息。"""
        result = runner.invoke(cli, ["plan", "--help"])
        assert result.exit_code == 0
        assert "生成减脂营养计划" in result.output

    def test_plan_daily_help(self, runner):
        """测试plan daily命令帮助信息。"""
        result = runner.invoke(cli, ["plan", "daily", "--help"])
        assert result.exit_code == 0
        assert "生成每日营养计划" in result.output

    def test_plan_weekly_help(self, runner):
        """测试plan weekly命令帮助信息。"""
        result = runner.invoke(cli, ["plan", "weekly", "--help"])
        assert result.exit_code == 0
        assert "生成每周营养计划" in result.output

    @patch('fatloss.cli.commands.plan.PlannerService')
    def test_plan_daily_with_existing_user(self, mock_planner_class, runner):
        """测试为现有用户生成每日营养计划。"""
        mock_planner = Mock()
        # 模拟每日营养计划
        mock_daily_plan = Mock(
            id=1001,
            plan_date=date(2026, 3, 12),
            target_tdee=2200.0,
            is_adjusted=False,
            adjustment_units=0,
            nutrition=Mock(
                carbohydrates_g=275.0,
                protein_g=165.0,
                fat_g=73.3,
                total_calories=2200.0
            )
        )
        mock_planner.generate_daily_nutrition_plan.return_value = mock_daily_plan
        mock_planner_class.return_value = mock_planner

        result = runner.invoke(cli, [
            "plan", "daily",
            "--user-id", "1",
            "--plan-date", "2026-03-12",
            "--exercise", "60",
            "--adjustment", "0"
        ])

        assert result.exit_code == 0
        assert "每日营养计划" in result.output
        assert "用户ID: 1" in result.output
        assert "计划日期: 2026-03-12" in result.output
        assert "TDEE目标: 2200.0 大卡/天" in result.output
        assert "碳水化合物: 275.0 g" in result.output
        assert "蛋白质: 165.0 g" in result.output
        assert "脂肪: 73.3 g" in result.output
        assert "总热量: 2200.0 大卡" in result.output
        assert "碳水化合物未调整" in result.output
        
        # 验证generate_daily_nutrition_plan调用
        mock_planner.generate_daily_nutrition_plan.assert_called_once()
        call_args = mock_planner.generate_daily_nutrition_plan.call_args
        assert call_args[0][0].user_id == 1
        assert call_args[0][0].plan_date == date(2026, 3, 12)
        assert call_args[0][0].exercise_minutes == 60.0
        assert call_args[0][0].adjustment_units == 0

    @patch('fatloss.cli.commands.plan.PlannerService')
    def test_plan_daily_create_new_user(self, mock_planner_class, runner):
        """测试创建新用户并生成每日营养计划。"""
        mock_planner = Mock()
        # 模拟创建用户
        mock_user = Mock(id=123, name="测试用户")
        mock_planner.create_user_profile.return_value = mock_user
        
        # 模拟每日营养计划
        mock_daily_plan = Mock(
            id=1002,
            plan_date=date(2026, 3, 12),
            target_tdee=2000.0,
            is_adjusted=True,
            adjustment_units=1,
            nutrition=Mock(
                carbohydrates_g=305.0,  # 调整后
                protein_g=165.0,
                fat_g=73.3,
                total_calories=2200.0
            )
        )
        mock_planner.generate_daily_nutrition_plan.return_value = mock_daily_plan
        mock_planner_class.return_value = mock_planner

        result = runner.invoke(cli, [
            "plan", "daily",
            "--name", "测试用户",
            "--gender", "男",
            "--birth-date", "1995-01-01",
            "--height", "175",
            "--weight", "70",
            "--activity-level", "中度活动",
            "--plan-date", "2026-03-12",
            "--exercise", "60",
            "--adjustment", "1"
        ])

        assert result.exit_code == 0
        assert "创建新用户" in result.output
        assert "用户ID: 123" in result.output
        assert "每日营养计划" in result.output
        assert "碳水化合物已调整" in result.output
        assert "增加 30g" in result.output
        
        # 验证create_user_profile调用
        mock_planner.create_user_profile.assert_called_once()
        user_call_args = mock_planner.create_user_profile.call_args
        assert user_call_args.kwargs["name"] == "测试用户"
        assert user_call_args.kwargs["height_cm"] == 175.0
        assert user_call_args.kwargs["initial_weight_kg"] == 70.0
        assert user_call_args.kwargs["activity_level"] == "中度活动"
        
        # 验证generate_daily_nutrition_plan调用
        mock_planner.generate_daily_nutrition_plan.assert_called_once()
        plan_call_args = mock_planner.generate_daily_nutrition_plan.call_args
        assert plan_call_args[0][0].user_id == 123
        assert plan_call_args[0][0].adjustment_units == 1

    @patch('fatloss.cli.commands.plan.PlannerService')
    def test_plan_daily_missing_new_user_params(self, mock_planner_class, runner):
        """测试创建新用户时缺少必要参数。"""
        mock_planner = Mock()
        mock_planner_class.return_value = mock_planner

        # 缺少--name参数
        result = runner.invoke(cli, [
            "plan", "daily",
            "--gender", "male",
            "--birth-date", "1995-01-01",
            "--height", "175",
            "--weight", "70",
            "--plan-date", "2026-03-12"
        ])

        assert result.exit_code != 0
        assert "创建新用户需要以下参数" in result.output
        assert "--name" in result.output
        # 不应该调用create_user_profile
        mock_planner.create_user_profile.assert_not_called()

    @patch('fatloss.cli.commands.plan.PlannerService')
    def test_plan_daily_missing_gender_param(self, mock_planner_class, runner):
        """测试创建新用户时缺少gender参数。"""
        mock_planner = Mock()
        mock_planner_class.return_value = mock_planner

        # 缺少--gender参数，但提供其他参数
        result = runner.invoke(cli, [
            "plan", "daily",
            "--name", "测试用户",
            "--birth-date", "1995-01-01",
            "--height", "175",
            "--weight", "70",
            "--plan-date", "2026-03-12"
        ])

        assert result.exit_code != 0
        assert "创建新用户需要以下参数" in result.output
        assert "--gender" in result.output
        # 不应该调用create_user_profile
        mock_planner.create_user_profile.assert_not_called()

    @patch('fatloss.cli.commands.plan.PlannerService')
    def test_plan_daily_missing_birth_date_param(self, mock_planner_class, runner):
        """测试创建新用户时缺少birth-date参数。"""
        mock_planner = Mock()
        mock_planner_class.return_value = mock_planner

        # 缺少--birth-date参数
        result = runner.invoke(cli, [
            "plan", "daily",
            "--name", "测试用户",
            "--gender", "male",
            "--height", "175",
            "--weight", "70",
            "--plan-date", "2026-03-12"
        ])

        assert result.exit_code != 0
        assert "创建新用户需要以下参数" in result.output
        assert "--birth-date" in result.output
        mock_planner.create_user_profile.assert_not_called()

    @patch('fatloss.cli.commands.plan.PlannerService')
    def test_plan_daily_missing_height_param(self, mock_planner_class, runner):
        """测试创建新用户时缺少height参数。"""
        mock_planner = Mock()
        mock_planner_class.return_value = mock_planner

        # 缺少--height参数
        result = runner.invoke(cli, [
            "plan", "daily",
            "--name", "测试用户",
            "--gender", "male",
            "--birth-date", "1995-01-01",
            "--weight", "70",
            "--plan-date", "2026-03-12"
        ])

        assert result.exit_code != 0
        assert "创建新用户需要以下参数" in result.output
        assert "--height" in result.output
        mock_planner.create_user_profile.assert_not_called()

    @patch('fatloss.cli.commands.plan.PlannerService')
    def test_plan_daily_missing_weight_param(self, mock_planner_class, runner):
        """测试创建新用户时缺少weight参数。"""
        mock_planner = Mock()
        mock_planner_class.return_value = mock_planner

        # 缺少--weight参数
        result = runner.invoke(cli, [
            "plan", "daily",
            "--name", "测试用户",
            "--gender", "male",
            "--birth-date", "1995-01-01",
            "--height", "175",
            "--plan-date", "2026-03-12"
        ])

        assert result.exit_code != 0
        assert "创建新用户需要以下参数" in result.output
        assert "--weight" in result.output
        mock_planner.create_user_profile.assert_not_called()

    @patch('fatloss.cli.commands.plan.PlannerService')
    def test_plan_daily_generation_failure(self, mock_planner_class, runner):
        """测试生成每日营养计划失败。"""
        mock_planner = Mock()
        mock_planner.generate_daily_nutrition_plan.side_effect = ValueError("用户不存在")
        mock_planner_class.return_value = mock_planner

        result = runner.invoke(cli, [
            "plan", "daily",
            "--user-id", "999",
            "--plan-date", "2026-03-12",
            "--exercise", "60"
        ])

        assert result.exit_code != 0
        assert "生成营养计划失败" in result.output
        assert "用户不存在" in result.output

    @patch('fatloss.cli.commands.plan.PlannerService')
    def test_plan_weekly_success(self, mock_planner_class, runner):
        """测试成功生成每周营养计划。"""
        mock_planner = Mock()
        # 模拟每日计划列表
        mock_daily_plan1 = Mock(
            plan_date=date(2026, 3, 10),
            target_tdee=2200.0,
            is_adjusted=False,
            adjustment_units=0,
            nutrition=Mock(carbohydrates_g=275.0, protein_g=165.0, fat_g=73.3)
        )
        mock_daily_plan2 = Mock(
            plan_date=date(2026, 3, 11),
            target_tdee=2150.0,
            is_adjusted=True,
            adjustment_units=1,
            nutrition=Mock(carbohydrates_g=305.0, protein_g=165.0, fat_g=73.3)
        )
        
        # 模拟每周营养计划
        mock_weekly_plan = Mock(
            id=2001,
            week_start_date=date(2026, 3, 10),
            week_end_date=date(2026, 3, 16),
            daily_plans=[mock_daily_plan1, mock_daily_plan2]
        )
        mock_planner.generate_weekly_nutrition_plan.return_value = mock_weekly_plan
        mock_planner_class.return_value = mock_planner

        result = runner.invoke(cli, [
            "plan", "weekly",
            "--user-id", "1",
            "--week-start", "2026-03-10"
        ])

        assert result.exit_code == 0
        assert "每周营养计划" in result.output
        assert "用户ID: 1" in result.output
        assert "周开始日期: 2026-03-10" in result.output
        assert "周结束日期: 2026-03-16" in result.output
        assert "每日计划数量: 2" in result.output
        assert "平均TDEE:" in result.output
        assert "2026-03-10: 2200 大卡" in result.output
        assert "2026-03-11: 2150 大卡 ⚖️" in result.output
        
        # 验证generate_weekly_nutrition_plan调用
        mock_planner.generate_weekly_nutrition_plan.assert_called_once_with(
            user_id=1,
            week_start_date=date(2026, 3, 10)
        )

    @patch('fatloss.cli.commands.plan.PlannerService')
    def test_plan_weekly_no_plans(self, mock_planner_class, runner):
        """测试生成每周营养计划（无每日计划数据）。"""
        mock_planner = Mock()
        mock_planner.generate_weekly_nutrition_plan.return_value = None
        mock_planner_class.return_value = mock_planner

        result = runner.invoke(cli, [
            "plan", "weekly",
            "--user-id", "1",
            "--week-start", "2026-03-10"
        ])

        assert result.exit_code == 0
        assert "无法生成每周营养计划" in result.output
        assert "可能缺少每日计划数据" in result.output

    @patch('fatloss.cli.commands.plan.PlannerService')
    def test_plan_weekly_empty_daily_plans(self, mock_planner_class, runner):
        """测试生成每周营养计划（每日计划列表为空）。"""
        mock_planner = Mock()
        # 模拟每周营养计划，但daily_plans为空列表
        mock_weekly_plan = Mock(
            id=2002,
            week_start_date=date(2026, 3, 10),
            week_end_date=date(2026, 3, 16),
            daily_plans=[]
        )
        mock_planner.generate_weekly_nutrition_plan.return_value = mock_weekly_plan
        mock_planner_class.return_value = mock_planner

        result = runner.invoke(cli, [
            "plan", "weekly",
            "--user-id", "1",
            "--week-start", "2026-03-10"
        ])

        assert result.exit_code == 0
        assert "每周营养计划" in result.output
        assert "用户ID: 1" in result.output
        assert "每日计划数量: 0" in result.output
        # 验证空列表情况下的else分支被覆盖
        # 平均TDEE等应该显示为0.0

    @patch('fatloss.cli.commands.plan.PlannerService')
    def test_plan_weekly_generation_failure(self, mock_planner_class, runner):
        """测试生成每周营养计划失败。"""
        mock_planner = Mock()
        mock_planner.generate_weekly_nutrition_plan.side_effect = ValueError("用户不存在")
        mock_planner_class.return_value = mock_planner

        result = runner.invoke(cli, [
            "plan", "weekly",
            "--user-id", "999",
            "--week-start", "2026-03-10"
        ])

        assert result.exit_code != 0
        assert "生成每周营养计划失败" in result.output
        assert "用户不存在" in result.output

    @patch('fatloss.cli.commands.plan.PlannerService')
    def test_plan_daily_with_negative_adjustment(self, mock_planner_class, runner):
        """测试生成每日营养计划（负调整）。"""
        mock_planner = Mock()
        mock_daily_plan = Mock(
            id=1003,
            plan_date=date(2026, 3, 12),
            target_tdee=2100.0,
            is_adjusted=True,
            adjustment_units=-2,
            nutrition=Mock(
                carbohydrates_g=215.0,  # 减少60g
                protein_g=165.0,
                fat_g=73.3,
                total_calories=2000.0
            )
        )
        mock_planner.generate_daily_nutrition_plan.return_value = mock_daily_plan
        mock_planner_class.return_value = mock_planner

        result = runner.invoke(cli, [
            "plan", "daily",
            "--user-id", "1",
            "--plan-date", "2026-03-12",
            "--exercise", "60",
            "--adjustment", "-2"
        ])

        assert result.exit_code == 0
        assert "碳水化合物已调整" in result.output
        assert "减少 60g" in result.output