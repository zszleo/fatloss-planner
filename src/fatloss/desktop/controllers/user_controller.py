"""用户控制器模块。

提供用户档案的CRUD操作和业务逻辑。
"""

from typing import List, Optional
from datetime import date

from PyQt5.QtWidgets import QWidget

from fatloss.models.user_profile import UserProfile
from fatloss.models.enums import Gender, ActivityLevel
from fatloss.planner.planner_service import PlannerService
from fatloss.repository.unit_of_work import unit_of_work
from fatloss.desktop.utils.error_handler import ErrorHandler


class UserController:
    """用户控制器，处理用户档案相关的业务逻辑和UI交互。"""
    
    # 常量定义
    MIN_HEIGHT_CM = 100.0
    MAX_HEIGHT_CM = 250.0
    MIN_WEIGHT_KG = 30.0
    MAX_WEIGHT_KG = 200.0
    MAX_NAME_LENGTH = 100
    
    def __init__(self, planner_service: PlannerService):
        """初始化用户控制器。
        
        Args:
            planner_service: PlannerService业务服务实例
        """
        self.planner_service = planner_service
    
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
    
    def create_user(
        self,
        name: str,
        gender: Gender,
        birth_date: date,
        height_cm: float,
        initial_weight_kg: float,
        activity_level: ActivityLevel = ActivityLevel.MODERATE,
        parent_widget: Optional[QWidget] = None
    ) -> Optional[UserProfile]:
        """创建新用户档案。
        
        Args:
            name: 姓名
            gender: 性别
            birth_date: 出生日期
            height_cm: 身高（厘米）
            initial_weight_kg: 初始体重（千克）
            activity_level: 活动水平，默认为中度
            parent_widget: 父窗口部件，用于显示错误消息
            
        Returns:
            创建的用户档案对象，如果创建失败则返回None
        """
        try:
            # 验证输入
            self._validate_user_input(
                name=name,
                height_cm=height_cm,
                initial_weight_kg=initial_weight_kg,
                parent_widget=parent_widget
            )
            
            # 创建用户档案
            user = self.planner_service.create_user_profile(
                name=name,
                gender=gender,
                birth_date=birth_date,
                height_cm=height_cm,
                initial_weight_kg=initial_weight_kg,
                activity_level=activity_level
            )
            
            ErrorHandler.show_success(f"用户 '{name}' 创建成功", parent_widget)
            return user
            
        except Exception as e:
            ErrorHandler.handle_service_error(e, parent_widget)
            return None
    
    def update_user(
        self,
        user_id: int,
        name: str,
        gender: Gender,
        birth_date: date,
        height_cm: float,
        initial_weight_kg: float,
        activity_level: ActivityLevel,
        parent_widget: Optional[QWidget] = None
    ) -> Optional[UserProfile]:
        """更新用户档案。
        
        Args:
            user_id: 用户ID
            name: 姓名
            gender: 性别
            birth_date: 出生日期
            height_cm: 身高（厘米）
            initial_weight_kg: 初始体重（千克）
            activity_level: 活动水平
            parent_widget: 父窗口部件，用于显示错误消息
            
        Returns:
            更新后的用户档案对象，如果更新失败则返回None
        """
        try:
            # 验证输入
            self._validate_user_input(
                name=name,
                height_cm=height_cm,
                initial_weight_kg=initial_weight_kg,
                parent_widget=parent_widget
            )
            
            # 获取现有用户
            with unit_of_work(self.planner_service.database_url) as uow:
                existing_user = uow.users.get_by_id(user_id)
                if existing_user is None:
                    ErrorHandler.show_warning(f"用户ID {user_id} 不存在", parent_widget)
                    return None
                
                # 更新用户信息
                user_data = {
                    "id": user_id,
                    "name": name,
                    "gender": gender,
                    "birth_date": birth_date,
                    "height_cm": height_cm,
                    "initial_weight_kg": initial_weight_kg,
                    "activity_level": activity_level,
                    "created_at": existing_user.created_at,
                    "updated_at": date.today(),
                }
                
                updated_user = UserProfile(**user_data)
                uow.users.update(updated_user)
                uow.commit()
                
                ErrorHandler.show_success(f"用户 '{name}' 更新成功", parent_widget)
                return updated_user
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, parent_widget)
            return None
    
    def delete_user(
        self,
        user_id: int,
        parent_widget: Optional[QWidget] = None
    ) -> bool:
        """删除用户档案。
        
        Args:
            user_id: 用户ID
            parent_widget: 父窗口部件，用于显示错误消息
            
        Returns:
            是否成功删除
        """
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                # 检查用户是否存在
                user = uow.users.get_by_id(user_id)
                if user is None:
                    ErrorHandler.show_warning(f"用户ID {user_id} 不存在", parent_widget)
                    return False
                
                # 删除用户（这将级联删除相关记录）
                uow.users.delete(user_id)
                uow.commit()
                
                ErrorHandler.show_success(f"用户 '{user.name}' 删除成功", parent_widget)
                return True
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, parent_widget)
            return False
    
    def search_users(
        self,
        name_query: Optional[str] = None,
        gender: Optional[Gender] = None,
        min_age: Optional[int] = None,
        max_age: Optional[int] = None
    ) -> List[UserProfile]:
        """搜索用户档案。
        
        Args:
            name_query: 姓名查询（模糊匹配）
            gender: 性别筛选
            min_age: 最小年龄
            max_age: 最大年龄
            
        Returns:
            匹配的用户档案列表
        """
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                # 获取基础用户列表
                users = uow.users.get_all()
                
                # 应用过滤器
                filtered_users = []
                
                for user in users:
                    # 姓名过滤
                    if name_query and name_query.strip():
                        query_lower = name_query.strip().lower()
                        name_lower = user.name.lower()
                        if query_lower not in name_lower:
                            continue
                    
                    # 性别过滤
                    if gender is not None and user.gender != gender:
                        continue
                    
                    # 年龄过滤
                    if min_age is not None and user.age < min_age:
                        continue
                    if max_age is not None and user.age > max_age:
                        continue
                    
                    filtered_users.append(user)
                
                return filtered_users
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            return []
    
    def get_user_count(self) -> int:
        """获取用户总数。
        
        Returns:
            用户总数
        """
        try:
            with unit_of_work(self.planner_service.database_url) as uow:
                return uow.users.count()
        except Exception as e:
            ErrorHandler.handle_service_error(e)
            return 0
    
    def _validate_user_input(
        self,
        name: str,
        height_cm: float,
        initial_weight_kg: float,
        parent_widget: Optional[QWidget] = None
    ) -> None:
        """验证用户输入数据。
        
        Args:
            name: 姓名
            height_cm: 身高（厘米）
            initial_weight_kg: 初始体重（千克）
            parent_widget: 父窗口部件，用于显示错误消息
            
        Raises:
            ValueError: 如果验证失败
        """
        # 验证姓名
        name = name.strip()
        if not name:
            raise ValueError("姓名不能为空")
        
        if len(name) > self.MAX_NAME_LENGTH:
            raise ValueError(f"姓名长度不能超过{self.MAX_NAME_LENGTH}个字符")
        
        # 验证身高
        if not (self.MIN_HEIGHT_CM <= height_cm <= self.MAX_HEIGHT_CM):
            raise ValueError(f"身高必须在{self.MIN_HEIGHT_CM}到{self.MAX_HEIGHT_CM}厘米之间")
        
        # 验证体重
        if not (self.MIN_WEIGHT_KG <= initial_weight_kg <= self.MAX_WEIGHT_KG):
            raise ValueError(f"体重必须在{self.MIN_WEIGHT_KG}到{self.MAX_WEIGHT_KG}千克之间")