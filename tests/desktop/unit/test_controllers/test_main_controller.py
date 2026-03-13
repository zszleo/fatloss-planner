"""MainController单元测试"""

from unittest.mock import Mock, patch, MagicMock
import pytest

from fatloss.desktop.controllers.main_controller import MainController


class TestMainController:
    """MainController单元测试类"""

    def test_initialization_without_database_url(self):
        """测试不带数据库URL的初始化"""
        # Act
        controller = MainController(database_url=None)
        
        # Assert
        assert controller.database_url is None
        assert controller.planner_service is not None
        assert controller.logger.name == "fatloss.desktop.controllers.main_controller"

    def test_initialization_with_database_url(self):
        """测试带数据库URL的初始化"""
        # Arrange
        test_url = "sqlite:///:memory:"
        
        # Act
        controller = MainController(database_url=test_url)
        
        # Assert
        assert controller.database_url == test_url
        assert controller.planner_service is not None

    @patch("fatloss.desktop.controllers.main_controller.unit_of_work")
    def test_initialize_database_success(self, mock_unit_of_work):
        """测试数据库连接初始化成功"""
        # Arrange
        mock_uow = MagicMock()
        mock_uow.__enter__.return_value = mock_uow
        mock_uow.users.get_all.return_value = []
        mock_unit_of_work.return_value = mock_uow
        
        controller = MainController(database_url=None)
        
        # Act - _initialize_database is called during __init__
        
        # Assert
        mock_unit_of_work.assert_called_once_with(None)
        mock_uow.users.get_all.assert_called_once_with(limit=1)

    @patch("fatloss.desktop.controllers.main_controller.unit_of_work")
    def test_initialize_database_failure(self, mock_unit_of_work, caplog):
        """测试数据库连接初始化失败（记录错误但不抛出异常）"""
        # Arrange
        mock_unit_of_work.side_effect = Exception("Connection failed")
        
        # Act - 应该记录错误但不抛出异常
        controller = MainController(database_url=None)
        
        # Assert
        assert "数据库连接初始化失败" in caplog.text

    def test_get_application_info(self):
        """测试获取应用信息"""
        # Arrange
        controller = MainController(database_url=None)
        
        # Act
        info = controller.get_application_info()
        
        # Assert
        assert info["name"] == "Fatloss Planner"
        assert info["version"] == "0.1.0"
        assert info["description"] == "科学减脂计划工具"
        assert info["author"] == "Fatloss Planner Team"

    @patch("fatloss.desktop.controllers.main_controller.unit_of_work")
    def test_test_database_connection_success(self, mock_unit_of_work):
        """测试数据库连接成功"""
        # Arrange
        mock_uow = MagicMock()
        mock_uow.__enter__.return_value = mock_uow
        mock_uow.users.get_all.return_value = []
        mock_unit_of_work.return_value = mock_uow
        
        controller = MainController(database_url=None)
        
        # Act
        result = controller.test_database_connection()
        
        # Assert
        assert result is True
        # unit_of_work 应该被调用两次：一次在初始化时，一次在连接测试时
        assert mock_unit_of_work.call_count == 2
        # 检查两次调用都使用了正确的参数
        assert mock_unit_of_work.call_args_list[0] == ((None,), {})
        assert mock_unit_of_work.call_args_list[1] == ((None,), {})
        # users.get_all 应该被调用两次，都带 limit=1
        assert mock_uow.users.get_all.call_count == 2
        mock_uow.users.get_all.assert_called_with(limit=1)

    @patch("fatloss.desktop.controllers.main_controller.unit_of_work")
    def test_test_database_connection_failure(self, mock_unit_of_work, caplog):
        """测试数据库连接失败"""
        # Arrange
        mock_unit_of_work.side_effect = Exception("Connection failed")
        
        controller = MainController(database_url=None)
        
        # Act
        result = controller.test_database_connection()
        
        # Assert
        assert result is False
        assert "数据库连接测试失败" in caplog.text

    @patch("fatloss.desktop.controllers.main_controller.unit_of_work")
    def test_get_user_count_success(self, mock_unit_of_work):
        """测试成功获取用户数量"""
        # Arrange
        mock_users = [Mock(), Mock(), Mock()]
        mock_uow = MagicMock()
        mock_uow.__enter__.return_value = mock_uow
        mock_uow.users.get_all.return_value = mock_users
        mock_unit_of_work.return_value = mock_uow
        
        controller = MainController(database_url=None)
        
        # Act
        count = controller.get_user_count()
        
        # Assert
        assert count == 3
        # unit_of_work 应该被调用两次：一次在初始化时，一次在获取用户数量时
        assert mock_unit_of_work.call_count == 2
        # 检查两次调用都使用了正确的参数
        assert mock_unit_of_work.call_args_list[0] == ((None,), {})
        assert mock_unit_of_work.call_args_list[1] == ((None,), {})
        # users.get_all 应该被调用两次：第一次 limit=1，第二次不带参数
        assert mock_uow.users.get_all.call_count == 2
        # 第一次调用带 limit=1
        mock_uow.users.get_all.assert_any_call(limit=1)
        # 第二次调用不带参数
        mock_uow.users.get_all.assert_any_call()

    @patch("fatloss.desktop.controllers.main_controller.unit_of_work")
    def test_get_user_count_failure(self, mock_unit_of_work, caplog):
        """测试获取用户数量失败"""
        # Arrange
        mock_unit_of_work.side_effect = Exception("Database error")
        
        controller = MainController(database_url=None)
        
        # Act
        count = controller.get_user_count()
        
        # Assert
        assert count == 0
        assert "获取用户数量失败" in caplog.text