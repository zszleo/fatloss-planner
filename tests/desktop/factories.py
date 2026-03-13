"""桌面测试数据工厂。

提供一致的测试数据生成，支持单元测试和集成测试。
"""

import random
from datetime import date, timedelta
from typing import Optional

from fatloss.calculator.nutrition_calculator import NutritionDistribution
from fatloss.models.app_config import AppConfig, Theme, UnitSystem
from fatloss.models.nutrition_plan import DailyNutritionPlan
from fatloss.models.user_profile import ActivityLevel, Gender, UserProfile
from fatloss.models.weight_record import WeightRecord


class TestDataFactory:
    """测试数据工厂，生成一致的测试数据"""

    @staticmethod
    def create_user_profile(**kwargs) -> UserProfile:
        """创建用户档案测试数据。

        Args:
            **kwargs: 覆盖默认值的用户属性

        Returns:
            UserProfile: 配置好的用户档案实例
        """
        defaults = {
            "name": f"测试用户{random.randint(1, 1000)}",
            "gender": Gender.MALE,
            "birth_date": date(1990, 1, 1),
            "height_cm": 175.0,
            "initial_weight_kg": 70.0,
            "activity_level": ActivityLevel.MODERATE,
            "target_weight_kg": 65.0,
            "weekly_weight_loss_kg": 0.5,
        }
        defaults.update(kwargs)
        return UserProfile(**defaults)

    @staticmethod
    def create_weight_record(user_id: int, **kwargs) -> WeightRecord:
        """创建体重记录测试数据。

        Args:
            user_id: 用户ID
            **kwargs: 覆盖默认值的体重记录属性

        Returns:
            WeightRecord: 配置好的体重记录实例
        """
        defaults = {
            "user_id": user_id,
            "weight_kg": 70.0 + random.uniform(-2.0, 2.0),
            "record_date": date.today() - timedelta(days=random.randint(0, 30)),
            "notes": "测试体重记录",
        }
        defaults.update(kwargs)
        return WeightRecord(**defaults)

    @staticmethod
    def create_weight_records(
        user_id: int, count: int = 30, start_date: Optional[date] = None
    ) -> list[WeightRecord]:
        """创建连续体重记录序列。

        Args:
            user_id: 用户ID
            count: 记录数量（默认30）
            start_date: 开始日期（默认今天-count天）

        Returns:
            list[WeightRecord]: 按日期排序的体重记录列表
        """
        if start_date is None:
            start_date = date.today() - timedelta(days=count)

        records = []
        base_weight = 70.0

        for i in range(count):
            record_date = start_date + timedelta(days=i)
            # 模拟体重逐渐下降，加入随机波动
            weight = base_weight + random.uniform(-1.0, 1.0) - (i * 0.1)

            records.append(
                WeightRecord(
                    user_id=user_id,
                    weight_kg=round(weight, 1),
                    record_date=record_date,
                    notes=f"第{i+1}天记录" if i % 7 == 0 else None,
                )
            )

        return records

    @staticmethod
    def create_nutrition_plan(user_id: int, **kwargs) -> DailyNutritionPlan:
        """创建营养计划测试数据。

        Args:
            user_id: 用户ID
            **kwargs: 覆盖默认值的营养计划属性

        Returns:
            DailyNutritionPlan: 配置好的营养计划实例
        """
        defaults = {
            "user_id": user_id,
            "plan_date": date.today(),  # DailyNutritionPlan uses plan_date, not calculation_date
            "target_tdee": 2000.0,
            "nutrition": NutritionDistribution(
                carbohydrates_g=150.0,
                protein_g=120.0,
                fat_g=50.0,
                total_calories=1800.0,
            ),
            "is_adjusted": False,
            "adjustment_units": 0,
            "notes": "测试营养计划",
        }
        defaults.update(kwargs)
        return DailyNutritionPlan(**defaults)

    @staticmethod
    def create_app_config(user_id: int, **kwargs) -> AppConfig:
        """创建应用配置测试数据。

        Args:
            user_id: 用户ID
            **kwargs: 覆盖默认值的应用配置属性

        Returns:
            AppConfig: 配置好的应用配置实例
        """
        defaults = {
            "user_id": user_id,
            "unit_system": UnitSystem.METRIC,
            "theme": Theme.DARK,
            "language": "zh-CN",
            "weekly_check_day": 1,  # 星期一
            "carb_adjustment_unit_g": 10,
            "monthly_loss_percentage": 0.05,
            "exercise_calories_per_minute": 5.0,
            "enable_notifications": True,
            "data_retention_days": 365,
        }
        defaults.update(kwargs)
        return AppConfig(**defaults)

    @staticmethod
    def create_controller_test_data(user_count: int = 3) -> dict:
        """创建控制器测试用的完整数据集。

        Args:
            user_count: 用户数量（默认3）

        Returns:
            dict: 包含用户、体重记录、营养计划和应用配置的字典
        """
        data = {
            "users": [],
            "weight_records": [],
            "nutrition_plans": [],
            "app_configs": [],
        }

        for i in range(user_count):
            user = TestDataFactory.create_user_profile(
                name=f"测试用户{i+1}",
                initial_weight_kg=70.0 + i * 2.0,
                target_weight_kg=65.0 + i * 2.0,
            )
            user.id = i + 1  # 模拟数据库分配的ID
            data["users"].append(user)

            # 为每个用户创建体重记录
            weight_records = TestDataFactory.create_weight_records(
                user_id=user.id, count=15
            )
            data["weight_records"].extend(weight_records)

            # 为每个用户创建营养计划
            nutrition_plan = TestDataFactory.create_nutrition_plan(
                user_id=user.id,
                calories=1800 - i * 100,
                protein_g=120.0 - i * 10.0,
            )
            data["nutrition_plans"].append(nutrition_plan)

            # 为每个用户创建应用配置
            app_config = TestDataFactory.create_app_config(user_id=user.id)
            data["app_configs"].append(app_config)

        return data
