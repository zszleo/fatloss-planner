"""Planner业务服务。

整合计算引擎和存储层，提供核心业务逻辑。
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional, Tuple

from src.fatloss.calculator.bmr_calculator import Gender, calculate_bmr
from src.fatloss.calculator.nutrition_calculator import (
    adjust_carbohydrates,
    calculate_nutrition,
)
from src.fatloss.calculator.tdee_calculator import calculate_tdee
from src.fatloss.calculator.time_predictor import (
    calculate_weekly_adjustment,
    predict_weight_loss_time,
)
from src.fatloss.models.app_config import AppConfig
from src.fatloss.models.nutrition_plan import DailyNutritionPlan, WeeklyNutritionPlan
from src.fatloss.models.user_profile import UserProfile
from src.fatloss.models.weight_record import WeightRecord
from src.fatloss.repository.unit_of_work import unit_of_work


@dataclass
class NutritionPlanRequest:
    """营养计划请求"""

    user_id: int
    plan_date: date
    exercise_minutes: float = 60.0
    adjustment_units: int = 0


@dataclass
class WeightLossProgress:
    """减脂进度"""

    user_id: int
    current_weight_kg: float
    target_weight_kg: float
    total_loss_kg: float
    progress_percentage: float
    estimated_completion_date: date
    weekly_adjustment_needed: int  # 0=无调整，1=增加碳水，-1=减少碳水


class PlannerService:
    """Planner业务服务类"""

    def __init__(self, database_url: str = None):
        """初始化Planner服务。

        Args:
            database_url: 数据库连接URL
        """
        self.database_url = database_url

    def create_user_profile(
        self,
        name: str,
        gender: Gender,
        birth_date: date,
        height_cm: float,
        initial_weight_kg: float,
        activity_level: str = "moderate",
    ) -> UserProfile:
        """创建用户档案。

        Args:
            name: 用户姓名
            gender: 性别
            birth_date: 出生日期
            height_cm: 身高（厘米）
            initial_weight_kg: 初始体重（千克）
            activity_level: 活动水平

        Returns:
            创建的用户档案
        """
        user_profile = UserProfile(
            name=name,
            gender=gender,
            birth_date=birth_date,
            height_cm=height_cm,
            initial_weight_kg=initial_weight_kg,
            activity_level=activity_level,
        )

        with unit_of_work(self.database_url) as uow:
            # 创建用户档案
            created_user = uow.users.create(user_profile)

            # 创建初始体重记录
            weight_record = WeightRecord(
                user_id=created_user.id,
                weight_kg=initial_weight_kg,
                record_date=date.today(),
                notes="初始体重记录",
            )
            uow.weights.create(weight_record)

            # 创建默认应用配置
            app_config = AppConfig(user_id=created_user.id)
            uow.app_configs.create(app_config)

            return created_user

    def record_weight(
        self, user_id: int, weight_kg: float, record_date: date = None, notes: str = ""
    ) -> WeightRecord:
        """记录体重。

        Args:
            user_id: 用户ID
            weight_kg: 体重（千克）
            record_date: 记录日期，如果为None则使用今天
            notes: 备注

        Returns:
            创建的体重记录
        """
        if record_date is None:
            record_date = date.today()

        weight_record = WeightRecord(
            user_id=user_id, weight_kg=weight_kg, record_date=record_date, notes=notes
        )

        with unit_of_work(self.database_url) as uow:
            return uow.weights.create(weight_record)

    def generate_daily_nutrition_plan(
        self, request: NutritionPlanRequest
    ) -> DailyNutritionPlan:
        """生成每日营养计划。

        Args:
            request: 营养计划请求

        Returns:
            每日营养计划
        """
        with unit_of_work(self.database_url) as uow:
            # 获取用户档案和应用配置
            user = uow.users.get_by_id(request.user_id)
            if user is None:
                raise ValueError(f"用户不存在: {request.user_id}")

            config = uow.app_configs.get_by_user_id(request.user_id)
            if config is None:
                config = AppConfig(user_id=request.user_id)

            # 获取最新体重
            latest_weight = uow.weights.find_latest_by_user_id(request.user_id)
            if latest_weight is None:
                raise ValueError(f"用户没有体重记录: {request.user_id}")

            # 计算BMR和TDEE
            bmr = calculate_bmr(
                weight_kg=latest_weight.weight_kg,
                height_cm=user.height_cm,
                age_years=user.age,
                gender=user.gender,
            )

            tdee = calculate_tdee(bmr=bmr, exercise_minutes=request.exercise_minutes)

            # 计算营养素分配
            nutrition = calculate_nutrition(tdee=tdee)

            # 应用碳水化合物调整
            if request.adjustment_units != 0:
                adjusted_carb = adjust_carbohydrates(
                    base_carb_g=nutrition.carbohydrates_g,
                    adjustment_units=request.adjustment_units,
                )
                nutrition.carbohydrates_g = adjusted_carb
                is_adjusted = True
            else:
                is_adjusted = False

            # 创建每日营养计划
            daily_plan = DailyNutritionPlan(
                user_id=request.user_id,
                plan_date=request.plan_date,
                target_tdee=tdee,
                nutrition=nutrition,
                is_adjusted=is_adjusted,
                adjustment_units=request.adjustment_units,
            )

            # 保存到数据库
            return uow.daily_nutrition.create_or_update(daily_plan)

    def generate_weekly_nutrition_plan(
        self, user_id: int, week_start_date: date
    ) -> Optional[WeeklyNutritionPlan]:
        """生成每周营养计划。

        Args:
            user_id: 用户ID
            week_start_date: 周开始日期（周一）

        Returns:
            每周营养计划，如果无法生成则返回None
        """
        with unit_of_work(self.database_url) as uow:
            # 检查是否已有该周的每周计划
            existing_weekly = uow.weekly_nutrition.find_by_user_and_week(
                user_id, week_start_date
            )
            if existing_weekly is not None:
                return existing_weekly

            # 生成该周每天的营养计划
            daily_plans = []
            for day_offset in range(7):
                plan_date = week_start_date + timedelta(days=day_offset)

                # 检查是否已有当天的计划
                existing_daily = uow.daily_nutrition.find_by_user_and_date(
                    user_id, plan_date
                )
                if existing_daily is not None:
                    daily_plans.append(existing_daily)
                    continue

                # 生成新的每日计划（使用默认值）
                request = NutritionPlanRequest(
                    user_id=user_id,
                    plan_date=plan_date,
                    exercise_minutes=60.0,  # 默认60分钟训练
                    adjustment_units=0,
                )

                try:
                    daily_plan = self.generate_daily_nutrition_plan(request)
                    daily_plans.append(daily_plan)
                except Exception as e:
                    # 如果某天无法生成计划，记录错误但继续
                    print(f"无法生成{plan_date}的营养计划: {e}")

            if not daily_plans:
                return None

            # 创建每周计划
            return uow.weekly_nutrition.create_from_daily_plans(
                daily_repository=uow.daily_nutrition,
                user_id=user_id,
                week_start_date=week_start_date,
            )

    def calculate_weight_loss_progress(
        self, user_id: int, target_weight_kg: float
    ) -> WeightLossProgress:
        """计算减脂进度。

        Args:
            user_id: 用户ID
            target_weight_kg: 目标体重（千克）

        Returns:
            减脂进度信息
        """
        with unit_of_work(self.database_url) as uow:
            # 获取用户最新体重
            latest_weight = uow.weights.find_latest_by_user_id(user_id)
            if latest_weight is None:
                raise ValueError(f"用户没有体重记录: {user_id}")

            # 获取用户配置
            config = uow.app_configs.get_by_user_id(user_id)
            if config is None:
                config = AppConfig(user_id=user_id)

            # 计算减脂时间预测
            prediction = predict_weight_loss_time(
                current_weight_kg=latest_weight.weight_kg,
                target_weight_kg=target_weight_kg,
            )

            # 计算进度百分比
            total_loss_needed = latest_weight.weight_kg - target_weight_kg
            if total_loss_needed <= 0:
                progress_percentage = 100.0
            else:
                actual_loss = (
                    latest_weight.weight_kg - latest_weight.weight_kg
                )  # 这里需要实际已减重量
                # 简化：假设从初始体重开始计算
                user = uow.users.get_by_id(user_id)
                if user and user.initial_weight_kg > target_weight_kg:
                    total_possible_loss = user.initial_weight_kg - target_weight_kg
                    actual_loss_so_far = (
                        user.initial_weight_kg - latest_weight.weight_kg
                    )
                    progress_percentage = (
                        actual_loss_so_far / total_possible_loss
                    ) * 100
                else:
                    progress_percentage = 0.0

            # 计算每周调整建议
            # 获取上周体重记录
            one_week_ago = date.today() - timedelta(days=7)
            previous_weight = uow.weights.find_previous_by_user_id(
                user_id, latest_weight.record_date
            )

            weekly_adjustment = 0
            if previous_weight:
                expected_weekly_loss = (
                    latest_weight.weight_kg * config.monthly_loss_percentage / 4
                )
                weekly_adjustment = calculate_weekly_adjustment(
                    current_weight_kg=latest_weight.weight_kg,
                    previous_weight_kg=previous_weight.weight_kg,
                    expected_weekly_loss_kg=expected_weekly_loss,
                )

            # 计算预计完成日期
            estimated_weeks = prediction.estimated_weeks
            estimated_completion = date.today() + timedelta(
                days=int(estimated_weeks * 7)
            )

            return WeightLossProgress(
                user_id=user_id,
                current_weight_kg=latest_weight.weight_kg,
                target_weight_kg=target_weight_kg,
                total_loss_kg=prediction.total_loss_kg,
                progress_percentage=round(progress_percentage, 1),
                estimated_completion_date=estimated_completion,
                weekly_adjustment_needed=weekly_adjustment,
            )

    def get_weekly_adjustment_recommendation(self, user_id: int) -> Tuple[int, str]:
        """获取本周碳水化合物调整建议。

        Args:
            user_id: 用户ID

        Returns:
            (调整单位数, 建议说明)
        """
        with unit_of_work(self.database_url) as uow:
            # 获取最新体重记录
            latest_weight = uow.weights.find_latest_by_user_id(user_id)
            if latest_weight is None:
                return 0, "需要先记录体重"

            # 获取一周前的体重记录
            one_week_ago = latest_weight.record_date - timedelta(days=7)
            previous_weight = uow.weights.find_previous_by_user_id(
                user_id, latest_weight.record_date
            )

            if previous_weight is None:
                return 0, "需要至少两次体重记录才能提供调整建议"

            # 获取用户配置
            config = uow.app_configs.get_by_user_id(user_id)
            if config is None:
                config = AppConfig(user_id=user_id)

            # 计算预期每周减重量
            expected_weekly_loss = (
                latest_weight.weight_kg * config.monthly_loss_percentage / 4
            )

            # 计算调整建议
            adjustment = calculate_weekly_adjustment(
                current_weight_kg=latest_weight.weight_kg,
                previous_weight_kg=previous_weight.weight_kg,
                expected_weekly_loss_kg=expected_weekly_loss,
            )

            # 生成建议说明
            actual_loss = previous_weight.weight_kg - latest_weight.weight_kg
            if adjustment > 0:
                message = f"体重下降过快（实际减{actual_loss:.1f}kg，预期减{expected_weekly_loss:.1f}kg），建议增加碳水摄入"
            elif adjustment < 0:
                message = f"体重下降过慢（实际减{actual_loss:.1f}kg，预期减{expected_weekly_loss:.1f}kg），建议减少碳水摄入"
            else:
                message = f"体重变化正常（实际减{actual_loss:.1f}kg，预期减{expected_weekly_loss:.1f}kg），无需调整"

            return adjustment, message

    def get_user_summary(self, user_id: int) -> dict:
        """获取用户摘要信息。

        Args:
            user_id: 用户ID

        Returns:
            用户摘要字典
        """
        with unit_of_work(self.database_url) as uow:
            user = uow.users.get_by_id(user_id)
            if user is None:
                raise ValueError(f"用户不存在: {user_id}")

            latest_weight = uow.weights.find_latest_by_user_id(user_id)
            weight_records_count = uow.weights.count()

            # 计算BMR和TDEE（基于最新体重）
            if latest_weight:
                bmr = calculate_bmr(
                    weight_kg=latest_weight.weight_kg,
                    height_cm=user.height_cm,
                    age_years=user.age,
                    gender=user.gender,
                )
                tdee = calculate_tdee(bmr=bmr, exercise_minutes=60.0)  # 默认60分钟训练
                nutrition = calculate_nutrition(tdee=tdee)
            else:
                bmr = tdee = 0.0
                nutrition = None

            # 获取最新营养计划
            latest_daily_plan = uow.daily_nutrition.find_latest_by_date(user_id=user_id)
            latest_weekly_plan = uow.weekly_nutrition.find_latest_by_user_id(user_id)

            return {
                "user": user,
                "latest_weight": latest_weight,
                "weight_records_count": weight_records_count,
                "bmr": bmr,
                "tdee": tdee,
                "nutrition": nutrition,
                "latest_daily_plan": latest_daily_plan,
                "latest_weekly_plan": latest_weekly_plan,
            }
