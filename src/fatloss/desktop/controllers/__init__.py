"""桌面应用控制器模块。

提供连接视图和业务逻辑的控制器类。
"""

from fatloss.desktop.controllers.main_controller import MainController
from fatloss.desktop.controllers.user_controller import UserController
from fatloss.desktop.controllers.nutrition_controller import NutritionController
from fatloss.desktop.controllers.weight_controller import WeightController
from fatloss.desktop.controllers.dashboard_controller import DashboardController

__all__ = ["MainController", "UserController", "NutritionController", "WeightController", "DashboardController"]