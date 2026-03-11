#!/usr/bin/env python3
"""计算命令CLI单元测试。"""

from unittest.mock import Mock, patch
import pytest
from click.testing import CliRunner

from fatloss.cli.main import cli


class TestCalculateCommand:
    """计算命令测试类。"""

    @pytest.fixture
    def runner(self):
        """提供CliRunner实例。"""
        return CliRunner()

    def test_calculate_help(self, runner):
        """测试calculate命令帮助信息。"""
        result = runner.invoke(cli, ["calculate", "--help"])
        assert result.exit_code == 0
        assert "计算基础代谢率" in result.output

    def test_calculate_success(self, runner):
        """测试成功计算。"""
        result = runner.invoke(cli, [
            "calculate",
            "--weight", "70",
            "--height", "175",
            "--age", "30",
            "--gender", "男",
            "--exercise", "60"
        ])

        assert result.exit_code == 0
        assert "基础代谢率（BMR）" in result.output
        assert "每日总能量消耗（TDEE）" in result.output
        assert "三大营养素分配" in result.output

    def test_calculate_with_female(self, runner):
        """测试计算女性数据。"""
        result = runner.invoke(cli, [
            "calculate",
            "--weight", "60",
            "--height", "165",
            "--age", "25",
            "--gender", "女",
            "--exercise", "45"
        ])

        assert result.exit_code == 0
        assert "性别: 女" in result.output

    def test_calculate_invalid_gender(self, runner):
        """测试无效性别参数。"""
        # Click的choice验证会捕获无效性别，不会执行到AttributeError
        result = runner.invoke(cli, [
            "calculate",
            "--weight", "70",
            "--height", "175",
            "--age", "30",
            "--gender", "invalid",
            "--exercise", "60"
        ])

        assert result.exit_code != 0
        # Click会验证choice并显示错误

    @patch('fatloss.cli.commands.calculate.calculate_bmr')
    def test_calculate_bmr_exception(self, mock_calculate_bmr, runner):
        """测试BMR计算异常。"""
        mock_calculate_bmr.side_effect = ValueError("体重超出范围")

        result = runner.invoke(cli, [
            "calculate",
            "--weight", "300",  # 无效体重
            "--height", "175",
            "--age", "30",
            "--gender", "男",
            "--exercise", "60"
        ])

        assert result.exit_code != 0
        assert "体重超出范围" in result.output

    @patch('fatloss.cli.commands.calculate.calculate_tdee')
    @patch('fatloss.cli.commands.calculate.calculate_bmr')
    def test_calculate_tdee_exception(self, mock_calculate_bmr, mock_calculate_tdee, runner):
        """测试TDEE计算异常。"""
        mock_calculate_bmr.return_value = 1600.0
        mock_calculate_tdee.side_effect = ValueError("训练时间超出范围")

        result = runner.invoke(cli, [
            "calculate",
            "--weight", "70",
            "--height", "175",
            "--age", "30",
            "--gender", "男",
            "--exercise", "300"
        ])

        assert result.exit_code != 0
        assert "训练时间超出范围" in result.output

    def test_calculate_default_exercise(self, runner):
        """测试使用默认训练时间。"""
        result = runner.invoke(cli, [
            "calculate",
            "--weight", "70",
            "--height", "175",
            "--age", "30",
            "--gender", "男"
            # 不提供--exercise，使用默认值60
        ])

        assert result.exit_code == 0
        assert "训练时间: 60.0 分钟/天" in result.output