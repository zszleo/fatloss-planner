"""主控制器模块。

提供桌面应用的核心控制器，协调视图和业务逻辑。
"""

import logging
from typing import Optional

from fatloss.planner.planner_service import PlannerService
from fatloss.repository.unit_of_work import unit_of_work


class MainController:
    """主控制器，协调桌面应用的所有业务逻辑。"""
    
    def __init__(self, database_url: Optional[str] = None):
        """初始化主控制器。
        
        Args:
            database_url: 数据库连接URL，为None时使用默认配置
        """
        self.database_url = database_url
        self.planner_service = PlannerService(database_url)
        self.logger = logging.getLogger(__name__)
        
        # 初始化数据库连接
        self._initialize_database()
        
    def _initialize_database(self) -> None:
        """初始化数据库连接。"""
        try:
            # 测试数据库连接
            with unit_of_work(self.database_url) as uow:
                # 尝试获取用户数量来测试连接
                users = uow.users.get_all(limit=1)
            self.logger.info("数据库连接初始化成功")
        except Exception as e:
            self.logger.error(f"数据库连接初始化失败: {e}")
            # 数据库文件可能不存在，将在首次使用时创建
    
    def get_application_info(self) -> dict:
        """获取应用信息。
        
        Returns:
            包含应用信息的字典
        """
        return {
            "name": "Fatloss Planner",
            "version": "0.1.0",
            "description": "科学减脂计划工具",
            "author": "Fatloss Planner Team",
        }
    
    def test_database_connection(self) -> bool:
        """测试数据库连接。
        
        Returns:
            连接成功返回True，否则返回False
        """
        try:
            with unit_of_work(self.database_url) as uow:
                # 尝试获取一个用户来测试连接
                uow.users.get_all(limit=1)
            return True
        except Exception as e:
            self.logger.error(f"数据库连接测试失败: {e}")
            return False
    
    def get_user_count(self) -> int:
        """获取用户数量。
        
        Returns:
            用户数量
        """
        try:
            with unit_of_work(self.database_url) as uow:
                users = uow.users.get_all()
                return len(users)
        except Exception as e:
            self.logger.error(f"获取用户数量失败: {e}")
            return 0