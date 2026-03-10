"""应用程序配置Repository集成测试"""

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.fatloss.models.app_config import AppConfig, Theme, UnitSystem
from src.fatloss.repository import AppConfigRepository, init_database


class TestAppConfigRepositoryIntegration:
    """应用程序配置Repository集成测试类"""

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
        """创建AppConfigRepository"""
        return AppConfigRepository(session)

    @pytest.fixture
    def sample_config(self):
        """创建测试配置"""
        return AppConfig(
            user_id=1,
            unit_system=UnitSystem.METRIC,
            theme=Theme.DARK,
            language="zh-CN",
            weekly_check_day=1,
            carb_adjustment_unit_g=30,
            monthly_loss_percentage=0.05,
            exercise_calories_per_minute=10,
            enable_notifications=True,
            data_retention_days=365,
        )

    def test_create_and_retrieve_config(self, repository, sample_config):
        """测试创建和检索配置"""
        # 创建配置
        created = repository.create(sample_config)

        # 验证ID已分配
        assert created.id is not None
        assert created.user_id == 1
        assert created.unit_system == UnitSystem.METRIC
        assert created.theme == Theme.DARK

        # 根据ID检索
        retrieved = repository.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.user_id == created.user_id

        # 验证日期字段
        assert isinstance(retrieved.created_at, date)
        assert isinstance(retrieved.updated_at, date)

    def test_get_by_user_id(self, repository, sample_config):
        """测试根据用户ID获取配置"""
        # 创建配置
        created = repository.create(sample_config)

        # 根据用户ID检索
        retrieved = repository.get_by_user_id(created.user_id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.user_id == created.user_id

        # 测试不存在的用户ID
        non_existent = repository.get_by_user_id(999)
        assert non_existent is None

    def test_create_or_update_existing(self, repository, sample_config):
        """测试创建或更新已有配置"""
        # 首次创建
        created = repository.create(sample_config)
        original_id = created.id

        # 修改配置
        updated_config = AppConfig(
            user_id=1,
            unit_system=UnitSystem.IMPERIAL,
            theme=Theme.LIGHT,
            language="en-US",
            weekly_check_day=2,
            carb_adjustment_unit_g=50,
            monthly_loss_percentage=0.07,
            exercise_calories_per_minute=12,
            enable_notifications=False,
            data_retention_days=180,
        )

        # 调用create_or_update（应更新现有配置）
        result = repository.create_or_update(updated_config)

        # 验证ID相同（更新而非新建）
        assert result.id == original_id
        assert result.unit_system == UnitSystem.IMPERIAL
        assert result.theme == Theme.LIGHT
        assert result.language == "en-US"
        assert result.weekly_check_day == 2
        assert result.carb_adjustment_unit_g == 50
        assert result.monthly_loss_percentage == 0.07
        assert result.exercise_calories_per_minute == 12
        assert result.enable_notifications is False
        assert result.data_retention_days == 180

        # 验证数据库中的更新
        retrieved = repository.get_by_id(original_id)
        assert retrieved.unit_system == UnitSystem.IMPERIAL

    def test_create_or_update_new(self, repository, sample_config):
        """测试创建或更新新配置"""
        # 确保没有现有配置
        existing = repository.get_by_user_id(sample_config.user_id)
        assert existing is None

        # 调用create_or_update（应创建新配置）
        result = repository.create_or_update(sample_config)

        # 验证已创建
        assert result.id is not None
        assert result.user_id == sample_config.user_id

        # 验证数据库中存在
        retrieved = repository.get_by_user_id(sample_config.user_id)
        assert retrieved is not None

    def test_update_by_user_id(self, repository, sample_config):
        """测试根据用户ID更新配置"""
        # 创建配置
        created = repository.create(sample_config)

        # 更新特定字段
        updated = repository.update_by_user_id(
            user_id=created.user_id,
            theme=Theme.LIGHT,
            language="en-US",
            enable_notifications=False,
        )

        assert updated is not None
        assert updated.id == created.id
        assert updated.theme == Theme.LIGHT
        assert updated.language == "en-US"
        assert updated.enable_notifications is False

        # 验证其他字段保持不变
        assert updated.unit_system == created.unit_system
        assert updated.weekly_check_day == created.weekly_check_day

        # 验证数据库中的更新
        retrieved = repository.get_by_id(created.id)
        assert retrieved.theme == Theme.LIGHT

    def test_update_by_user_id_nonexistent(self, repository):
        """测试更新不存在的用户配置"""
        result = repository.update_by_user_id(
            user_id=999,
            theme=Theme.LIGHT,
        )
        assert result is None

    def test_get_all_configs(self, repository):
        """测试获取所有配置"""
        # 创建多个配置
        config1 = AppConfig(user_id=1, unit_system=UnitSystem.METRIC)
        config2 = AppConfig(user_id=2, unit_system=UnitSystem.IMPERIAL)

        created1 = repository.create(config1)
        created2 = repository.create(config2)

        # 获取所有配置
        all_configs = repository.get_all()

        assert len(all_configs) >= 2

        # 验证配置存在
        config_ids = [config.id for config in all_configs]
        assert created1.id in config_ids
        assert created2.id in config_ids

    def test_update_config(self, repository, sample_config):
        """测试更新配置"""
        # 创建配置
        created = repository.create(sample_config)

        # 更新配置
        created.theme = Theme.LIGHT
        created.language = "en-US"

        updated = repository.update(created.id, created)

        assert updated is not None
        assert updated.id == created.id
        assert updated.theme == Theme.LIGHT
        assert updated.language == "en-US"

        # 验证数据库中的更新
        retrieved = repository.get_by_id(created.id)
        assert retrieved.theme == Theme.LIGHT

    def test_delete_config(self, repository, sample_config):
        """测试删除配置"""
        # 创建配置
        created = repository.create(sample_config)

        # 删除配置
        deleted = repository.delete(created.id)
        assert deleted is True

        # 验证配置已删除
        retrieved = repository.get_by_id(created.id)
        assert retrieved is None

    def test_find_by_filter(self, repository):
        """测试根据过滤器查找配置"""
        # 创建测试配置
        config1 = AppConfig(
            user_id=1,
            unit_system=UnitSystem.METRIC,
            theme=Theme.DARK,
        )
        config2 = AppConfig(
            user_id=2,
            unit_system=UnitSystem.IMPERIAL,
            theme=Theme.LIGHT,
        )

        repository.create(config1)
        repository.create(config2)

        # 查找使用公制的配置
        metric_configs = repository.find_by_filter(unit_system="metric")
        assert len(metric_configs) == 1
        assert metric_configs[0].user_id == 1

        # 查找使用深色主题的配置
        dark_configs = repository.find_by_filter(theme="dark")
        assert len(dark_configs) == 1
        assert dark_configs[0].user_id == 1

    def test_count_configs(self, repository, sample_config):
        """测试统计配置数量"""
        # 初始数量
        initial_count = repository.count()

        # 创建配置
        repository.create(sample_config)

        # 验证数量增加
        new_count = repository.count()
        assert new_count == initial_count + 1