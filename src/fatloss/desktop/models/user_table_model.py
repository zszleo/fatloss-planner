"""用户表格数据模型。

提供Qt表格模型，用于在QTableView中显示用户列表。
"""

from typing import List, Optional, Any
from datetime import date

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
from PyQt5.QtGui import QBrush, QColor

from fatloss.models.user_profile import UserProfile
from fatloss.models.enums import Gender, ActivityLevel


class UserTableModel(QAbstractTableModel):
    """用户表格数据模型，用于在QTableView中显示用户列表。"""

    # 列定义
    COLUMN_NAMES = [
        "ID",
        "姓名", 
        "性别",
        "年龄",
        "身高(cm)",
        "体重(kg)",
        "活动水平",
        "创建日期"
    ]
    
    # 列对应的UserProfile属性
    COLUMN_ATTRIBUTES = [
        "id",
        "name",
        "gender",
        "age",
        "height_cm",
        "initial_weight_kg",
        "activity_level",
        "created_at"
    ]

    def __init__(self, users: Optional[List[UserProfile]] = None):
        """初始化用户表格模型。
        
        Args:
            users: 用户列表，如果为None则创建空模型
        """
        super().__init__()
        self.users = users or []
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """返回行数（用户数量）。"""
        return len(self.users)
    
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
        if not index.isValid() or index.row() >= len(self.users):
            return QVariant()
        
        user = self.users[index.row()]
        col = index.column()
        
        if role == Qt.DisplayRole or role == Qt.EditRole:
            # 获取对应的属性值
            attr_name = self.COLUMN_ATTRIBUTES[col]
            
            if attr_name == "age":
                # 计算年龄
                return user.age
            elif attr_name == "gender":
                # 性别显示
                gender = user.gender
                if hasattr(gender, 'value'):
                    return gender.value
                else:
                    return gender  # 假设是字符串
            elif attr_name == "activity_level":
                # 活动水平显示
                activity = user.activity_level
                if hasattr(activity, 'value'):
                    return activity.value
                else:
                    return activity  # 假设是字符串
            elif attr_name == "created_at":
                # 日期格式化
                if isinstance(user.created_at, date):
                    return user.created_at.strftime("%Y-%m-%d")
                return str(user.created_at)
            else:
                # 直接属性
                value = getattr(user, attr_name)
                if value is None:
                    return ""
                return str(value)
                
        elif role == Qt.TextAlignmentRole:
            # 数字列右对齐
            if col in [0, 3, 4, 5]:  # ID, 年龄, 身高, 体重
                return Qt.AlignRight | Qt.AlignVCenter
            else:
                return Qt.AlignLeft | Qt.AlignVCenter
                
        elif role == Qt.BackgroundRole:
            # 交替行颜色
            if index.row() % 2 == 0:
                return QBrush(QColor(240, 240, 240))
        
        return QVariant()
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        """返回表头数据。
        
        Args:
            section: 列/行索引
            orientation: 水平或垂直表头
            role: 数据角色
            
        Returns:
            表头数据
        """
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section < len(self.COLUMN_NAMES):
                    return self.COLUMN_NAMES[section]
            elif orientation == Qt.Vertical:
                return section + 1  # 行号从1开始
        
        return QVariant()
    
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """返回项目的标志。
        
        Args:
            index: 表格索引
            
        Returns:
            项目标志
        """
        if not index.isValid():
            return Qt.NoItemFlags
            
        # 所有单元格只读
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
    def set_users(self, users: List[UserProfile]) -> None:
        """设置用户数据并刷新视图。
        
        Args:
            users: 新的用户列表
        """
        self.beginResetModel()
        self.users = users
        self.endResetModel()
    
    def get_user_at(self, row: int) -> Optional[UserProfile]:
        """获取指定行的用户。
        
        Args:
            row: 行索引
            
        Returns:
            用户对象，如果索引无效则返回None
        """
        if 0 <= row < len(self.users):
            return self.users[row]
        return None
    
    def add_user(self, user: UserProfile) -> None:
        """添加新用户到模型。
        
        Args:
            user: 用户对象
        """
        row = len(self.users)
        self.beginInsertRows(QModelIndex(), row, row)
        self.users.append(user)
        self.endInsertRows()
    
    def update_user(self, row: int, user: UserProfile) -> None:
        """更新指定行的用户。
        
        Args:
            row: 行索引
            user: 更新后的用户对象
        """
        if 0 <= row < len(self.users):
            self.users[row] = user
            index = self.createIndex(row, 0)
            self.dataChanged.emit(index, index)
    
    def remove_user(self, row: int) -> None:
        """移除指定行的用户。
        
        Args:
            row: 行索引
        """
        if 0 <= row < len(self.users):
            self.beginRemoveRows(QModelIndex(), row, row)
            del self.users[row]
            self.endRemoveRows()