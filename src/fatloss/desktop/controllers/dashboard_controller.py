"""仪表盘控制器模块。

提供仪表盘数据的整合和业务逻辑。
"""

from typing import Dict, Any, Optional, List
from datetime import date, timedelta

from PyQt5.QtWidgets import QWidget

from fatloss.models.user_profile import UserProfile
from fatloss.models.weight_record import WeightRecord
from fatloss.models.nutrition_plan import DailyNutritionPlan
from fatloss.planner.planner_service import PlannerService
from fatloss.repository.unit_of_work import unit_of_work
from fatloss.desktop.utils.error_handler import ErrorHandler


class DashboardController:
    """仪表盘控制器，处理仪表盘数据的整合和业务逻辑。"""
    
    # 常量定义
    DEFAULT_CHART_DAYS = 30
    MAX_CHART_DAYS = 90
    RECENT_PLANS_LIMIT = 5
    
    def __init__(self, planner_service: PlannerService):
        """初始化仪表盘控制器。
        
        Args:
            planner_service: PlannerService业务服务实例
        """
        self.planner_service = planner_service
    
    def get_dashboard_data(
        self,
        user_id: int,
        parent_widget: Optional[QWidget] = None
    ) -> Optional[Dict[str, Any]]:
        """获取仪表盘数据。
        
        Args:
            user_id: 用户ID
            parent_widget: 父窗口部件，用于显示错误消息
            
        Returns:
            仪表盘数据字典，如果获取失败则返回None
        """
        try:
            # 获取用户摘要（PlannerService中的现有方法）
            summary = self.planner_service.get_user_summary(user_id)
            
            if not summary:
                return None
            
            # 获取额外数据
            weight_stats = self._get_weight_stats(user_id)
            recent_plans = self._get_recent_nutrition_plans(user_id)
            progress_info = self._get_weight_loss_progress(user_id)
            chart_data = self._get_weight_chart_data(user_id)
            
            # 整合数据
            dashboard_data = {
                **summary,
                "weight_stats": weight_stats,
                "recent_plans": recent_plans,
                "progress_info": progress_info,
                "chart_data": chart_data,
                "dashboard_metrics": self._calculate_dashboard_metrics(summary, weight_stats, progress_info)
            }
            
            return dashboard_data
            
        except Exception as e:
            ErrorHandler.handle_service_error(e, parent_widget)
            return None
    
    def get_user_summary(
        self,
        user_id: int,
        parent_widget: Optional[QWidget] = None
    ) -> Optional[Dict[str, Any]]:
        """获取用户摘要信息。
        
        Args:
            user_id: 用户ID
            parent_widget: 父窗口部件，用于显示错误消息
            
        Returns:
            用户摘要字典，如果获取失败则返回None
        """
        try:
            return self.planner_service.get_user_summary(user_id)
        except Exception as e:
            ErrorHandler.handle_service_error(e, parent_widget)
            return None
    
    def get_weight_loss_progress(
        self,
        user_id: int,
        target_weight_kg: Optional[float] = None,
        parent_widget: Optional[QWidget] = None
    ) -> Optional[Any]:
        """获取减脂进度信息。
        
        Args:
            user_id: 用户ID
            target_weight_kg: 目标体重，如果为None则使用用户初始体重的95%
            parent_widget: 父窗口部件，用于显示错误消息
            
        Returns:
            减脂进度信息，如果获取失败则返回None
        """
        try:
            # 如果没有提供目标体重，使用默认值
            if target_weight_kg is None:
                with unit_of_work(self.planner_service.database_url) as uow:
                    user = uow.users.get_by_id(user_id)
                    if user:
                        target_weight_kg = user.initial_weight_kg * 0.95
            
            if target_weight_kg:
                return self.planner_service.calculate_weight_loss_progress(
                    user_id=user_id,
                    target_weight_kg=target_weight_kg
                )
            else:
                return None
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, parent_widget)
            return None
    
    def get_weekly_adjustment_recommendation(
        self,
        user_id: int,
        parent_widget: Optional[QWidget] = None
    ) -> Optional[Dict[str, Any]]:
        """获取每周调整建议。
        
        Args:
            user_id: 用户ID
            parent_widget: 父窗口部件，用于显示错误消息
            
        Returns:
            调整建议字典，如果获取失败则返回None
        """
        try:
            adjustment_units, recommendation = self.planner_service.get_weekly_adjustment_recommendation(user_id)
            
            return {
                "adjustment_units": adjustment_units,
                "recommendation": recommendation,
                "carb_adjustment_g": adjustment_units * 30  # 每单位30g碳水
            }
            
        except Exception as e:
            ErrorHandler.handle_service_error(e, parent_widget)
            return None
    
    def get_recent_activities(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取最近活动记录。
        
        Args:
            user_id: 用户ID
            limit: 返回记录数量限制
            
        Returns:
            活动记录列表
        """
        activities = []
        
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                # 获取最近体重记录
                weight_records = uow.weights.find_by_user_id(user_id)
                weight_records.sort(key=lambda x: x.record_date, reverse=True)
                
                for record in weight_records[:limit]:
                    activities.append({
                        "type": "weight_record",
                        "date": record.record_date,
                        "description": f"记录体重: {record.weight_kg} kg",
                        "data": record
                    })
                
                # 获取最近营养计划
                nutrition_plans = uow.daily_nutrition.find_by_user_id(user_id)
                nutrition_plans.sort(key=lambda x: x.plan_date, reverse=True)
                nutrition_plans = nutrition_plans[:limit]
                
                for plan in nutrition_plans:
                    activities.append({
                        "type": "nutrition_plan",
                        "date": plan.plan_date,
                        "description": f"营养计划: {plan.nutrition.total_calories:.0f} kcal",
                        "data": plan
                    })
                
                # 按日期排序
                activities.sort(key=lambda x: x["date"], reverse=True)
                
                return activities[:limit]
                
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            return []
    
    def get_all_users(self) -> List[UserProfile]:
        """获取所有用户档案。
        
        Returns:
            用户档案列表
        """
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                return uow.users.get_all()
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
                return uow.users.get_by_id(user_id)
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            return None
    
    # 私有辅助方法
    def _get_weight_stats(self, user_id: int) -> Dict[str, Any]:
        """获取体重统计信息。
        
        Args:
            user_id: 用户ID
            
        Returns:
            体重统计信息字典
        """
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                # 获取最近30天记录
                end_date = date.today()
                start_date = end_date - timedelta(days=30)
                
                records = uow.weights.find_by_date_range(
                    start_date=start_date,
                    end_date=end_date,
                    user_id=user_id
                )
                
                if not records:
                    return {
                        "has_data": False,
                        "record_count": 0,
                        "latest_weight": None,
                        "min_weight": None,
                        "max_weight": None,
                        "avg_weight": None,
                        "total_change": 0.0,
                        "avg_daily_change": 0.0
                    }
                
                # 按日期排序
                records.sort(key=lambda x: x.record_date)
                
                # 计算统计信息
                weights = [r.weight_kg for r in records]
                latest_weight = records[-1] if records else None
                first_weight = records[0] if records else None
                
                stats = {
                    "has_data": True,
                    "record_count": len(records),
                    "latest_weight": latest_weight,
                    "min_weight": min(weights),
                    "max_weight": max(weights),
                    "avg_weight": sum(weights) / len(weights),
                    "total_change": (latest_weight.weight_kg - first_weight.weight_kg) if latest_weight and first_weight else 0.0,
                }
                
                # 计算平均每日变化
                if len(records) >= 2:
                    days_diff = (records[-1].record_date - records[0].record_date).days
                    if days_diff > 0:
                        stats["avg_daily_change"] = stats["total_change"] / days_diff
                    else:
                        stats["avg_daily_change"] = 0.0
                else:
                    stats["avg_daily_change"] = 0.0
                
                return stats
                
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            return {
                "has_data": False,
                "record_count": 0,
                "latest_weight": None,
                "min_weight": None,
                "max_weight": None,
                "avg_weight": None,
                "total_change": 0.0,
                "avg_daily_change": 0.0
            }
    
    def _get_recent_nutrition_plans(self, user_id: int) -> List[Dict[str, Any]]:
        """获取最近营养计划。
        
        Args:
            user_id: 用户ID
            
        Returns:
            营养计划列表
        """
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                plans = uow.daily_nutrition.find_by_user_id(user_id)
                plans.sort(key=lambda x: x.plan_date, reverse=True)
                plans = plans[:self.RECENT_PLANS_LIMIT]
                
                formatted_plans = []
                for plan in plans:
                    formatted_plans.append({
                        "date": plan.plan_date,
                        "tdee": plan.target_tdee,
                        "protein_g": plan.nutrition.protein_g,
                        "carbs_g": plan.nutrition.carbohydrates_g,
                        "fat_g": plan.nutrition.fat_g,
                        "calories": plan.nutrition.total_calories,
                        "is_adjusted": plan.is_adjusted,
                        "adjustment_units": plan.adjustment_units
                    })
                
                return formatted_plans
                
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            return []
    
    def _get_weight_loss_progress(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取减脂进度信息。
        
        Args:
            user_id: 用户ID
            
        Returns:
            减脂进度信息字典
        """
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                user = uow.users.get_by_id(user_id)
                if not user:
                    return None
                
                latest_weight = uow.weights.find_latest_by_user_id(user_id)
                if not latest_weight:
                    return None
                
                # 使用默认目标体重（初始体重的95%）
                target_weight = user.initial_weight_kg * 0.95
                
                # 计算进度
                total_possible_loss = user.initial_weight_kg - target_weight
                actual_loss_so_far = user.initial_weight_kg - latest_weight.weight_kg
                
                if total_possible_loss > 0:
                    progress_percentage = (actual_loss_so_far / total_possible_loss) * 100
                else:
                    progress_percentage = 0.0
                
                return {
                    "current_weight": latest_weight.weight_kg,
                    "initial_weight": user.initial_weight_kg,
                    "target_weight": target_weight,
                    "progress_percentage": min(100, max(0, progress_percentage)),
                    "weight_to_lose": max(0, latest_weight.weight_kg - target_weight),
                    "weight_lost": max(0, user.initial_weight_kg - latest_weight.weight_kg)
                }
                
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            return None
    
    def _get_weight_chart_data(self, user_id: int) -> Dict[str, Any]:
        """获取体重图表数据。
        
        Args:
            user_id: 用户ID
            
        Returns:
            图表数据字典
        """
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                end_date = date.today()
                start_date = end_date - timedelta(days=self.DEFAULT_CHART_DAYS)
                
                records = uow.weights.find_by_date_range(
                    start_date=start_date,
                    end_date=end_date,
                    user_id=user_id
                )
                
                # 按日期排序
                records.sort(key=lambda x: x.record_date)
                
                # 提取数据
                dates = [r.record_date for r in records]
                weights = [r.weight_kg for r in records]
                
                # 计算趋势线（简单线性回归）
                trend_data = []
                if len(dates) >= 2:
                    # 将日期转换为数值（天数差）
                    date_nums = [(d - dates[0]).days for d in dates]
                    
                    # 计算线性回归
                    n = len(date_nums)
                    sum_x = sum(date_nums)
                    sum_y = sum(weights)
                    sum_xy = sum(x * y for x, y in zip(date_nums, weights))
                    sum_xx = sum(x * x for x in date_nums)
                    
                    if n * sum_xx - sum_x * sum_x != 0:
                        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
                        intercept = (sum_y - slope * sum_x) / n
                        
                        # 生成趋势线数据
                        if date_nums:
                            trend_data = [intercept + slope * x for x in date_nums]
                
                return {
                    "dates": dates,
                    "weights": weights,
                    "trend": trend_data,
                    "has_data": len(records) > 0,
                    "record_count": len(records),
                    "day_range": self.DEFAULT_CHART_DAYS
                }
                
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            return {
                "dates": [],
                "weights": [],
                "trend": [],
                "has_data": False,
                "record_count": 0,
                "day_range": self.DEFAULT_CHART_DAYS
            }
    
    def _calculate_dashboard_metrics(
        self,
        summary: Dict[str, Any],
        weight_stats: Dict[str, Any],
        progress_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """计算仪表盘指标。
        
        Args:
            summary: 用户摘要
            weight_stats: 体重统计
            progress_info: 进度信息
            
        Returns:
            仪表盘指标字典
        """
        metrics = {}
        
        # 用户基本信息
        if "user" in summary:
            user = summary["user"]
            metrics["user_name"] = user.name
            metrics["user_age"] = user.age
            gender = user.gender
            metrics["user_gender"] = gender.value if hasattr(gender, 'value') else gender
        
        # 体重相关指标
        if weight_stats.get("has_data", False):
            metrics["current_weight"] = weight_stats["latest_weight"].weight_kg if weight_stats["latest_weight"] else None
            metrics["weight_change_30d"] = weight_stats["total_change"]
            metrics["avg_daily_change"] = weight_stats["avg_daily_change"]
        
        # TDEE和营养指标
        if "tdee" in summary:
            metrics["tdee"] = summary["tdee"]
        
        if "nutrition" in summary and summary["nutrition"]:
            nutrition = summary["nutrition"]
            metrics["protein_g"] = nutrition.protein_g
            metrics["carbs_g"] = nutrition.carbohydrates_g
            metrics["fat_g"] = nutrition.fat_g
            metrics["calories"] = nutrition.calories_kcal
        
        # 进度指标
        if progress_info:
            metrics["progress_percentage"] = progress_info.get("progress_percentage", 0)
            metrics["weight_to_lose"] = progress_info.get("weight_to_lose", 0)
            metrics["weight_lost"] = progress_info.get("weight_lost", 0)
        
        # 记录数量指标
        if "weight_records_count" in summary:
            metrics["weight_records_count"] = summary["weight_records_count"]
        
        # 计算健康状况评分（简化版）
        health_score = 0
        
        # 基于体重变化趋势评分
        if weight_stats.get("avg_daily_change", 0) < 0:  # 体重下降
            health_score += 30
        elif abs(weight_stats.get("avg_daily_change", 0)) < 0.05:  # 体重稳定
            health_score += 20
        else:  # 体重上升
            health_score += 10
        
        # 基于记录频率评分
        if weight_stats.get("record_count", 0) >= 10:
            health_score += 30
        elif weight_stats.get("record_count", 0) >= 5:
            health_score += 20
        else:
            health_score += 10
        
        # 基于进度评分
        if progress_info and progress_info.get("progress_percentage", 0) > 50:
            health_score += 40
        elif progress_info and progress_info.get("progress_percentage", 0) > 20:
            health_score += 20
        else:
            health_score += 10
        
        metrics["health_score"] = min(100, health_score)
        
        return metrics