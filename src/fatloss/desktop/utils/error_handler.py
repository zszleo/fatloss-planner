"""错误处理工具模块。

提供统一的错误处理和用户反馈功能。
"""

from typing import Optional, Type

from PyQt5.QtWidgets import QMessageBox, QWidget
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError


class ErrorHandler:
    """统一错误处理类。"""
    
    @staticmethod
    def handle_service_error(
        error: Exception, 
        parent_widget: Optional[QWidget] = None
    ) -> None:
        """处理业务服务错误。
        
        Args:
            error: 捕获的异常
            parent_widget: 父窗口部件，用于对话框显示
        """
        if isinstance(error, ValidationError):
            ErrorHandler._show_validation_error(error, parent_widget)
        elif isinstance(error, SQLAlchemyError):
            ErrorHandler._show_database_error(error, parent_widget)
        else:
            ErrorHandler._show_generic_error(error, parent_widget)
    
    @staticmethod
    def _show_validation_error(
        error: ValidationError, 
        parent_widget: Optional[QWidget] = None
    ) -> None:
        """显示验证错误。
        
        Args:
            error: Pydantic验证错误
            parent_widget: 父窗口部件
        """
        error_messages = []
        for err in error.errors():
            field = " -> ".join(str(loc) for loc in err["loc"])
            msg = err["msg"]
            error_messages.append(f"{field}: {msg}")
        
        error_text = "\n".join(error_messages)
        QMessageBox.warning(
            parent_widget,
            "输入验证错误",
            f"请检查以下输入字段：\n\n{error_text}"
        )
    
    @staticmethod
    def _show_database_error(
        error: SQLAlchemyError, 
        parent_widget: Optional[QWidget] = None
    ) -> None:
        """显示数据库错误。
        
        Args:
            error: SQLAlchemy数据库错误
            parent_widget: 父窗口部件
        """
        QMessageBox.critical(
            parent_widget,
            "数据库错误",
            f"数据库操作失败：{error}\n\n请检查数据库连接和权限。"
        )
    
    @staticmethod
    def _show_generic_error(
        error: Exception, 
        parent_widget: Optional[QWidget] = None
    ) -> None:
        """显示通用错误。
        
        Args:
            error: 通用异常
            parent_widget: 父窗口部件
        """
        QMessageBox.critical(
            parent_widget,
            "系统错误",
            f"发生未预期的错误：\n\n{error}"
        )
    
    @staticmethod
    def show_success(
        message: str, 
        parent_widget: Optional[QWidget] = None
    ) -> None:
        """显示成功消息。
        
        Args:
            message: 成功消息内容
            parent_widget: 父窗口部件
        """
        QMessageBox.information(
            parent_widget,
            "操作成功",
            message
        )
    
    @staticmethod
    def show_warning(
        message: str, 
        parent_widget: Optional[QWidget] = None
    ) -> None:
        """显示警告消息。
        
        Args:
            message: 警告消息内容
            parent_widget: 父窗口部件
        """
        QMessageBox.warning(
            parent_widget,
            "警告",
            message
        )
    
    @staticmethod
    def show_info(
        message: str, 
        parent_widget: Optional[QWidget] = None
    ) -> None:
        """显示信息消息。
        
        Args:
            message: 信息消息内容
            parent_widget: 父窗口部件
        """
        QMessageBox.information(
            parent_widget,
            "信息",
            message
        )