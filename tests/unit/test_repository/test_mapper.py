"""Mapper模块测试"""

import pytest
from datetime import date

from fatloss.calculator.nutrition_calculator import NutritionDistribution
from fatloss.models.app_config import AppConfig, Theme, UnitSystem
from fatloss.models.nutrition_plan import DailyNutritionPlan, WeeklyNutritionPlan
from fatloss.models.user_profile import ActivityLevel, Gender, UserProfile
from fatloss.models.weight_record import WeightRecord
from fatloss.repository.mapper import (
    app_config_from_model,
    app_config_to_model,
    daily_nutrition_plan_from_model,
    daily_nutrition_plan_to_model,
    to_pydantic_activity_level,
    to_pydantic_gender,
    to_pydantic_theme,
    to_pydantic_unit_system,
    to_sqlalchemy_activity_level,
    to_sqlalchemy_gender,
    to_sqlalchemy_theme,
    to_sqlalchemy_unit_system,
    user_profile_from_model,
    user_profile_to_model,
    weekly_nutrition_plan_from_model,
    weekly_nutrition_plan_to_model,
    weight_record_from_model,
    weight_record_to_model,
)
from fatloss.repository.models import (
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


class TestMapper:
    """Mapper测试类"""

    def test_to_sqlalchemy_gender_with_string(self):
        """测试to_sqlalchemy_gender函数接受字符串输入"""
        # 测试字符串输入（注意：枚举值是小写）
        result = to_sqlalchemy_gender("male")
        assert result == GenderEnum.MALE
        
        result = to_sqlalchemy_gender("female")
        assert result == GenderEnum.FEMALE
        
        # 测试枚举输入
        result = to_sqlalchemy_gender(Gender.MALE)
        assert result == GenderEnum.MALE

    def test_to_sqlalchemy_activity_level_with_string(self):
        """测试to_sqlalchemy_activity_level函数接受字符串输入"""
        # 测试字符串输入（注意：枚举值是小写）
        result = to_sqlalchemy_activity_level("sedentary")
        assert result == ActivityLevelEnum.SEDENTARY
        
        result = to_sqlalchemy_activity_level("light")
        assert result == ActivityLevelEnum.LIGHT
        
        # 测试枚举输入
        result = to_sqlalchemy_activity_level(ActivityLevel.MODERATE)
        assert result == ActivityLevelEnum.MODERATE

    def test_to_sqlalchemy_unit_system_with_string(self):
        """测试to_sqlalchemy_unit_system函数接受字符串输入"""
        # 测试字符串输入（注意：枚举值是小写）
        result = to_sqlalchemy_unit_system("metric")
        assert result == UnitSystemEnum.METRIC
        
        result = to_sqlalchemy_unit_system("imperial")
        assert result == UnitSystemEnum.IMPERIAL
        
        # 测试枚举输入
        result = to_sqlalchemy_unit_system(UnitSystem.METRIC)
        assert result == UnitSystemEnum.METRIC

    def test_to_sqlalchemy_theme_with_string(self):
        """测试to_sqlalchemy_theme函数接受字符串输入"""
        # 测试字符串输入（注意：枚举值是小写）
        result = to_sqlalchemy_theme("light")
        assert result == ThemeEnum.LIGHT
        
        result = to_sqlalchemy_theme("dark")
        assert result == ThemeEnum.DARK
        
        # 测试枚举输入
        result = to_sqlalchemy_theme(Theme.DARK)
        assert result == ThemeEnum.DARK

    def test_user_profile_conversion(self):
        """测试用户配置文件转换"""
        user_profile = UserProfile(
            id=1,
            name="测试用户",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=70.0,
            activity_level=ActivityLevel.MODERATE,
            created_at=date(2025, 1, 1),
            updated_at=date(2025, 1, 2),
        )
        
        # 转换为模型
        model = user_profile_to_model(user_profile)
        assert isinstance(model, UserProfileModel)
        assert model.id == 1
        assert model.name == "测试用户"
        assert model.gender == GenderEnum.MALE
        assert model.birth_date == date(1990, 1, 1)
        
        # 转换回Pydantic
        result = user_profile_from_model(model)
        assert isinstance(result, UserProfile)
        assert result.id == 1
        assert result.name == "测试用户"
        assert result.gender == Gender.MALE

    def test_weight_record_conversion(self):
        """测试体重记录转换"""
        weight_record = WeightRecord(
            id=1,
            user_id=2,
            weight_kg=70.5,
            record_date=date(2025, 1, 1),
            notes="测试记录",
            created_at=date(2025, 1, 1),
        )
        
        # 转换为模型
        model = weight_record_to_model(weight_record)
        assert isinstance(model, WeightRecordModel)
        assert model.id == 1
        assert model.user_id == 2
        assert model.weight_kg == 70.5
        
        # 转换回Pydantic
        result = weight_record_from_model(model)
        assert isinstance(result, WeightRecord)
        assert result.id == 1
        assert result.user_id == 2
        assert result.weight_kg == 70.5

    def test_daily_nutrition_plan_conversion(self):
        """测试每日营养计划转换"""
        nutrition = NutritionDistribution(
            carbohydrates_g=200.0,
            protein_g=150.0,
            fat_g=70.0,
            total_calories=2000.0,
        )
        
        # 使用今天或未来的日期，因为plan_date不能是过去日期
        from datetime import date, timedelta
        future_date = date.today() + timedelta(days=1)
        
        daily_plan = DailyNutritionPlan(
            id=1,
            user_id=2,
            plan_date=future_date,
            target_tdee=2000.0,
            nutrition=nutrition,
            is_adjusted=False,
            adjustment_units=0,
            notes="测试计划",
            created_at=date(2025, 1, 1),
        )
        
        # 转换为模型
        model = daily_nutrition_plan_to_model(daily_plan)
        assert isinstance(model, DailyNutritionPlanModel)
        assert model.id == 1
        assert model.user_id == 2
        assert model.target_tdee == 2000.0
        assert model.carbohydrates_g == 200.0
        
        # 转换回Pydantic
        result = daily_nutrition_plan_from_model(model)
        assert isinstance(result, DailyNutritionPlan)
        assert result.id == 1
        assert result.user_id == 2
        assert result.target_tdee == 2000.0
        assert result.nutrition.carbohydrates_g == 200.0

    def test_app_config_conversion(self):
        """测试应用配置转换"""
        app_config = AppConfig(
            id=1,
            user_id=2,
            unit_system=UnitSystem.METRIC,
            theme=Theme.DARK,
            language="zh-CN",
            weekly_check_day=1,
            carb_adjustment_unit_g=10,
            monthly_loss_percentage=0.05,
            exercise_calories_per_minute=5.0,
            enable_notifications=True,
            data_retention_days=365,
            created_at=date(2025, 1, 1),
            updated_at=date(2025, 1, 2),
        )
        
        # 转换为模型
        model = app_config_to_model(app_config)
        assert isinstance(model, AppConfigModel)
        assert model.id == 1
        assert model.user_id == 2
        assert model.unit_system == UnitSystemEnum.METRIC
        assert model.theme == ThemeEnum.DARK
        
        # 转换回Pydantic
        result = app_config_from_model(model)
        assert isinstance(result, AppConfig)
        assert result.id == 1
        assert result.user_id == 2
        assert result.unit_system == UnitSystem.METRIC
        assert result.theme == Theme.DARK

    def test_enum_conversion_functions(self):
        """测试枚举转换函数"""
        # 测试to_pydantic函数
        assert to_pydantic_gender(GenderEnum.MALE) == Gender.MALE
        assert to_pydantic_gender(GenderEnum.FEMALE) == Gender.FEMALE
        
        assert to_pydantic_activity_level(ActivityLevelEnum.MODERATE) == ActivityLevel.MODERATE
        assert to_pydantic_activity_level(ActivityLevelEnum.ACTIVE) == ActivityLevel.ACTIVE
        
        assert to_pydantic_unit_system(UnitSystemEnum.METRIC) == UnitSystem.METRIC
        assert to_pydantic_unit_system(UnitSystemEnum.IMPERIAL) == UnitSystem.IMPERIAL
        
        assert to_pydantic_theme(ThemeEnum.LIGHT) == Theme.LIGHT
        assert to_pydantic_theme(ThemeEnum.DARK) == Theme.DARK