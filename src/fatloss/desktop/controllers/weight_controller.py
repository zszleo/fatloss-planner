"""体重控制器模块。

提供体重记录的CRUD操作和业务逻辑。
"""

from typing import List, Optional, Dict, Any
from datetime import date, timedelta

from PyQt5.QtWidgets import QWidget

from fatloss.models.weight_record import WeightRecord
from fatloss.planner.planner_service import PlannerService
from fatloss.repository.unit_of_work import unit_of_work
from fatloss.desktop.utils.error_handler import ErrorHandler


class WeightController:
    """体重控制器，处理体重记录相关的业务逻辑和UI交互。"""
    
    # 常量定义
    MIN_WEIGHT_KG = 30.0
    MAX_WEIGHT_KG = 200.0
    MAX_NOTES_LENGTH = 500
    
    # 图表相关常量
    DEFAULT_CHART_DAYS = 30
    MAX_CHART_DAYS = 365
    
    def __init__(self, planner_service: PlannerService):
        """初始化体重控制器。
        
        Args:
            planner_service: PlannerService业务服务实例
        """
        self.planner_service = planner_service
    
    def record_weight(
        self,
        user_id: int,
        weight_kg: float,
        record_date: Optional[date] = None,
        notes: str = "",
        parent_widget: Optional[QWidget] = None
    ) -> Optional[WeightRecord]:
        """记录体重。
        
        Args:
            user_id: 用户ID
            weight_kg: 体重（千克）
            record_date: 记录日期，如果为None则使用今天
            notes: 备注
            parent_widget: 父窗口部件，用于显示错误消息
            
        Returns:
            创建的体重记录对象，如果创建失败则返回None
        """
        try:
            # 验证输入
            self._validate_weight_input(
                weight_kg=weight_kg,
                notes=notes,
                parent_widget=parent_widget
            )
            
            # 记录体重
            weight_record = self.planner_service.record_weight(
                user_id=user_id,
                weight_kg=weight_kg,
                record_date=record_date,
                notes=notes
            )
            
            ErrorHandler.show_success(f"体重记录成功: {weight_kg} kg", parent_widget)
            return weight_record
            
        except Exception as e:
            ErrorHandler.handle_service_error(e, parent_widget)
            return None
    
    def get_weight_history(
        self,
        user_id: int,
        limit: int = 50,
        descending: bool = True
    ) -> List[WeightRecord]:
        """获取用户体重历史记录。
        
        Args:
            user_id: 用户ID
            limit: 返回记录数量限制
            descending: 是否按日期降序排列
            
        Returns:
            体重记录列表
        """
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                # 获取所有记录
                records = uow.weights.find_by_user_id(user_id)
                
                # 排序
                records.sort(key=lambda x: x.record_date, reverse=descending)
                
                # 限制数量
                if limit > 0:
                    records = records[:limit]
                
                return records
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            return []
    
    def get_weight_by_id(
        self,
        weight_id: int
    ) -> Optional[WeightRecord]:
        """根据ID获取体重记录。
        
        Args:
            weight_id: 体重记录ID
            
        Returns:
            体重记录对象，如果不存在则返回None
        """
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                # 注意：WeightRepository可能没有get_by_id方法，但基类可能有
                # 这里使用通用方法
                all_records = uow.weights.find_all()
                for record in all_records:
                    if record.id == weight_id:
                        return record
                return None
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            return None
    
    def update_weight(
        self,
        weight_id: int,
        weight_kg: float,
        record_date: date,
        notes: str = "",
        parent_widget: Optional[QWidget] = None
    ) -> Optional[WeightRecord]:
        """更新体重记录。
        
        Args:
            weight_id: 体重记录ID
            weight_kg: 体重（千克）
            record_date: 记录日期
            notes: 备注
            parent_widget: 父窗口部件，用于显示错误消息
            
        Returns:
            更新后的体重记录对象，如果更新失败则返回None
        """
        try:
            # 验证输入
            self._validate_weight_input(
                weight_kg=weight_kg,
                notes=notes,
                parent_widget=parent_widget
            )
            
            # 获取现有记录
            with unit_of_work(self.planner_service.database_url) as uow:
                # 查找记录
                existing_record = None
                all_records = uow.weights.find_all()
                for record in all_records:
                    if record.id == weight_id:
                        existing_record = record
                        break
                
                if existing_record is None:
                    ErrorHandler.show_warning(f"体重记录ID {weight_id} 不存在", parent_widget)
                    return None
                
                # 更新记录
                updated_record = WeightRecord(
                    id=weight_id,
                    user_id=existing_record.user_id,
                    weight_kg=weight_kg,
                    record_date=record_date,
                    notes=notes,
                    created_at=existing_record.created_at
                )
                
                # 保存更新
                uow.weights.update(updated_record)
                uow.commit()
                
                ErrorHandler.show_success(f"体重记录更新成功: {weight_kg} kg", parent_widget)
                return updated_record
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, parent_widget)
            return None
    
    def delete_weight(
        self,
        weight_id: int,
        parent_widget: Optional[QWidget] = None
    ) -> bool:
        """删除体重记录。
        
        Args:
            weight_id: 体重记录ID
            parent_widget: 父窗口部件，用于显示错误消息
            
        Returns:
            是否成功删除
        """
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                # 查找记录
                existing_record = None
                all_records = uow.weights.find_all()
                for record in all_records:
                    if record.id == weight_id:
                        existing_record = record
                        break
                
                if existing_record is None:
                    ErrorHandler.show_warning(f"体重记录ID {weight_id} 不存在", parent_widget)
                    return False
                
                # 删除记录
                uow.weights.delete(weight_id)
                uow.commit()
                
                ErrorHandler.show_success(f"体重记录删除成功", parent_widget)
                return True
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, parent_widget)
            return False
    
    def get_weight_stats(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取体重统计信息。
        
        Args:
            user_id: 用户ID
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                # 获取最近记录
                end_date = date.today()
                start_date = end_date - timedelta(days=days)
            
                records = uow.weights.find_by_date_range(
                    start_date=start_date,
                    end_date=end_date,
                    user_id=user_id
                )
                
                if not records:
                    return {
                        "count": 0,
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
                    "count": len(records),
                    "latest_weight": latest_weight,
                    "min_weight": min(weights) if weights else None,
                    "max_weight": max(weights) if weights else None,
                    "avg_weight": sum(weights) / len(weights) if weights else None,
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
                "count": 0,
                "latest_weight": None,
                "min_weight": None,
                "max_weight": None,
                "avg_weight": None,
                "total_change": 0.0,
                "avg_daily_change": 0.0
            }
    
    def get_latest_weight(self, user_id: int) -> Optional[WeightRecord]:
        """获取用户最新体重记录。
        
        Args:
            user_id: 用户ID
            
        Returns:
            最新体重记录，如果不存在则返回None
        """
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                return uow.weights.find_latest_by_user_id(user_id)
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            return None
    
    def get_chart_data(
        self,
        user_id: int,
        days: int = DEFAULT_CHART_DAYS
    ) -> Dict[str, Any]:
        """获取图表数据。
        
        Args:
            user_id: 用户ID
            days: 图表天数
            
        Returns:
            图表数据字典
        """
        # 限制天数范围
        days = max(7, min(days, self.MAX_CHART_DAYS))
        
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                end_date = date.today()
                start_date = end_date - timedelta(days=days)
            
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
                
                return {
                    "dates": dates,
                    "weights": weights,
                    "records": records,
                    "day_count": days
                }
                
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            return {
                "dates": [],
                "weights": [],
                "records": [],
                "day_count": days
            }
    
    def calculate_weight_loss_progress(
        self,
        user_id: int,
        target_weight_kg: float,
        parent_widget: Optional[QWidget] = None
    ) -> Optional[Any]:
        """计算减脂进度。
        
        Args:
            user_id: 用户ID
            target_weight_kg: 目标体重
            parent_widget: 父窗口部件，用于显示错误消息
            
        Returns:
            减脂进度信息，如果计算失败则返回None
        """
        try:
            progress = self.planner_service.calculate_weight_loss_progress(
                user_id=user_id,
                target_weight_kg=target_weight_kg
            )
            return progress
        except Exception as e:
            ErrorHandler.handle_service_error(e, parent_widget)
            return None
    
    def _validate_weight_input(
        self,
        weight_kg: float,
        notes: str,
        parent_widget: Optional[QWidget] = None
    ) -> None:
        """验证体重输入数据。
        
        Args:
            weight_kg: 体重（千克）
            notes: 备注
            parent_widget: 父窗口部件，用于显示错误消息
            
        Raises:
            ValueError: 如果验证失败
        """
        # 验证体重
        if not (self.MIN_WEIGHT_KG <= weight_kg <= self.MAX_WEIGHT_KG):
            raise ValueError(f"体重必须在{self.MIN_WEIGHT_KG}到{self.MAX_WEIGHT_KG}千克之间")
        
        # 验证备注长度
        if len(notes) > self.MAX_NOTES_LENGTH:
            raise ValueError(f"备注长度不能超过{self.MAX_NOTES_LENGTH}个字符")
    
    def get_user_by_id(self, user_id: int) -> Optional[Any]:
        """根据ID获取用户档案（用于界面显示）。
        
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
    
    def get_all_users(self) -> List[Any]:
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