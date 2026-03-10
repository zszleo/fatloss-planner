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
            assert user.gender == Gender.MALE.value
            assert user.height_cm == 175.0
            assert user.initial_weight_kg == 70.0
            assert user.activity_level == ActivityLevel.MODERATE.value

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

        # 先生成几天的营养计划（从今天开始）
        week_start = date.today()  # 从今天开始

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
            # daily_plans may be empty if not loaded
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

    def test_generate_daily_nutrition_plan_user_not_found(self, planner_service, session):
        """测试生成每日营养计划 - 用户不存在"""
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            # 尝试为不存在的用户生成计划
            request = NutritionPlanRequest(
                user_id=999,  # 不存在的用户ID
                plan_date=date.today(),
                exercise_minutes=60.0,
            )

            with pytest.raises(ValueError, match="用户不存在: 999"):
                planner_service.generate_daily_nutrition_plan(request)

    def test_generate_daily_nutrition_plan_no_config(self, planner_service, session, sample_user_data):
        """测试生成每日营养计划 - 用户没有配置（应创建默认配置）"""
        # 创建用户但不创建配置
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork
            from src.fatloss.repository.app_config_repository import AppConfigRepository

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            user = planner_service.create_user_profile(**sample_user_data)
            planner_service.record_weight(user_id=user.id, weight_kg=70.0)

            # 删除用户的配置
            config_repo = AppConfigRepository(session)
            config = config_repo.get_by_user_id(user.id)
            if config and config.id is not None:
                config_repo.delete(config.id)

        # 生成营养计划 - 应该会创建默认配置
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            request = NutritionPlanRequest(
                user_id=user.id,
                plan_date=date.today(),
                exercise_minutes=60.0,
            )

            daily_plan = planner_service.generate_daily_nutrition_plan(request)
            assert daily_plan is not None
            # 验证计划生成成功，表明默认配置已创建

    def test_generate_daily_nutrition_plan_no_weight_record(self, planner_service, session, sample_user_data):
        """测试生成每日营养计划 - 用户没有体重记录"""
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork
            from src.fatloss.repository.weight_repository import WeightRepository

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            # 创建用户（这会创建初始体重记录）
            user = planner_service.create_user_profile(**sample_user_data)
            
            # 删除体重记录
            weight_repo = WeightRepository(session)
            weights = weight_repo.find_by_user_id(user.id)
            for weight in weights:
                if weight.id is not None:
                    weight_repo.delete(weight.id)

            # 尝试生成营养计划 - 应该失败
            request = NutritionPlanRequest(
                user_id=user.id,
                plan_date=date.today(),
                exercise_minutes=60.0,
            )

            with pytest.raises(ValueError, match=f"用户没有体重记录: {user.id}"):
                planner_service.generate_daily_nutrition_plan(request)

    def test_generate_weekly_nutrition_plan_existing(self, planner_service, session, sample_user_data):
        """测试生成每周营养计划 - 已存在周计划"""
        # 创建用户并记录体重
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            user = planner_service.create_user_profile(**sample_user_data)
            planner_service.record_weight(user_id=user.id, weight_kg=70.0)

        week_start = date.today()

        # 先生成一个周计划
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            # 生成几天的计划
            for day_offset in range(3):
                request = NutritionPlanRequest(
                    user_id=user.id,
                    plan_date=week_start + timedelta(days=day_offset),
                    exercise_minutes=60.0,
                )
                planner_service.generate_daily_nutrition_plan(request)

            # 生成周计划
            weekly_plan1 = planner_service.generate_weekly_nutrition_plan(
                user_id=user.id, week_start_date=week_start
            )
            assert weekly_plan1 is not None

        # 再次生成同周计划 - 应该返回现有的
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            weekly_plan2 = planner_service.generate_weekly_nutrition_plan(
                user_id=user.id, week_start_date=week_start
            )
            assert weekly_plan2 is not None
            assert weekly_plan2.id == weekly_plan1.id  # 应该是同一个计划

    def test_generate_weekly_nutrition_plan_exception_handling(self, planner_service, session, sample_user_data):
        """测试生成每周营养计划 - 处理生成异常"""
        # 创建用户并记录体重
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            user = planner_service.create_user_profile(**sample_user_data)
            planner_service.record_weight(user_id=user.id, weight_kg=70.0)

        week_start = date.today()

        # 模拟 generate_daily_nutrition_plan 在某些天抛出异常
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork
            from unittest.mock import MagicMock

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            # 创建一个模拟的 planner_service，让 generate_daily_nutrition_plan 在某些天失败
            original_generate = planner_service.generate_daily_nutrition_plan
            
            call_count = 0
            def mock_generate(request):
                nonlocal call_count
                call_count += 1
                # 让第2天和第4天失败
                if call_count in [2, 4]:
                    raise ValueError("模拟失败")
                return original_generate(request)
            
            planner_service.generate_daily_nutrition_plan = MagicMock(side_effect=mock_generate)

            # 生成周计划 - 应该处理异常并继续
            weekly_plan = planner_service.generate_weekly_nutrition_plan(
                user_id=user.id, week_start_date=week_start
            )
            
            # 即使有些天失败，周计划可能仍然生成（如果有其他成功的天）
            # 这里我们主要测试异常处理分支，不关心最终结果
            assert planner_service.generate_daily_nutrition_plan.call_count > 0

    def test_generate_weekly_nutrition_plan_no_daily_plans(self, planner_service, session, sample_user_data):
        """测试生成每周营养计划 - 没有任何日计划"""
        # 创建用户并记录体重
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            user = planner_service.create_user_profile(**sample_user_data)
            planner_service.record_weight(user_id=user.id, weight_kg=70.0)

        week_start = date.today()

        # 模拟 generate_daily_nutrition_plan 在所有天都失败
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork
            from unittest.mock import MagicMock

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            # 让 generate_daily_nutrition_plan 在所有天都抛出异常
            planner_service.generate_daily_nutrition_plan = MagicMock(side_effect=ValueError("模拟失败"))

            # 生成周计划 - 应该返回None
            weekly_plan = planner_service.generate_weekly_nutrition_plan(
                user_id=user.id, week_start_date=week_start
            )
            
            assert weekly_plan is None

    def test_calculate_weight_loss_progress_no_weight_record(self, planner_service, session, sample_user_data):
        """测试计算减脂进度 - 没有体重记录"""
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork
            from src.fatloss.repository.weight_repository import WeightRepository

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            # 创建用户（这会创建初始体重记录）
            user = planner_service.create_user_profile(**sample_user_data)
            
            # 删除体重记录
            weight_repo = WeightRepository(session)
            weights = weight_repo.find_by_user_id(user.id)
            for weight in weights:
                if weight.id is not None:
                    weight_repo.delete(weight.id)

            # 尝试计算进度 - 应该失败
            with pytest.raises(ValueError, match=f"用户没有体重记录: {user.id}"):
                planner_service.calculate_weight_loss_progress(
                    user_id=user.id, target_weight_kg=65.0
                )

    def test_calculate_weight_loss_progress_no_config(self, planner_service, session, sample_user_data):
        """测试计算减脂进度 - 用户没有配置（应创建默认配置）"""
        # 创建用户并记录体重
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork
            from src.fatloss.repository.app_config_repository import AppConfigRepository

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            user = planner_service.create_user_profile(**sample_user_data)
            planner_service.record_weight(user_id=user.id, weight_kg=70.0)

            # 删除用户的配置
            config_repo = AppConfigRepository(session)
            config = config_repo.get_by_user_id(user.id)
            if config and config.id is not None:
                config_repo.delete(config.id)

        # 计算进度 - 应该会创建默认配置
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            progress = planner_service.calculate_weight_loss_progress(
                user_id=user.id, target_weight_kg=65.0
            )

            assert progress is not None
            assert progress.user_id == user.id
            assert progress.current_weight_kg == 70.0
            assert progress.target_weight_kg == 65.0

    def test_calculate_weight_loss_progress_target_reached(self, planner_service, session, sample_user_data):
        """测试计算减脂进度 - 目标已达成（当前体重≤目标体重）"""
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork
            from unittest.mock import patch as mock_patch
            from src.fatloss.calculator.time_predictor import WeightLossPrediction

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            user = planner_service.create_user_profile(**sample_user_data)
            
            # 模拟 predict_weight_loss_time 返回一个预测，避免抛出异常
            with mock_patch("src.fatloss.planner.planner_service.predict_weight_loss_time") as mock_predict:
                # 创建模拟预测
                mock_prediction = WeightLossPrediction(
                    total_loss_kg=0.0,
                    monthly_loss_kg=0.0,
                    weekly_loss_kg=0.0,
                    estimated_months=0.0,
                    estimated_weeks=0.0
                )
                mock_predict.return_value = mock_prediction
                
                # 目标体重等于当前体重，触发total_loss_needed <= 0分支
                progress = planner_service.calculate_weight_loss_progress(
                    user_id=user.id, target_weight_kg=70.0  # 目标体重等于当前体重
                )

                assert progress.progress_percentage == 100.0

    def test_calculate_weight_loss_progress_with_previous_weight(self, planner_service, session, sample_user_data):
        """测试计算减脂进度 - 有前次体重记录（应计算调整）"""
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            user = planner_service.create_user_profile(**sample_user_data)
            
            # 记录两次体重（间隔一周）
            today = date.today()
            one_week_ago = today - timedelta(days=7)
            
            planner_service.record_weight(
                user_id=user.id, weight_kg=71.0, record_date=one_week_ago
            )
            planner_service.record_weight(
                user_id=user.id, weight_kg=70.0, record_date=today
            )

            # 计算进度
            progress = planner_service.calculate_weight_loss_progress(
                user_id=user.id, target_weight_kg=65.0
            )

            assert progress is not None
            assert progress.user_id == user.id
            # 应该计算了weekly_adjustment_needed
            assert isinstance(progress.weekly_adjustment_needed, int)

    def test_get_weekly_adjustment_recommendation_no_weight(self, planner_service, session, sample_user_data):
        """测试获取每周调整建议 - 没有体重记录"""
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork
            from src.fatloss.repository.weight_repository import WeightRepository

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            # 创建用户（这会创建初始体重记录）
            user = planner_service.create_user_profile(**sample_user_data)
            
            # 删除体重记录
            weight_repo = WeightRepository(session)
            weights = weight_repo.find_by_user_id(user.id)
            for weight in weights:
                if weight.id is not None:
                    weight_repo.delete(weight.id)

            # 获取调整建议 - 应该返回需要先记录体重
            adjustment, message = planner_service.get_weekly_adjustment_recommendation(
                user_id=user.id
            )

            assert adjustment == 0
            assert "需要先记录体重" in message

    def test_get_weekly_adjustment_recommendation_only_one_weight(self, planner_service, session, sample_user_data):
        """测试获取每周调整建议 - 只有一次体重记录"""
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            # 创建用户并记录一次体重
            user = planner_service.create_user_profile(**sample_user_data)
            planner_service.record_weight(user_id=user.id, weight_kg=70.0)

            # 获取调整建议 - 应该返回需要至少两次体重记录
            adjustment, message = planner_service.get_weekly_adjustment_recommendation(
                user_id=user.id
            )

            assert adjustment == 0
            assert "需要至少两次体重记录" in message

    def test_get_weekly_adjustment_recommendation_no_config(self, planner_service, session, sample_user_data):
        """测试获取每周调整建议 - 用户没有配置（应创建默认配置）"""
        # 创建用户并记录两次体重
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork
            from src.fatloss.repository.app_config_repository import AppConfigRepository

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            user = planner_service.create_user_profile(**sample_user_data)
            
            # 记录两次体重（间隔一周）
            today = date.today()
            one_week_ago = today - timedelta(days=7)
            
            planner_service.record_weight(
                user_id=user.id, weight_kg=71.0, record_date=one_week_ago
            )
            planner_service.record_weight(
                user_id=user.id, weight_kg=70.0, record_date=today
            )

            # 删除用户的配置
            config_repo = AppConfigRepository(session)
            config = config_repo.get_by_user_id(user.id)
            if config and config.id is not None:
                config_repo.delete(config.id)

        # 获取调整建议 - 应该会创建默认配置
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            adjustment, message = planner_service.get_weekly_adjustment_recommendation(
                user_id=user.id
            )

            assert isinstance(adjustment, int)
            assert isinstance(message, str)
            # 应该成功返回建议，表明默认配置已创建

    def test_get_weekly_adjustment_recommendation_adjustment_positive(self, planner_service, session, sample_user_data):
        """测试获取每周调整建议 - 调整>0（体重下降过快）"""
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork
            from src.fatloss.repository.app_config_repository import AppConfigRepository
            from src.fatloss.models.app_config import AppConfig as AppConfigModel

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            user = planner_service.create_user_profile(**sample_user_data)
            
            # 修改配置，设置月减重百分比为5%（0.05）
            config_repo = AppConfigRepository(session)
            config = config_repo.get_by_user_id(user.id)
            if config:
                config.monthly_loss_percentage = 5.0  # 5%
                session.commit()
            
            # 记录两次体重：实际减重1.5kg，预期减重约0.875kg（70 * 0.05 / 4）
            today = date.today()
            one_week_ago = today - timedelta(days=7)
            
            # 当前体重70kg，一周前体重71.5kg，实际减重1.5kg
            planner_service.record_weight(
                user_id=user.id, weight_kg=71.5, record_date=one_week_ago
            )
            planner_service.record_weight(
                user_id=user.id, weight_kg=70.0, record_date=today
            )

            # 获取调整建议 - 应该返回adjustment > 0
            adjustment, message = planner_service.get_weekly_adjustment_recommendation(
                user_id=user.id
            )

            assert adjustment > 0
            assert "增加碳水摄入" in message

    def test_get_weekly_adjustment_recommendation_adjustment_negative(self, planner_service, session, sample_user_data):
        """测试获取每周调整建议 - 调整<0（体重下降过慢）"""
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork
            from src.fatloss.repository.app_config_repository import AppConfigRepository

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            user = planner_service.create_user_profile(**sample_user_data)
            
            # 修改配置，设置月减重百分比为5%（0.05）
            config_repo = AppConfigRepository(session)
            config = config_repo.get_by_user_id(user.id)
            if config:
                config.monthly_loss_percentage = 5.0  # 5%
                session.commit()
            
            # 记录两次体重：实际减重0.2kg，预期减重约0.875kg（70 * 0.05 / 4）
            today = date.today()
            one_week_ago = today - timedelta(days=7)
            
            # 当前体重70kg，一周前体重70.2kg，实际减重0.2kg
            planner_service.record_weight(
                user_id=user.id, weight_kg=70.2, record_date=one_week_ago
            )
            planner_service.record_weight(
                user_id=user.id, weight_kg=70.0, record_date=today
            )

            # 获取调整建议 - 应该返回adjustment < 0
            adjustment, message = planner_service.get_weekly_adjustment_recommendation(
                user_id=user.id
            )

            assert adjustment < 0
            assert "减少碳水摄入" in message

    def test_get_user_summary_user_not_found(self, planner_service, session):
        """测试获取用户摘要 - 用户不存在"""
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            # 尝试获取不存在的用户的摘要
            with pytest.raises(ValueError, match="用户不存在: 999"):
                planner_service.get_user_summary(user_id=999)

    def test_get_user_summary_no_weight_record(self, planner_service, session, sample_user_data):
        """测试获取用户摘要 - 没有体重记录"""
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork
            from src.fatloss.repository.weight_repository import WeightRepository

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            # 创建用户（这会创建初始体重记录）
            user = planner_service.create_user_profile(**sample_user_data)
            
            # 删除体重记录
            weight_repo = WeightRepository(session)
            weights = weight_repo.find_by_user_id(user.id)
            for weight in weights:
                if weight.id is not None:
                    weight_repo.delete(weight.id)

            # 获取摘要
            summary = planner_service.get_user_summary(user_id=user.id)

            assert "user" in summary
            assert summary["user"].id == user.id
            assert summary["latest_weight"] is None
            assert summary["bmr"] == 0.0
            assert summary["tdee"] == 0.0
            assert summary["nutrition"] is None

    def test_calculate_weight_loss_progress_zero_progress(self, planner_service, session, sample_user_data):
        """测试计算减脂进度 - 进度为0（用户不存在或初始体重≤目标体重）"""
        with patch("src.fatloss.planner.planner_service.unit_of_work") as mock_uow:
            from src.fatloss.repository.unit_of_work import UnitOfWork
            from unittest.mock import patch as mock_patch
            from src.fatloss.calculator.time_predictor import WeightLossPrediction

            uow = UnitOfWork(session)
            mock_uow.return_value.__enter__.return_value = uow

            user = planner_service.create_user_profile(**sample_user_data)
            planner_service.record_weight(user_id=user.id, weight_kg=70.0)
            
            # 模拟 predict_weight_loss_time 返回预测
            with mock_patch("src.fatloss.planner.planner_service.predict_weight_loss_time") as mock_predict:
                mock_prediction = WeightLossPrediction(
                    total_loss_kg=5.0,
                    monthly_loss_kg=3.5,
                    weekly_loss_kg=0.875,
                    estimated_months=1.428,
                    estimated_weeks=5.714
                )
                mock_predict.return_value = mock_prediction
                
                # 模拟 uow.users.get_by_id 返回 None，触发进度为0分支
                with mock_patch.object(uow.users, 'get_by_id', return_value=None):
                    progress = planner_service.calculate_weight_loss_progress(
                        user_id=user.id, target_weight_kg=65.0
                    )
                    
                    assert progress.progress_percentage == 0.0
