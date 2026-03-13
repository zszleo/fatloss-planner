"""用户表格数据模型测试。

测试重点:
1. 数据加载和刷新
2. 列定义和格式
3. 排序和筛选功能
4. 数据编辑和验证
5. 信号发射（dataChanged）
"""

import pytest
from datetime import date
from unittest.mock import Mock

from PyQt5.QtCore import Qt, QModelIndex

from fatloss.desktop.models.user_table_model import UserTableModel
from tests.desktop.factories import TestDataFactory


class TestUserTableModel:
    """用户表格模型测试类"""

    @pytest.fixture
    def model(self):
        """创建空的用户表格模型"""
        return UserTableModel()

    @pytest.fixture
    def model_with_data(self):
        """创建带有测试数据的用户表格模型"""
        users = [
            TestDataFactory.create_user_profile(
                name="张三",
                birth_date=date(1990, 1, 1),
                height_cm=175.0,
                initial_weight_kg=70.0
            ),
            TestDataFactory.create_user_profile(
                name="李四",
                birth_date=date(1985, 5, 15),
                height_cm=168.0,
                initial_weight_kg=65.0
            ),
        ]
        # 设置ID以模拟数据库分配
        users[0].id = 1
        users[1].id = 2
        return UserTableModel(users)

    def test_initialization_empty(self, model):
        """测试初始化空模型"""
        assert model.rowCount() == 0
        assert model.columnCount() == 8  # 8列定义

    def test_initialization_with_data(self, model_with_data):
        """测试初始化带数据的模型"""
        assert model_with_data.rowCount() == 2
        assert model_with_data.columnCount() == 8

    def test_column_definitions(self, model):
        """测试列定义和名称"""
        assert len(model.COLUMN_NAMES) == 8
        assert model.COLUMN_NAMES[0] == "ID"
        assert model.COLUMN_NAMES[1] == "姓名"
        assert model.COLUMN_NAMES[2] == "性别"
        assert model.COLUMN_NAMES[3] == "年龄"
        assert model.COLUMN_NAMES[4] == "身高(cm)"
        assert model.COLUMN_NAMES[5] == "体重(kg)"
        assert model.COLUMN_NAMES[6] == "活动水平"
        assert model.COLUMN_NAMES[7] == "创建日期"

    def test_header_data_horizontal(self, model_with_data):
        """测试水平表头数据"""
        # 测试所有列的表头
        for i, expected_name in enumerate(model_with_data.COLUMN_NAMES):
            header = model_with_data.headerData(i, Qt.Horizontal, Qt.DisplayRole)
            assert header == expected_name

    def test_header_data_vertical(self, model_with_data):
        """测试垂直表头数据（行号）"""
        # 第1行应该显示1
        header = model_with_data.headerData(0, Qt.Vertical, Qt.DisplayRole)
        assert header == 1
        # 第2行应该显示2
        header = model_with_data.headerData(1, Qt.Vertical, Qt.DisplayRole)
        assert header == 2

    def test_data_display_role(self, model_with_data):
        """测试数据显示角色"""
        # 测试姓名列
        index = model_with_data.index(0, 1)  # 第1行，姓名列
        data = model_with_data.data(index, Qt.DisplayRole)
        assert data == "张三"

        # 测试ID列
        index = model_with_data.index(0, 0)  # 第1行，ID列
        data = model_with_data.data(index, Qt.DisplayRole)
        assert data == "1"

    def test_data_age_calculation(self, model_with_data):
        """测试年龄计算"""
        index = model_with_data.index(0, 3)  # 第1行，年龄列
        data = model_with_data.data(index, Qt.DisplayRole)
        # 1990年出生，应该计算出正确年龄（根据当前年份）
        expected_age = date.today().year - 1990
        assert data == expected_age

    def test_data_gender_display(self, model_with_data):
        """测试性别显示"""
        index = model_with_data.index(0, 2)  # 第1行，性别列
        data = model_with_data.data(index, Qt.DisplayRole)
        # 性别应该显示为字符串
        assert isinstance(data, str)

    def test_data_activity_level_display(self, model_with_data):
        """测试活动水平显示"""
        index = model_with_data.index(0, 6)  # 第1行，活动水平列
        data = model_with_data.data(index, Qt.DisplayRole)
        # 活动水平应该显示为字符串
        assert isinstance(data, str)

    def test_data_created_at_format(self, model_with_data):
        """测试创建日期格式化"""
        index = model_with_data.index(0, 7)  # 第1行，创建日期列
        data = model_with_data.data(index, Qt.DisplayRole)
        # 应该返回格式化的日期字符串
        assert isinstance(data, str)
        assert "-" in data  # 格式应为 YYYY-MM-DD

    def test_data_created_at_non_date(self, model):
        """测试创建日期（非date对象）"""
        # 使用 model_construct 创建带有字符串日期的用户
        from fatloss.models.user_profile import UserProfile
        from fatloss.models.enums import Gender, ActivityLevel
        
        user_with_string_date = UserProfile.model_construct(
            id=1,
            name="测试用户",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=70.0,
            activity_level=ActivityLevel.MODERATE,
            created_at="2025-01-01"  # 字符串而不是date对象
        )
        
        model.add_user(user_with_string_date)
        
        # 测试创建日期列显示
        index = model.index(0, 7)  # 创建日期列
        data = model.data(index, Qt.DisplayRole)
        assert data == "2025-01-01"

    def test_data_none_value(self, model_with_data):
        """测试None值处理"""
        # 创建一个包含None值的用户
        user_with_none = TestDataFactory.create_user_profile(name="测试用户")
        user_with_none.id = 3
        user_with_none.height_cm = None  # 设置为None

        model_with_data.add_user(user_with_none)

        # 测试None值应该返回空字符串
        index = model_with_data.index(2, 4)  # 第3行，身高列
        data = model_with_data.data(index, Qt.DisplayRole)
        assert data == ""

    def test_text_alignment_role(self, model_with_data):
        """测试文本对齐角色"""
        # ID列（第0列）应该右对齐
        index = model_with_data.index(0, 0)
        alignment = model_with_data.data(index, Qt.TextAlignmentRole)
        assert alignment == (Qt.AlignRight | Qt.AlignVCenter)

        # 姓名列（第1列）应该左对齐
        index = model_with_data.index(0, 1)
        alignment = model_with_data.data(index, Qt.TextAlignmentRole)
        assert alignment == (Qt.AlignLeft | Qt.AlignVCenter)

    def test_background_role(self, model_with_data):
        """测试背景色角色"""
        # 第0行（偶数行）应该有背景色
        index = model_with_data.index(0, 0)
        background = model_with_data.data(index, Qt.BackgroundRole)
        assert background is not None

        # 第1行（奇数行）不应该有背景色（返回QVariant）
        index = model_with_data.index(1, 0)
        background = model_with_data.data(index, Qt.BackgroundRole)
        # 奇数行返回QVariant，不是None
        from PyQt5.QtCore import QVariant
        assert isinstance(background, QVariant)

    def test_invalid_index(self, model_with_data):
        """测试无效索引"""
        # 无效行索引
        index = model_with_data.index(10, 0)
        data = model_with_data.data(index, Qt.DisplayRole)
        from PyQt5.QtCore import QVariant
        assert isinstance(data, QVariant)

        # 无效列索引（虽然列数固定，但测试边界）
        index = model_with_data.index(0, 10)
        data = model_with_data.data(index, Qt.DisplayRole)
        assert isinstance(data, QVariant)

    def test_flags_read_only(self, model_with_data):
        """测试项目标志（只读）"""
        index = model_with_data.index(0, 0)
        flags = model_with_data.flags(index)
        # 应该只启用和可选择，不可编辑
        assert flags & Qt.ItemIsEnabled
        assert flags & Qt.ItemIsSelectable
        assert not (flags & Qt.ItemIsEditable)

    def test_flags_invalid_index(self, model_with_data):
        """测试无效索引的项目标志"""
        # 创建一个无效的索引
        invalid_index = QModelIndex()
        flags = model_with_data.flags(invalid_index)
        # 应该返回 NoItemFlags
        assert flags == Qt.NoItemFlags

    def test_set_users(self, model):
        """测试设置用户数据"""
        users = [
            TestDataFactory.create_user_profile(name="用户1"),
            TestDataFactory.create_user_profile(name="用户2"),
        ]
        users[0].id = 1
        users[1].id = 2

        model.set_users(users)
        assert model.rowCount() == 2
        assert model.get_user_at(0).name == "用户1"

    def test_get_user_at(self, model_with_data):
        """测试获取指定行的用户"""
        user = model_with_data.get_user_at(0)
        assert user is not None
        assert user.name == "张三"

        # 无效索引应该返回None
        user = model_with_data.get_user_at(10)
        assert user is None

    def test_add_user(self, model_with_data, qtbot):
        """测试添加用户"""
        initial_count = model_with_data.rowCount()
        new_user = TestDataFactory.create_user_profile(name="新用户")
        new_user.id = 3

        # 监视rowsInserted信号
        with qtbot.waitSignal(model_with_data.rowsInserted, timeout=1000):
            model_with_data.add_user(new_user)

        assert model_with_data.rowCount() == initial_count + 1
        assert model_with_data.get_user_at(initial_count).name == "新用户"

    def test_update_user(self, model_with_data, qtbot):
        """测试更新用户"""
        updated_user = TestDataFactory.create_user_profile(name="更新后的用户")
        updated_user.id = 1  # 保持相同的ID

        # 监视dataChanged信号
        with qtbot.waitSignal(model_with_data.dataChanged, timeout=1000):
            model_with_data.update_user(0, updated_user)

        user = model_with_data.get_user_at(0)
        assert user.name == "更新后的用户"

    def test_remove_user(self, model_with_data, qtbot):
        """测试删除用户"""
        initial_count = model_with_data.rowCount()

        # 监视rowsRemoved信号
        with qtbot.waitSignal(model_with_data.rowsRemoved, timeout=1000):
            model_with_data.remove_user(0)

        assert model_with_data.rowCount() == initial_count - 1
        assert model_with_data.get_user_at(0).name == "李四"  # 原来的第2行变成第1行

    def test_remove_user_invalid_index(self, model_with_data):
        """测试删除无效索引的用户"""
        initial_count = model_with_data.rowCount()
        model_with_data.remove_user(10)  # 无效索引
        assert model_with_data.rowCount() == initial_count  # 计数不应改变

    def test_update_user_invalid_index(self, model_with_data):
        """测试更新无效索引的用户"""
        initial_user = model_with_data.get_user_at(0)
        updated_user = TestDataFactory.create_user_profile(name="不会被更新的用户")
        updated_user.id = 1

        model_with_data.update_user(10, updated_user)  # 无效索引
        # 用户应该没有改变
        assert model_with_data.get_user_at(0).name == initial_user.name

    def test_empty_model_operations(self, model):
        """测试空模型的操作"""
        # 空模型获取用户应该返回None
        assert model.get_user_at(0) is None
        assert model.get_user_at(-1) is None

        # 空模型更新/删除不应该崩溃
        user = TestDataFactory.create_user_profile(name="测试")
        user.id = 1
        model.update_user(0, user)  # 不应该崩溃
        model.remove_user(0)  # 不应该崩溃

    def test_data_gender_with_enum(self, model):
        """测试性别显示（枚举对象）"""
        # 测试当 gender 是枚举对象时的处理
        # 使用 model_construct 绕过 Pydantic 验证来创建 enum 对象
        from fatloss.models.user_profile import UserProfile
        from fatloss.models.enums import Gender, ActivityLevel
        
        # 使用 model_construct 创建带有 enum 对象的用户
        user_with_enum = UserProfile.model_construct(
            id=1,
            name="测试用户",
            gender=Gender.MALE,  # 枚举对象而不是字符串
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=70.0,
            activity_level=ActivityLevel.MODERATE,
            created_at=date(2025, 1, 1)
        )
        
        model.add_user(user_with_enum)
        
        # 测试性别列显示
        index = model.index(0, 2)  # 性别列
        data = model.data(index, Qt.DisplayRole)
        assert data == "男"  # 应该返回 enum.value

    def test_data_activity_level_with_enum(self, model):
        """测试活动水平显示（枚举对象）"""
        # 测试当 activity_level 是枚举对象时的处理
        # 使用 model_construct 绕过 Pydantic 验证来创建 enum 对象
        from fatloss.models.user_profile import UserProfile
        from fatloss.models.enums import Gender, ActivityLevel
        
        # 使用 model_construct 创建带有 enum 对象的用户
        user_with_enum = UserProfile.model_construct(
            id=1,
            name="测试用户",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=70.0,
            activity_level=ActivityLevel.MODERATE,  # 枚举对象而不是字符串
            created_at=date(2025, 1, 1)
        )
        
        model.add_user(user_with_enum)
        
        # 测试活动水平列显示
        index = model.index(0, 6)  # 活动水平列
        data = model.data(index, Qt.DisplayRole)
        assert data == "中度活动"  # 应该返回 enum.value

    def test_header_data_invalid_section(self, model_with_data):
        """测试表头数据（无效列索引）"""
        # 无效列索引应该返回QVariant
        header = model_with_data.headerData(100, Qt.Horizontal, Qt.DisplayRole)
        from PyQt5.QtCore import QVariant
        assert isinstance(header, QVariant)

    def test_column_attributes_match_names(self, model):
        """测试列属性与列名匹配"""
        # 列属性数量应该与列名数量一致
        assert len(model.COLUMN_ATTRIBUTES) == len(model.COLUMN_NAMES)
