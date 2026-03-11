#!/usr/bin/env python3
"""用户管理命令CLI单元测试。"""

from datetime import date
from unittest.mock import Mock, patch
import pytest
from click.testing import CliRunner

from fatloss.cli.main import cli


class TestUserCommand:
    """用户管理命令测试类。"""

    @pytest.fixture
    def runner(self):
        """提供CliRunner实例。"""
        return CliRunner()

    def test_user_help(self, runner):
        """测试user命令帮助信息。"""
        result = runner.invoke(cli, ["user", "--help"])
        assert result.exit_code == 0
        assert "用户管理" in result.output

    def test_user_create_help(self, runner):
        """测试user create命令帮助信息。"""
        result = runner.invoke(cli, ["user", "create", "--help"])
        assert result.exit_code == 0
        assert "创建新用户档案" in result.output

    def test_user_list_help(self, runner):
        """测试user list命令帮助信息。"""
        result = runner.invoke(cli, ["user", "list", "--help"])
        assert result.exit_code == 0
        assert "列出所有用户" in result.output

    def test_user_show_help(self, runner):
        """测试user show命令帮助信息。"""
        result = runner.invoke(cli, ["user", "show", "--help"])
        assert result.exit_code == 0
        assert "显示用户详细信息" in result.output

    @patch('fatloss.cli.commands.user.PlannerService')
    def test_user_create_success(self, mock_planner_class, runner):
        """测试成功创建用户。"""
        # 模拟PlannerService实例
        mock_planner = Mock()
        # 创建Mock用户档案，设置属性值
        mock_user_profile = Mock()
        mock_user_profile.id = 123
        mock_user_profile.name = "张三"
        mock_user_profile.gender = "男"
        mock_user_profile.age = 30
        mock_user_profile.height_cm = 175.0
        mock_user_profile.initial_weight_kg = 70.0
        mock_user_profile.activity_level = "中度活动"
        mock_planner.create_user_profile.return_value = mock_user_profile
        mock_planner_class.return_value = mock_planner

        result = runner.invoke(cli, [
            "user", "create",
            "--name", "张三",
            "--gender", "男",
            "--birth-date", "1995-01-01",
            "--height", "175",
            "--weight", "70",
            "--activity-level", "中度活动"
        ])

        assert result.exit_code == 0
        assert "✅ 用户创建成功！" in result.output
        assert "用户ID: 123" in result.output
        assert "姓名: 张三" in result.output
        assert "性别: 男" in result.output
        assert "年龄: 30 岁" in result.output
        assert "身高: 175.0 cm" in result.output
        assert "初始体重: 70.0 kg" in result.output
        assert "活动水平: 中度活动" in result.output
        
        # 验证create_user_profile调用
        mock_planner.create_user_profile.assert_called_once()
        call_args = mock_planner.create_user_profile.call_args
        assert call_args.kwargs["name"] == "张三"
        assert call_args.kwargs["height_cm"] == 175.0
        assert call_args.kwargs["initial_weight_kg"] == 70.0
        assert call_args.kwargs["activity_level"] == "中度活动"
        # 检查gender枚举转换
        from fatloss.calculator.bmr_calculator import Gender
        assert call_args.kwargs["gender"] == Gender.MALE
        # 检查birth_date转换为date对象
        assert call_args.kwargs["birth_date"] == date(1995, 1, 1)

    @patch('fatloss.cli.commands.user.PlannerService')
    def test_user_create_with_female(self, mock_planner_class, runner):
        """测试创建女性用户。"""
        mock_planner = Mock()
        # 创建Mock用户档案，设置属性值
        mock_user_profile = Mock()
        mock_user_profile.id = 124
        mock_user_profile.name = "李四"
        mock_user_profile.gender = "女"
        mock_user_profile.age = 25
        mock_user_profile.height_cm = 165.0
        mock_user_profile.initial_weight_kg = 60.0
        mock_user_profile.activity_level = "活跃"
        mock_planner.create_user_profile.return_value = mock_user_profile
        mock_planner_class.return_value = mock_planner

        result = runner.invoke(cli, [
            "user", "create",
            "--name", "李四",
            "--gender", "女",
            "--birth-date", "2000-05-15",
            "--height", "165",
            "--weight", "60",
            "--activity-level", "活跃"
        ])

        assert result.exit_code == 0
        assert "性别: 女" in result.output
        # 验证gender枚举转换
        from fatloss.calculator.bmr_calculator import Gender
        mock_planner.create_user_profile.assert_called_once()
        call_args = mock_planner.create_user_profile.call_args
        assert call_args.kwargs["gender"] == Gender.FEMALE

    @patch('fatloss.cli.commands.user.PlannerService')
    def test_user_create_failure(self, mock_planner_class, runner):
        """测试创建用户失败（异常）。"""
        mock_planner = Mock()
        mock_planner.create_user_profile.side_effect = ValueError("身高超出范围")
        mock_planner_class.return_value = mock_planner

        result = runner.invoke(cli, [
            "user", "create",
            "--name", "张三",
            "--gender", "男",
            "--birth-date", "1995-01-01",
            "--height", "300",  # 无效身高
            "--weight", "70",
            "--activity-level", "中度活动"
        ])

        assert result.exit_code != 0
        assert "创建用户失败" in result.output
        assert "身高超出范围" in result.output

    @patch('fatloss.cli.commands.user.unit_of_work')
    @patch('fatloss.cli.commands.user.PlannerService')
    def test_user_list_no_users(self, mock_planner_class, mock_uow, runner):
        """测试列出用户（无用户）。"""
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///:memory:"
        mock_planner_class.return_value = mock_planner
        
        # 模拟unit_of_work上下文管理器
        mock_uow_context = Mock()
        mock_uow_context.users.get_all.return_value = []
        mock_uow.return_value.__enter__.return_value = mock_uow_context

        result = runner.invoke(cli, ["user", "list"])

        assert result.exit_code == 0
        assert "没有用户" in result.output

    @patch('fatloss.cli.commands.user.unit_of_work')
    @patch('fatloss.cli.commands.user.PlannerService')
    def test_user_list_with_users(self, mock_planner_class, mock_uow, runner):
        """测试列出用户（有用户）。"""
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///:memory:"
        mock_planner_class.return_value = mock_planner
        
        # 模拟用户数据
        mock_user1 = Mock()
        mock_user1.id = 1
        mock_user1.name = "张三"
        mock_user1.gender = "男"
        mock_user1.age = 30
        
        mock_user2 = Mock()
        mock_user2.id = 2
        mock_user2.name = "李四"
        mock_user2.gender = "女"
        mock_user2.age = 25
        
        # 模拟体重记录
        mock_weight = Mock()
        mock_weight.weight_kg = 70.5
        
        # 模拟unit_of_work上下文管理器
        mock_uow_context = Mock()
        mock_uow_context.users.get_all.return_value = [mock_user1, mock_user2]
        mock_uow_context.weights.find_latest_by_user_id.side_effect = lambda uid: mock_weight if uid == 1 else None
        mock_uow.return_value.__enter__.return_value = mock_uow_context

        result = runner.invoke(cli, ["user", "list"])

        assert result.exit_code == 0
        assert "用户列表" in result.output
        assert "张三" in result.output
        assert "李四" in result.output
        assert "70.5 kg" in result.output  # 用户1有体重记录
        assert "无记录" in result.output  # 用户2无体重记录
        
        # 验证limit参数
        mock_uow_context.users.get_all.assert_called_once_with(limit=20)

    @patch('fatloss.cli.commands.user.unit_of_work')
    @patch('fatloss.cli.commands.user.PlannerService')
    def test_user_list_with_limit(self, mock_planner_class, mock_uow, runner):
        """测试列出用户（指定限制）。"""
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///:memory:"
        mock_planner_class.return_value = mock_planner
        
        mock_uow_context = Mock()
        mock_uow_context.users.get_all.return_value = []
        mock_uow.return_value.__enter__.return_value = mock_uow_context

        result = runner.invoke(cli, ["user", "list", "--limit", "5"])

        assert result.exit_code == 0
        mock_uow_context.users.get_all.assert_called_once_with(limit=5)

    @patch('fatloss.cli.commands.user.unit_of_work')
    @patch('fatloss.cli.commands.user.PlannerService')
    def test_user_list_exception(self, mock_planner_class, mock_uow, runner):
        """测试列出用户失败（异常）。"""
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///:memory:"
        mock_planner_class.return_value = mock_planner
        
        mock_uow.return_value.__enter__.side_effect = ValueError("数据库连接失败")

        result = runner.invoke(cli, ["user", "list"])

        assert result.exit_code != 0
        assert "列出用户失败" in result.output
        assert "数据库连接失败" in result.output

    @patch('fatloss.cli.commands.user.unit_of_work')
    @patch('fatloss.cli.commands.user.PlannerService')
    def test_user_show_success(self, mock_planner_class, mock_uow, runner):
        """测试成功显示用户详情。"""
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///:memory:"
        mock_planner_class.return_value = mock_planner
        
        # 模拟用户数据
        mock_user = Mock()
        mock_user.id = 1
        mock_user.name = "张三"
        mock_user.gender = "男"
        mock_user.birth_date = date(1995, 1, 1)
        mock_user.age = 30
        mock_user.height_cm = 175.0
        mock_user.initial_weight_kg = 70.0
        mock_user.activity_level = "中度活动"
        mock_user.created_at = "2026-03-11 10:00:00"
        
        # 模拟体重记录
        mock_weight = Mock()
        mock_weight.weight_kg = 69.5
        mock_weight.record_date = date(2026, 3, 11)
        
        # 模拟unit_of_work上下文管理器
        mock_uow_context = Mock()
        mock_uow_context.users.get_by_id.return_value = mock_user
        mock_uow_context.weights.find_latest_by_user_id.return_value = mock_weight
        # 模拟count_by_user_id方法存在并返回值
        mock_uow_context.weights.count_by_user_id.return_value = 5
        mock_uow_context.daily_nutrition.count_by_user_id.return_value = 3
        mock_uow_context.weekly_nutrition.count_by_user_id.return_value = 1
        mock_uow.return_value.__enter__.return_value = mock_uow_context

        result = runner.invoke(cli, ["user", "show", "--user-id", "1"])

        assert result.exit_code == 0
        assert "👤 用户详情" in result.output
        assert "姓名: 张三" in result.output
        assert "用户ID: 1" in result.output
        assert "性别: 男" in result.output
        assert "出生日期: 1995-01-01" in result.output
        assert "年龄: 30 岁" in result.output
        assert "身高: 175.0 cm" in result.output
        assert "初始体重: 70.0 kg" in result.output
        assert "活动水平: 中度活动" in result.output
        assert "创建时间: 2026-03-11 10:00:00" in result.output
        assert "统计数据" in result.output
        assert "最新体重: 69.5 kg (2026-03-11)" in result.output

    @patch('fatloss.cli.commands.user.unit_of_work')
    @patch('fatloss.cli.commands.user.PlannerService')
    def test_user_show_user_not_found(self, mock_planner_class, mock_uow, runner):
        """测试显示用户详情（用户不存在）。"""
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///:memory:"
        mock_planner_class.return_value = mock_planner
        
        mock_uow_context = Mock()
        mock_uow_context.users.get_by_id.return_value = None
        mock_uow.return_value.__enter__.return_value = mock_uow_context

        result = runner.invoke(cli, ["user", "show", "--user-id", "999"])

        assert result.exit_code != 0
        assert "用户不存在" in result.output
        assert "999" in result.output

    @patch('fatloss.cli.commands.user.unit_of_work')
    @patch('fatloss.cli.commands.user.PlannerService')
    def test_user_show_without_weight_record(self, mock_planner_class, mock_uow, runner):
        """测试显示用户详情（无体重记录）。"""
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///:memory:"
        mock_planner_class.return_value = mock_planner
        
        mock_user = Mock()
        mock_user.id = 1
        mock_user.name = "张三"
        mock_user.gender = "男"
        mock_user.birth_date = date(1995, 1, 1)
        mock_user.age = 30
        mock_user.height_cm = 175.0
        mock_user.initial_weight_kg = 70.0
        mock_user.activity_level = "中度活动"
        mock_user.created_at = "2026-03-11 10:00:00"
        
        mock_uow_context = Mock()
        mock_uow_context.users.get_by_id.return_value = mock_user
        mock_uow_context.weights.find_latest_by_user_id.return_value = None
        # 模拟count_by_user_id方法存在并返回值
        mock_uow_context.weights.count_by_user_id.return_value = 0
        mock_uow_context.daily_nutrition.count_by_user_id.return_value = 0
        mock_uow_context.weekly_nutrition.count_by_user_id.return_value = 0
        mock_uow.return_value.__enter__.return_value = mock_uow_context

        result = runner.invoke(cli, ["user", "show", "--user-id", "1"])

        assert result.exit_code == 0
        assert "最新体重:" not in result.output or "最新体重: 无" in result.output
        # 应显示其他信息
        assert "姓名: 张三" in result.output

    @patch('fatloss.cli.commands.user.unit_of_work')
    @patch('fatloss.cli.commands.user.PlannerService')
    def test_user_show_exception(self, mock_planner_class, mock_uow, runner):
        """测试显示用户详情失败（异常）。"""
        mock_planner = Mock()
        mock_planner.database_url = "sqlite:///:memory:"
        mock_planner_class.return_value = mock_planner
        
        mock_uow.return_value.__enter__.side_effect = ValueError("数据库错误")

        result = runner.invoke(cli, ["user", "show", "--user-id", "1"])

        assert result.exit_code != 0
        assert "显示用户失败" in result.output
        assert "数据库错误" in result.output