"""用户Repository集成测试"""

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fatloss.models.user_profile import ActivityLevel, Gender, UserProfile
from fatloss.repository import UserRepository, init_database


class TestUserRepositoryIntegration:
    """用户Repository集成测试类"""

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
        """创建UserRepository"""
        return UserRepository(session)

    @pytest.fixture
    def sample_user(self):
        """创建测试用户"""
        return UserProfile(
            name="测试用户",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=70.0,
            activity_level=ActivityLevel.MODERATE,
        )

    def test_create_and_retrieve_user(self, repository, sample_user):
        """测试创建和检索用户"""
        # 创建用户
        created = repository.create(sample_user)

        # 验证ID已分配
        assert created.id is not None
        assert created.name == "测试用户"
        assert created.gender == Gender.MALE
        assert created.height_cm == 175.0

        # 根据ID检索
        retrieved = repository.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name

        # 验证年龄计算
        assert retrieved.age > 0

    def test_get_all_users(self, repository, sample_user):
        """测试获取所有用户"""
        # 创建多个用户
        user1 = sample_user
        user1.name = "用户1"

        user2 = UserProfile(
            name="用户2",
            gender=Gender.FEMALE,
            birth_date=date(1995, 5, 15),
            height_cm=165.0,
            initial_weight_kg=60.0,
            activity_level=ActivityLevel.ACTIVE,
        )

        created1 = repository.create(user1)
        created2 = repository.create(user2)

        # 获取所有用户
        all_users = repository.get_all()

        assert len(all_users) >= 2

        # 验证用户存在
        user_ids = [user.id for user in all_users]
        assert created1.id in user_ids
        assert created2.id in user_ids

    def test_update_user(self, repository, sample_user):
        """测试更新用户"""
        # 创建用户
        created = repository.create(sample_user)

        # 更新用户信息
        created.name = "更新后的用户"
        created.height_cm = 180.0

        updated = repository.update(created.id, created)

        assert updated is not None
        assert updated.id == created.id
        assert updated.name == "更新后的用户"
        assert updated.height_cm == 180.0

        # 验证数据库中的更新
        retrieved = repository.get_by_id(created.id)
        assert retrieved.name == "更新后的用户"

    def test_delete_user(self, repository, sample_user):
        """测试删除用户"""
        # 创建用户
        created = repository.create(sample_user)

        # 删除用户
        deleted = repository.delete(created.id)
        assert deleted is True

        # 验证用户已删除
        retrieved = repository.get_by_id(created.id)
        assert retrieved is None

    def test_find_by_name(self, repository):
        """测试根据姓名查找用户"""
        # 创建测试用户
        user1 = UserProfile(
            name="张三",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=70.0,
            activity_level=ActivityLevel.MODERATE,
        )

        user2 = UserProfile(
            name="李四",
            gender=Gender.FEMALE,
            birth_date=date(1995, 5, 15),
            height_cm=165.0,
            initial_weight_kg=60.0,
            activity_level=ActivityLevel.ACTIVE,
        )

        repository.create(user1)
        repository.create(user2)

        # 查找包含"三"的用户
        results = repository.find_by_name("三")
        assert len(results) == 1
        assert results[0].name == "张三"

        # 查找包含"李"的用户
        results = repository.find_by_name("李")
        assert len(results) == 1
        assert results[0].name == "李四"

    def test_find_by_gender(self, repository):
        """测试根据性别查找用户"""
        # 创建测试用户
        male_user = UserProfile(
            name="男性用户",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=70.0,
            activity_level=ActivityLevel.MODERATE,
        )

        female_user = UserProfile(
            name="女性用户",
            gender=Gender.FEMALE,
            birth_date=date(1995, 5, 15),
            height_cm=165.0,
            initial_weight_kg=60.0,
            activity_level=ActivityLevel.ACTIVE,
        )

        repository.create(male_user)
        repository.create(female_user)

        # 查找男性用户
        male_users = repository.find_by_gender("男")
        assert len(male_users) == 1
        assert male_users[0].name == "男性用户"

        # 查找女性用户
        female_users = repository.find_by_gender("女")
        assert len(female_users) == 1
        assert female_users[0].name == "女性用户"

    def test_find_by_age_range(self, repository):
        """测试根据年龄范围查找用户"""
        from datetime import date
        
        # 创建测试用户
        user1 = UserProfile(
            name="年轻用户",
            gender=Gender.MALE,
            birth_date=date(2000, 1, 1),  # 约24岁（假设当前年份为2025）
            height_cm=175.0,
            initial_weight_kg=70.0,
            activity_level=ActivityLevel.MODERATE,
        )
        
        user2 = UserProfile(
            name="中年用户",
            gender=Gender.FEMALE,
            birth_date=date(1980, 1, 1),  # 约44岁
            height_cm=165.0,
            initial_weight_kg=60.0,
            activity_level=ActivityLevel.ACTIVE,
        )
        
        user3 = UserProfile(
            name="老年用户",
            gender=Gender.MALE,
            birth_date=date(1960, 1, 1),  # 约64岁
            height_cm=180.0,
            initial_weight_kg=80.0,
            activity_level=ActivityLevel.SEDENTARY,
        )
        
        repository.create(user1)
        repository.create(user2)
        repository.create(user3)
        
        # 查找20-30岁的用户
        young_users = repository.find_by_age_range(20, 30)
        assert len(young_users) == 1
        assert young_users[0].name == "年轻用户"
        
        # 查找40-50岁的用户
        middle_users = repository.find_by_age_range(40, 50)
        assert len(middle_users) == 1
        assert middle_users[0].name == "中年用户"
        
        # 查找60-70岁的用户
        old_users = repository.find_by_age_range(60, 70)
        assert len(old_users) == 1
        assert old_users[0].name == "老年用户"
        
        # 查找0-100岁的用户（应该返回所有用户）
        all_age_users = repository.find_by_age_range(0, 100)
        assert len(all_age_users) >= 3

    def test_count_users(self, repository, sample_user):
        """测试统计用户数量"""
        # 初始数量
        initial_count = repository.count()

        # 创建用户
        repository.create(sample_user)

        # 验证数量增加
        new_count = repository.count()
        assert new_count == initial_count + 1
