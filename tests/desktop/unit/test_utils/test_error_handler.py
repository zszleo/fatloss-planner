"""ErrorHandler单元测试"""

from unittest.mock import Mock, patch, MagicMock
import pytest
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from fatloss.desktop.utils.error_handler import ErrorHandler


class TestErrorHandler:
    """ErrorHandler单元测试类"""

    @patch("fatloss.desktop.utils.error_handler.QMessageBox")
    def test_handle_service_error_validation_error(self, mock_qmessagebox):
        """测试处理Pydantic验证错误"""
        # Arrange
        mock_parent = Mock()
        mock_error = ValidationError.from_exception_data(
            "Validation Error",
            [{"loc": ("name",), "msg": "Field required", "type": "missing"}]
        )
        mock_message_box = Mock()
        mock_qmessagebox.warning.return_value = mock_message_box

        # Act
        ErrorHandler.handle_service_error(mock_error, mock_parent)

        # Assert
        mock_qmessagebox.warning.assert_called_once_with(
            mock_parent,
            "输入验证错误",
            "请检查以下输入字段：\n\nname: Field required"
        )

    @patch("fatloss.desktop.utils.error_handler.QMessageBox")
    def test_handle_service_error_database_error(self, mock_qmessagebox):
        """测试处理SQLAlchemy数据库错误"""
        # Arrange
        mock_parent = Mock()
        mock_error = SQLAlchemyError("Database connection failed")
        mock_message_box = Mock()
        mock_qmessagebox.critical.return_value = mock_message_box

        # Act
        ErrorHandler.handle_service_error(mock_error, mock_parent)

        # Assert
        mock_qmessagebox.critical.assert_called_once_with(
            mock_parent,
            "数据库错误",
            "数据库操作失败：Database connection failed\n\n请检查数据库连接和权限。"
        )

    @patch("fatloss.desktop.utils.error_handler.QMessageBox")
    def test_handle_service_error_generic_error(self, mock_qmessagebox):
        """测试处理通用错误"""
        # Arrange
        mock_parent = Mock()
        mock_error = Exception("Something went wrong")
        mock_message_box = Mock()
        mock_qmessagebox.critical.return_value = mock_message_box

        # Act
        ErrorHandler.handle_service_error(mock_error, mock_parent)

        # Assert
        mock_qmessagebox.critical.assert_called_once_with(
            mock_parent,
            "系统错误",
            "发生未预期的错误：\n\nSomething went wrong"
        )

    @patch("fatloss.desktop.utils.error_handler.QMessageBox")
    def test_handle_service_error_no_parent(self, mock_qmessagebox):
        """测试处理错误时无父窗口"""
        # Arrange
        # 模拟ValidationError
        mock_error = MagicMock(spec=ValidationError)
        mock_error.errors.return_value = [
            {
                "loc": ("age",),
                "msg": "Value must be positive",
                "type": "value_error"
            }
        ]
        mock_message_box = Mock()
        mock_qmessagebox.warning.return_value = mock_message_box

        # Act
        ErrorHandler.handle_service_error(mock_error, None)

        # Assert
        mock_qmessagebox.warning.assert_called_once_with(
            None,
            "输入验证错误",
            "请检查以下输入字段：\n\nage: Value must be positive"
        )

    @patch("fatloss.desktop.utils.error_handler.QMessageBox")
    def test_show_success(self, mock_qmessagebox):
        """测试显示成功消息"""
        # Arrange
        mock_parent = Mock()
        mock_message_box = Mock()
        mock_qmessagebox.information.return_value = mock_message_box

        # Act
        ErrorHandler.show_success("操作成功完成", mock_parent)

        # Assert
        mock_qmessagebox.information.assert_called_once_with(
            mock_parent,
            "操作成功",
            "操作成功完成"
        )

    @patch("fatloss.desktop.utils.error_handler.QMessageBox")
    def test_show_warning(self, mock_qmessagebox):
        """测试显示警告消息"""
        # Arrange
        mock_parent = Mock()
        mock_message_box = Mock()
        mock_qmessagebox.warning.return_value = mock_message_box

        # Act
        ErrorHandler.show_warning("请注意此操作", mock_parent)

        # Assert
        mock_qmessagebox.warning.assert_called_once_with(
            mock_parent,
            "警告",
            "请注意此操作"
        )

    @patch("fatloss.desktop.utils.error_handler.QMessageBox")
    def test_show_info(self, mock_qmessagebox):
        """测试显示信息消息"""
        # Arrange
        mock_parent = Mock()
        mock_message_box = Mock()
        mock_qmessagebox.information.return_value = mock_message_box

        # Act
        ErrorHandler.show_info("这是一条信息", mock_parent)

        # Assert
        mock_qmessagebox.information.assert_called_once_with(
            mock_parent,
            "信息",
            "这是一条信息"
        )