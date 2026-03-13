"""营养表格数据模型测试。

测试重点:
1. 营养计划数据展示
2. 宏营养素格式化和单位转换
3. 进度状态可视化
4. 自定义角色数据提供
5. 数据更新和刷新机制
"""

import pytest
from datetime import date
from unittest.mock import Mock

from PyQt5.QtCore import Qt, QModelIndex

from fatloss.desktop.models.nutrition_table_model import NutritionTableModel
from fatloss.calculator.nutrition_calculator import NutritionDistribution
from tests.desktop.factories import TestDataFactory


class TestNutritionTableModel:
    """营养表格模型测试类"""

    @pytest.fixture
    def model(self):
        """创建空的营养表格模型"""
        return NutritionTableModel()

    @pytest.fixture
    def model_with_data(self):
        """创建带有测试数据的营养表格模型"""
        plans = [
            TestDataFactory.create_nutrition_plan(
                user_id=1,
                plan_date=date(2025, 1, 1),
                target_tdee=2000.0,
                nutrition=NutritionDistribution(
                    carbohydrates_g=150.0,
                    protein_g=120.0,
                    fat_g=50.0,
                    total_calories=1800.0,
                ),
                is_adjusted=False,
                adjustment_units=0
            ),
            TestDataFactory.create_nutrition_plan(
                user_id=1,
                plan_date=date(2025, 1, 2),
                target_tdee=2050.0,
                nutrition=NutritionDistribution(
                    carbohydrates_g=160.0,
                    protein_g=125.0,
                    fat_g=55.0,
                    total_calories=1900.0,
                ),
                is_adjusted=True,
                adjustment_units=2  # 增加2个单位（60g碳水）
            ),
        ]
        return NutritionTableModel(plans)

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
        assert model.COLUMN_NAMES[0] == "日期"
        assert model.COLUMN_NAMES[1] == "TDEE (kcal)"
        assert model.COLUMN_NAMES[2] == "蛋白质 (g)"
        assert model.COLUMN_NAMES[3] == "碳水 (g)"
        assert model.COLUMN_NAMES[4] == "脂肪 (g)"
        assert model.COLUMN_NAMES[5] == "总热量 (kcal)"
        assert model.COLUMN_NAMES[6] == "调整"
        assert model.COLUMN_NAMES[7] == "调整量"

    def test_header_data_horizontal(self, model_with_data):
        """测试水平表头数据"""
        for i, expected_name in enumerate(model_with_data.COLUMN_NAMES):
            header = model_with_data.headerData(i, Qt.Horizontal, Qt.DisplayRole)
            assert header == expected_name

    def test_header_data_vertical(self, model_with_data):
        """测试垂直表头数据（行号）"""
        header = model_with_data.headerData(0, Qt.Vertical, Qt.DisplayRole)
        assert header == "1"
        header = model_with_data.headerData(1, Qt.Vertical, Qt.DisplayRole)
        assert header == "2"

    def test_data_date_display(self, model_with_data):
        """测试日期显示"""
        index = model_with_data.index(0, 0)  # 第1行，日期列
        data = model_with_data.data(index, Qt.DisplayRole)
        assert data == "2025-01-01"

    def test_data_tdee_display(self, model_with_data):
        """测试TDEE显示"""
        index = model_with_data.index(0, 1)  # 第1行，TDEE列
        data = model_with_data.data(index, Qt.DisplayRole)
        assert data == "2000"  # 格式化为整数

    def test_data_protein_display(self, model_with_data):
        """测试蛋白质显示"""
        index = model_with_data.index(0, 2)  # 第1行，蛋白质列
        data = model_with_data.data(index, Qt.DisplayRole)
        assert data == "120.0"  # 保留1位小数

    def test_data_carbs_display(self, model_with_data):
        """测试碳水显示"""
        index = model_with_data.index(0, 3)  # 第1行，碳水列
        data = model_with_data.data(index, Qt.DisplayRole)
        assert data == "150.0"  # 保留1位小数

    def test_data_fat_display(self, model_with_data):
        """测试脂肪显示"""
        index = model_with_data.index(0, 4)  # 第1行，脂肪列
        data = model_with_data.data(index, Qt.DisplayRole)
        assert data == "50.0"  # 保留1位小数

    def test_data_calories_display(self, model_with_data):
        """测试总热量显示"""
        index = model_with_data.index(0, 5)  # 第1行，总热量列
        data = model_with_data.data(index, Qt.DisplayRole)
        assert data == "1800"  # 格式化为整数

    def test_data_adjusted_display_no_adjustment(self, model_with_data):
        """测试调整状态显示（未调整）"""
        index = model_with_data.index(0, 6)  # 第1行，调整列
        data = model_with_data.data(index, Qt.DisplayRole)
        assert data == "否"

    def test_data_adjusted_display_with_adjustment(self, model_with_data):
        """测试调整状态显示（已调整）"""
        index = model_with_data.index(1, 6)  # 第2行，调整列
        data = model_with_data.data(index, Qt.DisplayRole)
        assert data == "是"

    def test_data_adjustment_amount_display_no_adjustment(self, model_with_data):
        """测试调整量显示（未调整）"""
        index = model_with_data.index(0, 7)  # 第1行，调整量列
        data = model_with_data.data(index, Qt.DisplayRole)
        assert data == "无"

    def test_data_adjustment_amount_display_with_adjustment(self, model_with_data):
        """测试调整量显示（已调整）"""
        index = model_with_data.index(1, 7)  # 第2行，调整量列
        data = model_with_data.data(index, Qt.DisplayRole)
        # adjustment_units=2, 每个单位30g, 所以是 "+60g"
        assert data == "+60g"

    def test_data_adjustment_amount_negative(self, model_with_data):
        """测试调整量显示（负调整）"""
        # 创建一个调整量为负数的计划
        plan = TestDataFactory.create_nutrition_plan(
            user_id=1,
            plan_date=date(2025, 1, 3),
            is_adjusted=True,
            adjustment_units=-1  # 减少1个单位（30g碳水）
        )
        model_with_data.plans.append(plan)
        
        index = model_with_data.index(2, 7)  # 第3行，调整量列
        data = model_with_data.data(index, Qt.DisplayRole)
        assert data == "-30g"

    def test_text_alignment_role(self, model_with_data):
        """测试文本对齐角色"""
        # 数值列（1-5列）应该右对齐
        for col in [1, 2, 3, 4, 5]:
            index = model_with_data.index(0, col)
            alignment = model_with_data.data(index, Qt.TextAlignmentRole)
            assert alignment == (Qt.AlignRight | Qt.AlignVCenter)

        # 日期列（0列）应该左对齐
        index = model_with_data.index(0, 0)
        alignment = model_with_data.data(index, Qt.TextAlignmentRole)
        assert alignment == (Qt.AlignLeft | Qt.AlignVCenter)

    def test_background_role_adjusted(self, model_with_data):
        """测试背景色角色（调整过的行）"""
        # 第2行是已调整的（增加碳水），应该有浅绿色背景
        index = model_with_data.index(1, 0)
        background = model_with_data.data(index, Qt.BackgroundRole)
        assert background is not None

    def test_tooltip_role_adjusted(self, model_with_data):
        """测试工具提示角色（调整过的行）"""
        # 第2行是已调整的，第7列（index 6）是"调整"列
        # 注意：NutritionTableModel 中只有 column 6 (adjusted) 才有 tooltip
        index = model_with_data.index(1, 6)  # Row 1, Column 6 ("调整"列)
        
        tooltip = model_with_data.data(index, Qt.ToolTipRole)
        
        # 应该返回调整信息
        assert tooltip is not None
        # If it's QVariant, we can't check string content directly
        if hasattr(tooltip, 'toString'):
             tooltip_str = tooltip.toString()
        else:
             tooltip_str = str(tooltip)
        assert "调整" in tooltip_str

    def test_tooltip_role_non_adjusted_column(self, model_with_data):
        """测试工具提示角色（非调整列应返回QVariant）"""
        # 测试非调整列（如第0列，ID列）的tooltip应返回QVariant
        index = model_with_data.index(0, 0)
        tooltip = model_with_data.data(index, Qt.ToolTipRole)
        from PyQt5.QtCore import QVariant
        assert isinstance(tooltip, QVariant)

    def test_invalid_index(self, model_with_data):
        """测试无效索引"""
        # 无效行索引
        index = model_with_data.index(10, 0)
        data = model_with_data.data(index, Qt.DisplayRole)
        from PyQt5.QtCore import QVariant
        assert isinstance(data, QVariant)

    def test_set_plans(self, model):
        """测试设置营养计划数据"""
        plans = [
            TestDataFactory.create_nutrition_plan(user_id=1, plan_date=date(2025, 1, 1)),
            TestDataFactory.create_nutrition_plan(user_id=1, plan_date=date(2025, 1, 2)),
        ]
        model.set_plans(plans)
        assert model.rowCount() == 2

    def test_get_plan_at(self, model_with_data):
        """测试获取指定行的营养计划"""
        plan = model_with_data.get_plan_at(0)
        assert plan is not None
        assert plan.plan_date == date(2025, 1, 1)

        # 无效索引应该返回None
        plan = model_with_data.get_plan_at(10)
        assert plan is None

    def test_get_plan_by_date(self, model_with_data):
        """测试根据日期获取营养计划"""
        plan = model_with_data.get_plan_by_date(date(2025, 1, 1))
        assert plan is not None
        assert plan.plan_date == date(2025, 1, 1)

        # 不存在的日期应该返回None
        plan = model_with_data.get_plan_by_date(date(2025, 1, 3))
        assert plan is None

    def test_clear(self, model_with_data):
        """测试清空模型"""
        assert model_with_data.rowCount() > 0
        model_with_data.clear()
        assert model_with_data.rowCount() == 0

    def test_background_role_negative_adjustment(self, model_with_data):
        """测试背景色角色（减少碳水）"""
        # 创建一个减少碳水的计划
        plan = TestDataFactory.create_nutrition_plan(
            user_id=1,
            plan_date=date(2025, 1, 3),
            is_adjusted=True,
            adjustment_units=-1  # 减少1个单位（30g碳水）
        )
        model_with_data.set_plans([plan])
        
        # 测试调整列的背景色
        index = model_with_data.index(0, 6)  # 调整列
        background = model_with_data.data(index, Qt.BackgroundRole)
        # 应该返回浅红色背景
        assert background is not None

    def test_header_data_invalid_section(self, model_with_data):
        """测试表头数据（无效列索引）"""
        # 无效列索引应该返回QVariant
        header = model_with_data.headerData(100, Qt.Horizontal, Qt.DisplayRole)
        from PyQt5.QtCore import QVariant
        assert isinstance(header, QVariant)

    def test_column_attributes_match_names(self, model):
        """测试列属性与列名匹配"""
        assert len(model.COLUMN_ATTRIBUTES) == len(model.COLUMN_NAMES)
