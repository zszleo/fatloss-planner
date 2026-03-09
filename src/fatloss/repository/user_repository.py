"""用户档案Repository实现。

用户档案数据访问层。
"""

from sqlalchemy.orm import Session

from src.fatloss.models.user_profile import UserProfile
from src.fatloss.repository.mapper import user_profile_from_model, user_profile_to_model
from src.fatloss.repository.models import UserProfileModel
from src.fatloss.repository.sqlalchemy_repository import SQLAlchemyFilterableRepository


class UserRepository(
    SQLAlchemyFilterableRepository[UserProfile, UserProfileModel, int]
):
    """用户档案Repository"""

    def __init__(self, session: Session):
        """初始化用户Repository。

        Args:
            session: SQLAlchemy会话
        """
        super().__init__(session, UserProfileModel)

    def _to_model(self, entity: UserProfile) -> UserProfileModel:
        """将UserProfile转换为UserProfileModel"""
        return user_profile_to_model(entity)

    def _to_pydantic(self, model: UserProfileModel) -> UserProfile:
        """将UserProfileModel转换为UserProfile"""
        return user_profile_from_model(model)

    def find_by_name(self, name: str) -> list[UserProfile]:
        """根据姓名查找用户。

        Args:
            name: 用户姓名（支持模糊匹配）

        Returns:
            用户列表
        """
        models = (
            self.session.query(UserProfileModel)
            .filter(UserProfileModel.name.ilike(f"%{name}%"))
            .all()
        )
        return [self._to_pydantic(model) for model in models]

    def find_by_gender(self, gender: str) -> list[UserProfile]:
        """根据性别查找用户。

        Args:
            gender: 性别（"male"或"female"）

        Returns:
            用户列表
        """
        return self.find_by_filter(gender=gender)

    def find_by_age_range(self, min_age: int, max_age: int) -> list[UserProfile]:
        """根据年龄范围查找用户。

        Args:
            min_age: 最小年龄
            max_age: 最大年龄

        Returns:
            用户列表
        """
        # 注意：这里需要计算年龄，由于数据库存储的是出生日期
        # 这是一个简化实现，实际生产环境可能需要更复杂的查询
        from datetime import date

        today = date.today()

        max_birth_date = date(today.year - min_age, today.month, today.day)
        min_birth_date = date(today.year - max_age, today.month, today.day)

        models = (
            self.session.query(UserProfileModel)
            .filter(
                UserProfileModel.birth_date >= min_birth_date,
                UserProfileModel.birth_date <= max_birth_date,
            )
            .all()
        )

        return [self._to_pydantic(model) for model in models]
