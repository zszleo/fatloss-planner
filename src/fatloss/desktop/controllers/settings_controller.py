"""配置设置控制器模块。

提供应用程序配置管理相关的业务逻辑和UI交互。
"""

from typing import Optional, Dict, Any

from PyQt5.QtWidgets import QWidget

from fatloss.models.app_config import AppConfig
from fatloss.models.enums import UnitSystem, Theme
from fatloss.planner.planner_service import PlannerService
from fatloss.repository.unit_of_work import unit_of_work
from fatloss.desktop.utils.error_handler import ErrorHandler


class SettingsController:
    """配置设置控制器，处理应用程序配置管理相关的业务逻辑。"""
    
    # 常量定义
    MIN_CARB_ADJUSTMENT_UNIT_G = 10
    MAX_CARB_ADJUSTMENT_UNIT_G = 100
    
    MIN_MONTHLY_LOSS_PERCENTAGE = 0.01  # 1%
    MAX_MONTHLY_LOSS_PERCENTAGE = 0.10  # 10%
    
    MIN_EXERCISE_CALORIES_PER_MINUTE = 5
    MAX_EXERCISE_CALORIES_PER_MINUTE = 20
    
    MIN_DATA_RETENTION_DAYS = 30
    MAX_DATA_RETENTION_DAYS = 3650  # 10年
    
    def __init__(self, planner_service: PlannerService):
        """初始化配置设置控制器。
        
        Args:
            planner_service: PlannerService业务服务实例
        """
        self.planner_service = planner_service
    
    def get_config(self, user_id: int) -> Optional[AppConfig]:
        """获取用户配置。
        
        Args:
            user_id: 用户ID
            
        Returns:
            应用配置对象，如果不存在则返回None
        """
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                config = uow.app_configs.get_by_user_id(user_id)
                
                if config is None:
                    # 如果配置不存在，创建默认配置
                    config = AppConfig(user_id=user_id)
                    created_config = uow.app_configs.create(config)
                    uow.commit()
                    return created_config
                
                return config
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            return None
    
    def save_config(
        self,
        user_id: int,
        unit_system: UnitSystem,
        theme: Theme,
        language: str,
        weekly_check_day: int,
        carb_adjustment_unit_g: int,
        monthly_loss_percentage: float,
        exercise_calories_per_minute: float,
        enable_notifications: bool,
        data_retention_days: int,
        parent_widget: Optional[QWidget] = None
    ) -> Optional[AppConfig]:
        """保存用户配置。
        
        Args:
            user_id: 用户ID
            unit_system: 单位制
            theme: 主题
            language: 语言
            weekly_check_day: 周检查日（0=周日，1=周一，...）
            carb_adjustment_unit_g: 碳水化合物调整单位（克）
            monthly_loss_percentage: 每月减脂百分比
            exercise_calories_per_minute: 每分钟训练消耗热量
            enable_notifications: 启用通知
            data_retention_days: 数据保留天数
            parent_widget: 父窗口部件，用于显示错误消息
            
        Returns:
            保存的应用配置对象，如果保存失败则返回None
        """
        try:
            # 验证输入
            self._validate_config_input(
                weekly_check_day=weekly_check_day,
                carb_adjustment_unit_g=carb_adjustment_unit_g,
                monthly_loss_percentage=monthly_loss_percentage,
                exercise_calories_per_minute=exercise_calories_per_minute,
                data_retention_days=data_retention_days,
                parent_widget=parent_widget
            )
            
            with unit_of_work(self.planner_service.database_url) as uow:
                # 检查是否已有配置
                existing_config = uow.app_configs.get_by_user_id(user_id)
                
                if existing_config:
                    # 更新现有配置
                    updated_config = AppConfig(
                        id=existing_config.id,
                        user_id=user_id,
                        unit_system=unit_system,
                        theme=theme,
                        language=language,
                        weekly_check_day=weekly_check_day,
                        carb_adjustment_unit_g=carb_adjustment_unit_g,
                        monthly_loss_percentage=monthly_loss_percentage,
                        exercise_calories_per_minute=exercise_calories_per_minute,
                        enable_notifications=enable_notifications,
                        data_retention_days=data_retention_days,
                        created_at=existing_config.created_at,
                    )
                    
                    uow.app_configs.update(existing_config.id, updated_config)
                    uow.commit()
                    
                    ErrorHandler.show_success("配置保存成功", parent_widget)
                    return updated_config
                else:
                    # 创建新配置
                    new_config = AppConfig(
                        user_id=user_id,
                        unit_system=unit_system,
                        theme=theme,
                        language=language,
                        weekly_check_day=weekly_check_day,
                        carb_adjustment_unit_g=carb_adjustment_unit_g,
                        monthly_loss_percentage=monthly_loss_percentage,
                        exercise_calories_per_minute=exercise_calories_per_minute,
                        enable_notifications=enable_notifications,
                        data_retention_days=data_retention_days,
                    )
                    
                    created_config = uow.app_configs.create(new_config)
                    uow.commit()
                    
                    ErrorHandler.show_success("配置创建成功", parent_widget)
                    return created_config
                    
        except Exception as e:
            ErrorHandler.handle_service_error(e, parent_widget)
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取用户信息。
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户信息字典，如果不存在则返回None
        """
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                user = uow.users.get_by_id(user_id)
                if user:
                    return {
                        "id": user.id,
                        "name": user.name,
                        "gender": user.gender.value if hasattr(user.gender, 'value') else user.gender,
                        "age": user.age,
                        "height_cm": user.height_cm,
                    }
                return None
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            return None
    
    def get_all_users(self) -> list[Dict[str, Any]]:
        """获取所有用户信息。
        
        Returns:
            用户信息字典列表
        """
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                users = uow.users.get_all()
                result = []
                
                for user in users:
                    result.append({
                        "id": user.id,
                        "name": user.name,
                        "gender": user.gender.value if hasattr(user.gender, 'value') else user.gender,
                        "age": user.age,
                        "height_cm": user.height_cm,
                    })
                
                return result
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            return []
    
    def backup_database(self, backup_path: str, parent_widget: Optional[QWidget] = None) -> bool:
        """备份数据库。
        
        Args:
            backup_path: 备份文件路径
            parent_widget: 父窗口部件，用于显示错误消息
            
        Returns:
            是否成功备份
        """
        try:
            import shutil
            import os
            from pathlib import Path
            
            # 获取数据库文件路径
            if self.planner_service.database_url:
                # 从数据库URL中提取文件路径
                # SQLite URL格式: sqlite:///path/to/database.db
                db_url = self.planner_service.database_url
                if db_url.startswith("sqlite:///"):
                    db_path = db_url.replace("sqlite:///", "")
                else:
                    db_path = db_url
            else:
                # 默认数据库路径
                db_path = str(Path.home() / ".fatloss-planner" / "fatloss.db")
            
            # 检查数据库文件是否存在
            if not os.path.exists(db_path):
                ErrorHandler.show_warning(f"数据库文件不存在: {db_path}", parent_widget)
                return False
            
            # 创建备份目录（如果不存在）
            backup_dir = os.path.dirname(backup_path)
            if backup_dir and not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # 复制数据库文件
            shutil.copy2(db_path, backup_path)
            
            # 计算备份文件大小
            backup_size = os.path.getsize(backup_path)
            size_mb = backup_size / (1024 * 1024)
            
            ErrorHandler.show_success(
                f"数据库备份成功\n路径: {backup_path}\n大小: {size_mb:.2f} MB",
                parent_widget
            )
            return True
            
        except Exception as e:
            ErrorHandler.handle_service_error(e, parent_widget)
            return False
    
    def restore_database(self, backup_path: str, parent_widget: Optional[QWidget] = None) -> bool:
        """恢复数据库。
        
        Args:
            backup_path: 备份文件路径
            parent_widget: 父窗口部件，用于显示错误消息
            
        Returns:
            是否成功恢复
        """
        try:
            import shutil
            import os
            from pathlib import Path
            
            # 检查备份文件是否存在
            if not os.path.exists(backup_path):
                ErrorHandler.show_warning(f"备份文件不存在: {backup_path}", parent_widget)
                return False
            
            # 获取数据库文件路径
            if self.planner_service.database_url:
                db_url = self.planner_service.database_url
                if db_url.startswith("sqlite:///"):
                    db_path = db_url.replace("sqlite:///", "")
                else:
                    db_path = db_url
            else:
                db_path = str(Path.home() / ".fatloss-planner" / "fatloss.db")
            
            # 检查备份文件是否是有效的SQLite数据库
            try:
                import sqlite3
                conn = sqlite3.connect(backup_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                conn.close()
                
                if not tables:
                    ErrorHandler.show_warning("备份文件不是有效的SQLite数据库", parent_widget)
                    return False
            except:
                ErrorHandler.show_warning("备份文件不是有效的SQLite数据库", parent_widget)
                return False
            
            # 备份当前数据库（以防万一）
            backup_dir = os.path.dirname(db_path)
            if backup_dir:
                timestamp = os.path.splitext(os.path.basename(db_path))[0]
                current_backup = os.path.join(
                    backup_dir,
                    f"{timestamp}_restore_backup_{int(os.path.getmtime(backup_path))}.db"
                )
                if os.path.exists(db_path):
                    shutil.copy2(db_path, current_backup)
            
            # 恢复数据库
            shutil.copy2(backup_path, db_path)
            
            ErrorHandler.show_success(
                f"数据库恢复成功\n从: {backup_path}\n到: {db_path}",
                parent_widget
            )
            return True
            
        except Exception as e:
            ErrorHandler.handle_service_error(e, parent_widget)
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """获取数据库信息。
        
        Returns:
            数据库信息字典
        """
        try:
            import os
            import sqlite3
            from pathlib import Path
            
            # 获取数据库文件路径
            if self.planner_service.database_url:
                db_url = self.planner_service.database_url
                if db_url.startswith("sqlite:///"):
                    db_path = db_url.replace("sqlite:///", "")
                else:
                    db_path = db_url
            else:
                db_path = str(Path.home() / ".fatloss-planner" / "fatloss.db")
            
            info = {
                "path": db_path,
                "exists": False,
                "size_mb": 0.0,
                "last_modified": None,
                "table_count": 0,
                "total_records": 0,
            }
            
            if os.path.exists(db_path):
                info["exists"] = True
                info["size_mb"] = os.path.getsize(db_path) / (1024 * 1024)
                info["last_modified"] = os.path.getmtime(db_path)
                
                # 获取数据库统计信息
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # 获取表数量
                    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                    info["table_count"] = cursor.fetchone()[0]
                    
                    # 获取总记录数（主要表）
                    total_records = 0
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    
                    for (table_name,) in tables:
                        if not table_name.startswith("sqlite_"):
                            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                            count = cursor.fetchone()[0]
                            total_records += count
                    
                    info["total_records"] = total_records
                    
                    conn.close()
                except:
                    pass
            
            return info
            
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            return {
                "path": "未知",
                "exists": False,
                "size_mb": 0.0,
                "last_modified": None,
                "table_count": 0,
                "total_records": 0,
            }
    
    def _validate_config_input(
        self,
        weekly_check_day: int,
        carb_adjustment_unit_g: int,
        monthly_loss_percentage: float,
        exercise_calories_per_minute: float,
        data_retention_days: int,
        parent_widget: Optional[QWidget] = None
    ) -> None:
        """验证配置输入数据。
        
        Args:
            weekly_check_day: 周检查日
            carb_adjustment_unit_g: 碳水化合物调整单位（克）
            monthly_loss_percentage: 每月减脂百分比
            exercise_calories_per_minute: 每分钟训练消耗热量
            data_retention_days: 数据保留天数
            parent_widget: 父窗口部件，用于显示错误消息
            
        Raises:
            ValueError: 如果验证失败
        """
        # 验证周检查日
        if not (0 <= weekly_check_day <= 6):
            raise ValueError("周检查日必须在0（周日）到6（周六）之间")
        
        # 验证碳水化合物调整单位
        if not (self.MIN_CARB_ADJUSTMENT_UNIT_G <= carb_adjustment_unit_g <= self.MAX_CARB_ADJUSTMENT_UNIT_G):
            raise ValueError(f"碳水化合物调整单位必须在{self.MIN_CARB_ADJUSTMENT_UNIT_G}到{self.MAX_CARB_ADJUSTMENT_UNIT_G}克之间")
        
        # 验证每月减脂百分比
        if not (self.MIN_MONTHLY_LOSS_PERCENTAGE <= monthly_loss_percentage <= self.MAX_MONTHLY_LOSS_PERCENTAGE):
            raise ValueError(f"每月减脂百分比必须在{self.MIN_MONTHLY_LOSS_PERCENTAGE*100}%到{self.MAX_MONTHLY_LOSS_PERCENTAGE*100}%之间")
        
        # 验证每分钟训练消耗热量
        if not (self.MIN_EXERCISE_CALORIES_PER_MINUTE <= exercise_calories_per_minute <= self.MAX_EXERCISE_CALORIES_PER_MINUTE):
            raise ValueError(f"每分钟训练消耗热量必须在{self.MIN_EXERCISE_CALORIES_PER_MINUTE}到{self.MAX_EXERCISE_CALORIES_PER_MINUTE}大卡之间")
        
        # 验证数据保留天数
        if not (self.MIN_DATA_RETENTION_DAYS <= data_retention_days <= self.MAX_DATA_RETENTION_DAYS):
            raise ValueError(f"数据保留天数必须在{self.MIN_DATA_RETENTION_DAYS}到{self.MAX_DATA_RETENTION_DAYS}天之间")
    
    def export_user_data(
        self,
        user_id: int,
        export_format: str,
        output_path: str,
        include_weight_records: bool = True,
        include_nutrition_plans: bool = True,
        parent_widget: Optional[QWidget] = None
    ) -> Dict[str, Any]:
        """导出用户数据为JSON或CSV格式。
        
        Args:
            user_id: 用户ID
            export_format: 导出格式，支持"json"或"csv"
            output_path: 输出文件路径
            include_weight_records: 是否包含体重记录
            include_nutrition_plans: 是否包含营养计划
            parent_widget: 父窗口部件，用于显示错误消息
            
        Returns:
            导出统计信息字典，包含导出内容和数量
            
        Raises:
            ValueError: 如果参数无效
            Exception: 如果导出过程中出现错误
        """
        import json
        import csv
        from datetime import date
        from pathlib import Path
        
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                # 获取用户信息
                user = uow.users.get_by_id(user_id)
                if user is None:
                    raise ValueError(f"用户不存在：{user_id}")
                
                # 获取用户配置
                config = uow.app_configs.get_by_user_id(user_id)
                if config is None:
                    config_data = {}
                else:
                    config_data = config.model_dump()
                
                # 构建导出数据结构
                export_data = {
                    "user": user.model_dump(),
                    "config": config_data,
                    "export_date": date.today().isoformat(),
                    "export_format": export_format,
                }
                
                # 包含体重记录
                if include_weight_records:
                    weight_records = uow.weights.find_by_user_id(user_id)
                    export_data["weight_records"] = [
                        record.model_dump() for record in weight_records
                    ]
                
                # 包含营养计划
                if include_nutrition_plans:
                    daily_plans = uow.daily_nutrition.find_by_user_id(user_id)
                    weekly_plans = uow.weekly_nutrition.find_by_user_id(user_id)
                    
                    export_data["daily_nutrition_plans"] = [
                        plan.model_dump() for plan in daily_plans
                    ]
                    export_data["weekly_nutrition_plans"] = [
                        plan.model_dump() for plan in weekly_plans
                    ]
                
                # 导出到文件
                output_path_obj = Path(output_path)
                output_path_obj.parent.mkdir(parents=True, exist_ok=True)
                
                if export_format.lower() == "json":
                    with open(output_path_obj, "w", encoding="utf-8") as f:
                        json.dump(
                            export_data,
                            f,
                            ensure_ascii=False,
                            indent=2,
                            default=str,
                        )
                elif export_format.lower() == "csv":
                    # CSV导出简化：只导出体重记录（如果包含）
                    if include_weight_records and "weight_records" in export_data:
                        weight_records = export_data["weight_records"]
                        if weight_records:
                            with open(output_path_obj, "w", newline="", encoding="utf-8") as f:
                                writer = csv.DictWriter(f, fieldnames=weight_records[0].keys())
                                writer.writeheader()
                                writer.writerows(weight_records)
                        else:
                            # 如果没有体重记录，创建空文件
                            with open(output_path_obj, "w", encoding="utf-8") as f:
                                f.write("No weight records to export\n")
                    else:
                        # 如果没有选择体重记录，导出基本用户信息
                        with open(output_path_obj, "w", newline="", encoding="utf-8") as f:
                            writer = csv.writer(f)
                            writer.writerow(["Field", "Value"])
                            writer.writerow(["User ID", user.id])
                            writer.writerow(["User Name", user.name])
                            writer.writerow(["Gender", user.gender])
                            writer.writerow(["Birth Date", user.birth_date])
                            writer.writerow(["Height (cm)", user.height_cm])
                            writer.writerow(["Initial Weight (kg)", user.initial_weight_kg])
                            writer.writerow(["Activity Level", user.activity_level])
                else:
                    raise ValueError(f"不支持的导出格式: {export_format}，支持 'json' 或 'csv'")
                
                # 构建统计信息
                stats = {
                    "output_path": str(output_path_obj),
                    "export_format": export_format,
                    "user_info": True,
                    "config_info": True,
                    "weight_records_count": len(export_data.get("weight_records", [])),
                    "daily_nutrition_plans_count": len(export_data.get("daily_nutrition_plans", [])),
                    "weekly_nutrition_plans_count": len(export_data.get("weekly_nutrition_plans", [])),
                }
                
                return stats
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, parent_widget)
            raise