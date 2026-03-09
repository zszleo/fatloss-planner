"""Repository数据访问层。

提供数据访问的抽象层和具体实现。
"""

from src.fatloss.repository.abstract_repository import (
    BaseRepository,
    DateRangeRepository,
    FilterableRepository,
)
from src.fatloss.repository.app_config_repository import AppConfigRepository
from src.fatloss.repository.database import (
    Base,
    create_engine_from_url,
    create_session_factory,
    get_database_url,
    get_session,
    init_database,
)
from src.fatloss.repository.mapper import (
    app_config_from_model,
    app_config_to_model,
    daily_nutrition_plan_from_model,
    daily_nutrition_plan_to_model,
    user_profile_from_model,
    user_profile_to_model,
    weekly_nutrition_plan_from_model,
    weekly_nutrition_plan_to_model,
    weight_record_from_model,
    weight_record_to_model,
)
from src.fatloss.repository.models import (
    AppConfigModel,
    DailyNutritionPlanModel,
    UserProfileModel,
    WeeklyNutritionPlanModel,
    WeightRecordModel,
)
from src.fatloss.repository.nutrition_repository import (
    DailyNutritionRepository,
    WeeklyNutritionRepository,
)
from src.fatloss.repository.sqlalchemy_repository import (
    SQLAlchemyDateRangeRepository,
    SQLAlchemyFilterableRepository,
    SQLAlchemyRepository,
)
from src.fatloss.repository.unit_of_work import (
    DatabaseContext,
    UnitOfWork,
    unit_of_work,
)
from src.fatloss.repository.user_repository import UserRepository
from src.fatloss.repository.weight_repository import WeightRepository

__all__ = [
    # 抽象层
    "BaseRepository",
    "FilterableRepository",
    "DateRangeRepository",
    # 数据库配置
    "Base",
    "get_database_url",
    "create_engine_from_url",
    "create_session_factory",
    "init_database",
    "get_session",
    # ORM模型
    "UserProfileModel",
    "WeightRecordModel",
    "DailyNutritionPlanModel",
    "WeeklyNutritionPlanModel",
    "AppConfigModel",
    # 映射器
    "user_profile_to_model",
    "user_profile_from_model",
    "weight_record_to_model",
    "weight_record_from_model",
    "daily_nutrition_plan_to_model",
    "daily_nutrition_plan_from_model",
    "weekly_nutrition_plan_to_model",
    "weekly_nutrition_plan_from_model",
    "app_config_to_model",
    "app_config_from_model",
    # SQLAlchemy实现
    "SQLAlchemyRepository",
    "SQLAlchemyFilterableRepository",
    "SQLAlchemyDateRangeRepository",
    # 具体Repository
    "UserRepository",
    "WeightRepository",
    "DailyNutritionRepository",
    "WeeklyNutritionRepository",
    "AppConfigRepository",
    # 工作单元
    "UnitOfWork",
    "unit_of_work",
    "DatabaseContext",
]
