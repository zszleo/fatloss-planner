"""体重记录Repository集成测试"""

from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fatloss.models.weight_record import WeightRecord
from fatloss.repository import WeightRepository, init_database


class TestWeightRepositoryIntegration:
    """体重记录Repository集成测试类"""

    @pytest.fixture
    def engine(self):
        """创建内存数据库引擎"""
        engine = create_engine("sqlite:///:memory:", echo=False)
        init_database(engine)
        return engine

    @pytest.fixture
    def session(self, engine):
        """创建数据库会话"""
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    @pytest.fixture
    def repository(self, session):
        """创建WeightRepository"""
        return WeightRepository(session)

    @pytest.fixture
    def sample_weight_records(self):
        """创建测试体重记录"""
        base_date = date(2024, 1, 1)
        return [
            WeightRecord(
                user_id=1, weight_kg=70.0, record_date=base_date, notes="初始记录"
            ),
            WeightRecord(
                user_id=1,
                weight_kg=69.5,
                record_date=base_date + timedelta(days=7),
                notes="一周后",
            ),
            WeightRecord(
                user_id=1,
                weight_kg=69.0,
                record_date=base_date + timedelta(days=14),
                notes="两周后",
            ),
            WeightRecord(
                user_id=2, weight_kg=80.0, record_date=base_date, notes="用户2初始记录"
            ),
        ]

    def test_create_and_retrieve_weight_record(self, repository, sample_weight_records):
        """测试创建和检索体重记录"""
        sample_record = sample_weight_records[0]

        # 创建记录
        created = repository.create(sample_record)

        # 验证ID已分配
        assert created.id is not None
        assert created.user_id == 1
        assert created.weight_kg == 70.0
        assert created.record_date == date(2024, 1, 1)

        # 根据ID检索
        retrieved = repository.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.weight_kg == 70.0

    def test_find_by_user_id(self, repository, sample_weight_records):
        """测试根据用户ID查找体重记录"""
        # 创建多个记录
        for record in sample_weight_records:
            repository.create(record)

        # 查找用户1的记录
        user1_records = repository.find_by_user_id(1)

        # 应该找到3条记录，按日期倒序
        assert len(user1_records) == 3

        # 验证按日期倒序排序
        dates = [record.record_date for record in user1_records]
        assert dates == sorted(dates, reverse=True)

        # 验证数据正确
        weights = [record.weight_kg for record in user1_records]
        assert set(weights) == {70.0, 69.5, 69.0}

    def test_find_latest_by_user_id(self, repository, sample_weight_records):
        """测试查找用户最新的体重记录"""
        # 创建多个记录
        for record in sample_weight_records:
            repository.create(record)

        # 查找用户1的最新记录
        latest = repository.find_latest_by_user_id(1)

        assert latest is not None
        assert latest.user_id == 1
        assert latest.weight_kg == 69.0  # 最新的记录
        assert latest.record_date == date(2024, 1, 15)

    def test_find_by_date_range(self, repository, sample_weight_records):
        """测试根据日期范围查找体重记录"""
        # 创建多个记录
        for record in sample_weight_records:
            repository.create(record)

        # 查找2024年1月1日到1月10日的记录
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 10)

        records = repository.find_by_date_range(start_date, end_date, user_id=1)

        # 应该找到2条记录（1月1日和1月8日）
        assert len(records) == 2

        dates = [record.record_date for record in records]
        assert date(2024, 1, 1) in dates
        assert date(2024, 1, 8) in dates

        # 验证按日期排序
        assert dates == sorted(dates)

    def test_find_previous_by_user_id(self, repository, sample_weight_records):
        """测试查找指定日期之前的最近一次记录"""
        # 创建多个记录
        for record in sample_weight_records:
            repository.create(record)

        # 查找2024年1月15日之前的最近一次记录
        target_date = date(2024, 1, 15)
        previous = repository.find_previous_by_user_id(1, target_date)

        assert previous is not None
        assert previous.user_id == 1
        assert previous.weight_kg == 69.5  # 1月8日的记录
        assert previous.record_date == date(2024, 1, 8)

        # 查找2024年1月1日之前的记录（应该没有）
        previous = repository.find_previous_by_user_id(1, date(2024, 1, 1))
        assert previous is None

    def test_calculate_weight_change(self, repository, sample_weight_records):
        """测试计算体重变化"""
        # 创建多个记录
        for record in sample_weight_records:
            repository.create(record)

        # 计算1月1日到1月15日的体重变化
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 15)

        change = repository.calculate_weight_change(1, start_date, end_date)

        # 从70.0kg到69.0kg，减少了1.0kg
        assert change is not None
        assert change == -1.0  # 负值表示减重

        # 测试没有数据的情况
        change = repository.calculate_weight_change(99, start_date, end_date)
        assert change is None

    def test_calculate_average_weight(self, repository, sample_weight_records):
        """测试计算平均体重"""
        # 创建多个记录
        for record in sample_weight_records:
            repository.create(record)

        # 计算1月1日到1月15日的平均体重
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 15)

        average = repository.calculate_average_weight(1, start_date, end_date)

        # 平均体重 = (70.0 + 69.5 + 69.0) / 3 = 69.5
        assert average is not None
        assert average == pytest.approx(69.5, abs=0.01)

        # 测试没有数据的情况
        average = repository.calculate_average_weight(99, start_date, end_date)
        assert average is None

    def test_update_weight_record(self, repository, sample_weight_records):
        """测试更新体重记录"""
        sample_record = sample_weight_records[0]

        # 创建记录
        created = repository.create(sample_record)

        # 更新记录
        created.weight_kg = 71.0
        created.notes = "更新后的记录"

        updated = repository.update(created.id, created)

        assert updated is not None
        assert updated.id == created.id
        assert updated.weight_kg == 71.0
        assert updated.notes == "更新后的记录"

        # 验证数据库中的更新
        retrieved = repository.get_by_id(created.id)
        assert retrieved.weight_kg == 71.0

    def test_delete_weight_record(self, repository, sample_weight_records):
        """测试删除体重记录"""
        sample_record = sample_weight_records[0]

        # 创建记录
        created = repository.create(sample_record)

        # 删除记录
        deleted = repository.delete(created.id)
        assert deleted is True

        # 验证记录已删除
        retrieved = repository.get_by_id(created.id)
        assert retrieved is None

    def test_count_records(self, repository, sample_weight_records):
        """测试统计记录数量"""
        # 初始数量
        initial_count = repository.count()

        # 创建记录
        for record in sample_weight_records:
            repository.create(record)

        # 验证数量增加
        new_count = repository.count()
        assert new_count == initial_count + len(sample_weight_records)
