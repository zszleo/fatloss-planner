"""用户档案模型测试"""

from datetime import date
import pytest

from fatloss.models.user_profile import UserProfile, Gender, ActivityLevel


class TestUserProfile:
    """用户档案模型测试类"""

    def test_create_user_profile_minimal(self):
        """测试创建最小化用户档案"""
        user = UserProfile(
            name="张三",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=70.0,
        )
        assert user.id is None
        assert user.name == "张三"
        assert user.gender == Gender.MALE.value  # 因为 use_enum_values=True
        assert user.birth_date == date(1990, 1, 1)
        assert user.height_cm == 175.0
        assert user.initial_weight_kg == 70.0
        assert user.activity_level == ActivityLevel.MODERATE.value
        assert user.created_at == date.today()
        assert user.updated_at == date.today()

    def test_create_user_profile_full(self):
        """测试创建完整用户档案"""
        user = UserProfile(
            id=1,
            name="李四",
            gender=Gender.FEMALE,
            birth_date=date(1985, 5, 15),
            height_cm=165.0,
            initial_weight_kg=60.0,
            activity_level=ActivityLevel.ACTIVE,
            created_at=date(2024, 1, 1),
            updated_at=date(2024, 1, 2),
        )
        assert user.id == 1
        assert user.name == "李四"
        assert user.gender == Gender.FEMALE.value
        assert user.birth_date == date(1985, 5, 15)
        assert user.height_cm == 165.0
        assert user.initial_weight_kg == 60.0
        assert user.activity_level == ActivityLevel.ACTIVE.value
        assert user.created_at == date(2024, 1, 1)
        assert user.updated_at == date(2024, 1, 2)

    def test_age_calculation(self):
        """测试年龄计算"""
        # 使用固定日期以确保测试可重复性
        from unittest.mock import patch
        with patch("fatloss.models.user_profile.date") as mock_date:
            mock_date.today.return_value = date(2024, 12, 31)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
            
            user = UserProfile(
                name="测试",
                gender=Gender.MALE,
                birth_date=date(1990, 6, 15),
                height_cm=175.0,
                initial_weight_kg=70.0,
            )
            # 生日未过：2024-12-31 - 1990-06-15 = 34岁（因为生日在6月，12月已过生日）
            assert user.age == 34

    def test_age_calculation_before_birthday(self):
        """测试生日前的年龄计算"""
        from unittest.mock import patch
        with patch("fatloss.models.user_profile.date") as mock_date:
            mock_date.today.return_value = date(2024, 3, 1)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
            
            user = UserProfile(
                name="测试",
                gender=Gender.MALE,
                birth_date=date(1990, 6, 15),
                height_cm=175.0,
                initial_weight_kg=70.0,
            )
            # 生日未过：2024-03-01 - 1990-06-15 = 33岁（因为生日在6月，3月还未过生日）
            assert user.age == 33

    def test_height_validation(self):
        """测试身高验证"""
        # 正常范围
        user = UserProfile(
            name="测试",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=150.0,
            initial_weight_kg=70.0,
        )
        assert user.height_cm == 150.0
        
        # 边界值
        user = UserProfile(
            name="测试",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=100.0,
            initial_weight_kg=70.0,
        )
        assert user.height_cm == 100.0
        
        user = UserProfile(
            name="测试",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=250.0,
            initial_weight_kg=70.0,
        )
        assert user.height_cm == 250.0
        
        # 超出范围应引发错误
        with pytest.raises(ValueError, match="身高必须在100-250厘米之间"):
            UserProfile(
                name="测试",
                gender=Gender.MALE,
                birth_date=date(1990, 1, 1),
                height_cm=99.9,
                initial_weight_kg=70.0,
            )
        
        with pytest.raises(ValueError, match="身高必须在100-250厘米之间"):
            UserProfile(
                name="测试",
                gender=Gender.MALE,
                birth_date=date(1990, 1, 1),
                height_cm=250.1,
                initial_weight_kg=70.0,
            )

    def test_weight_validation(self):
        """测试体重验证"""
        # 正常范围
        user = UserProfile(
            name="测试",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=50.0,
        )
        assert user.initial_weight_kg == 50.0
        
        # 边界值
        user = UserProfile(
            name="测试",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=30.0,
        )
        assert user.initial_weight_kg == 30.0
        
        user = UserProfile(
            name="测试",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=200.0,
        )
        assert user.initial_weight_kg == 200.0
        
        # 超出范围应引发错误
        with pytest.raises(ValueError, match="体重必须在30-200千克之间"):
            UserProfile(
                name="测试",
                gender=Gender.MALE,
                birth_date=date(1990, 1, 1),
                height_cm=175.0,
                initial_weight_kg=29.9,
            )
        
        with pytest.raises(ValueError, match="体重必须在30-200千克之间"):
            UserProfile(
                name="测试",
                gender=Gender.MALE,
                birth_date=date(1990, 1, 1),
                height_cm=175.0,
                initial_weight_kg=200.1,
            )

    def test_name_length_validation(self):
        """测试姓名长度验证"""
        # 正常姓名
        user = UserProfile(
            name="张三",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=70.0,
        )
        assert user.name == "张三"
        
        # 最小长度
        user = UserProfile(
            name="A",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=70.0,
        )
        assert user.name == "A"
        
        # 最大长度
        long_name = "张" * 100
        user = UserProfile(
            name=long_name,
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=70.0,
        )
        assert user.name == long_name
        
        # 空字符串应引发错误
        with pytest.raises(ValueError, match="at least 1 character"):
            UserProfile(
                name="",
                gender=Gender.MALE,
                birth_date=date(1990, 1, 1),
                height_cm=175.0,
                initial_weight_kg=70.0,
            )

    def test_json_serialization(self):
        """测试JSON序列化"""
        user = UserProfile(
            id=1,
            name="张三",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=70.0,
            created_at=date(2024, 1, 1),
            updated_at=date(2024, 1, 2),
        )
        
        json_data = user.model_dump_json()
        assert '"id":1' in json_data
        assert '"name":"张三"' in json_data
        assert '"gender":"male"' in json_data
        assert '"birth_date":"1990-01-01"' in json_data
        assert '"height_cm":175.0' in json_data
        assert '"initial_weight_kg":70.0' in json_data
        assert '"created_at":"2024-01-01"' in json_data
        assert '"updated_at":"2024-01-02"' in json_data