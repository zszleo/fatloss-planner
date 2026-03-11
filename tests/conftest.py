"""Pytest配置和共享fixture。

提供全局测试fixture，避免数据库模型重复定义错误。
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fatloss.repository.database import Base, init_database


@pytest.fixture(scope="session")
def test_engine():
    """创建测试数据库引擎（session作用域，整个测试会话只创建一次）。"""
    # 使用内存数据库避免文件冲突
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # 创建所有表（只执行一次）
    init_database(engine)
    
    yield engine
    
    # 清理
    engine.dispose()


@pytest.fixture
def test_session(test_engine):
    """创建测试数据库会话（function作用域，每个测试函数独立）。"""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    
    try:
        yield session
        # 测试结束后回滚，保持数据库干净
        session.rollback()
    finally:
        session.close()


@pytest.fixture
def test_uow(test_session):
    """创建测试工作单元（function作用域）。"""
    from fatloss.repository.unit_of_work import UnitOfWork
    return UnitOfWork(test_session)


@pytest.fixture
def sample_user():
    """创建示例用户档案（function作用域）。"""
    from datetime import date
    from fatloss.models.user_profile import ActivityLevel, Gender, UserProfile
    
    return UserProfile(
        name="测试用户",
        gender=Gender.MALE,
        birth_date=date(1990, 1, 1),
        height_cm=175.0,
        initial_weight_kg=70.0,
        activity_level=ActivityLevel.MODERATE,
    )


@pytest.fixture
def sample_weight_record():
    """创建示例体重记录（function作用域）。"""
    from datetime import date
    from fatloss.models.weight_record import WeightRecord
    
    return WeightRecord(
        user_id=1,
        weight_kg=70.5,
        record_date=date(2025, 1, 1),
        notes="测试记录",
    )


@pytest.fixture
def sample_app_config():
    """创建示例应用配置（function作用域）。"""
    from fatloss.models.app_config import AppConfig, Theme, UnitSystem
    
    return AppConfig(
        user_id=1,
        unit_system=UnitSystem.METRIC,
        theme=Theme.DARK,
        language="zh-CN",
        weekly_check_day=1,
        carb_adjustment_unit_g=10,
        monthly_loss_percentage=0.05,
        exercise_calories_per_minute=5.0,
        enable_notifications=True,
        data_retention_days=365,
    )