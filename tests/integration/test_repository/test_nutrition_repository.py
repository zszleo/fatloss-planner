"""营养计划Repository集成测试"""

from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.fatloss.models.nutrition_plan import DailyNutritionPlan, WeeklyNutritionPlan
from src.fatloss.calculator.nutrition_calculator import NutritionDistribution
from src.fatloss.repository import DailyNutritionRepository, WeeklyNutritionRepository, init_database


class TestNutritionRepositoryIntegration:
    """营养计划Repository集成测试类"""

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
    def daily_repo(self, session):
        """创建DailyNutritionRepository"""
        return DailyNutritionRepository(session)

    @pytest.fixture
    def weekly_repo(self, session):
        """创建WeeklyNutritionRepository"""
        return WeeklyNutritionRepository(session)

    @pytest.fixture
    def sample_nutrition(self):
        """创建测试营养数据"""
        return NutritionDistribution(
            carbohydrates_g=200.0,
            protein_g=150.0,
            fat_g=50.0,
            total_calories=2000.0,
        )

    @pytest.fixture
    def sample_daily_plan(self):
        """创建测试每日计划"""
        return DailyNutritionPlan(
            user_id=1,
            plan_date=date(2030, 1, 1),
            target_tdee=2000.0,
            nutrition=NutritionDistribution(carbohydrates_g=200.0, protein_g=150.0, fat_g=50.0, total_calories=2000.0),
            is_adjusted=False,
            notes="测试每日计划",
        )

    @pytest.fixture
    def sample_weekly_plan(self):
        """创建测试每周计划"""
        return WeeklyNutritionPlan(
            user_id=1,
            week_start_date=date(2030, 1, 1),
            week_end_date=date(2030, 1, 7),
            daily_plans=[],
            total_carbohydrates_g=1400.0,
            total_protein_g=1050.0,
            total_fat_g=350.0,
        )

    def test_create_and_retrieve_daily_plan(self, daily_repo, sample_daily_plan):
        """测试创建和检索每日计划"""
        created = daily_repo.create(sample_daily_plan)
        assert created.id is not None
        assert created.user_id == 1
        assert created.plan_date == date(2030, 1, 1)
        assert created.nutrition.carbohydrates_g == 200.0

        retrieved = daily_repo.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_find_by_user_id(self, daily_repo, sample_daily_plan):
        """测试根据用户ID查找每日计划"""
        # 创建多个计划
        plan1 = sample_daily_plan
        plan2 = DailyNutritionPlan(
            user_id=1,
            plan_date=date(2030, 1, 2),
            target_tdee=2000.0,
            nutrition=NutritionDistribution(carbohydrates_g=180.0, protein_g=140.0, fat_g=45.0, total_calories=2000.0),
            is_adjusted=True,
        )
        plan3 = DailyNutritionPlan(
            user_id=2,  # 不同用户
            plan_date=date(2030, 1, 1),
            target_tdee=2000.0,
            nutrition=NutritionDistribution(carbohydrates_g=220.0, protein_g=160.0, fat_g=55.0, total_calories=2000.0),
        )

        daily_repo.create(plan1)
        daily_repo.create(plan2)
        daily_repo.create(plan3)

        # 查找用户1的计划
        user1_plans = daily_repo.find_by_user_id(1)
        assert len(user1_plans) == 2
        # 应按日期倒序排列
        assert user1_plans[0].plan_date == date(2030, 1, 2)
        assert user1_plans[1].plan_date == date(2030, 1, 1)

        # 查找用户2的计划
        user2_plans = daily_repo.find_by_user_id(2)
        assert len(user2_plans) == 1
        assert user2_plans[0].user_id == 2

    def test_find_by_user_and_date(self, daily_repo, sample_daily_plan):
        """测试查找用户指定日期的计划"""
        created = daily_repo.create(sample_daily_plan)

        found = daily_repo.find_by_user_and_date(1, date(2030, 1, 1))
        assert found is not None
        assert found.id == created.id

        # 不存在的日期
        not_found = daily_repo.find_by_user_and_date(1, date(2030, 1, 2))
        assert not_found is None

    def test_find_adjusted_plans(self, daily_repo, sample_daily_plan):
        """测试查找已调整的计划"""
        # 创建已调整和未调整的计划
        adjusted_plan = DailyNutritionPlan(
            user_id=1,
            plan_date=date(2030, 1, 1),
            target_tdee=2000.0,
            nutrition=NutritionDistribution(carbohydrates_g=200.0, protein_g=150.0, fat_g=50.0, total_calories=2000.0),
            is_adjusted=True,
        )
        normal_plan = DailyNutritionPlan(
            user_id=1,
            plan_date=date(2030, 1, 2),
            target_tdee=2000.0,
            nutrition=NutritionDistribution(carbohydrates_g=180.0, protein_g=140.0, fat_g=45.0, total_calories=2000.0),
            is_adjusted=False,
        )

        daily_repo.create(adjusted_plan)
        daily_repo.create(normal_plan)

        adjusted_plans = daily_repo.find_adjusted_plans(1)
        assert len(adjusted_plans) == 1
        assert adjusted_plans[0].is_adjusted is True
        assert adjusted_plans[0].plan_date == date(2030, 1, 1)

    def test_find_plans_for_week(self, daily_repo):
        """测试查找指定周的每日计划"""
        # 创建一周内的计划
        week_start = date(2030, 1, 6)  # 周一
        for i in range(7):
            plan = DailyNutritionPlan(
                user_id=1,
                plan_date=week_start + timedelta(days=i),
                target_tdee=2000.0,
                nutrition=NutritionDistribution(carbohydrates_g=200.0 + i * 10, protein_g=150.0, fat_g=50.0, total_calories=2000.0),
            )
            daily_repo.create(plan)

        # 创建前一周的计划
        prev_week_plan = DailyNutritionPlan(
            user_id=1,
            plan_date=date(2030, 1, 5),
            target_tdee=2000.0,
            nutrition=NutritionDistribution(carbohydrates_g=100.0, protein_g=100.0, fat_g=30.0, total_calories=2000.0),
        )
        daily_repo.create(prev_week_plan)

        week_plans = daily_repo.find_plans_for_week(1, week_start)
        assert len(week_plans) == 7
        # 应按日期排序
        assert week_plans[0].plan_date == week_start
        assert week_plans[6].plan_date == week_start + timedelta(days=6)

    def test_create_or_update(self, daily_repo, sample_daily_plan):
        """测试创建或更新每日计划"""
        # 首次创建
        created = daily_repo.create_or_update(sample_daily_plan)
        assert created.id is not None
        original_id = created.id

        # 更新现有计划
        updated_plan = DailyNutritionPlan(
            user_id=1,
            plan_date=date(2030, 1, 1),
            target_tdee=2000.0,
            nutrition=NutritionDistribution(carbohydrates_g=250.0, protein_g=180.0, fat_g=60.0, total_calories=2000.0),
            is_adjusted=True,
            notes="更新后的计划",
        )
        updated = daily_repo.create_or_update(updated_plan)
        assert updated.id == original_id
        assert updated.nutrition.carbohydrates_g == 250.0
        assert updated.is_adjusted is True

    def test_find_by_user_id_weekly(self, weekly_repo, sample_weekly_plan):
        """测试根据用户ID查找每周计划"""
        # 创建多个每周计划
        plan1 = sample_weekly_plan
        plan2 = WeeklyNutritionPlan(
            user_id=1,
            week_start_date=date(2030, 1, 8),
            week_end_date=date(2030, 1, 14),
            daily_plans=[],
            total_carbohydrates_g=1500.0,
            total_protein_g=1100.0,
            total_fat_g=400.0,
        )
        plan3 = WeeklyNutritionPlan(
            user_id=2,
            week_start_date=date(2030, 1, 1),
            week_end_date=date(2030, 1, 7),
            daily_plans=[],
            total_carbohydrates_g=1600.0,
            total_protein_g=1200.0,
            total_fat_g=450.0,
        )

        weekly_repo.create(plan1)
        weekly_repo.create(plan2)
        weekly_repo.create(plan3)

        # 查找用户1的计划
        user1_plans = weekly_repo.find_by_user_id(1)
        assert len(user1_plans) == 2
        # 应按周开始日期倒序排列
        assert user1_plans[0].week_start_date == date(2030, 1, 8)
        assert user1_plans[1].week_start_date == date(2030, 1, 1)

    def test_find_by_user_and_week(self, weekly_repo, sample_weekly_plan):
        """测试查找用户指定周的每周计划"""
        created = weekly_repo.create(sample_weekly_plan)

        found = weekly_repo.find_by_user_and_week(1, date(2030, 1, 1))
        assert found is not None
        assert found.id == created.id

        # 不存在的周
        not_found = weekly_repo.find_by_user_and_week(1, date(2030, 1, 8))
        assert not_found is None

    def test_find_latest_by_user_id(self, weekly_repo, sample_weekly_plan):
        """测试查找用户最新的每周计划"""
        # 创建多个每周计划，按日期排序
        plan1 = sample_weekly_plan  # 2030-01-01
        plan2 = WeeklyNutritionPlan(
            user_id=1,
            week_start_date=date(2030, 2, 1),  # 更晚的日期
            week_end_date=date(2030, 2, 7),
            daily_plans=[],
            total_carbohydrates_g=1500.0,
            total_protein_g=1100.0,
            total_fat_g=400.0,
        )

        weekly_repo.create(plan1)
        weekly_repo.create(plan2)

        latest = weekly_repo.find_latest_by_user_id(1)
        assert latest is not None
        assert latest.week_start_date == date(2030, 2, 1)

        # 不存在的用户
        no_plan = weekly_repo.find_latest_by_user_id(999)
        assert no_plan is None

    def test_create_from_daily_plans(self, daily_repo, weekly_repo):
        """测试从每日计划创建每周计划"""
        week_start = date(2030, 1, 6)
        
        # 创建一周的每日计划
        daily_plans = []
        for i in range(5):  # 只创建5天，模拟不完整的一周
            plan = DailyNutritionPlan(
                user_id=1,
                plan_date=week_start + timedelta(days=i),
                target_tdee=2000.0,
                nutrition=NutritionDistribution(carbohydrates_g=200.0, protein_g=150.0, fat_g=50.0, total_calories=2000.0),
            )
            created = daily_repo.create(plan)
            daily_plans.append(created)

        # 从每日计划创建每周计划
        weekly_plan = weekly_repo.create_from_daily_plans(daily_repo, 1, week_start)
        assert weekly_plan is not None
        assert weekly_plan.user_id == 1
        assert weekly_plan.week_start_date == week_start
        assert weekly_plan.week_end_date == week_start + timedelta(days=4)
        assert weekly_plan.total_carbohydrates_g == 1000.0  # 200 * 5
        assert weekly_plan.total_protein_g == 750.0  # 150 * 5
        assert weekly_plan.total_fat_g == 250.0  # 50 * 5

        # 测试没有每日计划的情况
        empty_weekly = weekly_repo.create_from_daily_plans(daily_repo, 1, date(2030, 2, 1))
        assert empty_weekly is None