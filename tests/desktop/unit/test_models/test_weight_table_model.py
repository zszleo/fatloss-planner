"""体重表格数据模型测试。

测试重点:
1. 体重记录时间序列展示
2. 趋势分析和变化计算
3. 目标对比和进度显示
4. 数据排序（按日期）
5. 批量数据处理
"""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock

from PyQt5.QtCore import Qt, QModelIndex

from fatloss.desktop.models.weight_table_model import WeightTableModel
from tests.desktop.factories import TestDataFactory


class TestWeightTableModel:
    """体重表格模型测试类"""

    @pytest.fixture
    def model(self):
        """创建空的体重表格模型"""
        return WeightTableModel()

    @pytest.fixture
    def model_with_data(self):
        """创建带有测试数据的体重表格模型"""
        records = TestDataFactory.create_weight_records(user_id=1, count=5)
        return WeightTableModel(records)

    def test_initialization_empty(self, model):
        """测试初始化空模型"""
        assert model.rowCount() == 0
        assert model.columnCount() == 6  # 6列定义

    def test_initialization_with_data(self, model_with_data):
        """测试初始化带数据的模型"""
        assert model_with_data.rowCount() == 5
        assert model_with_data.columnCount() == 6

    def test_column_definitions(self, model):
        """测试列定义和名称"""
        assert len(model.COLUMN_NAMES) == 6
        assert model.COLUMN_NAMES[0] == "ID"
        assert model.COLUMN_NAMES[1] == "日期"
        assert model.COLUMN_NAMES[2] == "体重(kg)"
        assert model.COLUMN_NAMES[3] == "变化(kg)"
        assert model.COLUMN_NAMES[4] == "备注"
        assert model.COLUMN_NAMES[5] == "创建日期"

    def test_header_data_horizontal(self, model_with_data):
        """测试水平表头数据"""
        for i, expected_name in enumerate(model_with_data.COLUMN_NAMES):
            header = model_with_data.headerData(i, Qt.Horizontal, Qt.DisplayRole)
            assert header == expected_name

    def test_header_data_vertical(self, model_with_data):
        """测试垂直表头数据（行号）"""
        header = model_with_data.headerData(0, Qt.Vertical, Qt.DisplayRole)
        assert header == 1
        header = model_with_data.headerData(1, Qt.Vertical, Qt.DisplayRole)
        assert header == 2

    def test_data_date_display(self, model_with_data):
        """测试日期显示"""
        index = model_with_data.index(0, 1)  # 第1行，日期列
        data = model_with_data.data(index, Qt.DisplayRole)
        assert isinstance(data, str)
        assert "-" in data  # 格式应为 YYYY-MM-DD

    def test_data_weight_display(self, model_with_data):
        """测试体重显示"""
        index = model_with_data.index(0, 2)  # 第1行，体重列
        data = model_with_data.data(index, Qt.DisplayRole)
        # 应该返回字符串格式，保留2位小数
        assert isinstance(data, str)
        assert "." in data  # 包含小数点

    def test_data_change_display_first_record(self, model_with_data):
        """测试变化显示（第一条记录）"""
        index = model_with_data.index(0, 3)  # 第1行，变化列
        data = model_with_data.data(index, Qt.DisplayRole)
        # 第一条记录的变化应该是0.00
        assert data == "0.00"

    def test_data_change_display_subsequent_records(self, model_with_data):
        """测试变化显示（后续记录）"""
        # 检查第二条记录的变化（相对于第一条）
        index = model_with_data.index(1, 3)  # 第2行，变化列
        data = model_with_data.data(index, Qt.DisplayRole)
        # 应该包含 +/- 符号或0.00
        assert isinstance(data, str)

    def test_data_notes_display(self, model_with_data):
        """测试备注显示"""
        index = model_with_data.index(0, 4)  # 第1行，备注列
        data = model_with_data.data(index, Qt.DisplayRole)
        # 备注可能为空或包含文本
        assert isinstance(data, str)

    def test_data_notes_truncation(self, model_with_data):
        """测试备注截断"""
        # 创建一个长备注的记录（超过50个字符）
        # 51+ characters to ensure truncation
        long_note = "这是一个非常长的备注，它超过了50个字符的限制，因此应该被截断显示，末尾加上省略号"  # 45 chars
        # Let's make it longer
        long_note = "这是一个非常长的备注，它超过了50个字符的限制，因此应该被截断显示，末尾加上省略号" + " Extra text to make it longer"
        record = TestDataFactory.create_weight_record(user_id=1, notes=long_note)
        model_with_data.add_record(record)

        index = model_with_data.index(model_with_data.rowCount() - 1, 4)
        data = model_with_data.data(index, Qt.DisplayRole)
        # 应该被截断
        assert "..." in data
        assert len(data) <= 50

    def test_data_created_at_display(self, model_with_data):
        """测试创建日期显示"""
        index = model_with_data.index(0, 5)  # 第1行，创建日期列
        data = model_with_data.data(index, Qt.DisplayRole)
        assert isinstance(data, str)
        assert "-" in data

    def test_text_alignment_role(self, model_with_data):
        """测试文本对齐角色"""
        # ID列（0列）应该右对齐
        index = model_with_data.index(0, 0)
        alignment = model_with_data.data(index, Qt.TextAlignmentRole)
        assert alignment == (Qt.AlignRight | Qt.AlignVCenter)

        # 日期列（1列）应该左对齐
        index = model_with_data.index(0, 1)
        alignment = model_with_data.data(index, Qt.TextAlignmentRole)
        assert alignment == (Qt.AlignLeft | Qt.AlignVCenter)

        # 体重列（2列）应该右对齐
        index = model_with_data.index(0, 2)
        alignment = model_with_data.data(index, Qt.TextAlignmentRole)
        assert alignment == (Qt.AlignRight | Qt.AlignVCenter)

    def test_background_role_alternating_rows(self, model_with_data):
        """测试背景色角色（交替行颜色）"""
        # 第0行（偶数行）应该有背景色
        index = model_with_data.index(0, 0)
        background = model_with_data.data(index, Qt.BackgroundRole)
        assert background is not None

        # 第1行（奇数行）不应该有背景色（返回QVariant）
        index = model_with_data.index(1, 0)
        background = model_with_data.data(index, Qt.BackgroundRole)
        from PyQt5.QtCore import QVariant
        assert isinstance(background, QVariant)

    def test_background_role_change_column(self, model_with_data):
        """测试背景色角色（变化列的特殊背景）"""
        # 假设第二条记录体重下降（变化为负）
        index = model_with_data.index(1, 3)  # 变化列
        background = model_with_data.data(index, Qt.BackgroundRole)
        # 应该返回背景色对象（浅绿色或浅红色）
        assert background is not None

    def test_foreground_role_change_column(self, model_with_data):
        """测试前景色角色（变化列的特殊颜色）"""
        # 变化列应该有特殊颜色
        index = model_with_data.index(1, 3)  # 变化列
        foreground = model_with_data.data(index, Qt.ForegroundRole)
        # 应该返回颜色对象
        assert foreground is not None

    def test_tooltip_role_change_column(self, model_with_data):
        """测试工具提示角色（变化列）"""
        index = model_with_data.index(1, 3)  # 变化列
        tooltip = model_with_data.data(index, Qt.ToolTipRole)
        # 应该包含变化信息
        assert tooltip is not None
        assert isinstance(tooltip, str)

    def test_user_role(self, model_with_data):
        """测试用户角色（返回原始记录）"""
        index = model_with_data.index(0, 0)
        record = model_with_data.data(index, Qt.UserRole)
        assert record is not None
        assert hasattr(record, 'weight_kg')

    def test_invalid_index(self, model_with_data):
        """测试无效索引"""
        # 无效行索引
        index = model_with_data.index(10, 0)
        data = model_with_data.data(index, Qt.DisplayRole)
        from PyQt5.QtCore import QVariant
        assert isinstance(data, QVariant)

    def test_set_weight_records(self, model):
        """测试设置体重记录数据"""
        records = TestDataFactory.create_weight_records(user_id=1, count=3)
        model.set_weight_records(records)
        assert model.rowCount() == 3

    def test_get_record_at(self, model_with_data):
        """测试获取指定行的体重记录"""
        record = model_with_data.get_record_at(0)
        assert record is not None
        assert hasattr(record, 'weight_kg')

        # 无效索引应该返回None
        record = model_with_data.get_record_at(10)
        assert record is None

    def test_add_record(self, model_with_data, qtbot):
        """测试添加体重记录"""
        initial_count = model_with_data.rowCount()
        new_record = TestDataFactory.create_weight_record(user_id=1)

        with qtbot.waitSignal(model_with_data.rowsInserted, timeout=1000):
            model_with_data.add_record(new_record)

        assert model_with_data.rowCount() == initial_count + 1

    def test_update_record(self, model_with_data, qtbot):
        """测试更新体重记录"""
        updated_record = TestDataFactory.create_weight_record(user_id=1, weight_kg=80.0)
        updated_record.id = model_with_data.get_record_at(0).id

        with qtbot.waitSignal(model_with_data.dataChanged, timeout=1000):
            model_with_data.update_record(0, updated_record)

        record = model_with_data.get_record_at(0)
        assert record.weight_kg == 80.0

    def test_remove_record(self, model_with_data, qtbot):
        """测试删除体重记录"""
        initial_count = model_with_data.rowCount()

        with qtbot.waitSignal(model_with_data.rowsRemoved, timeout=1000):
            model_with_data.remove_record(0)

        assert model_with_data.rowCount() == initial_count - 1

    def test_clear(self, model_with_data):
        """测试清空模型"""
        assert model_with_data.rowCount() > 0
        model_with_data.clear()
        assert model_with_data.rowCount() == 0
        assert len(model_with_data._changes) == 0

    def test_sort_by_date(self, model_with_data):
        """测试按日期排序"""
        # 创建乱序的记录
        records = [
            TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 3)),
            TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 1)),
            TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 2)),
        ]
        model = WeightTableModel(records)

        # 默认应该是按日期排序的（因为create_weight_records返回排序的列表）
        # 但我们要测试sort_by_date方法
        model.sort_by_date(ascending=True)

        # 检查是否按日期升序排列
        for i in range(model.rowCount() - 1):
            current = model.get_record_at(i)
            next_record = model.get_record_at(i + 1)
            assert current.record_date <= next_record.record_date

    def test_get_records_for_chart(self, model_with_data):
        """测试获取图表数据"""
        dates, weights = model_with_data.get_records_for_chart()
        assert len(dates) == model_with_data.rowCount()
        assert len(weights) == model_with_data.rowCount()
        # 日期应该是按顺序的
        for i in range(len(dates) - 1):
            assert dates[i] <= dates[i + 1]

    def test_calculate_changes(self, model_with_data):
        """测试变化计算"""
        # 检查内部变化列表是否正确计算
        assert len(model_with_data._changes) == model_with_data.rowCount()
        # 第一条记录的变化应该是0
        assert model_with_data._changes[0] == 0.0

    def test_column_attributes_match_names(self, model):
        """测试列属性与列名匹配"""
        assert len(model.COLUMN_ATTRIBUTES) == len(model.COLUMN_NAMES)

    def test_empty_model_operations(self, model):
        """测试空模型的操作"""
        # 空模型获取记录应该返回None
        assert model.get_record_at(0) is None
        assert model.get_record_at(-1) is None

        # 空模型更新/删除不应该崩溃
        record = TestDataFactory.create_weight_record(user_id=1)
        model.update_record(0, record)  # 不应该崩溃
        model.remove_record(0)  # 不应该崩溃

        # 空模型排序不应该崩溃
        model.sort_by_date()

        # 空模型获取图表数据
        dates, weights = model.get_records_for_chart()
        assert len(dates) == 0
        assert len(weights) == 0

    def test_data_notes_empty(self, model_with_data):
        """测试空备注显示"""
        # 记录索引1对应第2条记录 (i=1), 备注应为空字符串
        # Factory: notes=f"第{i+1}天记录" if i % 7 == 0 else ""
        index = model_with_data.index(1, 4)  # 第2行，备注列
        data = model_with_data.data(index, Qt.DisplayRole)
        assert data == ""

    def test_data_record_date_non_date(self, model):
        """测试记录日期（非date对象）"""
        # 使用 model_construct 创建带有字符串日期的记录
        from fatloss.models.weight_record import WeightRecord
        
        record_with_string_date = WeightRecord.model_construct(
            id=1,
            user_id=1,
            record_date="2025-01-01",  # 字符串而不是date对象
            weight_kg=70.0,
            notes="测试备注",
            created_at=date(2025, 1, 1)
        )
        
        model.add_record(record_with_string_date)
        
        # 测试记录日期列显示
        index = model.index(0, 1)  # 日期列
        data = model.data(index, Qt.DisplayRole)
        assert data == "2025-01-01"

    def test_data_created_at_non_date(self, model):
        """测试创建日期（非date对象）"""
        # 使用 model_construct 创建带有字符串日期的记录
        from fatloss.models.weight_record import WeightRecord
        
        record_with_string_date = WeightRecord.model_construct(
            id=1,
            user_id=1,
            record_date=date(2025, 1, 1),
            weight_kg=70.0,
            notes="测试备注",
            created_at="2025-01-01"  # 字符串而不是date对象
        )
        
        model.add_record(record_with_string_date)
        
        # 测试创建日期列显示
        index = model.index(0, 5)  # 创建日期列
        data = model.data(index, Qt.DisplayRole)
        assert data == "2025-01-01"

    def test_data_change_positive(self, model):
        """测试变化列显示（正变化）"""
        # 创建体重增加的记录
        record1 = TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 1), weight_kg=70.0)
        record1.id = 1
        record2 = TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 2), weight_kg=72.0)  # 增加2kg
        record2.id = 2
        records = [record1, record2]
        model.set_weight_records(records)
        
        # 第二条记录应该是 +2.00
        index = model.index(1, 3)  # 变化列
        data = model.data(index, Qt.DisplayRole)
        assert data == "+2.00"

    def test_data_change_negative(self, model):
        """测试变化列显示（负变化）"""
        # 创建体重减少的记录
        record1 = TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 1), weight_kg=72.0)
        record1.id = 1
        record2 = TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 2), weight_kg=70.0)  # 减少2kg
        record2.id = 2
        records = [record1, record2]
        model.set_weight_records(records)
        
        # 第二条记录应该是 -2.00
        index = model.index(1, 3)  # 变化列
        data = model.data(index, Qt.DisplayRole)
        assert data == "-2.00"

    def test_data_change_zero(self, model):
        """测试变化列显示（零变化）"""
        # 创建体重不变的记录
        record1 = TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 1), weight_kg=70.0)
        record1.id = 1
        record2 = TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 2), weight_kg=70.0)  # 不变
        record2.id = 2
        records = [record1, record2]
        model.set_weight_records(records)
        
        # 第二条记录应该是 0.00
        index = model.index(1, 3)  # 变化列
        data = model.data(index, Qt.DisplayRole)
        assert data == "0.00"

    def test_text_alignment_invalid_column(self, model_with_data):
        """测试文本对齐（无效列索引）"""
        # 测试列索引超出范围时的对齐方式
        # 注意：Qt中column >= columnCount()的索引被认为是无效的
        # 所以会返回QVariant而不是对齐方式
        index = model_with_data.index(0, 10)  # 无效列索引
        alignment = model_with_data.data(index, Qt.TextAlignmentRole)
        # 应该返回QVariant而不是对齐方式
        from PyQt5.QtCore import QVariant
        assert isinstance(alignment, QVariant)

    def test_change_column_colors(self, model):
        """测试变化列的背景色和前景色"""
        # 创建体重增加和减少的记录
        record1 = TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 1), weight_kg=70.0)
        record1.id = 1
        record2 = TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 2), weight_kg=72.0)  # 增加2kg
        record2.id = 2
        record3 = TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 3), weight_kg=70.0)  # 减少2kg
        record3.id = 3
        records = [record1, record2, record3]
        model.set_weight_records(records)
        
        # 测试体重增加的背景色（浅红色）
        index = model.index(1, 3)  # 第二条记录，变化列
        background = model.data(index, Qt.BackgroundRole)
        assert background is not None
        assert hasattr(background, 'color')
        
        # 测试体重增加的前景色（红色）
        foreground = model.data(index, Qt.ForegroundRole)
        assert foreground is not None
        assert hasattr(foreground, 'color')
        
        # 测试体重减少的背景色（浅绿色）
        index = model.index(2, 3)  # 第三条记录，变化列
        background = model.data(index, Qt.BackgroundRole)
        assert background is not None
        
        # 测试体重减少的前景色（绿色）
        foreground = model.data(index, Qt.ForegroundRole)
        assert foreground is not None
        assert hasattr(foreground, 'color')

    def test_change_column_tooltips(self, model):
        """测试变化列的工具提示"""
        # 创建体重增加和减少的记录
        record1 = TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 1), weight_kg=70.0)
        record1.id = 1
        record2 = TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 2), weight_kg=72.0)  # 增加2kg
        record2.id = 2
        record3 = TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 3), weight_kg=70.0)  # 减少2kg
        record3.id = 3
        records = [record1, record2, record3]
        model.set_weight_records(records)
        
        # 测试体重增加的工具提示
        index = model.index(1, 3)  # 第二条记录，变化列
        tooltip = model.data(index, Qt.ToolTipRole)
        assert "增加" in tooltip or "+2" in tooltip
        
        # 测试体重减少的工具提示
        index = model.index(2, 3)  # 第三条记录，变化列
        tooltip = model.data(index, Qt.ToolTipRole)
        assert "减少" in tooltip or "-2" in tooltip
        
        # 测试备注列的工具提示
        record_with_notes = TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 4), weight_kg=70.0, notes="这是一个长备注")
        record_with_notes.id = 4
        model.add_record(record_with_notes)
        
        index = model.index(3, 4)  # 第四条记录，备注列
        tooltip = model.data(index, Qt.ToolTipRole)
        assert tooltip == "这是一个长备注"

    def test_invalid_role(self, model_with_data):
        """测试无效角色返回QVariant"""
        # 测试一个不支持的角色
        index = model_with_data.index(0, 0)
        # 使用一个不常见的角色（如UserRole + 100）
        data = model_with_data.data(index, Qt.UserRole + 100)
        from PyQt5.QtCore import QVariant
        assert isinstance(data, QVariant)

    def test_flags_invalid_index(self, model_with_data):
        """测试无效索引的flags"""
        # 测试无效索引的flags
        invalid_index = QModelIndex()
        flags = model_with_data.flags(invalid_index)
        # 应该返回 NoItemFlags
        assert flags == Qt.NoItemFlags
    
    def test_flags_valid_index(self, model_with_data):
        """测试有效索引的flags"""
        # 测试有效索引的flags
        index = model_with_data.index(0, 0)
        flags = model_with_data.flags(index)
        # 应该返回 ItemIsEnabled | ItemIsSelectable
        assert flags == (Qt.ItemIsEnabled | Qt.ItemIsSelectable)

    def test_get_change_for_record_out_of_bounds(self, model):
        """测试_get_change_for_record当row超出范围时"""
        # 创建一条记录
        record = TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 1), weight_kg=70.0)
        record.id = 1
        model.add_record(record)
        
        # 手动调用_get_change_for_record，传入超出范围的row
        # 由于只有1条记录，_changes应该只有1个元素（索引0）
        # 传入row=1应该返回0.0
        change = model._get_change_for_record(record, 1)
        assert change == 0.0
    
    def test_get_change_for_record_valid_row(self, model):
        """测试_get_change_for_record当row在有效范围内时"""
        # 创建多条记录
        record1 = TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 1), weight_kg=70.0)
        record1.id = 1
        record2 = TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 2), weight_kg=72.0)
        record2.id = 2
        model.add_record(record1)
        model.add_record(record2)
        
        # 调用_get_change_for_record，传入有效范围的row
        # row=0应该返回0.0（第一条记录）
        change1 = model._get_change_for_record(record1, 0)
        assert change1 == 0.0
        
        # row=1应该返回2.0（第二条记录相对于第一条的变化）
        change2 = model._get_change_for_record(record2, 1)
        assert change2 == 2.0

    def test_data_change_no_matching_record(self, model):
        """测试变化列当记录ID不匹配时"""
        # 创建一条记录并添加到模型
        record = TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 1), weight_kg=70.0)
        record.id = 1
        model.add_record(record)
        
        # 创建一个不在模型中的记录对象
        other_record = TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 2), weight_kg=72.0)
        other_record.id = 999
        
        # 手动将other_record添加到weight_records但不调用_calculate_changes
        # 这样other_record的ID在_changes中没有对应项
        model.weight_records.append(other_record)
        
        # 获取变化列数据（第2行，即other_record）
        index = model.index(1, 3)  # 变化列
        data = model.data(index, Qt.DisplayRole)
        # 应该返回"0.00"因为找不到匹配的记录ID在_changes中
        assert data == "0.00"
    
    def test_data_id_column_none_value(self, model):
        """测试ID列当值为None时"""
        # 使用 model_construct 创建带有None ID的记录
        from fatloss.models.weight_record import WeightRecord
        
        # 创建一个ID为None的记录
        record_with_none_id = WeightRecord.model_construct(
            id=None,
            user_id=1,
            record_date=date(2025, 1, 1),
            weight_kg=70.0,
            notes="测试备注",
            created_at=date(2025, 1, 1)
        )
        
        model.add_record(record_with_none_id)
        
        # 测试ID列显示（None值应该返回空字符串）
        index = model.index(0, 0)  # ID列
        data = model.data(index, Qt.DisplayRole)
        assert data == ""
    
    def test_data_id_column_non_none_value(self, model):
        """测试ID列当值为非None时"""
        # 创建一个带ID的记录
        record = TestDataFactory.create_weight_record(user_id=1)
        record.id = 123  # 设置非None的ID
        model.add_record(record)
        
        # ID列应该显示ID的字符串形式
        index = model.index(0, 0)  # ID列
        data = model.data(index, Qt.DisplayRole)
        # 应该返回非空字符串
        assert isinstance(data, str)
        assert data != ""
        assert data == "123"
    
    def test_text_alignment_invalid_column_fallback(self, model_with_data):
        """测试文本对齐（无效列索引的fallback）"""
        # 测试列索引超出范围时的对齐方式
        # 注意：Qt中column >= columnCount()的索引被认为是无效的
        # 所以会返回QVariant而不是对齐方式
        index = model_with_data.index(0, 10)  # 无效列索引
        alignment = model_with_data.data(index, Qt.TextAlignmentRole)
        # 应该返回QVariant而不是对齐方式
        from PyQt5.QtCore import QVariant
        assert isinstance(alignment, QVariant)
    
    def test_header_data_invalid_section(self, model_with_data):
        """测试表头数据（无效列索引）"""
        # 测试无效列索引
        header = model_with_data.headerData(10, Qt.Horizontal, Qt.DisplayRole)
        from PyQt5.QtCore import QVariant
        assert isinstance(header, QVariant)

    def test_data_none_value_weight_record(self, model):
        """测试WeightRecord的None值处理"""
        # 使用 model_construct 创建带有None值的记录
        from fatloss.models.weight_record import WeightRecord
        
        # 创建一个ID为None的记录
        record_with_none_id = WeightRecord.model_construct(
            user_id=1,
            record_date=date(2025, 1, 1),
            weight_kg=70.0,
            notes=None,  # None值
            created_at=date(2025, 1, 1)
        )
        
        model.add_record(record_with_none_id)
        
        # 测试备注列显示（None值应该返回空字符串）
        index = model.index(0, 4)  # 备注列
        data = model.data(index, Qt.DisplayRole)
        assert data == ""

    def test_background_color_negative_change(self, model):
        """测试负变化的背景色"""
        # 创建体重减少的记录
        record1 = TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 1), weight_kg=72.0)
        record1.id = 1
        record2 = TestDataFactory.create_weight_record(user_id=1, record_date=date(2025, 1, 2), weight_kg=70.0)  # 减少2kg
        record2.id = 2
        records = [record1, record2]
        model.set_weight_records(records)
        
        # 测试负变化的背景色
        index = model.index(1, 3)  # 第二条记录，变化列
        background = model.data(index, Qt.BackgroundRole)
        assert background is not None
        # 检查颜色是否是浅绿色
        color = background.color()
        assert color.red() == 200
        assert color.green() == 255
        assert color.blue() == 200
