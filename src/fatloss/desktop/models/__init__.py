"""桌面应用数据模型模块。

包含Qt数据模型类，用于在表格和列表视图中显示数据。
"""

from fatloss.desktop.models.user_table_model import UserTableModel
from fatloss.desktop.models.nutrition_table_model import NutritionTableModel

__all__ = ["UserTableModel", "NutritionTableModel"]