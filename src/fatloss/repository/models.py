"""SQLAlchemy ORM模型定义。

定义数据库表结构和SQLAlchemy ORM模型。
"""

import enum
from datetime import date

from sqlalchemy import Boolean, Column, Date, Enum, Float, Integer, String, Text
from sqlalchemy.sql import func

from src.fatloss.repository.database import Base


class GenderEnum(str, enum.Enum):
    """性别枚举（数据库兼容版本）"""

    MALE = "male"
    FEMALE = "female"


class ActivityLevelEnum(str, enum.Enum):
    """活动水平枚举（数据库兼容版本）"""

    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"


class UnitSystemEnum(str, enum.Enum):
    """单位制枚举（数据库兼容版本）"""

    METRIC = "metric"
    IMPERIAL = "imperial"


class ThemeEnum(str, enum.Enum):
    """主题枚举（数据库兼容版本）"""

    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class UserProfileModel(Base):
    """用户档案ORM模型"""

    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    gender = Column(Enum(GenderEnum), nullable=False)
    birth_date = Column(Date, nullable=False)
    height_cm = Column(Float, nullable=False)
    initial_weight_kg = Column(Float, nullable=False)
    activity_level = Column(
        Enum(ActivityLevelEnum), nullable=False, default=ActivityLevelEnum.MODERATE
    )
    created_at = Column(Date, nullable=False, server_default=func.current_date())
    updated_at = Column(
        Date,
        nullable=False,
        server_default=func.current_date(),
        onupdate=func.current_date(),
    )

    def __repr__(self):
        return f"<UserProfileModel(id={self.id}, name='{self.name}')>"


class WeightRecordModel(Base):
    """体重记录ORM模型"""

    __tablename__ = "weight_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    weight_kg = Column(Float, nullable=False)
    record_date = Column(Date, nullable=False, index=True)
    notes = Column(Text, default="")
    created_at = Column(Date, nullable=False, server_default=func.current_date())

    def __repr__(self):
        return f"<WeightRecordModel(id={self.id}, user_id={self.user_id}, weight={self.weight_kg}kg)>"


class DailyNutritionPlanModel(Base):
    """每日营养计划ORM模型"""

    __tablename__ = "daily_nutrition_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    plan_date = Column(Date, nullable=False, index=True)
    target_tdee = Column(Float, nullable=False)
    carbohydrates_g = Column(Float, nullable=False)
    protein_g = Column(Float, nullable=False)
    fat_g = Column(Float, nullable=False)
    is_adjusted = Column(Boolean, default=False)
    adjustment_units = Column(Integer, default=0)
    notes = Column(Text, default="")
    created_at = Column(Date, nullable=False, server_default=func.current_date())

    def __repr__(self):
        return f"<DailyNutritionPlanModel(id={self.id}, user_id={self.user_id}, date={self.plan_date})>"


class WeeklyNutritionPlanModel(Base):
    """每周营养计划ORM模型"""

    __tablename__ = "weekly_nutrition_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    week_start_date = Column(Date, nullable=False, index=True)
    week_end_date = Column(Date, nullable=False, index=True)
    total_carbohydrates_g = Column(Float, nullable=False)
    total_protein_g = Column(Float, nullable=False)
    total_fat_g = Column(Float, nullable=False)
    notes = Column(Text, default="")
    created_at = Column(Date, nullable=False, server_default=func.current_date())

    def __repr__(self):
        return f"<WeeklyNutritionPlanModel(id={self.id}, user_id={self.user_id}, week={self.week_start_date})>"


class AppConfigModel(Base):
    """应用程序配置ORM模型"""

    __tablename__ = "app_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True, unique=True)
    unit_system = Column(
        Enum(UnitSystemEnum), nullable=False, default=UnitSystemEnum.METRIC
    )
    theme = Column(Enum(ThemeEnum), nullable=False, default=ThemeEnum.AUTO)
    language = Column(String(10), nullable=False, default="zh-CN")
    weekly_check_day = Column(Integer, nullable=False, default=1)
    carb_adjustment_unit_g = Column(Integer, nullable=False, default=30)
    monthly_loss_percentage = Column(Float, nullable=False, default=0.05)
    exercise_calories_per_minute = Column(Float, nullable=False, default=10)
    enable_notifications = Column(Boolean, nullable=False, default=True)
    data_retention_days = Column(Integer, nullable=False, default=365)
    created_at = Column(Date, nullable=False, server_default=func.current_date())
    updated_at = Column(
        Date,
        nullable=False,
        server_default=func.current_date(),
        onupdate=func.current_date(),
    )

    def __repr__(self):
        return f"<AppConfigModel(id={self.id}, user_id={self.user_id})>"
