"""UserController单元测试。

测试用户管理控制器的业务逻辑和数据处理。
"""

from datetime import date
from unittest.mock import MagicMock, Mock, patch

import pytest

from fatloss.desktop.controllers.user_controller import UserController
from fatloss.models.user_profile import ActivityLevel, Gender, UserProfile
from tests.desktop.factories import TestDataFactory


class TestUserController:
    """UserController单元测试类"""

    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker):
        """自动设置模拟，避免GUI调用和数据库访问"""
        # 模拟unit_of_work
        self.mock_unit_of_work = mocker.patch(
            "fatloss.desktop.controllers.user_controller.unit_of_work"
        )
        mock_uow = MagicMock()
        mock_uow.__enter__.return_value = mock_uow
        mock_uow.__exit__.return_value = None

        # 模拟用户仓库
        mock_users = MagicMock()
        mock_users.get_by_id.return_value = None
        mock_users.get_all.return_value = []
        mock_users.count.return_value = 0
        mock_users.update.return_value = None
        mock_users.delete.return_value = None
        mock_uow.users = mock_users

        self.mock_unit_of_work.return_value = mock_uow

        # 模拟ErrorHandler
        self.mock_error_handler = mocker.patch(
            "fatloss.desktop.controllers.user_controller.ErrorHandler"
        )
        self.mock_error_handler.handle_service_error = mocker.Mock()
        self.mock_error_handler.show_success = mocker.Mock()
        self.mock_error_handler.show_warning = mocker.Mock()
        self.mock_error_handler.show_info = mocker.Mock()

    @pytest.fixture
    def mock_planner_service(self):
        """模拟PlannerService依赖"""
        service = Mock()
        service.create_user_profile.return_value = None
        service.database_url = "sqlite:///:memory:"
        return service

    @pytest.fixture
    def user_controller(self, mock_planner_service):
        """创建UserController实例"""
        return UserController(planner_service=mock_planner_service)

    def test_get_all_users_success(self, user_controller):
        """测试获取所有用户成功"""
        # 准备
        users = [
            TestDataFactory.create_user_profile(id=1, name="用户1"),
            TestDataFactory.create_user_profile(id=2, name="用户2"),
        ]
        self.mock_unit_of_work.return_value.users.get_all.return_value = users

        # 执行
        result = user_controller.get_all_users()

        # 验证
        assert len(result) == 2
        assert result[0].name == "用户1"
        assert result[1].name == "用户2"
        self.mock_error_handler.handle_service_error.assert_not_called()

    def test_get_all_users_empty(self, user_controller):
        """测试获取所有用户，返回空列表"""
        # 准备
        self.mock_unit_of_work.return_value.users.get_all.return_value = []

        # 执行
        result = user_controller.get_all_users()

        # 验证
        assert result == []
        self.mock_error_handler.handle_service_error.assert_not_called()

    def test_get_all_users_exception(self, user_controller):
        """测试获取所有用户时发生异常"""
        # 准备
        self.mock_unit_of_work.return_value.users.get_all.side_effect = Exception(
            "数据库错误"
        )

        # 执行
        result = user_controller.get_all_users()

        # 验证
        assert result == []
        self.mock_error_handler.handle_service_error.assert_called_once()

    def test_get_user_by_id_success(self, user_controller):
        """测试根据ID获取用户成功"""
        # 准备
        user = TestDataFactory.create_user_profile(id=1, name="测试用户")
        self.mock_unit_of_work.return_value.users.get_by_id.return_value = user

        # 执行
        result = user_controller.get_user_by_id(1)

        # 验证
        assert result is not None
        assert result.id == 1
        assert result.name == "测试用户"
        self.mock_error_handler.handle_service_error.assert_not_called()

    def test_get_user_by_id_not_found(self, user_controller):
        """测试根据ID获取用户，用户不存在"""
        # 准备
        self.mock_unit_of_work.return_value.users.get_by_id.return_value = None

        # 执行
        result = user_controller.get_user_by_id(999)

        # 验证
        assert result is None
        self.mock_error_handler.handle_service_error.assert_not_called()

    def test_get_user_by_id_exception(self, user_controller):
        """测试根据ID获取用户时发生异常"""
        # 准备
        self.mock_unit_of_work.return_value.users.get_by_id.side_effect = Exception(
            "数据库错误"
        )

        # 执行
        result = user_controller.get_user_by_id(1)

        # 验证
        assert result is None
        self.mock_error_handler.handle_service_error.assert_called_once()

    def test_create_user_success(self, user_controller, mock_planner_service):
        """测试创建用户成功"""
        # 准备
        user = TestDataFactory.create_user_profile(id=1, name="新用户")
        mock_planner_service.create_user_profile.return_value = user

        # 执行
        result = user_controller.create_user(
            name="新用户",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=70.0,
            activity_level=ActivityLevel.MODERATE,
        )

        # 验证
        assert result is not None
        assert result.name == "新用户"
        mock_planner_service.create_user_profile.assert_called_once()
        self.mock_error_handler.show_success.assert_called_once()

    def test_create_user_validation_error(self, user_controller):
        """测试创建用户时验证错误"""
        # 执行
        result = user_controller.create_user(
            name="",  # 空姓名
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=70.0,
        )

        # 验证
        assert result is None
        self.mock_error_handler.handle_service_error.assert_called_once()

    def test_create_user_exception(self, user_controller, mock_planner_service):
        """测试创建用户时发生异常"""
        # 准备
        mock_planner_service.create_user_profile.side_effect = Exception("创建失败")

        # 执行
        result = user_controller.create_user(
            name="新用户",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=70.0,
        )

        # 验证
        assert result is None
        self.mock_error_handler.handle_service_error.assert_called_once()

    def test_update_user_success(self, user_controller):
        """测试更新用户成功"""
        # 准备
        existing_user = TestDataFactory.create_user_profile(id=1, name="原用户")
        self.mock_unit_of_work.return_value.users.get_by_id.return_value = existing_user

        # 执行
        result = user_controller.update_user(
            user_id=1,
            name="更新用户",
            gender=Gender.FEMALE,
            birth_date=date(1995, 5, 5),
            height_cm=165.0,
            initial_weight_kg=60.0,
            activity_level=ActivityLevel.LIGHT,
        )

        # 验证
        assert result is not None
        assert result.name == "更新用户"
        assert result.gender == Gender.FEMALE
        self.mock_error_handler.show_success.assert_called_once()

    def test_update_user_not_found(self, user_controller):
        """测试更新用户，用户不存在"""
        # 准备
        self.mock_unit_of_work.return_value.users.get_by_id.return_value = None

        # 执行
        result = user_controller.update_user(
            user_id=999,
            name="更新用户",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=70.0,
            activity_level=ActivityLevel.MODERATE,
        )

        # 验证
        assert result is None
        self.mock_error_handler.show_warning.assert_called_once()

    def test_update_user_exception(self, user_controller):
        """测试更新用户时发生异常"""
        # 准备
        self.mock_unit_of_work.return_value.users.get_by_id.side_effect = Exception(
            "数据库错误"
        )

        # 执行
        result = user_controller.update_user(
            user_id=1,
            name="更新用户",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=70.0,
            activity_level=ActivityLevel.MODERATE,
        )

        # 验证
        assert result is None
        self.mock_error_handler.handle_service_error.assert_called_once()

    def test_delete_user_success(self, user_controller):
        """测试删除用户成功"""
        # 准备
        user = TestDataFactory.create_user_profile(id=1, name="待删除用户")
        self.mock_unit_of_work.return_value.users.get_by_id.return_value = user

        # 执行
        result = user_controller.delete_user(1)

        # 验证
        assert result is True
        self.mock_unit_of_work.return_value.users.delete.assert_called_once_with(1)
        self.mock_unit_of_work.return_value.commit.assert_called_once()
        self.mock_error_handler.show_success.assert_called_once()

    def test_delete_user_not_found(self, user_controller):
        """测试删除用户，用户不存在"""
        # 准备
        self.mock_unit_of_work.return_value.users.get_by_id.return_value = None

        # 执行
        result = user_controller.delete_user(999)

        # 验证
        assert result is False
        self.mock_error_handler.show_warning.assert_called_once()

    def test_delete_user_exception(self, user_controller):
        """测试删除用户时发生异常"""
        # 准备
        user = TestDataFactory.create_user_profile(id=1, name="待删除用户")
        self.mock_unit_of_work.return_value.users.get_by_id.return_value = user
        self.mock_unit_of_work.return_value.commit.side_effect = Exception("数据库错误")

        # 执行
        result = user_controller.delete_user(1)

        # 验证
        assert result is False
        self.mock_error_handler.handle_service_error.assert_called_once()

    def test_search_users_by_name(self, user_controller):
        """测试按姓名搜索用户"""
        # 准备
        users = [
            TestDataFactory.create_user_profile(id=1, name="张三"),
            TestDataFactory.create_user_profile(id=2, name="李四"),
            TestDataFactory.create_user_profile(id=3, name="王五"),
        ]
        self.mock_unit_of_work.return_value.users.get_all.return_value = users

        # 执行
        result = user_controller.search_users(name_query="张")

        # 验证
        assert len(result) == 1
        assert result[0].name == "张三"

    def test_search_users_by_gender(self, user_controller):
        """测试按性别搜索用户"""
        # 准备
        users = [
            TestDataFactory.create_user_profile(id=1, name="张三", gender=Gender.MALE),
            TestDataFactory.create_user_profile(
                id=2, name="李四", gender=Gender.FEMALE
            ),
            TestDataFactory.create_user_profile(id=3, name="王五", gender=Gender.MALE),
        ]
        self.mock_unit_of_work.return_value.users.get_all.return_value = users

        # 执行
        result = user_controller.search_users(gender=Gender.FEMALE)

        # 验证
        assert len(result) == 1
        assert result[0].name == "李四"

    def test_search_users_by_age_range(self, user_controller):
        """测试按年龄范围搜索用户"""
        # 准备
        users = [
            TestDataFactory.create_user_profile(
                id=1, name="青年", birth_date=date(2000, 1, 1)
            ),  # 26岁 (2026-2000)
            TestDataFactory.create_user_profile(
                id=2, name="儿童", birth_date=date(2016, 1, 1)
            ),  # 10岁 (2026-2016) - 会被 min_age 排除
            TestDataFactory.create_user_profile(
                id=3, name="老年", birth_date=date(1960, 1, 1)
            ),  # 66岁 - 会被 max_age 排除
        ]
        self.mock_unit_of_work.return_value.users.get_all.return_value = users
        
        # 执行
        # min_age=20, max_age=40 -> 只有26岁符合
        result = user_controller.search_users(min_age=20, max_age=40)
        
        # 验证
        assert len(result) == 1
        assert result[0].name == "青年"  # 26岁在20-40范围内
        
    def test_search_users_exception(self, user_controller):
        """测试搜索用户时数据库异常"""
        # 模拟数据库异常
        self.mock_unit_of_work.return_value.users.get_all.side_effect = Exception("Database error")
        
        # 执行
        result = user_controller.search_users(name_query="test")
        
        # 验证
        assert result == []
        self.mock_error_handler.handle_service_error.assert_called_once()

    def test_search_users_combined_filters(self, user_controller):
        """测试组合条件搜索用户"""
        # 准备
        users = [
            TestDataFactory.create_user_profile(
                id=1, name="张三", gender=Gender.MALE, birth_date=date(1990, 1, 1)
            ),
            TestDataFactory.create_user_profile(
                id=2, name="李四", gender=Gender.FEMALE, birth_date=date(1995, 1, 1)
            ),
            TestDataFactory.create_user_profile(
                id=3, name="王五", gender=Gender.MALE, birth_date=date(1985, 1, 1)
            ),
        ]
        self.mock_unit_of_work.return_value.users.get_all.return_value = users

        # 执行
        result = user_controller.search_users(name_query="张", gender=Gender.MALE)

        # 验证
        assert len(result) == 1
        assert result[0].name == "张三"

    def test_get_user_count_success(self, user_controller):
        """测试获取用户总数"""
        # 准备
        self.mock_unit_of_work.return_value.users.count.return_value = 5

        # 执行
        result = user_controller.get_user_count()

        # 验证
        assert result == 5

    def test_get_user_count_exception(self, user_controller):
        """测试获取用户总数时发生异常"""
        # 准备
        self.mock_unit_of_work.return_value.users.count.side_effect = Exception(
            "数据库错误"
        )

        # 执行
        result = user_controller.get_user_count()

        # 验证
        assert result == 0
        self.mock_error_handler.handle_service_error.assert_called_once()

    def test_validate_user_input_valid(self, user_controller):
        """测试验证用户输入有效"""
        # 不应该抛出异常
        user_controller._validate_user_input(
            name="测试用户", height_cm=175.0, initial_weight_kg=70.0
        )

    def test_validate_user_input_empty_name(self, user_controller):
        """测试验证用户输入，姓名为空"""
        with pytest.raises(ValueError) as exc_info:
            user_controller._validate_user_input(
                name="", height_cm=175.0, initial_weight_kg=70.0
            )

        assert "姓名不能为空" in str(exc_info.value)

    def test_validate_user_input_name_too_long(self, user_controller):
        """测试验证用户输入，姓名过长"""
        long_name = "a" * 101
        with pytest.raises(ValueError) as exc_info:
            user_controller._validate_user_input(
                name=long_name, height_cm=175.0, initial_weight_kg=70.0
            )

        assert "姓名长度不能超过100个字符" in str(exc_info.value)

    def test_validate_user_input_height_too_low(self, user_controller):
        """测试验证用户输入，身高过低"""
        with pytest.raises(ValueError) as exc_info:
            user_controller._validate_user_input(
                name="测试用户", height_cm=90.0, initial_weight_kg=70.0
            )

        assert "身高必须在100.0到250.0厘米之间" in str(exc_info.value)

    def test_validate_user_input_weight_too_high(self, user_controller):
        """测试验证用户输入，体重过高"""
        with pytest.raises(ValueError) as exc_info:
            user_controller._validate_user_input(
                name="测试用户", height_cm=175.0, initial_weight_kg=250.0
            )

        assert "体重必须在30.0到200.0千克之间" in str(exc_info.value)
