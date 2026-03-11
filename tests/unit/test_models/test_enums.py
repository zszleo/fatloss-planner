"""枚举类型测试"""

import pytest

from fatloss.models.enums import (
    Gender,
    ActivityLevel,
    UnitSystem,
    Theme,
    get_enum_from_string,
    get_enum_values,
    validate_enum_value,
)


class TestEnums:
    """枚举类型测试类"""

    def test_gender_enum_values(self):
        """测试性别枚举值"""
        assert Gender.MALE == "男"
        assert Gender.FEMALE == "女"
        assert Gender.MALE.value == "男"
        assert Gender.FEMALE.value == "女"
        assert len(list(Gender)) == 2

    def test_activity_level_enum_values(self):
        """测试活动水平枚举值"""
        assert ActivityLevel.SEDENTARY == "久坐"
        assert ActivityLevel.LIGHT == "轻度活动"
        assert ActivityLevel.MODERATE == "中度活动"
        assert ActivityLevel.ACTIVE == "活跃"
        assert ActivityLevel.VERY_ACTIVE == "非常活跃"
        assert len(list(ActivityLevel)) == 5

    def test_unit_system_enum_values(self):
        """测试单位制枚举值"""
        assert UnitSystem.METRIC == "metric"
        assert UnitSystem.IMPERIAL == "imperial"
        assert len(list(UnitSystem)) == 2

    def test_theme_enum_values(self):
        """测试主题枚举值"""
        assert Theme.LIGHT == "light"
        assert Theme.DARK == "dark"
        assert Theme.AUTO == "auto"
        assert len(list(Theme)) == 3

    def test_get_enum_from_string_case_sensitive(self):
        """测试区分大小写的枚举字符串转换"""
        # 测试中文值 - 区分大小写无影响，但应该精确匹配
        result = get_enum_from_string(Gender, "男", case_sensitive=True)
        assert result == Gender.MALE
        
        result = get_enum_from_string(ActivityLevel, "中度活动", case_sensitive=True)
        assert result == ActivityLevel.MODERATE
        
        # 测试英文主题的大小写敏感
        result = get_enum_from_string(Theme, "light", case_sensitive=True)
        assert result == Theme.LIGHT
        
        with pytest.raises(ValueError):
            get_enum_from_string(Theme, "LIGHT", case_sensitive=True)
            
        # 测试单位制的大小写敏感
        result = get_enum_from_string(UnitSystem, "metric", case_sensitive=True)
        assert result == UnitSystem.METRIC
        
        with pytest.raises(ValueError):
            get_enum_from_string(UnitSystem, "METRIC", case_sensitive=True)

    def test_get_enum_from_string_case_insensitive(self):
        """测试不区分大小写的枚举字符串转换"""
        # 测试中文值（不区分大小写无影响）
        result = get_enum_from_string(Gender, "男", case_sensitive=False)
        assert result == Gender.MALE
        
        result = get_enum_from_string(Gender, "女", case_sensitive=False)
        assert result == Gender.FEMALE
        
        # 测试英文值不区分大小写
        result = get_enum_from_string(Theme, "LIGHT", case_sensitive=False)
        assert result == Theme.LIGHT
        
        result = get_enum_from_string(Theme, "Light", case_sensitive=False)
        assert result == Theme.LIGHT
        
        result = get_enum_from_string(Theme, "light", case_sensitive=False)
        assert result == Theme.LIGHT
        
        result = get_enum_from_string(UnitSystem, "METRIC", case_sensitive=False)
        assert result == UnitSystem.METRIC

    def test_get_enum_from_string_invalid_value(self):
        """测试无效的枚举字符串转换"""
        with pytest.raises(ValueError) as exc_info:
            get_enum_from_string(Gender, "unknown", case_sensitive=False)
        assert "无效的值" in str(exc_info.value)
        assert "男" in str(exc_info.value)
        assert "女" in str(exc_info.value)

    def test_get_enum_values(self):
        """测试获取枚举值列表"""
        gender_values = get_enum_values(Gender)
        assert gender_values == ["男", "女"]
        
        activity_values = get_enum_values(ActivityLevel)
        assert activity_values == ["久坐", "轻度活动", "中度活动", "活跃", "非常活跃"]
        
        unit_values = get_enum_values(UnitSystem)
        assert unit_values == ["metric", "imperial"]
        
        theme_values = get_enum_values(Theme)
        assert theme_values == ["light", "dark", "auto"]

    def test_validate_enum_value_true(self):
        """测试验证有效的枚举值"""
        assert validate_enum_value(Gender, "男") is True
        assert validate_enum_value(Gender, "女") is True
        assert validate_enum_value(ActivityLevel, "中度活动") is True
        assert validate_enum_value(Theme, "light") is True
        assert validate_enum_value(Theme, "LIGHT", case_sensitive=False) is True
        
        # 区分大小写的情况
        assert validate_enum_value(Theme, "light", case_sensitive=True) is True
        assert validate_enum_value(Theme, "LIGHT", case_sensitive=True) is False

    def test_validate_enum_value_false(self):
        """测试验证无效的枚举值"""
        assert validate_enum_value(Gender, "unknown") is False
        assert validate_enum_value(ActivityLevel, "不存在的活动") is False
        assert validate_enum_value(UnitSystem, "invalid") is False
        assert validate_enum_value(Theme, "invalid") is False
        
        # 区分大小写的情况
        assert validate_enum_value(Theme, "LIGHT", case_sensitive=True) is False