"""SQLAlchemy Repository测试"""

from datetime import date
from typing import Optional

import pytest
from sqlalchemy import Column, Date, Float, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from src.fatloss.repository.sqlalchemy_repository import (
    SQLAlchemyDateRangeRepository,
    SQLAlchemyFilterableRepository,
    SQLAlchemyRepository,
)

# 创建测试用的Pydantic模型（模拟）
class TestEntity:
    """测试用的Pydantic实体类"""
    
    def __init__(self, id: Optional[int] = None, name: str = "", value: float = 0.0, 
                 record_date: Optional[date] = None):
        self.id = id
        self.name = name
        self.value = value
        self.record_date = record_date

# 创建测试用的SQLAlchemy模型
Base = declarative_base()

class TestModel(Base):
    """测试用的SQLAlchemy模型类"""
    __tablename__ = "test_models"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    record_date = Column(Date, nullable=True)

# 创建具体的Repository实现用于测试
class TestRepository(SQLAlchemyRepository[TestEntity, TestModel, int]):
    """测试用的Repository实现"""
    
    def _to_model(self, entity: TestEntity) -> TestModel:
        """将TestEntity转换为TestModel"""
        return TestModel(
            id=entity.id,
            name=entity.name,
            value=entity.value,
            record_date=entity.record_date,
        )
    
    def _to_pydantic(self, model: TestModel) -> TestEntity:
        """将TestModel转换为TestEntity"""
        return TestEntity(
            id=model.id,
            name=model.name,
            value=model.value,
            record_date=model.record_date,
        )

class TestFilterableRepository(SQLAlchemyFilterableRepository[TestEntity, TestModel, int]):
    """测试用的FilterableRepository实现"""
    
    def _to_model(self, entity: TestEntity) -> TestModel:
        """将TestEntity转换为TestModel"""
        return TestModel(
            id=entity.id,
            name=entity.name,
            value=entity.value,
            record_date=entity.record_date,
        )
    
    def _to_pydantic(self, model: TestModel) -> TestEntity:
        """将TestModel转换为TestEntity"""
        return TestEntity(
            id=model.id,
            name=model.name,
            value=model.value,
            record_date=model.record_date,
        )

class TestDateRangeRepository(SQLAlchemyDateRangeRepository[TestEntity, TestModel, int]):
    """测试用的DateRangeRepository实现"""
    
    def _to_model(self, entity: TestEntity) -> TestModel:
        """将TestEntity转换为TestModel"""
        return TestModel(
            id=entity.id,
            name=entity.name,
            value=entity.value,
            record_date=entity.record_date,
        )
    
    def _to_pydantic(self, model: TestModel) -> TestEntity:
        """将TestModel转换为TestEntity"""
        return TestEntity(
            id=model.id,
            name=model.name,
            value=model.value,
            record_date=model.record_date,
        )


class TestSQLAlchemyRepository:
    """SQLAlchemyRepository测试类"""
    
    @pytest.fixture
    def engine(self):
        """创建内存数据库引擎"""
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
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
        """创建测试Repository"""
        return TestRepository(session, TestModel)
    
    @pytest.fixture
    def filterable_repository(self, session):
        """创建测试FilterableRepository"""
        return TestFilterableRepository(session, TestModel)
    
    @pytest.fixture
    def date_range_repository(self, session):
        """创建测试DateRangeRepository"""
        return TestDateRangeRepository(session, TestModel, "record_date")
    
    @pytest.fixture
    def sample_entity(self):
        """创建测试实体"""
        return TestEntity(
            name="测试实体",
            value=100.0,
            record_date=date(2025, 1, 1),
        )
    
    def test_update_non_existent_entity(self, repository):
        """测试更新不存在的实体（应返回None）"""
        # 尝试更新不存在的ID
        entity = TestEntity(id=999, name="不存在的实体", value=200.0)
        result = repository.update(999, entity)
        
        # 应该返回None，因为实体不存在
        assert result is None
    
    def test_delete_non_existent_entity(self, repository):
        """测试删除不存在的实体（应返回False）"""
        # 尝试删除不存在的ID
        result = repository.delete(999)
        
        # 应该返回False，因为实体不存在
        assert result is False
    
    def test_find_by_filter_with_list_value(self, filterable_repository):
        """测试使用列表值进行过滤查询"""
        # 创建多个测试实体
        entities = [
            TestEntity(name="实体1", value=10.0),
            TestEntity(name="实体2", value=20.0),
            TestEntity(name="实体3", value=30.0),
        ]
        
        # 保存实体
        saved_entities = []
        for entity in entities:
            saved = filterable_repository.create(entity)
            saved_entities.append(saved)
        
        # 使用列表值进行IN查询
        result = filterable_repository.find_by_filter(
            value=[10.0, 30.0]  # 查找value为10.0或30.0的实体
        )
        
        # 应该找到2个实体（实体1和实体3）
        assert len(result) == 2
        
        # 验证找到的实体
        result_values = [entity.value for entity in result]
        assert 10.0 in result_values
        assert 30.0 in result_values
        assert 20.0 not in result_values  # 实体2不应该被找到
    
    def test_find_by_filter_with_single_value(self, filterable_repository):
        """测试使用单个值进行过滤查询"""
        # 创建测试实体
        entity1 = TestEntity(name="实体A", value=50.0)
        entity2 = TestEntity(name="实体B", value=50.0)
        entity3 = TestEntity(name="实体C", value=100.0)
        
        # 保存实体
        filterable_repository.create(entity1)
        filterable_repository.create(entity2)
        filterable_repository.create(entity3)
        
        # 使用单个值进行等值查询
        result = filterable_repository.find_by_filter(value=50.0)
        
        # 应该找到2个实体（实体A和实体B）
        assert len(result) == 2
        
        # 验证找到的实体
        result_names = [entity.name for entity in result]
        assert "实体A" in result_names
        assert "实体B" in result_names
        assert "实体C" not in result_names
    
    def test_find_one_by_filter(self, filterable_repository):
        """测试查找单个实体"""
        # 创建测试实体
        entity1 = TestEntity(name="唯一实体", value=75.0)
        entity2 = TestEntity(name="另一个实体", value=75.0)
        
        # 保存实体
        saved1 = filterable_repository.create(entity1)
        filterable_repository.create(entity2)
        
        # 查找不存在的实体
        result = filterable_repository.find_one_by_filter(name="不存在的实体")
        assert result is None
        
        # 查找存在的实体
        result = filterable_repository.find_one_by_filter(name="唯一实体")
        assert result is not None
        assert result.name == "唯一实体"
        assert result.value == 75.0
    
    def test_find_by_date_range(self, date_range_repository):
        """测试按日期范围查找"""
        # 创建不同日期的测试实体
        entities = [
            TestEntity(name="实体-2024-12-01", value=10.0, record_date=date(2024, 12, 1)),
            TestEntity(name="实体-2025-01-01", value=20.0, record_date=date(2025, 1, 1)),
            TestEntity(name="实体-2025-01-15", value=30.0, record_date=date(2025, 1, 15)),
            TestEntity(name="实体-2025-02-01", value=40.0, record_date=date(2025, 2, 1)),
        ]
        
        # 保存实体
        for entity in entities:
            date_range_repository.create(entity)
        
        # 查找2025年1月的实体
        result = date_range_repository.find_by_date_range(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )
        
        # 应该找到2个实体（2025-01-01和2025-01-15）
        assert len(result) == 2
        
        # 验证找到的实体
        result_names = [entity.name for entity in result]
        assert "实体-2025-01-01" in result_names
        assert "实体-2025-01-15" in result_names
        assert "实体-2024-12-01" not in result_names
        assert "实体-2025-02-01" not in result_names
        
        # 验证按日期排序
        assert result[0].record_date == date(2025, 1, 1)
        assert result[1].record_date == date(2025, 1, 15)
    
    def test_find_latest_by_date(self, date_range_repository):
        """测试查找最新日期的实体"""
        # 创建不同日期的测试实体
        entities = [
            TestEntity(name="旧实体", value=10.0, record_date=date(2024, 12, 1)),
            TestEntity(name="新实体", value=20.0, record_date=date(2025, 1, 15)),
            TestEntity(name="中间实体", value=30.0, record_date=date(2025, 1, 1)),
        ]
        
        # 保存实体
        for entity in entities:
            date_range_repository.create(entity)
        
        # 查找最新日期的实体
        result = date_range_repository.find_latest_by_date()
        
        # 应该找到"新实体"
        assert result is not None
        assert result.name == "新实体"
        assert result.record_date == date(2025, 1, 15)
    
    def test_repository_basic_operations(self, repository, sample_entity):
        """测试Repository基本操作"""
        # 创建实体
        created = repository.create(sample_entity)
        assert created.id is not None
        assert created.name == "测试实体"
        assert created.value == 100.0
        
        # 根据ID获取实体
        retrieved = repository.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "测试实体"
        
        # 获取不存在的实体
        non_existent = repository.get_by_id(999)
        assert non_existent is None
        
        # 获取所有实体
        all_entities = repository.get_all()
        assert len(all_entities) >= 1
        
        # 统计实体数量
        count = repository.count()
        assert count >= 1
        
        # 更新实体
        updated_entity = TestEntity(
            id=created.id,
            name="更新后的实体",
            value=200.0,
            record_date=date(2025, 1, 2),
        )
        updated = repository.update(created.id, updated_entity)
        assert updated is not None
        assert updated.name == "更新后的实体"
        assert updated.value == 200.0
        
        # 删除实体
        delete_result = repository.delete(created.id)
        assert delete_result is True
        
        # 验证实体已被删除
        deleted = repository.get_by_id(created.id)
        assert deleted is None