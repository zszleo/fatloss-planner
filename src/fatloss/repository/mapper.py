"""Pydantic模型与SQLAlchemy模型之间的映射器。

提供在Pydantic数据模型和SQLAlchemy ORM模型之间转换的功能。
"""

from datetime import date
from typing import Optional

from src.fatloss.calculator.nutrition_calculator import NutritionDistribution
from src.fatloss.models.app_config import AppConfig, Theme, UnitSystem
from src.fatloss.models.nutrition_plan import DailyNutritionPlan, WeeklyNutritionPlan
from src.fatloss.models.user_profile import ActivityLevel, Gender, UserProfile
from src.fatloss.models.weight_record import WeightRecord
from src.fatloss.repository.models import (
    ActivityLevelEnum,
    AppConfigModel,
    DailyNutritionPlanModel,
    GenderEnum,
    ThemeEnum,
    UnitSystemEnum,
    UserProfileModel,
    WeeklyNutritionPlanModel,
    WeightRecordModel,
)


def to_sqlalchemy_gender(gender: Gender | str) -> GenderEnum:
    """将Pydantic Gender或字符串转换为SQLAlchemy GenderEnum"""
    if isinstance(gender, str):
        return GenderEnum(gender)
    return GenderEnum(gender.value)


def to_pydantic_gender(gender: GenderEnum) -> Gender:
    """将SQLAlchemy GenderEnum转换为Pydantic Gender"""
    return Gender(gender.value)


def to_sqlalchemy_activity_level(level: ActivityLevel | str) -> ActivityLevelEnum:
    """将Pydantic ActivityLevel或字符串转换为SQLAlchemy ActivityLevelEnum"""
    if isinstance(level, str):
        return ActivityLevelEnum(level)
    return ActivityLevelEnum(level.value)


def to_pydantic_activity_level(level: ActivityLevelEnum) -> ActivityLevel:
    """将SQLAlchemy ActivityLevelEnum转换为Pydantic ActivityLevel"""
    return ActivityLevel(level.value)


def to_sqlalchemy_unit_system(unit: UnitSystem | str) -> UnitSystemEnum:
    """将Pydantic UnitSystem或字符串转换为SQLAlchemy UnitSystemEnum"""
    if isinstance(unit, str):
        return UnitSystemEnum(unit)
    return UnitSystemEnum(unit.value)


def to_pydantic_unit_system(unit: UnitSystemEnum) -> UnitSystem:
    """将SQLAlchemy UnitSystemEnum转换为Pydantic UnitSystem"""
    return UnitSystem(unit.value)


def to_sqlalchemy_theme(theme: Theme | str) -> ThemeEnum:
    """将Pydantic Theme或字符串转换为SQLAlchemy ThemeEnum"""
    if isinstance(theme, str):
        return ThemeEnum(theme)
    return ThemeEnum(theme.value)


def to_pydantic_theme(theme: ThemeEnum) -> Theme:
    """将SQLAlchemy ThemeEnum转换为Pydantic Theme"""
    return Theme(theme.value)


def user_profile_to_model(user_profile: UserProfile) -> UserProfileModel:
    """将UserProfile Pydantic模型转换为UserProfileModel ORM模型"""
    return UserProfileModel(
        id=user_profile.id,
        name=user_profile.name,
        gender=to_sqlalchemy_gender(user_profile.gender),
        birth_date=user_profile.birth_date,
        height_cm=user_profile.height_cm,
        initial_weight_kg=user_profile.initial_weight_kg,
        activity_level=to_sqlalchemy_activity_level(user_profile.activity_level),
        created_at=user_profile.created_at,
        updated_at=user_profile.updated_at,
    )


def user_profile_from_model(model: UserProfileModel) -> UserProfile:
    """将UserProfileModel ORM模型转换为UserProfile Pydantic模型"""
    return UserProfile(
        id=model.id,
        name=model.name,
        gender=to_pydantic_gender(model.gender),
        birth_date=model.birth_date,
        height_cm=model.height_cm,
        initial_weight_kg=model.initial_weight_kg,
        activity_level=to_pydantic_activity_level(model.activity_level),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def weight_record_to_model(weight_record: WeightRecord) -> WeightRecordModel:
    """将WeightRecord Pydantic模型转换为WeightRecordModel ORM模型"""
    return WeightRecordModel(
        id=weight_record.id,
        user_id=weight_record.user_id,
        weight_kg=weight_record.weight_kg,
        record_date=weight_record.record_date,
        notes=weight_record.notes,
        created_at=weight_record.created_at,
    )


def weight_record_from_model(model: WeightRecordModel) -> WeightRecord:
    """将WeightRecordModel ORM模型转换为WeightRecord Pydantic模型"""
    return WeightRecord(
        id=model.id,
        user_id=model.user_id,
        weight_kg=model.weight_kg,
        record_date=model.record_date,
        notes=model.notes,
        created_at=model.created_at,
    )


def daily_nutrition_plan_to_model(plan: DailyNutritionPlan) -> DailyNutritionPlanModel:
    """将DailyNutritionPlan Pydantic模型转换为DailyNutritionPlanModel ORM模型"""
    return DailyNutritionPlanModel(
        id=plan.id,
        user_id=plan.user_id,
        plan_date=plan.plan_date,
        target_tdee=plan.target_tdee,
        carbohydrates_g=plan.nutrition.carbohydrates_g,
        protein_g=plan.nutrition.protein_g,
        fat_g=plan.nutrition.fat_g,
        is_adjusted=plan.is_adjusted,
        adjustment_units=plan.adjustment_units,
        notes=plan.notes,
        created_at=plan.created_at,
    )


def daily_nutrition_plan_from_model(
    model: DailyNutritionPlanModel,
) -> DailyNutritionPlan:
    """将DailyNutritionPlanModel ORM模型转换为DailyNutritionPlan Pydantic模型"""
    nutrition = NutritionDistribution(
        carbohydrates_g=model.carbohydrates_g,
        protein_g=model.protein_g,
        fat_g=model.fat_g,
        total_calories=model.target_tdee,
    )

    return DailyNutritionPlan(
        id=model.id,
        user_id=model.user_id,
        plan_date=model.plan_date,
        target_tdee=model.target_tdee,
        nutrition=nutrition,
        is_adjusted=model.is_adjusted,
        adjustment_units=model.adjustment_units,
        notes=model.notes,
        created_at=model.created_at,
    )


def weekly_nutrition_plan_to_model(
    plan: WeeklyNutritionPlan,
) -> WeeklyNutritionPlanModel:
    """将WeeklyNutritionPlan Pydantic模型转换为WeeklyNutritionPlanModel ORM模型"""
    return WeeklyNutritionPlanModel(
        id=plan.id,
        user_id=plan.user_id,
        week_start_date=plan.week_start_date,
        week_end_date=plan.week_end_date,
        total_carbohydrates_g=plan.total_carbohydrates_g,
        total_protein_g=plan.total_protein_g,
        total_fat_g=plan.total_fat_g,
        notes=plan.notes,
        created_at=plan.created_at,
    )


def weekly_nutrition_plan_from_model(
    model: WeeklyNutritionPlanModel,
) -> WeeklyNutritionPlan:
    """将WeeklyNutritionPlanModel ORM模型转换为WeeklyNutritionPlan Pydantic模型"""
    # 注意：WeeklyNutritionPlan需要daily_plans，这里只创建基础对象
    # 实际使用时应从数据库加载关联的daily_plans
    return WeeklyNutritionPlan(
        id=model.id,
        user_id=model.user_id,
        week_start_date=model.week_start_date,
        week_end_date=model.week_end_date,
        daily_plans=[],  # 需要额外加载
        total_carbohydrates_g=model.total_carbohydrates_g,
        total_protein_g=model.total_protein_g,
        total_fat_g=model.total_fat_g,
        notes=model.notes,
        created_at=model.created_at,
    )


def app_config_to_model(config: AppConfig) -> AppConfigModel:
    """将AppConfig Pydantic模型转换为AppConfigModel ORM模型"""
    return AppConfigModel(
        id=config.id,
        user_id=config.user_id,
        unit_system=to_sqlalchemy_unit_system(config.unit_system),
        theme=to_sqlalchemy_theme(config.theme),
        language=config.language,
        weekly_check_day=config.weekly_check_day,
        carb_adjustment_unit_g=config.carb_adjustment_unit_g,
        monthly_loss_percentage=config.monthly_loss_percentage,
        exercise_calories_per_minute=config.exercise_calories_per_minute,
        enable_notifications=config.enable_notifications,
        data_retention_days=config.data_retention_days,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


def app_config_from_model(model: AppConfigModel) -> AppConfig:
    """将AppConfigModel ORM模型转换为AppConfig Pydantic模型"""
    return AppConfig(
        id=model.id,
        user_id=model.user_id,
        unit_system=to_pydantic_unit_system(model.unit_system),
        theme=to_pydantic_theme(model.theme),
        language=model.language,
        weekly_check_day=model.weekly_check_day,
        carb_adjustment_unit_g=model.carb_adjustment_unit_g,
        monthly_loss_percentage=model.monthly_loss_percentage,
        exercise_calories_per_minute=model.exercise_calories_per_minute,
        enable_notifications=model.enable_notifications,
        data_retention_days=model.data_retention_days,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
