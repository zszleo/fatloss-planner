"""验证工具模块测试。"""

import pytest

from fatloss.utils.validation import validate_range, validate_positive


class TestValidateRange:
    """测试validate_range函数。"""

    def test_validate_range_success_without_unit(self):
        """测试验证范围内值（无单位）。"""
        # 正常值应该在范围内不抛出异常
        validate_range(50, 30, 200, "体重")
        
    def test_validate_range_success_with_unit(self):
        """测试验证范围内值（有单位）。"""
        validate_range(50, 30, 200, "体重", "kg")
        
    def test_validate_range_edge_min(self):
        """测试验证边界最小值。"""
        validate_range(30, 30, 200, "体重", "kg")
        
    def test_validate_range_edge_max(self):
        """测试验证边界最大值。"""
        validate_range(200, 30, 200, "体重", "kg")
        
    def test_validate_range_below_min(self):
        """测试验证低于最小值。"""
        with pytest.raises(ValueError) as exc_info:
            validate_range(20, 30, 200, "体重", "kg")
        assert "体重必须在30-200kg之间" in str(exc_info.value)
        
    def test_validate_range_above_max(self):
        """测试验证高于最大值。"""
        with pytest.raises(ValueError) as exc_info:
            validate_range(210, 30, 200, "体重", "kg")
        assert "体重必须在30-200kg之间" in str(exc_info.value)
        
    def test_validate_range_below_min_no_unit(self):
        """测试验证低于最小值（无单位）。"""
        with pytest.raises(ValueError) as exc_info:
            validate_range(20, 30, 200, "体重")
        assert "体重必须在30-200之间" in str(exc_info.value)
        
    def test_validate_range_float_values(self):
        """测试验证浮点数值。"""
        validate_range(75.5, 30.0, 200.0, "体重", "kg")


class TestValidatePositive:
    """测试validate_positive函数。"""

    def test_validate_positive_success(self):
        """测试验证正数成功。"""
        validate_positive(10, "体重")
        validate_positive(0.1, "体重")
        
    def test_validate_positive_zero_not_allowed(self):
        """测试验证正数（不允许零）。"""
        with pytest.raises(ValueError) as exc_info:
            validate_positive(0, "体重")
        assert "体重必须为正数" in str(exc_info.value)
        
    def test_validate_positive_zero_allowed(self):
        """测试验证正数（允许零）。"""
        validate_positive(0, "体重", allow_zero=True)
        
    def test_validate_positive_negative_not_allowed(self):
        """测试验证正数（负数不允许）。"""
        with pytest.raises(ValueError) as exc_info:
            validate_positive(-5, "体重")
        assert "体重必须为正数" in str(exc_info.value)
        
    def test_validate_positive_negative_with_zero_allowed(self):
        """测试验证正数（允许零时负数仍不允许）。"""
        with pytest.raises(ValueError) as exc_info:
            validate_positive(-5, "体重", allow_zero=True)
        assert "体重不能为负数" in str(exc_info.value)
        
    def test_validate_positive_float_values(self):
        """测试验证浮点正数。"""
        validate_positive(15.5, "体重")