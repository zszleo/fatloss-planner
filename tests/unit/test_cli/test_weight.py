#!/usr/bin/env python3
"""体重命令CLI单元测试。"""

from datetime import date
import datetime
from unittest.mock import Mock, patch, MagicMock
import pytest
from click.testing import CliRunner

from fatloss.cli.main import cli


class TestWeightCommand:
    """体重命令测试类。"""

    @pytest.fixture
    def runner(self):
        """提供CliRunner实例。"""
        return CliRunner()

    def test_weight_help(self, runner):
        """测试weight命令帮助信息。"""
        result = runner.invoke(cli, ["weight", "--help"])
        assert result.exit_code == 0
        assert "体重记录管理" in result.output

    def test_weight_record_help(self, runner):
        """测试weight record命令帮助信息。"""
        result = runner.invoke(cli, ["weight", "record", "--help"])
        assert result.exit_code == 0
        assert "记录体重" in result.output

    def test_weight_history_help(self, runner):
        """测试weight history命令帮助信息。"""
        result = runner.invoke(cli, ["weight", "history", "--help"])
        assert result.exit_code == 0
        assert "查看体重历史记录" in result.output

    def test_weight_progress_help(self, runner):
        """测试weight progress命令帮助信息。"""
        result = runner.invoke(cli, ["weight", "progress", "--help"])
        assert result.exit_code == 0
        assert "查看减脂进度" in result.output

    @patch('fatloss.cli.commands.weight.PlannerService')
    def test_weight_record_success(self, mock_planner_class, runner):
        """测试成功记录体重。"""
        # 模拟PlannerService实例
        mock_planner = Mock()
        mock_weight_record = Mock(id=123)
        mock_planner.record_weight.return_value = mock_weight_record
        mock_planner_class.return_value = mock_planner

        result = runner.invoke(cli, [
            "weight", "record",
            "--user-id", "1",
            "--weight", "70.5",
            "--date", "2026-03-11",
            "--notes", "早晨空腹"
        ])

        assert result.exit_code == 0
        assert "✅ 体重记录成功！" in result.output
        assert "用户ID: 1" in result.output
        assert "体重: 70.5 kg" in result.output
        assert "记录日期: 2026-03-11" in result.output
        assert "备注: 早晨空腹" in result.output
        assert "记录ID: 123" in result.output
        
        # 验证record_weight调用
        mock_planner.record_weight.assert_called_once_with(
            user_id=1,
            weight_kg=70.5,
            record_date=date(2026, 3, 11),
            notes="早晨空腹"
        )

    @patch('fatloss.cli.commands.weight.PlannerService')
    @patch('datetime.date')
    def test_weight_record_without_date(self, mock_date_class, mock_planner_class, runner):
        """测试记录体重（使用默认日期）。"""
        mock_planner = Mock()
        mock_weight_record = Mock(id=124)
        mock_planner.record_weight.return_value = mock_weight_record
        mock_planner_class.return_value = mock_planner
        
        # 设置模拟date类的today方法
        mock_date_class.today.return_value = date(2026, 3, 11)

        result = runner.invoke(cli, [
            "weight", "record",
            "--user-id", "1",
            "--weight", "72.0"
        ])

        assert result.exit_code == 0
        mock_planner.record_weight.assert_called_once_with(
            user_id=1,
            weight_kg=72.0,
            record_date=date(2026, 3, 11),
            notes=""
        )

    @patch('fatloss.cli.commands.weight.PlannerService')
    @patch('datetime.date')
    def test_weight_record_failure(self, mock_date_class, mock_planner_class, runner):
        """测试记录体重失败（异常）。"""
        mock_planner = Mock()
        mock_planner.record_weight.side_effect = ValueError("体重超出范围")
        mock_planner_class.return_value = mock_planner
        # 设置模拟date类的today方法
        mock_date_class.today.return_value = date(2026, 3, 11)

        result = runner.invoke(cli, [
            "weight", "record",
            "--user-id", "1",
            "--weight", "300"  # 无效体重
        ])

        assert result.exit_code != 0
        assert "记录体重失败" in result.output
        assert "体重超出范围" in result.output

    @patch('fatloss.cli.commands.weight.unit_of_work')
    @patch('fatloss.cli.commands.weight.PlannerService')
    def test_weight_history_no_records(self, mock_planner_class, mock_uow, runner):
        """测试查看体重历史（无记录）。"""
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///:memory:"
        mock_planner_class.return_value = mock_planner
        
        # 模拟unit_of_work上下文管理器
        mock_uow_context = Mock()
        mock_uow_context.users.get_by_id.return_value = Mock(id=1, name="测试用户")
        mock_uow_context.weights.find_all_by_user_id.return_value = []
        mock_uow.return_value.__enter__.return_value = mock_uow_context

        result = runner.invoke(cli, [
            "weight", "history",
            "--user-id", "1"
        ])

        assert result.exit_code == 0
        assert "没有体重记录" in result.output or "用户 测试用户 没有体重记录" in result.output
    @patch('fatloss.cli.commands.weight.unit_of_work')
    @patch('fatloss.cli.commands.weight.PlannerService')
    def test_weight_history_with_records(self, mock_planner_class, mock_uow, runner):
        """测试查看体重历史（有记录）。"""
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///:memory:"
        mock_planner_class.return_value = mock_planner
        
        # 模拟unit_of_work上下文管理器
        mock_uow_context = Mock()
        mock_uow_context.users.get_by_id.return_value = Mock(id=1, name="测试用户")
        # 创建模拟体重记录
        mock_record1 = Mock(weight_kg=70.0, record_date=date(2026, 3, 10), notes="")
        mock_record2 = Mock(weight_kg=69.5, record_date=date(2026, 3, 11), notes="早晨空腹")
        mock_uow_context.weights.find_all_by_user_id.return_value = [mock_record1, mock_record2]
        mock_uow.return_value.__enter__.return_value = mock_uow_context

        result = runner.invoke(cli, [
            "weight", "history",
            "--user-id", "1",
            "--limit", "5"
        ])

        assert result.exit_code == 0
        assert "体重历史记录" in result.output
        assert "70.0" in result.output
        assert "69.5" in result.output

    @patch('fatloss.cli.commands.weight.unit_of_work')
    @patch('fatloss.cli.commands.weight.PlannerService')
    def test_weight_progress_with_target(self, mock_planner_class, mock_uow, runner):
        """测试查看减脂进度（指定目标体重）。"""
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///:memory:"
        mock_planner.calculate_weight_loss_progress.return_value = Mock(
            current_weight_kg=70.0,
            target_weight_kg=65.0,
            total_loss_kg=5.0,
            progress_percentage=30.0,
            estimated_completion_date=date(2026, 6, 1),
            weekly_adjustment_needed=0
        )
        mock_planner_class.return_value = mock_planner
        
        # 模拟unit_of_work上下文管理器（用于用户存在性检查）
        mock_uow_context = Mock()
        mock_uow_context.users.get_by_id.return_value = Mock(id=1, name="测试用户", initial_weight_kg=72.0)
        mock_uow.return_value.__enter__.return_value = mock_uow_context

        result = runner.invoke(cli, [
            "weight", "progress",
            "--user-id", "1",
            "--target", "65.0"
        ])

        assert result.exit_code == 0
        assert "减脂进度报告" in result.output
        assert "当前体重: 70.0 kg" in result.output
        assert "目标体重: 65.0 kg" in result.output
        assert "需要减重: 5.0 kg" in result.output
        assert "进度: 30.0%" in result.output

    @patch('fatloss.cli.commands.weight.unit_of_work')
    @patch('fatloss.cli.commands.weight.PlannerService')
    def test_weight_progress_without_target(self, mock_planner_class, mock_uow, runner):
        """测试查看减脂进度（使用默认目标体重）。"""
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///:memory:"
        mock_planner.calculate_weight_loss_progress.return_value = Mock(
            current_weight_kg=70.0,
            target_weight_kg=68.4,  # 72.0 * 0.95
            total_loss_kg=1.6,
            progress_percentage=50.0,
            estimated_completion_date=date(2026, 5, 1),
            weekly_adjustment_needed=1
        )
        mock_planner_class.return_value = mock_planner
        
        # 模拟unit_of_work上下文管理器（用于用户存在性检查和默认目标计算）
        mock_uow_context = Mock()
        mock_uow_context.users.get_by_id.return_value = Mock(id=1, name="测试用户", initial_weight_kg=72.0)
        mock_uow.return_value.__enter__.return_value = mock_uow_context

        result = runner.invoke(cli, [
            "weight", "progress",
            "--user-id", "1"
        ])

        assert result.exit_code == 0
        assert "减脂进度报告" in result.output
        assert "使用默认目标体重" in result.output or "初始体重的95%" in result.output
        assert "当前体重: 70.0 kg" in result.output

    @patch('fatloss.cli.commands.weight.unit_of_work')
    @patch('fatloss.cli.commands.weight.PlannerService')
    def test_weight_history_user_not_found(self, mock_planner_class, mock_uow, runner):
        """测试查看体重历史（用户不存在）。"""
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///:memory:"
        mock_planner_class.return_value = mock_planner
        
        # 模拟unit_of_work上下文管理器，用户不存在
        mock_uow_context = Mock()
        mock_uow_context.users.get_by_id.return_value = None
        mock_uow.return_value.__enter__.return_value = mock_uow_context

        result = runner.invoke(cli, [
            "weight", "history",
            "--user-id", "999"
        ])

        assert result.exit_code != 0
        assert "用户不存在" in result.output

    @patch('fatloss.cli.commands.weight.PlannerService')
    def test_weight_progress_exception(self, mock_planner_class, runner):
        """测试查看减脂进度（异常）。"""
        mock_planner = Mock()
        mock_planner.calculate_weight_loss_progress.side_effect = ValueError("计算进度失败")
        mock_planner_class.return_value = mock_planner

        result = runner.invoke(cli, [
            "weight", "progress",
            "--user-id", "1"
        ])

        assert result.exit_code != 0
        assert "获取减脂进度失败" in result.output

    @patch('fatloss.cli.commands.weight.unit_of_work')
    @patch('fatloss.cli.commands.weight.PlannerService')
    def test_weight_progress_user_not_found(self, mock_planner_class, mock_uow, runner):
        """测试查看减脂进度（用户不存在）。"""
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///:memory:"
        mock_planner_class.return_value = mock_planner
        
        # 模拟unit_of_work上下文管理器，用户不存在
        mock_uow_context = Mock()
        mock_uow_context.users.get_by_id.return_value = None
        mock_uow.return_value.__enter__.return_value = mock_uow_context

        result = runner.invoke(cli, [
            "weight", "progress",
            "--user-id", "999"
        ])

        assert result.exit_code != 0
        assert "用户不存在" in result.output

    @patch('fatloss.cli.commands.weight.unit_of_work')
    @patch('fatloss.cli.commands.weight.PlannerService')
    def test_weight_progress_negative_adjustment(self, mock_planner_class, mock_uow, runner):
        """测试查看减脂进度（负调整建议）。"""
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///:memory:"
        mock_planner.calculate_weight_loss_progress.return_value = Mock(
            current_weight_kg=70.0,
            target_weight_kg=65.0,
            total_loss_kg=5.0,
            progress_percentage=30.0,
            estimated_completion_date=date(2026, 6, 1),
            weekly_adjustment_needed=-2
        )
        mock_planner_class.return_value = mock_planner
        
        # 模拟unit_of_work上下文管理器（用于用户存在性检查）
        mock_uow_context = Mock()
        mock_uow_context.users.get_by_id.return_value = Mock(id=1, name="测试用户", initial_weight_kg=72.0)
        mock_uow.return_value.__enter__.return_value = mock_uow_context

        result = runner.invoke(cli, [
            "weight", "progress",
            "--user-id", "1",
            "--target", "65.0"
        ])

        assert result.exit_code == 0
        assert "减少 2 单位碳水化合物摄入" in result.output

    @patch('fatloss.cli.commands.weight.unit_of_work')
    @patch('fatloss.cli.commands.weight.PlannerService')
    def test_weight_history_negative_change(self, mock_planner_class, mock_uow, runner):
        """测试查看体重历史（体重下降）。"""
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///:memory:"
        mock_planner_class.return_value = mock_planner
        
        # 模拟unit_of_work上下文管理器
        mock_uow_context = Mock()
        mock_uow_context.users.get_by_id.return_value = Mock(id=1, name="测试用户")
        # 创建模拟体重记录，体重下降
        mock_record1 = Mock(weight_kg=72.0, record_date=date(2026, 3, 10), notes="")
        mock_record2 = Mock(weight_kg=70.5, record_date=date(2026, 3, 11), notes="早晨空腹")
        mock_record3 = Mock(weight_kg=69.0, record_date=date(2026, 3, 12), notes="锻炼后")
        mock_uow_context.weights.find_all_by_user_id.return_value = [mock_record1, mock_record2, mock_record3]
        mock_uow.return_value.__enter__.return_value = mock_uow_context

        result = runner.invoke(cli, [
            "weight", "history",
            "--user-id", "1",
            "--reverse"  # 按日期升序排序，使相邻变化显示负值
        ])

        assert result.exit_code == 0
        assert "体重历史记录" in result.output
        # 验证体重下降显示负号（按升序排序：72.0 -> 70.5 -> 69.0）
        # 变化应该是：70.5-72.0 = -1.5, 69.0-70.5 = -1.5
        assert "(-1.5 kg)" in result.output
        # 验证统计信息中的平均每日变化（days_diff > 0分支）
        assert "平均每日变化" in result.output

    @patch('fatloss.cli.commands.weight.unit_of_work')
    @patch('fatloss.cli.commands.weight.PlannerService')
    def test_weight_history_zero_change(self, mock_planner_class, mock_uow, runner):
        """测试查看体重历史（体重变化为零）。"""
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///:memory:"
        mock_planner_class.return_value = mock_planner
        
        # 模拟unit_of_work上下文管理器
        mock_uow_context = Mock()
        mock_uow_context.users.get_by_id.return_value = Mock(id=1, name="测试用户")
        # 创建模拟体重记录，体重相同
        mock_record1 = Mock(weight_kg=70.0, record_date=date(2026, 3, 10), notes="")
        mock_record2 = Mock(weight_kg=70.0, record_date=date(2026, 3, 11), notes="")
        mock_uow_context.weights.find_all_by_user_id.return_value = [mock_record1, mock_record2]
        mock_uow.return_value.__enter__.return_value = mock_uow_context

        result = runner.invoke(cli, [
            "weight", "history",
            "--user-id", "1"
        ])

        assert result.exit_code == 0
        assert "(0 kg)" in result.output
