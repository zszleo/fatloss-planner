"""PlannerService集成测试"""

from datetime import date, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.fatloss.calculator.bmr_calculator import Gender
from src.fatloss.models.user_profile import ActivityLevel
from src.fatloss.planner.planner_service import PlannerService, NutritionPlanRequest
from src.fatloss.repository import init_database
from src.fatloss.repository.unit_of_work import unit_of_work


class TestPlannerServiceIntegration:
    """PlannerService集成测试类"""

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
    def planner_service(self, session):
        """创建PlannerService并配置为使用测试会话"""
        # 创建一个新的PlannerService实例
        service = PlannerService()

        # 创建一个monkey patch来使unit_of_work使用我们的会话
        # 我们将在每个测试中手动应用patch，或者在这里创建但让测试使用
        # 这里我们返回service，测试函数将应用patch
        return service

    @pytest.fixture
    def sample_user_data(self):
        """创建测试用户数据"""
        return {
            "name": "测试用户",
            "gender": Gender.MALE,
            "birth_date": date(1990, 1, 1),
            "height_cm": 175.0,
            "initial_weight_kg": 70.0,
            "activity_level": ActivityLevel.MODERATE,
        }

    def test_create_user_profile(self, planner_service, session, sample_user_data):
        """测试创建用户档案"""
        # Patch unit_of_work to use our session
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            # Configure mock to use our session
            from src.fatloss.repository.unit_of_work import UnitOfWork

            mock_uow.return_value.__enter__.return_value = UnitOfWork(session)

            user = planner_service.create_user_profile(**sample_user_data)

            assert user.id is not None
            assert user.name == "测试用户"
            assert user.gender == Gender.MALE
            assert user.height_cm == 175.0
            assert user.initial_weight_kg == 70.0
            assert user.activity_level == ActivityLevel.MODERATE

    def test_record_weight(self, planner_service, session, sample_user_data):
        """测试记录体重"""
        # 先创建用户
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            mock_uow.return_value.__enter__.return_value = UnitOfWork(session)

            user = planner_service.create_user_profile(**sample_user_data)

        # 记录体重
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            mock_uow.return_value.__enter__.return_value = UnitOfWork(session)

            weight_record = planner_service.record_weight(
                user_id=user.id,
                weight_kg=69.5,
                record_date=date.today(),
                notes="测试体重记录",
            )

            assert weight_record.id is not None
            assert weight_record.user_id == user.id
            assert weight_record.weight_kg == 69.5
            assert weight_record.record_date == date.today()
            assert weight_record.notes == "测试体重记录"

    def test_generate_daily_nutrition_plan(
        self, planner_service, session, sample_user_data
    ):
        """测试生成每日营养计划"""
        # 创建用户并记录体重
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            user = planner_service.create_user_profile(**sample_user_data)
            planner_service.record_weight(user_id=user.id, weight_kg=70.0)

        # 生成营养计划
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            request = NutritionPlanRequest(
                user_id=user.id,
                plan_date=date.today(),
                exercise_minutes=60.0,
                adjustment_units=0,
            )

            daily_plan = planner_service.generate_daily_nutrition_plan(request)

            assert daily_plan.id is not None
            assert daily_plan.user_id == user.id
            assert daily_plan.plan_date == date.today()
            assert daily_plan.target_tdee > 0
            assert daily_plan.nutrition is not None
            assert daily_plan.nutrition.carbohydrates_g > 0
            assert daily_plan.nutrition.protein_g > 0
            assert daily_plan.nutrition.fat_g > 0

    def test_generate_daily_nutrition_plan_with_adjustment(
        self, planner_service, session, sample_user_data
    ):
        """测试生成带有调整的每日营养计划"""
        # 创建用户并记录体重
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            user = planner_service.create_user_profile(**sample_user_data)
            planner_service.record_weight(user_id=user.id, weight_kg=70.0)

        # 生成带调整的营养计划
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            request = NutritionPlanRequest(
                user_id=user.id,
                plan_date=date.today(),
                exercise_minutes=60.0,
                adjustment_units=1,  # 增加碳水
            )

            daily_plan = planner_service.generate_daily_nutrition_plan(request)

            assert daily_plan.is_adjusted == True
            assert daily_plan.adjustment_units == 1

    def test_generate_weekly_nutrition_plan(
        self, planner_service, session, sample_user_data
    ):
        """测试生成每周营养计划"""
        # 创建用户并记录体重
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            user = planner_service.create_user_profile(**sample_user_data)
            planner_service.record_weight(user_id=user.id, weight_kg=70.0)

        # 先生成几天的营养计划
        week_start = date.today() - timedelta(days=date.today().weekday())  # 本周一

        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            for day_offset in range(3):  # 生成3天的计划
                request = NutritionPlanRequest(
                    user_id=user.id,
                    plan_date=week_start + timedelta(days=day_offset),
                    exercise_minutes=60.0,
                )
                planner_service.generate_daily_nutrition_plan(request)

        # 生成每周计划
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            weekly_plan = planner_service.generate_weekly_nutrition_plan(
                user_id=user.id, week_start_date=week_start
            )

            assert weekly_plan is not None
            assert weekly_plan.user_id == user.id
            assert weekly_plan.week_start_date == week_start
            assert len(weekly_plan.daily_plans) >= 1
            assert weekly_plan.total_carbohydrates_g > 0
            assert weekly_plan.total_protein_g > 0
            assert weekly_plan.total_fat_g > 0

    def test_calculate_weight_loss_progress(
        self, planner_service, session, sample_user_data
    ):
        """测试计算减脂进度"""
        # 创建用户并记录体重
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            user = planner_service.create_user_profile(**sample_user_data)
            planner_service.record_weight(user_id=user.id, weight_kg=70.0)

        # 计算进度（目标体重65kg）
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            progress = planner_service.calculate_weight_loss_progress(
                user_id=user.id, target_weight_kg=65.0
            )

            assert progress.user_id == user.id
            assert progress.current_weight_kg == 70.0
            assert progress.target_weight_kg == 65.0
            assert progress.total_loss_kg == 5.0
            assert 0 <= progress.progress_percentage <= 100
            assert progress.estimated_completion_date is not None
            assert isinstance(progress.weekly_adjustment_needed, int)

    def test_get_weekly_adjustment_recommendation(
        self, planner_service, session, sample_user_data
    ):
        """测试获取每周调整建议"""
        # 创建用户并记录两次体重（间隔一周）
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            user = planner_service.create_user_profile(**sample_user_data)
            today = date.today()
            one_week_ago = today - timedelta(days=7)

            planner_service.record_weight(
                user_id=user.id, weight_kg=71.0, record_date=one_week_ago
            )
            planner_service.record_weight(
                user_id=user.id, weight_kg=70.0, record_date=today
            )

        # 获取调整建议
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            adjustment, message = planner_service.get_weekly_adjustment_recommendation(
                user_id=user.id
            )

            assert isinstance(adjustment, int)
            assert isinstance(message, str)
            assert len(message) > 0

    def test_get_user_summary(self, planner_service, session, sample_user_data):
        """测试获取用户摘要"""
        # 创建用户并记录体重
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            user = planner_service.create_user_profile(**sample_user_data)
            planner_service.record_weight(user_id=user.id, weight_kg=70.0)

            # 生成营养计划
            request = NutritionPlanRequest(
                user_id=user.id, plan_date=date.today(), exercise_minutes=60.0
            )
            planner_service.generate_daily_nutrition_plan(request)

        # 获取用户摘要
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            summary = planner_service.get_user_summary(user_id=user.id)

            assert "user" in summary
            assert summary["user"].id == user.id
            assert "latest_weight" in summary
            assert summary["latest_weight"].weight_kg == 70.0
            assert "bmr" in summary
            assert "tdee" in summary
            assert "nutrition" in summary
            assert "latest_daily_plan" in summary
