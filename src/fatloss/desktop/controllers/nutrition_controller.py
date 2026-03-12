"""营养计算控制器模块。

提供营养计算相关的业务逻辑和UI交互。
"""

from typing import Optional, Dict, Any
from datetime import date

from PyQt5.QtWidgets import QWidget

from fatloss.models.user_profile import UserProfile
from fatloss.models.nutrition_plan import DailyNutritionPlan
from fatloss.calculator.nutrition_calculator import NutritionDistribution
from fatloss.planner.planner_service import PlannerService, NutritionPlanRequest
from fatloss.repository.unit_of_work import unit_of_work
from fatloss.desktop.utils.error_handler import ErrorHandler


class NutritionController:
    """营养计算控制器，处理营养计算相关的业务逻辑。"""
    
    # 常量定义
    MIN_EXERCISE_MINUTES = 0.0
    MAX_EXERCISE_MINUTES = 300.0
    MIN_ADJUSTMENT_UNITS = -10
    MAX_ADJUSTMENT_UNITS = 10
    
    DEFAULT_EXERCISE_MINUTES = 60.0
    DEFAULT_ADJUSTMENT_UNITS = 0
    
    def __init__(self, planner_service: PlannerService):
        """初始化营养计算控制器。
        
        Args:
            planner_service: PlannerService业务服务实例
        """
        self.planner_service = planner_service
    
    def calculate_nutrition_plan(
        self,
        user_id: int,
        plan_date: date,
        exercise_minutes: float,
        adjustment_units: int,
        parent_widget: Optional[QWidget] = None
    ) -> Optional[DailyNutritionPlan]:
        """计算每日营养计划。
        
        Args:
            user_id: 用户ID
            plan_date: 计划日期
            exercise_minutes: 训练分钟数
            adjustment_units: 调整单位（±碳水）
            parent_widget: 父窗口部件，用于显示错误消息
            
        Returns:
            每日营养计划对象，如果计算失败则返回None
        """
        try:
            # 验证输入
            self._validate_calculation_input(
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
            
            # 计算营养计划
            plan = self.planner_service.generate_daily_nutrition_plan(request)
            
            ErrorHandler.show_success(f"营养计划计算成功", parent_widget)
            return plan
            
        except Exception as e:
            ErrorHandler.handle_service_error(e, parent_widget)
            return None
    
    def get_user_nutrition_history(
        self,
        user_id: int,
        limit: int = 10
    ) -> list[DailyNutritionPlan]:
        """获取用户营养计划历史记录。
        
        Args:
            user_id: 用户ID
            limit: 返回记录数量限制
            
        Returns:
            营养计划历史记录列表
        """
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                plans = uow.daily_nutrition.find_by_user_id(user_id)
                return plans
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            return []
    
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
    
    def get_all_users(self) -> list[UserProfile]:
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
    
    def calculate_bmr_tdee(
        self,
        user: UserProfile,
        exercise_minutes: float
    ) -> Dict[str, float]:
        """计算BMR和TDEE。
        
        Args:
            user: 用户档案对象
            exercise_minutes: 训练分钟数
            
        Returns:
            包含BMR和TDEE的字典
        """
        try:
            # 导入计算函数（延迟导入，避免循环依赖）
            from fatloss.calculator.bmr_calculator import calculate_bmr
            from fatloss.calculator.tdee_calculator import calculate_tdee
            
            # 获取用户最新体重
            with unit_of_work(self.planner_service.database_url) as uow:
                latest_weight = uow.weights.find_latest_by_user_id(user.id)
                if latest_weight is None:
                    raise ValueError(f"用户没有体重记录: {user.id}")
                
                # 计算BMR
                bmr = calculate_bmr(
                    weight_kg=latest_weight.weight_kg,
                    height_cm=user.height_cm,
                    age_years=user.age,
                    gender=user.gender
                )
                
                # 计算TDEE
                tdee = calculate_tdee(bmr=bmr, exercise_minutes=exercise_minutes)
                
                return {
                    "bmr": bmr,
                    "tdee": tdee,
                    "weight_kg": latest_weight.weight_kg
                }
                
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            return {"bmr": 0.0, "tdee": 0.0, "weight_kg": 0.0}
    
    def calculate_nutrition_from_tdee(
        self,
        tdee: float,
        adjustment_units: int = 0
    ) -> NutritionDistribution:
        """根据TDEE计算营养素分配。
        
        Args:
            tdee: 每日总能量消耗
            adjustment_units: 调整单位（±碳水）
            
        Returns:
            营养素分配对象
        """
        try:
            # 导入计算函数
            from fatloss.calculator.nutrition_calculator import calculate_nutrition, adjust_carbohydrates
            
            # 计算基础营养素
            nutrition = calculate_nutrition(tdee=tdee)
            
            # 应用碳水化合物调整
            if adjustment_units != 0:
                adjusted_carb = adjust_carbohydrates(
                    base_carb_g=nutrition.carbohydrates_g,
                    adjustment_units=adjustment_units
                )
                nutrition.carbohydrates_g = adjusted_carb
            
            return nutrition
            
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            # 返回默认值
            return NutritionDistribution(
                total_calories=tdee,
                protein_g=tdee * 0.3 / 4,  # 30%蛋白质
                carbohydrates_g=tdee * 0.5 / 4,  # 50%碳水
                fat_g=tdee * 0.2 / 9  # 20%脂肪
            )
    
    def _validate_calculation_input(
        self,
        exercise_minutes: float,
        adjustment_units: int,
        parent_widget: Optional[QWidget] = None
    ) -> None:
        """验证计算输入数据。
        
        Args:
            exercise_minutes: 训练分钟数
            adjustment_units: 调整单位
            parent_widget: 父窗口部件，用于显示错误消息
            
        Raises:
            ValueError: 如果验证失败
        """
        # 验证训练分钟数
        if not (self.MIN_EXERCISE_MINUTES <= exercise_minutes <= self.MAX_EXERCISE_MINUTES):
            raise ValueError(f"训练分钟数必须在{self.MIN_EXERCISE_MINUTES}到{self.MAX_EXERCISE_MINUTES}之间")
        
        # 验证调整单位
        if not (self.MIN_ADJUSTMENT_UNITS <= adjustment_units <= self.MAX_ADJUSTMENT_UNITS):
            raise ValueError(f"调整单位必须在{self.MIN_ADJUSTMENT_UNITS}到{self.MAX_ADJUSTMENT_UNITS}之间")
    
    def format_nutrition_summary(self, plan: DailyNutritionPlan) -> str:
        """格式化营养计划摘要。
        
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
        
        return "\n".join(summary_lines)
    
    def format_nutrition_for_table(self, plan: DailyNutritionPlan) -> Dict[str, Any]:
        """将营养计划格式化为表格数据。
        
        Args:
            plan: 每日营养计划对象
            
        Returns:
            表格数据字典
        """
        nutrition = plan.nutrition
        
        return {
            "date": plan.plan_date.strftime("%Y-%m-%d"),
            "tdee": f"{plan.target_tdee:.0f}",
            "protein": f"{nutrition.protein_g:.1f} g",
            "carbs": f"{nutrition.carbohydrates_g:.1f} g",
            "fat": f"{nutrition.fat_g:.1f} g",
            "calories": f"{nutrition.total_calories:.0f} kcal",
            "adjusted": "是" if plan.is_adjusted else "否",
            "adjustment": f"{plan.adjustment_units * 30:+d}g" if plan.is_adjusted else "无"
        }