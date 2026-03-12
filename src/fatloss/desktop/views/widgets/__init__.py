"""自定义部件模块。

包含桌面应用的自定义部件和标签页。
"""

from .user_management_tab import UserManagementTab
from .nutrition_calculator_tab import NutritionCalculatorTab
from .weight_tracking_tab import WeightTrackingTab
from .dashboard_tab import DashboardTab

__all__ = ["UserManagementTab", "NutritionCalculatorTab", "WeightTrackingTab", "DashboardTab"]