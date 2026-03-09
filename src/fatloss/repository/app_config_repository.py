"""应用程序配置Repository实现。

应用程序配置数据访问层。
"""

from typing import Optional

from sqlalchemy.orm import Session

from src.fatloss.models.app_config import AppConfig
from src.fatloss.repository.mapper import app_config_from_model, app_config_to_model
from src.fatloss.repository.models import AppConfigModel
from src.fatloss.repository.sqlalchemy_repository import SQLAlchemyFilterableRepository


class AppConfigRepository(
    SQLAlchemyFilterableRepository[AppConfig, AppConfigModel, int]
):
    """应用程序配置Repository"""

    def __init__(self, session: Session):
        """初始化应用配置Repository。

        Args:
            session: SQLAlchemy会话
        """
        super().__init__(session, AppConfigModel)

    def _to_model(self, entity: AppConfig) -> AppConfigModel:
        """将AppConfig转换为AppConfigModel"""
        return app_config_to_model(entity)

    def _to_pydantic(self, model: AppConfigModel) -> AppConfig:
        """将AppConfigModel转换为AppConfig"""
        return app_config_from_model(model)

    def get_by_user_id(self, user_id: int) -> Optional[AppConfig]:
        """根据用户ID获取应用配置。

        Args:
            user_id: 用户ID

        Returns:
            应用配置，如果不存在则返回None
        """
        return self.find_one_by_filter(user_id=user_id)

    def create_or_update(self, config: AppConfig) -> AppConfig:
        """创建或更新应用配置。

        每个用户只有一个配置，如果已存在则更新。

        Args:
            config: 应用配置

        Returns:
            创建或更新后的应用配置
        """
        existing = self.get_by_user_id(config.user_id)
        if existing:
            return self.update(existing.id, config)
        else:
            return self.create(config)

    def update_by_user_id(self, user_id: int, **updates) -> Optional[AppConfig]:
        """根据用户ID更新应用配置的特定字段。

        Args:
            user_id: 用户ID
            **updates: 要更新的字段和值

        Returns:
            更新后的应用配置，如果不存在则返回None
        """
        config = self.get_by_user_id(user_id)
        if config is None:
            return None

        # 更新配置对象
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)

        return self.update(config.id, config)
