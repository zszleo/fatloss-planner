#!/usr/bin/env python3
"""导出命令CLI单元测试。"""

import json
import csv
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import pytest
from click.testing import CliRunner

from fatloss.cli.main import cli


class TestExportCommand:
    """导出命令测试类。"""

    @pytest.fixture
    def runner(self):
        """提供CliRunner实例。"""
        return CliRunner()

    def test_export_help(self, runner):
        """测试export命令帮助信息。"""
        result = runner.invoke(cli, ["export", "--help"])
        assert result.exit_code == 0
        assert "导出用户数据为JSON或CSV格式" in result.output

    @patch('fatloss.cli.commands.export.PlannerService')
    @patch('fatloss.cli.commands.export.unit_of_work')
    def test_export_json_basic(self, mock_unit_of_work, mock_planner_class, runner, tmp_path):
        """测试基本JSON导出（不包含额外数据）。"""
        # 模拟PlannerService
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///test.db"
        mock_planner_class.return_value = mock_planner
        
        # 模拟用户对象
        mock_user = Mock()
        mock_user.id = 1
        mock_user.name = "测试用户"
        mock_user.gender = "male"
        mock_user.birth_date = date(1990, 1, 1)
        mock_user.height_cm = 175.0
        mock_user.initial_weight_kg = 70.0
        mock_user.activity_level = "moderate"
        mock_user.model_dump.return_value = {
            "id": 1,
            "name": "测试用户",
            "gender": "male",
            "birth_date": "1990-01-01",
            "height_cm": 175.0,
            "initial_weight_kg": 70.0,
            "activity_level": "moderate"
        }
        
        # 模拟配置对象（不存在）
        mock_config = None
        
        # 模拟工作单元上下文管理器
        mock_uow = Mock()
        mock_uow.users.get_by_id.return_value = mock_user
        mock_uow.app_configs.get_by_user_id.return_value = mock_config
        mock_unit_of_work.return_value.__enter__.return_value = mock_uow
        
        # 设置临时输出文件
        output_file = tmp_path / "export_test.json"
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = runner.invoke(cli, [
                "export",
                "--user-id", "1",
                "--format", "json",
                "--output", str(output_file)
            ])
        
        assert result.exit_code == 0
        assert "✅ 数据已导出到：" in result.output
        assert "📊 导出内容：" in result.output
        assert "• 用户信息: ✓" in result.output
        assert "• 配置信息: ✓" in result.output
        # 不应该包含体重记录和营养计划
        assert "体重记录:" not in result.output
        assert "营养计划:" not in result.output
        
        # 验证调用
        mock_uow.users.get_by_id.assert_called_once_with(1)
        mock_uow.app_configs.get_by_user_id.assert_called_once_with(1)

    @patch('fatloss.cli.commands.export.PlannerService')
    @patch('fatloss.cli.commands.export.unit_of_work')
    def test_export_json_with_weight_records(self, mock_unit_of_work, mock_planner_class, runner, tmp_path):
        """测试JSON导出（包含体重记录）。"""
        # 模拟PlannerService
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///test.db"
        mock_planner_class.return_value = mock_planner
        
        # 模拟用户对象
        mock_user = Mock()
        mock_user.id = 1
        mock_user.model_dump.return_value = {"id": 1, "name": "测试用户"}
        
        # 模拟配置对象
        mock_config = Mock()
        mock_config.model_dump.return_value = {"theme": "light"}
        
        # 模拟体重记录
        mock_weight_record1 = Mock()
        mock_weight_record1.model_dump.return_value = {
            "id": 101,
            "weight_kg": 70.5,
            "record_date": "2026-03-10"
        }
        mock_weight_record2 = Mock()
        mock_weight_record2.model_dump.return_value = {
            "id": 102,
            "weight_kg": 70.2,
            "record_date": "2026-03-11"
        }
        
        # 模拟工作单元上下文管理器
        mock_uow = Mock()
        mock_uow.users.get_by_id.return_value = mock_user
        mock_uow.app_configs.get_by_user_id.return_value = mock_config
        mock_uow.weights.find_all_by_user_id.return_value = [
            mock_weight_record1, mock_weight_record2
        ]
        mock_unit_of_work.return_value.__enter__.return_value = mock_uow
        
        # 设置临时输出文件
        output_file = tmp_path / "export_test.json"
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = runner.invoke(cli, [
                "export",
                "--user-id", "1",
                "--format", "json",
                "--output", str(output_file),
                "--include-weight-records"
            ])
        
        assert result.exit_code == 0
        assert "✅ 数据已导出到：" in result.output
        assert "体重记录: 2 条" in result.output
        
        # 验证调用
        mock_uow.weights.find_all_by_user_id.assert_called_once_with(1)
        # 不应该调用营养计划相关方法
        assert not mock_uow.daily_nutrition.find_all_by_user_id.called
        assert not mock_uow.weekly_nutrition.find_all_by_user_id.called

    @patch('fatloss.cli.commands.export.PlannerService')
    @patch('fatloss.cli.commands.export.unit_of_work')
    def test_export_json_with_nutrition_plans(self, mock_unit_of_work, mock_planner_class, runner, tmp_path):
        """测试JSON导出（包含营养计划）。"""
        # 模拟PlannerService
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///test.db"
        mock_planner_class.return_value = mock_planner
        
        # 模拟用户对象
        mock_user = Mock()
        mock_user.id = 1
        mock_user.model_dump.return_value = {"id": 1}
        
        # 模拟配置对象
        mock_config = Mock()
        mock_config.model_dump.return_value = {}
        
        # 模拟营养计划
        mock_daily_plan = Mock()
        mock_daily_plan.model_dump.return_value = {"id": 201, "calories": 2000}
        mock_weekly_plan = Mock()
        mock_weekly_plan.model_dump.return_value = {"id": 301, "week_start": "2026-03-09"}
        
        # 模拟工作单元上下文管理器
        mock_uow = Mock()
        mock_uow.users.get_by_id.return_value = mock_user
        mock_uow.app_configs.get_by_user_id.return_value = mock_config
        mock_uow.daily_nutrition.find_all_by_user_id.return_value = [mock_daily_plan]
        mock_uow.weekly_nutrition.find_all_by_user_id.return_value = [mock_weekly_plan]
        mock_unit_of_work.return_value.__enter__.return_value = mock_uow
        
        # 设置临时输出文件
        output_file = tmp_path / "export_test.json"
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = runner.invoke(cli, [
                "export",
                "--user-id", "1",
                "--format", "json",
                "--output", str(output_file),
                "--include-nutrition-plans"
            ])
        
        assert result.exit_code == 0
        assert "✅ 数据已导出到：" in result.output
        assert "每日营养计划: 1 条" in result.output
        assert "每周营养计划: 1 条" in result.output
        
        # 验证调用
        mock_uow.daily_nutrition.find_all_by_user_id.assert_called_once_with(1)
        mock_uow.weekly_nutrition.find_all_by_user_id.assert_called_once_with(1)
        # 不应该调用体重记录相关方法
        assert not mock_uow.weights.find_all_by_user_id.called

    @patch('fatloss.cli.commands.export.PlannerService')
    @patch('fatloss.cli.commands.export.unit_of_work')
    def test_export_json_with_all_data(self, mock_unit_of_work, mock_planner_class, runner, tmp_path):
        """测试JSON导出（包含所有数据）。"""
        # 模拟PlannerService
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///test.db"
        mock_planner_class.return_value = mock_planner
        
        # 模拟用户对象
        mock_user = Mock()
        mock_user.id = 1
        mock_user.model_dump.return_value = {"id": 1}
        
        # 模拟配置对象
        mock_config = Mock()
        mock_config.model_dump.return_value = {}
        
        # 模拟数据
        mock_weight_record = Mock()
        mock_weight_record.model_dump.return_value = {"id": 101}
        mock_daily_plan = Mock()
        mock_daily_plan.model_dump.return_value = {"id": 201}
        mock_weekly_plan = Mock()
        mock_weekly_plan.model_dump.return_value = {"id": 301}
        
        # 模拟工作单元上下文管理器
        mock_uow = Mock()
        mock_uow.users.get_by_id.return_value = mock_user
        mock_uow.app_configs.get_by_user_id.return_value = mock_config
        mock_uow.weights.find_all_by_user_id.return_value = [mock_weight_record]
        mock_uow.daily_nutrition.find_all_by_user_id.return_value = [mock_daily_plan]
        mock_uow.weekly_nutrition.find_all_by_user_id.return_value = [mock_weekly_plan]
        mock_unit_of_work.return_value.__enter__.return_value = mock_uow
        
        # 设置临时输出文件
        output_file = tmp_path / "export_test.json"
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = runner.invoke(cli, [
                "export",
                "--user-id", "1",
                "--format", "json",
                "--output", str(output_file),
                "--include-weight-records",
                "--include-nutrition-plans"
            ])
        
        assert result.exit_code == 0
        assert "✅ 数据已导出到：" in result.output
        assert "体重记录: 1 条" in result.output
        assert "每日营养计划: 1 条" in result.output
        assert "每周营养计划: 1 条" in result.output

    @patch('fatloss.cli.commands.export.PlannerService')
    @patch('fatloss.cli.commands.export.unit_of_work')
    def test_export_csv_with_weight_records(self, mock_unit_of_work, mock_planner_class, runner, tmp_path):
        """测试CSV导出（包含体重记录）。"""
        # 模拟PlannerService
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///test.db"
        mock_planner_class.return_value = mock_planner
        
        # 模拟用户对象
        mock_user = Mock()
        mock_user.id = 1
        mock_user.name = "测试用户"
        mock_user.gender = "male"
        mock_user.birth_date = date(1990, 1, 1)
        mock_user.height_cm = 175.0
        mock_user.initial_weight_kg = 70.0
        mock_user.activity_level = "moderate"
        
        # 模拟配置对象
        mock_config = Mock()
        mock_config.model_dump.return_value = {}
        
        # 模拟体重记录
        mock_weight_record = Mock()
        mock_weight_record.model_dump.return_value = {
            "id": 101,
            "weight_kg": 70.5,
            "record_date": "2026-03-10"
        }
        
        # 模拟工作单元上下文管理器
        mock_uow = Mock()
        mock_uow.users.get_by_id.return_value = mock_user
        mock_uow.app_configs.get_by_user_id.return_value = mock_config
        mock_uow.weights.find_all_by_user_id.return_value = [mock_weight_record]
        mock_unit_of_work.return_value.__enter__.return_value = mock_uow
        
        # 设置临时输出文件
        output_file = tmp_path / "export_test.csv"
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = runner.invoke(cli, [
                "export",
                "--user-id", "1",
                "--format", "csv",
                "--output", str(output_file),
                "--include-weight-records"
            ])
        
        assert result.exit_code == 0
        assert "✅ 数据已导出到：" in result.output
        assert "体重记录: 1 条" in result.output

    @patch('fatloss.cli.commands.export.PlannerService')
    @patch('fatloss.cli.commands.export.unit_of_work')
    def test_export_csv_without_weight_records(self, mock_unit_of_work, mock_planner_class, runner, tmp_path):
        """测试CSV导出（不包含体重记录）。"""
        # 模拟PlannerService
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///test.db"
        mock_planner_class.return_value = mock_planner
        
        # 模拟用户对象
        mock_user = Mock()
        mock_user.id = 1
        mock_user.name = "测试用户"
        mock_user.gender = "male"
        mock_user.birth_date = date(1990, 1, 1)
        mock_user.height_cm = 175.0
        mock_user.initial_weight_kg = 70.0
        mock_user.activity_level = "moderate"
        
        # 模拟配置对象
        mock_config = Mock()
        mock_config.model_dump.return_value = {}
        
        # 模拟工作单元上下文管理器
        mock_uow = Mock()
        mock_uow.users.get_by_id.return_value = mock_user
        mock_uow.app_configs.get_by_user_id.return_value = mock_config
        mock_uow.weights.find_all_by_user_id.return_value = []  # 空体重记录
        mock_unit_of_work.return_value.__enter__.return_value = mock_uow
        
        # 设置临时输出文件
        output_file = tmp_path / "export_test.csv"
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = runner.invoke(cli, [
                "export",
                "--user-id", "1",
                "--format", "csv",
                "--output", str(output_file),
                "--include-weight-records"
            ])
        
        assert result.exit_code == 0
        assert "✅ 数据已导出到：" in result.output
        # 空体重记录应该被处理

    @patch('fatloss.cli.commands.export.PlannerService')
    @patch('fatloss.cli.commands.export.unit_of_work')
    def test_export_csv_basic(self, mock_unit_of_work, mock_planner_class, runner, tmp_path):
        """测试基本CSV导出（不包含体重记录）。"""
        # 模拟PlannerService
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///test.db"
        mock_planner_class.return_value = mock_planner
        
        # 模拟用户对象
        mock_user = Mock()
        mock_user.id = 1
        mock_user.name = "测试用户"
        mock_user.gender = "male"
        mock_user.birth_date = date(1990, 1, 1)
        mock_user.height_cm = 175.0
        mock_user.initial_weight_kg = 70.0
        mock_user.activity_level = "moderate"
        
        # 模拟配置对象
        mock_config = Mock()
        mock_config.model_dump.return_value = {}
        
        # 模拟工作单元上下文管理器
        mock_uow = Mock()
        mock_uow.users.get_by_id.return_value = mock_user
        mock_uow.app_configs.get_by_user_id.return_value = mock_config
        mock_unit_of_work.return_value.__enter__.return_value = mock_uow
        
        # 设置临时输出文件
        output_file = tmp_path / "export_test.csv"
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = runner.invoke(cli, [
                "export",
                "--user-id", "1",
                "--format", "csv",
                "--output", str(output_file)
            ])
        
        assert result.exit_code == 0
        assert "✅ 数据已导出到：" in result.output

    @patch('fatloss.cli.commands.export.PlannerService')
    @patch('fatloss.cli.commands.export.unit_of_work')
    def test_export_user_not_found(self, mock_unit_of_work, mock_planner_class, runner):
        """测试导出用户不存在的情况。"""
        # 模拟PlannerService
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///test.db"
        mock_planner_class.return_value = mock_planner
        
        # 模拟工作单元上下文管理器
        mock_uow = Mock()
        mock_uow.users.get_by_id.return_value = None  # 用户不存在
        mock_unit_of_work.return_value.__enter__.return_value = mock_uow
        
        result = runner.invoke(cli, [
            "export",
            "--user-id", "999",
            "--format", "json"
        ])
        
        assert result.exit_code != 0
        assert "导出失败" in result.output
        assert "用户不存在" in result.output

    @patch('fatloss.cli.commands.export.PlannerService')
    @patch('fatloss.cli.commands.export.unit_of_work')
    def test_export_default_filename(self, mock_unit_of_work, mock_planner_class, runner):
        """测试使用默认文件名导出。"""
        # 模拟PlannerService
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///test.db"
        mock_planner_class.return_value = mock_planner
        
        # 模拟用户对象
        mock_user = Mock()
        mock_user.id = 1
        mock_user.model_dump.return_value = {"id": 1}
        
        # 模拟配置对象
        mock_config = Mock()
        mock_config.model_dump.return_value = {}
        
        # 模拟工作单元上下文管理器
        mock_uow = Mock()
        mock_uow.users.get_by_id.return_value = mock_user
        mock_uow.app_configs.get_by_user_id.return_value = mock_config
        mock_unit_of_work.return_value.__enter__.return_value = mock_uow
        
        with patch('builtins.open', mock_open()) as mock_file, \
             patch('pathlib.Path.mkdir') as mock_mkdir:
            result = runner.invoke(cli, [
                "export",
                "--user-id", "1",
                "--format", "json"
                # 不提供--output，应该使用默认文件名
            ])
        
        assert result.exit_code == 0
        assert "✅ 数据已导出到：" in result.output
        # 默认文件名应该包含用户ID和日期
        assert "fatloss_export_1_" in result.output
        assert ".json" in result.output
        # 应该创建父目录
        assert mock_mkdir.called

    @patch('fatloss.cli.commands.export.PlannerService')
    @patch('fatloss.cli.commands.export.unit_of_work')
    def test_export_failure(self, mock_unit_of_work, mock_planner_class, runner):
        """测试导出失败的情况。"""
        # 模拟PlannerService
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///test.db"
        mock_planner_class.return_value = mock_planner
        
        # 模拟工作单元上下文管理器
        mock_uow = Mock()
        mock_uow.users.get_by_id.side_effect = Exception("数据库错误")
        mock_unit_of_work.return_value.__enter__.return_value = mock_uow
        
        result = runner.invoke(cli, [
            "export",
            "--user-id", "1",
            "--format", "json"
        ])
        
        assert result.exit_code != 0
        assert "导出失败" in result.output
        assert "数据库错误" in result.output