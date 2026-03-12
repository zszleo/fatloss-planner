"""营养计划数据模型"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict, field_serializer

from fatloss.calculator.nutrition_calculator import NutritionDistribution


class DailyNutritionPlan(BaseModel):
    """每日营养计划"""

    id: int | None = Field(default=None, description="计划ID")
    user_id: int = Field(..., gt=0, description="用户ID")
    plan_date: date = Field(..., description="计划日期")
    target_tdee: float = Field(..., gt=0, description="目标每日总能量消耗（大卡）")
    nutrition: NutritionDistribution = Field(..., description="营养素分配")
    is_adjusted: bool = Field(default=False, description="是否已调整")
    adjustment_units: int = Field(default=0, description="碳水化合物调整单位数")
    notes: str = Field(default="", max_length=500, description="备注")
    created_at: date = Field(default_factory=date.today, description="创建日期")

    @field_serializer('plan_date', 'created_at')
    def serialize_date(self, value: date, _info):
        """序列化日期字段为ISO格式"""
        return value.isoformat() if value else None

    model_config = ConfigDict()

    @field_validator("plan_date", mode="before")
    def validate_plan_date(cls, v):
        """验证计划日期（允许过去日期以便历史记录和查看）"""
        # 允许过去、现在和未来日期
        # 过去日期可用于历史记录和查看
        return v


class WeeklyNutritionPlan(BaseModel):
    """每周营养计划"""

    id: int | None = Field(default=None, description="计划ID")
    user_id: int = Field(..., gt=0, description="用户ID")
    week_start_date: date = Field(..., description="周开始日期")
    week_end_date: date = Field(..., description="周结束日期")
    daily_plans: list[DailyNutritionPlan] = Field(
        default_factory=list, description="每日计划列表"
    )
    total_carbohydrates_g: float = Field(
        ..., gt=0, description="周碳水化合物总量（克）"
    )
    total_protein_g: float = Field(..., gt=0, description="周蛋白质总量（克）")
    total_fat_g: float = Field(..., gt=0, description="周脂肪总量（克）")
    notes: str = Field(default="", max_length=1000, description="备注")
    created_at: date = Field(default_factory=date.today, description="创建日期")

    @field_serializer('week_start_date', 'week_end_date', 'created_at')
    def serialize_date(self, value: date, _info):
        """序列化日期字段为ISO格式"""
        return value.isoformat() if value else None

    @field_validator("week_end_date", mode="before")
    def validate_week_dates(cls, v, info):
        """验证周日期范围"""
        if (
            info.data
            and "week_start_date" in info.data
            and v <= info.data["week_start_date"]
        ):
            raise ValueError("周结束日期必须晚于周开始日期")
        return v

    @classmethod
    def from_daily_plans(
        cls, daily_plans: list[DailyNutritionPlan]
    ) -> "WeeklyNutritionPlan":
        """从每日计划列表创建周计划"""
        if not daily_plans:
            raise ValueError("每日计划列表不能为空")

        user_id = daily_plans[0].user_id
        week_start = min(p.plan_date for p in daily_plans)
        week_end = max(p.plan_date for p in daily_plans)

        total_carb = sum(p.nutrition.carbohydrates_g for p in daily_plans)
        total_protein = sum(p.nutrition.protein_g for p in daily_plans)
        total_fat = sum(p.nutrition.fat_g for p in daily_plans)

        return cls(
            user_id=user_id,
            week_start_date=week_start,
            week_end_date=week_end,
            daily_plans=daily_plans,
            total_carbohydrates_g=round(total_carb, 2),
            total_protein_g=round(total_protein, 2),
            total_fat_g=round(total_fat, 2),
        )
