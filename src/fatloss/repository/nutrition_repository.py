"""营养计划Repository实现。

营养计划数据访问层。
"""

from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from fatloss.models.nutrition_plan import DailyNutritionPlan, WeeklyNutritionPlan
from fatloss.repository.mapper import (
    daily_nutrition_plan_from_model,
    daily_nutrition_plan_to_model,
    weekly_nutrition_plan_from_model,
    weekly_nutrition_plan_to_model,
)
from fatloss.repository.models import (
    DailyNutritionPlanModel,
    WeeklyNutritionPlanModel,
)
from fatloss.repository.sqlalchemy_repository import SQLAlchemyDateRangeRepository


class DailyNutritionRepository(
    SQLAlchemyDateRangeRepository[DailyNutritionPlan, DailyNutritionPlanModel, int]
):
    """每日营养计划Repository"""

    def __init__(self, session: Session):
        """初始化每日营养Repository。

        Args:
            session: SQLAlchemy会话
        """
        super().__init__(session, DailyNutritionPlanModel, date_column="plan_date")

    def _to_model(self, entity: DailyNutritionPlan) -> DailyNutritionPlanModel:
        """将DailyNutritionPlan转换为DailyNutritionPlanModel"""
        return daily_nutrition_plan_to_model(entity)

    def _to_pydantic(self, model: DailyNutritionPlanModel) -> DailyNutritionPlan:
        """将DailyNutritionPlanModel转换为DailyNutritionPlan"""
        return daily_nutrition_plan_from_model(model)

    def find_by_user_id(self, user_id: int) -> List[DailyNutritionPlan]:
        """根据用户ID查找每日营养计划。

        Args:
            user_id: 用户ID

        Returns:
            每日营养计划列表（按日期倒序）
        """
        models = (
            self.session.query(DailyNutritionPlanModel)
            .filter(DailyNutritionPlanModel.user_id == user_id)
            .order_by(desc(DailyNutritionPlanModel.plan_date))
            .all()
        )
        return [self._to_pydantic(model) for model in models]

    def find_by_user_and_date(
        self, user_id: int, plan_date: date
    ) -> Optional[DailyNutritionPlan]:
        """查找用户指定日期的营养计划。

        Args:
            user_id: 用户ID
            plan_date: 计划日期

        Returns:
            每日营养计划，如果不存在则返回None
        """
        model = (
            self.session.query(DailyNutritionPlanModel)
            .filter(
                DailyNutritionPlanModel.user_id == user_id,
                DailyNutritionPlanModel.plan_date == plan_date,
            )
            .first()
        )

        if model is None:
            return None
        return self._to_pydantic(model)

    def find_adjusted_plans(self, user_id: int) -> List[DailyNutritionPlan]:
        """查找用户已调整的营养计划。

        Args:
            user_id: 用户ID

        Returns:
            已调整的营养计划列表
        """
        models = (
            self.session.query(DailyNutritionPlanModel)
            .filter(
                DailyNutritionPlanModel.user_id == user_id,
                DailyNutritionPlanModel.is_adjusted == True,
            )
            .order_by(desc(DailyNutritionPlanModel.plan_date))
            .all()
        )
        return [self._to_pydantic(model) for model in models]

    def find_plans_for_week(
        self, user_id: int, week_start_date: date
    ) -> List[DailyNutritionPlan]:
        """查找用户指定周的每日营养计划。

        Args:
            user_id: 用户ID
            week_start_date: 周开始日期（周一）

        Returns:
            周的每日营养计划列表（按日期排序）
        """
        week_end_date = week_start_date + timedelta(days=6)

        models = (
            self.session.query(DailyNutritionPlanModel)
            .filter(
                DailyNutritionPlanModel.user_id == user_id,
                DailyNutritionPlanModel.plan_date >= week_start_date,
                DailyNutritionPlanModel.plan_date <= week_end_date,
            )
            .order_by(DailyNutritionPlanModel.plan_date)
            .all()
        )

        return [self._to_pydantic(model) for model in models]

    def create_or_update(self, plan: DailyNutritionPlan) -> DailyNutritionPlan:
        """创建或更新每日营养计划。

        如果指定日期的计划已存在，则更新；否则创建新计划。

        Args:
            plan: 营养计划

        Returns:
            创建或更新后的营养计划
        """
        existing = self.find_by_user_and_date(plan.user_id, plan.plan_date)
        if existing:
            return self.update(existing.id, plan)
        else:
            return self.create(plan)


class WeeklyNutritionRepository(
    SQLAlchemyDateRangeRepository[WeeklyNutritionPlan, WeeklyNutritionPlanModel, int]
):
    """每周营养计划Repository"""

    def __init__(self, session: Session):
        """初始化每周营养Repository。

        Args:
            session: SQLAlchemy会话
        """
        super().__init__(
            session, WeeklyNutritionPlanModel, date_column="week_start_date"
        )

    def _to_model(self, entity: WeeklyNutritionPlan) -> WeeklyNutritionPlanModel:
        """将WeeklyNutritionPlan转换为WeeklyNutritionPlanModel"""
        return weekly_nutrition_plan_to_model(entity)

    def _to_pydantic(self, model: WeeklyNutritionPlanModel) -> WeeklyNutritionPlan:
        """将WeeklyNutritionPlanModel转换为WeeklyNutritionPlan"""
        return weekly_nutrition_plan_from_model(model)

    def find_by_user_id(self, user_id: int) -> List[WeeklyNutritionPlan]:
        """根据用户ID查找每周营养计划。

        Args:
            user_id: 用户ID

        Returns:
            每周营养计划列表（按周开始日期倒序）
        """
        models = (
            self.session.query(WeeklyNutritionPlanModel)
            .filter(WeeklyNutritionPlanModel.user_id == user_id)
            .order_by(desc(WeeklyNutritionPlanModel.week_start_date))
            .all()
        )
        return [self._to_pydantic(model) for model in models]

    def find_by_user_and_week(
        self, user_id: int, week_start_date: date
    ) -> Optional[WeeklyNutritionPlan]:
        """查找用户指定周的每周营养计划。

        Args:
            user_id: 用户ID
            week_start_date: 周开始日期

        Returns:
            每周营养计划，如果不存在则返回None
        """
        model = (
            self.session.query(WeeklyNutritionPlanModel)
            .filter(
                WeeklyNutritionPlanModel.user_id == user_id,
                WeeklyNutritionPlanModel.week_start_date == week_start_date,
            )
            .first()
        )

        if model is None:
            return None
        return self._to_pydantic(model)

    def find_latest_by_user_id(self, user_id: int) -> Optional[WeeklyNutritionPlan]:
        """查找用户最新的每周营养计划。

        Args:
            user_id: 用户ID

        Returns:
            最新的每周营养计划，如果不存在则返回None
        """
        model = (
            self.session.query(WeeklyNutritionPlanModel)
            .filter(WeeklyNutritionPlanModel.user_id == user_id)
            .order_by(desc(WeeklyNutritionPlanModel.week_start_date))
            .first()
        )

        if model is None:
            return None
        return self._to_pydantic(model)

    def create_from_daily_plans(
        self,
        daily_repository: DailyNutritionRepository,
        user_id: int,
        week_start_date: date,
    ) -> Optional[WeeklyNutritionPlan]:
        """从每日计划创建每周营养计划。

        Args:
            daily_repository: 每日营养计划Repository
            user_id: 用户ID
            week_start_date: 周开始日期

        Returns:
            创建的每周营养计划，如果每日计划为空则返回None
        """
        daily_plans = daily_repository.find_plans_for_week(user_id, week_start_date)
        if not daily_plans:
            return None

        # 计算周总量
        total_carb = sum(plan.nutrition.carbohydrates_g for plan in daily_plans)
        total_protein = sum(plan.nutrition.protein_g for plan in daily_plans)
        total_fat = sum(plan.nutrition.fat_g for plan in daily_plans)

        week_end_date = max(plan.plan_date for plan in daily_plans)

        weekly_plan = WeeklyNutritionPlan(
            user_id=user_id,
            week_start_date=week_start_date,
            week_end_date=week_end_date,
            daily_plans=daily_plans,
            total_carbohydrates_g=round(total_carb, 2),
            total_protein_g=round(total_protein, 2),
            total_fat_g=round(total_fat, 2),
        )

        return self.create(weekly_plan)
