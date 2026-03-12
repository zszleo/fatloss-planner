"""计划管理控制器模块。

提供营养计划管理相关的业务逻辑和UI交互。
"""

from typing import Optional, List, Dict, Any
from datetime import date, timedelta

from PyQt5.QtWidgets import QWidget

from fatloss.models.user_profile import UserProfile
from fatloss.models.nutrition_plan import DailyNutritionPlan, WeeklyNutritionPlan
from fatloss.planner.planner_service import PlannerService, NutritionPlanRequest
from fatloss.repository.unit_of_work import unit_of_work
from fatloss.desktop.utils.error_handler import ErrorHandler


class PlanController:
    """计划管理控制器，处理营养计划管理相关的业务逻辑。"""
    
    # 常量定义
    MIN_EXERCISE_MINUTES = 0.0
    MAX_EXERCISE_MINUTES = 300.0
    MIN_ADJUSTMENT_UNITS = -10
    MAX_ADJUSTMENT_UNITS = 10
    
    DEFAULT_EXERCISE_MINUTES = 60.0
    DEFAULT_ADJUSTMENT_UNITS = 0
    
    def __init__(self, planner_service: PlannerService):
        """初始化计划管理控制器。
        
        Args:
            planner_service: PlannerService业务服务实例
        """
        self.planner_service = planner_service
    
    def get_weekly_plan(
        self,
        user_id: int,
        week_start_date: date,
        parent_widget: Optional[QWidget] = None
    ) -> Optional[WeeklyNutritionPlan]:
        """获取或生成周营养计划。
        
        Args:
            user_id: 用户ID
            week_start_date: 周开始日期（周一）
            parent_widget: 父窗口部件，用于显示错误消息
            
        Returns:
            周营养计划对象，如果获取失败则返回None
        """
        try:
            # 生成或获取周计划
            weekly_plan = self.planner_service.generate_weekly_nutrition_plan(
                user_id=user_id,
                week_start_date=week_start_date
            )
            
            if weekly_plan:
                return weekly_plan
            else:
                ErrorHandler.show_warning(f"无法生成{week_start_date}开始的周计划", parent_widget)
                return None
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, parent_widget)
            return None
    
    def generate_weekly_plan(
        self,
        user_id: int,
        week_start_date: date,
        parent_widget: Optional[QWidget] = None
    ) -> Optional[WeeklyNutritionPlan]:
        """强制生成新的周营养计划（覆盖现有计划）。
        
        Args:
            user_id: 用户ID
            week_start_date: 周开始日期（周一）
            parent_widget: 父窗口部件，用于显示错误消息
            
        Returns:
            新生成的周营养计划对象，如果生成失败则返回None
        """
        try:
            # 先删除该周现有的所有每日计划
            with unit_of_work(self.planner_service.database_url) as uow:
                # 查找该周的所有每日计划
                for day_offset in range(7):
                    plan_date = week_start_date + timedelta(days=day_offset)
                    existing_daily = uow.daily_nutrition.find_by_user_and_date(
                        user_id, plan_date
                    )
                    if existing_daily:
                        uow.daily_nutrition.delete(existing_daily.id)
                
                # 删除该周的周计划（如果存在）
                existing_weekly = uow.weekly_nutrition.find_by_user_and_week(
                    user_id, week_start_date
                )
                if existing_weekly:
                    uow.weekly_nutrition.delete(existing_weekly.id)
                
                uow.commit()
            
            # 生成新的周计划
            weekly_plan = self.planner_service.generate_weekly_nutrition_plan(
                user_id=user_id,
                week_start_date=week_start_date
            )
            
            if weekly_plan:
                ErrorHandler.show_success(
                    f"{week_start_date}开始的周计划生成成功", 
                    parent_widget
                )
                return weekly_plan
            else:
                ErrorHandler.show_warning(f"无法生成{week_start_date}开始的周计划", parent_widget)
                return None
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, parent_widget)
            return None
    
    def update_daily_plan(
        self,
        user_id: int,
        plan_date: date,
        exercise_minutes: float,
        adjustment_units: int,
        parent_widget: Optional[QWidget] = None
    ) -> Optional[DailyNutritionPlan]:
        """更新或创建每日营养计划。
        
        Args:
            user_id: 用户ID
            plan_date: 计划日期
            exercise_minutes: 训练分钟数
            adjustment_units: 调整单位（±碳水）
            parent_widget: 父窗口部件，用于显示错误消息
            
        Returns:
            更新后的每日营养计划对象，如果更新失败则返回None
        """
        try:
            # 验证输入
            self._validate_plan_input(
                exercise_minutes=exercise_minutes,
                adjustment_units=adjustment_units,
                parent_widget=parent_widget
            )
            
            # 创建请求
            request = NutritionPlanRequest(
                user_id=user_id,
                plan_date=plan_date,
                exercise_minutes=exercise_minutes,
                adjustment_units=adjustment_units
            )
            
            # 生成或更新每日计划
            daily_plan = self.planner_service.generate_daily_nutrition_plan(request)
            
            ErrorHandler.show_success(f"{plan_date}的营养计划更新成功", parent_widget)
            return daily_plan
            
        except Exception as e:
            ErrorHandler.handle_service_error(e, parent_widget)
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[UserProfile]:
        """根据ID获取用户档案。
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户档案对象，如果不存在则返回None
        """
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                user = uow.users.get_by_id(user_id)
                return user
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            return None
    
    def get_all_users(self) -> List[UserProfile]:
        """获取所有用户档案。
        
        Returns:
            用户档案列表
        """
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                users = uow.users.get_all()
                return users
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            return []
    
    def get_daily_plans_for_week(
        self,
        user_id: int,
        week_start_date: date
    ) -> Dict[date, Optional[DailyNutritionPlan]]:
        """获取一周内的每日营养计划。
        
        Args:
            user_id: 用户ID
            week_start_date: 周开始日期（周一）
            
        Returns:
            日期到每日计划的映射字典
        """
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                result = {}
                
                for day_offset in range(7):
                    plan_date = week_start_date + timedelta(days=day_offset)
                    daily_plan = uow.daily_nutrition.find_by_user_and_date(
                        user_id, plan_date
                    )
                    result[plan_date] = daily_plan
                
                return result
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            return {}
    
    def get_available_weeks(self, user_id: int) -> List[date]:
        """获取用户已有计划的周开始日期列表。
        
        Args:
            user_id: 用户ID
            
        Returns:
            周开始日期列表（按日期降序排列）
        """
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                weekly_plans = uow.weekly_nutrition.find_by_user_id(user_id)
                week_starts = [plan.week_start_date for plan in weekly_plans]
                
                # 按日期降序排列
                week_starts.sort(reverse=True)
                
                return week_starts
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            return []
    
    def format_daily_plan_summary(self, plan: DailyNutritionPlan) -> str:
        """格式化每日营养计划摘要。
        
        Args:
            plan: 每日营养计划对象
            
        Returns:
            格式化后的摘要字符串
        """
        nutrition = plan.nutrition
        
        summary_lines = [
            f"📅 日期: {plan.plan_date}",
            f"🔥 TDEE: {plan.target_tdee:.0f} kcal",
            f"",
            f"🥩 蛋白质: {nutrition.protein_g:.1f} g",
            f"🍚 碳水化合物: {nutrition.carbohydrates_g:.1f} g",
            f"🥑 脂肪: {nutrition.fat_g:.1f} g",
            f"⚖️ 总热量: {nutrition.total_calories:.0f} kcal",
            f"",
        ]
        
        if plan.is_adjusted:
            adjustment_text = "增加" if plan.adjustment_units > 0 else "减少"
            summary_lines.append(f"📊 调整: {adjustment_text} {abs(plan.adjustment_units) * 30}g 碳水化合物")
        
        if plan.notes:
            summary_lines.append(f"📝 备注: {plan.notes}")
        
        return "\n".join(summary_lines)
    
    def format_weekly_plan_summary(self, plan: WeeklyNutritionPlan) -> str:
        """格式化周营养计划摘要。
        
        Args:
            plan: 周营养计划对象
            
        Returns:
            格式化后的摘要字符串
        """
        summary_lines = [
            f"📅 周计划: {plan.week_start_date} 至 {plan.week_end_date}",
            f"",
            f"📊 周总计:",
            f"🍚 碳水化合物: {plan.total_carbohydrates_g:.1f} g",
            f"🥩 蛋白质: {plan.total_protein_g:.1f} g",
            f"🥑 脂肪: {plan.total_fat_g:.1f} g",
            f"",
            f"📅 每日计划:",
        ]
        
        for i, daily_plan in enumerate(plan.daily_plans, 1):
            nutrition = daily_plan.nutrition
            day_name = self._get_day_name(daily_plan.plan_date)
            
            summary_lines.append(
                f"{i}. {day_name} ({daily_plan.plan_date}): "
                f"{nutrition.carbohydrates_g:.0f}g 碳水 | "
                f"{nutrition.protein_g:.0f}g 蛋白 | "
                f"{nutrition.fat_g:.0f}g 脂肪"
            )
        
        if plan.notes:
            summary_lines.append(f"")
            summary_lines.append(f"📝 备注: {plan.notes}")
        
        return "\n".join(summary_lines)
    
    def export_weekly_plan_to_text(self, plan: WeeklyNutritionPlan) -> str:
        """将周营养计划导出为文本格式。
        
        Args:
            plan: 周营养计划对象
            
        Returns:
            导出的文本内容
        """
        lines = [
            "=" * 50,
            f"Fatloss Planner - 周营养计划",
            f"生成时间: {date.today()}",
            "=" * 50,
            f"",
            f"📅 周计划: {plan.week_start_date} 至 {plan.week_end_date}",
            f"",
            f"📊 周总计:",
            f"🍚 碳水化合物: {plan.total_carbohydrates_g:.1f} g",
            f"🥩 蛋白质: {plan.total_protein_g:.1f} g",
            f"🥑 脂肪: {plan.total_fat_g:.1f} g",
            f"",
            f"📅 每日营养计划:",
            f"",
        ]
        
        for daily_plan in plan.daily_plans:
            day_name = self._get_day_name(daily_plan.plan_date)
            nutrition = daily_plan.nutrition
            
            lines.append(f"【{day_name}】{daily_plan.plan_date}")
            lines.append(f"  🔥 TDEE: {daily_plan.target_tdee:.0f} kcal")
            lines.append(f"  🍚 碳水化合物: {nutrition.carbohydrates_g:.1f} g")
            lines.append(f"  🥩 蛋白质: {nutrition.protein_g:.1f} g")
            lines.append(f"  🥑 脂肪: {nutrition.fat_g:.1f} g")
            lines.append(f"  ⚖️ 总热量: {nutrition.total_calories:.0f} kcal")
            
            if daily_plan.is_adjusted:
                adjustment = daily_plan.adjustment_units * 30
                lines.append(f"  📊 调整: {adjustment:+d}g 碳水化合物")
            
            if daily_plan.notes:
                lines.append(f"  📝 备注: {daily_plan.notes}")
            
            lines.append("")
        
        lines.append("=" * 50)
        lines.append(f"© {date.today().year} Fatloss Planner")
        lines.append("=" * 50)
        
        return "\n".join(lines)
    
    def _validate_plan_input(
        self,
        exercise_minutes: float,
        adjustment_units: int,
        parent_widget: Optional[QWidget] = None
    ) -> None:
        """验证计划输入数据。
        
        Args:
            exercise_minutes: 训练分钟数
            adjustment_units: 调整单位
            parent_widget: 父窗口部件，用于显示错误消息
            
        Raises:
            ValueError: 如果验证失败
        """
        # 验证训练分钟数
        if not (self.MIN_EXERCISE_MINUTES <= exercise_minutes <= self.MAX_EXERCISE_MINUTES):
            raise ValueError(
                f"训练分钟数必须在{self.MIN_EXERCISE_MINUTES}到{self.MAX_EXERCISE_MINUTES}之间"
            )
        
        # 验证调整单位
        if not (self.MIN_ADJUSTMENT_UNITS <= adjustment_units <= self.MAX_ADJUSTMENT_UNITS):
            raise ValueError(
                f"调整单位必须在{self.MIN_ADJUSTMENT_UNITS}到{self.MAX_ADJUSTMENT_UNITS}之间"
            )
    
    def _get_day_name(self, date_obj: date) -> str:
        """获取日期对应的星期几名称。
        
        Args:
            date_obj: 日期对象
            
        Returns:
            星期几名称（周一、周二等）
        """
        weekday = date_obj.weekday()
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return day_names[weekday]