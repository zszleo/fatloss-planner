"""体重记录模型测试"""

from datetime import date
import pytest

from fatloss.models.weight_record import WeightRecord


class TestWeightRecord:
    """体重记录模型测试类"""

    def test_create_weight_record_minimal(self):
        """测试创建最小化体重记录"""
        record = WeightRecord(
            user_id=1,
            weight_kg=70.0,
            record_date=date(2024, 1, 1),
        )
        assert record.id is None
        assert record.user_id == 1
        assert record.weight_kg == 70.0
        assert record.record_date == date(2024, 1, 1)
        assert record.notes == ""
        assert record.created_at == date.today()

    def test_create_weight_record_full(self):
        """测试创建完整体重记录"""
        record = WeightRecord(
            id=1,
            user_id=1,
            weight_kg=65.5,
            record_date=date(2024, 1, 15),
            notes="测试记录",
            created_at=date(2024, 1, 16),
        )
        assert record.id == 1
        assert record.user_id == 1
        assert record.weight_kg == 65.5
        assert record.record_date == date(2024, 1, 15)
        assert record.notes == "测试记录"
        assert record.created_at == date(2024, 1, 16)

    def test_weight_validation(self):
        """测试体重验证"""
        # 正常范围
        record = WeightRecord(
            user_id=1,
            weight_kg=50.0,
            record_date=date(2024, 1, 1),
        )
        assert record.weight_kg == 50.0
        
        # 边界值
        record = WeightRecord(
            user_id=1,
            weight_kg=30.0,
            record_date=date(2024, 1, 1),
        )
        assert record.weight_kg == 30.0
        
        record = WeightRecord(
            user_id=1,
            weight_kg=200.0,
            record_date=date(2024, 1, 1),
        )
        assert record.weight_kg == 200.0
        
        # 超出范围应引发错误
        with pytest.raises(ValueError, match="体重必须在30-200千克之间"):
            WeightRecord(
                user_id=1,
                weight_kg=29.9,
                record_date=date(2024, 1, 1),
            )
        
        with pytest.raises(ValueError, match="体重必须在30-200千克之间"):
            WeightRecord(
                user_id=1,
                weight_kg=200.1,
                record_date=date(2024, 1, 1),
            )

    def test_weight_rounding(self):
        """测试体重四舍五入"""
        record = WeightRecord(
            user_id=1,
            weight_kg=70.123,
            record_date=date(2024, 1, 1),
        )
        assert record.weight_kg == 70.12
        
        record = WeightRecord(
            user_id=1,
            weight_kg=70.126,
            record_date=date(2024, 1, 1),
        )
        assert record.weight_kg == 70.13  # 四舍五入

    def test_record_date_validation(self):
        """测试记录日期验证"""
        # 今天日期
        from unittest.mock import patch
        with patch("fatloss.models.weight_record.date") as mock_date:
            mock_date.today.return_value = date(2024, 1, 10)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
            
            record = WeightRecord(
                user_id=1,
                weight_kg=70.0,
                record_date=date(2024, 1, 10),
            )
            assert record.record_date == date(2024, 1, 10)
        
        # 过去日期
        record = WeightRecord(
            user_id=1,
            weight_kg=70.0,
            record_date=date(2023, 12, 31),
        )
        assert record.record_date == date(2023, 12, 31)
        
        # 未来日期应引发错误
        with patch("fatloss.models.weight_record.date") as mock_date:
            mock_date.today.return_value = date(2024, 1, 10)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
            
            with pytest.raises(ValueError, match="记录日期不能是未来日期"):
                WeightRecord(
                    user_id=1,
                    weight_kg=70.0,
                    record_date=date(2024, 1, 11),
                )

    def test_user_id_validation(self):
        """测试用户ID验证"""
        # 有效用户ID
        record = WeightRecord(
            user_id=1,
            weight_kg=70.0,
            record_date=date(2024, 1, 1),
        )
        assert record.user_id == 1
        
        # 零或负数应引发错误
        with pytest.raises(ValueError, match="greater than 0"):
            WeightRecord(
                user_id=0,
                weight_kg=70.0,
                record_date=date(2024, 1, 1),
            )
        
        with pytest.raises(ValueError, match="greater than 0"):
            WeightRecord(
                user_id=-1,
                weight_kg=70.0,
                record_date=date(2024, 1, 1),
            )

    def test_notes_length_validation(self):
        """测试备注长度验证"""
        # 正常备注
        record = WeightRecord(
            user_id=1,
            weight_kg=70.0,
            record_date=date(2024, 1, 1),
            notes="测试备注",
        )
        assert record.notes == "测试备注"
        
        # 长备注
        long_notes = "x" * 500
        record = WeightRecord(
            user_id=1,
            weight_kg=70.0,
            record_date=date(2024, 1, 1),
            notes=long_notes,
        )
        assert record.notes == long_notes
        
        # 超长备注应引发错误
        with pytest.raises(ValueError, match="at most 500 characters"):
            WeightRecord(
                user_id=1,
                weight_kg=70.0,
                record_date=date(2024, 1, 1),
                notes="x" * 501,
            )

    def test_json_serialization(self):
        """测试JSON序列化"""
        record = WeightRecord(
            id=1,
            user_id=1,
            weight_kg=70.5,
            record_date=date(2024, 1, 1),
            notes="测试",
            created_at=date(2024, 1, 2),
        )
        
        json_data = record.model_dump_json()
        assert '"id":1' in json_data
        assert '"user_id":1' in json_data
        assert '"weight_kg":70.5' in json_data
        assert '"record_date":"2024-01-01"' in json_data
        assert '"notes":"测试"' in json_data
        assert '"created_at":"2024-01-02"' in json_data