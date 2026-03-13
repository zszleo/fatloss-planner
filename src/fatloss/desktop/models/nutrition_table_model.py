"""营养表格数据模型。

提供Qt表格模型，用于在QTableView中显示营养计划历史记录。
"""

from typing import List, Optional, Any
from datetime import date

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
from PyQt5.QtGui import QBrush, QColor

from fatloss.models.nutrition_plan import DailyNutritionPlan


class NutritionTableModel(QAbstractTableModel):
    """营养表格数据模型，用于在QTableView中显示营养计划历史记录。"""

    # 列定义
    COLUMN_NAMES = [
        "日期",
        "TDEE (kcal)",
        "蛋白质 (g)",
        "碳水 (g)",
        "脂肪 (g)",
        "总热量 (kcal)",
        "调整",
        "调整量"
    ]
    
    COLUMN_ATTRIBUTES = [
        "date",
        "tdee",
        "protein",
        "carbs",
        "fat",
        "calories",
        "adjusted",
        "adjustment"
    ]
    
    def __init__(self, plans: List[DailyNutritionPlan] = None):
        """初始化营养表格模型。
        
        Args:
            plans: 营养计划列表
        """
        super().__init__()
        self.plans = plans or []
    
    def set_plans(self, plans: List[DailyNutritionPlan]) -> None:
        """设置营养计划列表。
        
        Args:
            plans: 营养计划列表
        """
        self.beginResetModel()
        self.plans = plans
        self.endResetModel()
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """返回行数。"""
        return len(self.plans)
    
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """返回列数。"""
        return len(self.COLUMN_NAMES)
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """返回指定索引的数据。
        
        Args:
            index: 表格索引
            role: 数据角色
            
        Returns:
            对应角色的数据
        """
        if not index.isValid() or index.row() >= len(self.plans):
            return QVariant()
        
        plan = self.plans[index.row()]
        col = index.column()
        
        if role == Qt.DisplayRole:
            # 获取对应的属性值
            attr_name = self.COLUMN_ATTRIBUTES[col]
            
            if attr_name == "date":
                return plan.plan_date.strftime("%Y-%m-%d")
            elif attr_name == "tdee":
                return f"{plan.target_tdee:.0f}"
            elif attr_name == "protein":
                return f"{plan.nutrition.protein_g:.1f}"
            elif attr_name == "carbs":
                return f"{plan.nutrition.carbohydrates_g:.1f}"
            elif attr_name == "fat":
                return f"{plan.nutrition.fat_g:.1f}"
            elif attr_name == "calories":
                return f"{plan.nutrition.total_calories:.0f}"
            elif attr_name == "adjusted":
                return "是" if plan.is_adjusted else "否"
            elif attr_name == "adjustment":
                if plan.is_adjusted:
                    return f"{plan.adjustment_units * 30:+d}g"
                else:
                    return "无"
        
        elif role == Qt.TextAlignmentRole:
            # 设置文本对齐方式
            if col in [1, 2, 3, 4, 5]:  # 数值列右对齐
                return Qt.AlignRight | Qt.AlignVCenter
            else:  # 其他列左对齐
                return Qt.AlignLeft | Qt.AlignVCenter
        
        elif role == Qt.BackgroundRole:
            # 设置背景色（对调整过的行使用不同背景）
            if plan.is_adjusted:
                if plan.adjustment_units > 0:
                    # 增加碳水，浅绿色背景
                    return QBrush(QColor(200, 255, 200))
                else:
                    # 减少碳水，浅红色背景
                    return QBrush(QColor(255, 200, 200))
        
        elif role == Qt.ToolTipRole:
            # 工具提示
            attr_name = self.COLUMN_ATTRIBUTES[col]
            if attr_name == "adjusted" and plan.is_adjusted:
                direction = "增加" if plan.adjustment_units > 0 else "减少"
                return f"已调整: {direction} {abs(plan.adjustment_units) * 30}g 碳水化合物"
        
        return QVariant()
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        """返回表头数据。
        
        Args:
            section: 表头部分（列索引或行索引）
            orientation: 方向（水平或垂直）
            role: 数据角色
            
        Returns:
            表头数据
        """
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section < len(self.COLUMN_NAMES):
                    return self.COLUMN_NAMES[section]
            elif orientation == Qt.Vertical:
                return str(section + 1)
        
        return QVariant()
    
    def get_plan_at(self, row: int) -> Optional[DailyNutritionPlan]:
        """获取指定行的营养计划。
        
        Args:
            row: 行索引
            
        Returns:
            营养计划对象，如果索引无效则返回None
        """
        if 0 <= row < len(self.plans):
            return self.plans[row]
        return None
    
    def get_plan_by_date(self, plan_date: date) -> Optional[DailyNutritionPlan]:
        """根据日期获取营养计划。
        
        Args:
            plan_date: 计划日期
            
        Returns:
            营养计划对象，如果不存在则返回None
        """
        for plan in self.plans:
            if plan.plan_date == plan_date:
                return plan
        return None
    
    def clear(self) -> None:
        """清空模型数据。"""
        self.beginResetModel()
        self.plans = []
        self.endResetModel()