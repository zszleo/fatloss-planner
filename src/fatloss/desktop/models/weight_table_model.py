"""体重表格数据模型。

提供Qt表格模型，用于在QTableView中显示体重记录列表。
"""

from typing import List, Optional, Any
from datetime import date

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
from PyQt5.QtGui import QBrush, QColor

from fatloss.models.weight_record import WeightRecord


class WeightTableModel(QAbstractTableModel):
    """体重表格数据模型，用于在QTableView中显示体重记录列表。"""

    # 列定义
    COLUMN_NAMES = [
        "ID",
        "日期",
        "体重(kg)",
        "变化(kg)",
        "备注",
        "创建日期"
    ]
    
    # 列对应的WeightRecord属性
    COLUMN_ATTRIBUTES = [
        "id",
        "record_date",
        "weight_kg",
        "change",  # 计算列
        "notes",
        "created_at"
    ]
    
    # 列对齐方式
    COLUMN_ALIGNMENT = [
        Qt.AlignRight | Qt.AlignVCenter,   # ID
        Qt.AlignLeft | Qt.AlignVCenter,    # 日期
        Qt.AlignRight | Qt.AlignVCenter,   # 体重
        Qt.AlignRight | Qt.AlignVCenter,   # 变化
        Qt.AlignLeft | Qt.AlignVCenter,    # 备注
        Qt.AlignLeft | Qt.AlignVCenter     # 创建日期
    ]

    def __init__(self, weight_records: Optional[List[WeightRecord]] = None):
        """初始化体重表格模型。
        
        Args:
            weight_records: 体重记录列表，如果为None则创建空模型
        """
        super().__init__()
        self.weight_records = weight_records or []
        self._calculate_changes()
    
    def _calculate_changes(self) -> None:
        """计算体重变化（相对于前一条记录）。"""
        if not self.weight_records:
            return
        
        # 按日期排序（升序）
        sorted_records = sorted(self.weight_records, key=lambda x: x.record_date)
        
        # 计算变化
        self._changes = []
        previous_weight = None
        
        for record in sorted_records:
            if previous_weight is not None:
                change = record.weight_kg - previous_weight
                self._changes.append(change)
            else:
                self._changes.append(0.0)
            
            previous_weight = record.weight_kg
    
    def _get_change_for_record(self, record: WeightRecord, row: int) -> float:
        """获取指定记录的变化值。
        
        Args:
            record: 体重记录
            row: 行索引（在排序后的列表中）
            
        Returns:
            变化值
        """
        if row < len(self._changes):
            return self._changes[row]
        return 0.0
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """返回行数（体重记录数量）。"""
        return len(self.weight_records)
    
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
        if not index.isValid() or index.row() >= len(self.weight_records):
            return QVariant()
        
        record = self.weight_records[index.row()]
        col = index.column()
        
        if role == Qt.DisplayRole or role == Qt.EditRole:
            # 获取对应的属性值
            attr_name = self.COLUMN_ATTRIBUTES[col]
            
            if attr_name == "record_date":
                # 日期格式化
                if isinstance(record.record_date, date):
                    return record.record_date.strftime("%Y-%m-%d")
                return str(record.record_date)
            
            elif attr_name == "weight_kg":
                # 体重显示（保留2位小数）
                return f"{record.weight_kg:.2f}"
            
            elif attr_name == "change":
                # 计算变化值
                # 需要找到记录在排序列表中的位置
                sorted_records = sorted(self.weight_records, key=lambda x: x.record_date)
                for i, sorted_record in enumerate(sorted_records):
                    if sorted_record.id == record.id:
                        change = self._changes[i] if i < len(self._changes) else 0.0
                        if change > 0:
                            return f"+{change:.2f}"
                        elif change < 0:
                            return f"{change:.2f}"
                        else:
                            return "0.00"
                # This line should never be reached since record is always in sorted_records
                return "0.00"  # pragma: no cover
            
            elif attr_name == "notes":
                # 备注显示（截断过长的备注）
                if record.notes and len(record.notes) > 50:
                    return record.notes[:47] + "..."
                return record.notes or ""
            
            elif attr_name == "created_at":
                # 创建日期格式化
                if isinstance(record.created_at, date):
                    return record.created_at.strftime("%Y-%m-%d")
                return str(record.created_at)
            
            else:
                # 直接属性（ID）
                value = getattr(record, attr_name)
                if value is None:
                    return ""
                return str(value)
        
        elif role == Qt.TextAlignmentRole:
            # 返回列对齐方式
            if col < len(self.COLUMN_ALIGNMENT):
                return self.COLUMN_ALIGNMENT[col]
            # This line should never be reached since Qt returns invalid index for out-of-bounds columns
            return Qt.AlignLeft | Qt.AlignVCenter  # pragma: no cover
        
        elif role == Qt.BackgroundRole:
            # 交替行颜色
            if index.row() % 2 == 0:
                return QBrush(QColor(240, 240, 240))
            
            # 变化列的特殊背景色
            if col == 3:  # 变化列
                # 获取变化值
                sorted_records = sorted(self.weight_records, key=lambda x: x.record_date)
                for i, sorted_record in enumerate(sorted_records):
                    if sorted_record.id == record.id:
                        change = self._changes[i] if i < len(self._changes) else 0.0
                        if change > 0:
                            # 体重增加，浅红色背景
                            return QBrush(QColor(255, 200, 200))
                        elif change < 0:
                            # 体重减少，浅绿色背景
                            return QBrush(QColor(200, 255, 200))
                        break
        
        elif role == Qt.ForegroundRole:
            # 变化列的特殊前景色
            if col == 3:  # 变化列
                sorted_records = sorted(self.weight_records, key=lambda x: x.record_date)
                for i, sorted_record in enumerate(sorted_records):
                    if sorted_record.id == record.id:
                        change = self._changes[i] if i < len(self._changes) else 0.0
                        if change > 0:
                            return QBrush(QColor(255, 0, 0))  # 红色
                        elif change < 0:
                            return QBrush(QColor(0, 128, 0))  # 绿色
                        break
        
        elif role == Qt.ToolTipRole:
            # 工具提示
            if col == 3:  # 变化列
                sorted_records = sorted(self.weight_records, key=lambda x: x.record_date)
                for i, sorted_record in enumerate(sorted_records):
                    if sorted_record.id == record.id:
                        change = self._changes[i] if i < len(self._changes) else 0.0
                        if change > 0:
                            return f"体重增加 {change:.2f} kg"
                        elif change < 0:
                            return f"体重减少 {abs(change):.2f} kg"
                        else:
                            return "体重无变化"
            
            elif col == 4 and record.notes:  # 备注列
                return record.notes
        
        elif role == Qt.UserRole:
            # 返回原始记录对象
            return record
        
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
    
    def set_weight_records(self, weight_records: List[WeightRecord]) -> None:
        """设置体重记录数据并刷新视图。
        
        Args:
            weight_records: 新的体重记录列表
        """
        self.beginResetModel()
        self.weight_records = weight_records
        self._calculate_changes()
        self.endResetModel()
    
    def get_record_at(self, row: int) -> Optional[WeightRecord]:
        """获取指定行的体重记录。
        
        Args:
            row: 行索引
            
        Returns:
            体重记录对象，如果索引无效则返回None
        """
        if 0 <= row < len(self.weight_records):
            return self.weight_records[row]
        return None
    
    def add_record(self, record: WeightRecord) -> None:
        """添加新体重记录到模型。
        
        Args:
            record: 体重记录对象
        """
        row = len(self.weight_records)
        self.beginInsertRows(QModelIndex(), row, row)
        self.weight_records.append(record)
        self._calculate_changes()
        self.endInsertRows()
    
    def update_record(self, row: int, record: WeightRecord) -> None:
        """更新指定行的体重记录。
        
        Args:
            row: 行索引
            record: 更新后的体重记录对象
        """
        if 0 <= row < len(self.weight_records):
            self.weight_records[row] = record
            self._calculate_changes()
            index = self.createIndex(row, 0)
            self.dataChanged.emit(index, index)
    
    def remove_record(self, row: int) -> None:
        """移除指定行的体重记录。
        
        Args:
            row: 行索引
        """
        if 0 <= row < len(self.weight_records):
            self.beginRemoveRows(QModelIndex(), row, row)
            del self.weight_records[row]
            self._calculate_changes()
            self.endRemoveRows()
    
    def clear(self) -> None:
        """清空模型数据。"""
        self.beginResetModel()
        self.weight_records = []
        self._changes = []
        self.endResetModel()
    
    def sort_by_date(self, ascending: bool = True) -> None:
        """按日期排序记录。
        
        Args:
            ascending: 是否升序排列
        """
        self.beginResetModel()
        self.weight_records.sort(key=lambda x: x.record_date, reverse=not ascending)
        self._calculate_changes()
        self.endResetModel()
    
    def get_records_for_chart(self) -> tuple[List[date], List[float]]:
        """获取图表数据。
        
        Returns:
            (日期列表, 体重列表) 元组
        """
        # 按日期排序
        sorted_records = sorted(self.weight_records, key=lambda x: x.record_date)
        
        dates = [r.record_date for r in sorted_records]
        weights = [r.weight_kg for r in sorted_records]
        
        return dates, weights