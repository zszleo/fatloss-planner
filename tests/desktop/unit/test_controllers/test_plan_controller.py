"""PlanController单元测试。

测试计划管理控制器的业务逻辑和数据处理。
"""

from datetime import date, timedelta
from unittest.mock import Mock, MagicMock, patch
import pytest

from fatloss.desktop.controllers.plan_controller import PlanController
from fatloss.models.user_profile import UserProfile, Gender, ActivityLevel
from fatloss.models.nutrition_plan import DailyNutritionPlan, WeeklyNutritionPlan
from fatloss.calculator.nutrition_calculator import NutritionDistribution
from tests.desktop.factories import TestDataFactory


class TestPlanController:
    """PlanController单元测试类"""

    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker):
        """自动设置模拟，避免GUI调用和数据库访问"""
        # 模拟ErrorHandler (必须在PlanController模块中模拟，因为它是直接导入的)
        self.mock_error_handler = mocker.patch(
            "fatloss.desktop.controllers.plan_controller.ErrorHandler"
        )
        self.mock_error_handler.handle_service_error = mocker.Mock()
        self.mock_error_handler.show_success = mocker.Mock()
        self.mock_error_handler.show_warning = mocker.Mock()

        # 模拟unit_of_work
        self.mock_unit_of_work = mocker.patch(
            "fatloss.desktop.controllers.plan_controller.unit_of_work"
        )
        mock_uow = MagicMock()
        mock_uow.__enter__.return_value = mock_uow
        mock_uow.__exit__.return_value = None

        # 模拟每日营养计划仓库
        mock_daily_nutrition = MagicMock()
        mock_daily_nutrition.find_by_user_and_date.return_value = None
        mock_daily_nutrition.find_by_user_id.return_value = []
        mock_uow.daily_nutrition = mock_daily_nutrition

        # 模拟每周营养计划仓库
        mock_weekly_nutrition = MagicMock()
        mock_weekly_nutrition.find_by_user_and_week.return_value = None
        mock_weekly_nutrition.find_by_user_id.return_value = []
        mock_uow.weekly_nutrition = mock_weekly_nutrition

        # 模拟用户仓库
        mock_users = MagicMock()
        mock_users.get_by_id.return_value = None
        mock_users.get_all.return_value = []
        mock_uow.users = mock_users

        self.mock_unit_of_work.return_value = mock_uow

    @pytest.fixture
    def mock_planner_service(self):
        """模拟PlannerService依赖"""
        service = Mock()
        service.generate_weekly_nutrition_plan.return_value = None
        service.generate_daily_nutrition_plan.return_value = None
        service.database_url = "sqlite:///:memory:"
        return service

    @pytest.fixture
    def plan_controller(self, mock_planner_service):
        """创建PlanController实例"""
        return PlanController(planner_service=mock_planner_service)

    @pytest.fixture
    def sample_daily_plan(self):
        """创建示例每日营养计划"""
        return TestDataFactory.create_nutrition_plan(user_id=1)

    @pytest.fixture
    def sample_weekly_plan(self, sample_daily_plan):
        """创建示例周营养计划"""
        from fatloss.models.nutrition_plan import WeeklyNutritionPlan

        week_start = date.today() - timedelta(days=date.today().weekday())
        week_end = week_start + timedelta(days=6)

        return WeeklyNutritionPlan(
            user_id=1,
            week_start_date=week_start,
            week_end_date=week_end,
            daily_plans=[sample_daily_plan],
            total_carbohydrates_g=1050.0,
            total_protein_g=840.0,
            total_fat_g=350.0,
            notes="测试周计划",
        )

    # Tests for get_weekly_plan
    def test_get_weekly_plan_success(
        self, plan_controller, mock_planner_service, sample_weekly_plan
    ):
        """测试成功获取周计划"""
        # 准备
        user_id = 1
        week_start = date.today() - timedelta(days=date.today().weekday())
        mock_planner_service.generate_weekly_nutrition_plan.return_value = (
            sample_weekly_plan
        )

        # 执行
        result = plan_controller.get_weekly_plan(user_id, week_start)

        # 验证
        assert result == sample_weekly_plan
        mock_planner_service.generate_weekly_nutrition_plan.assert_called_once_with(
            user_id=user_id, week_start_date=week_start
        )

    def test_get_weekly_plan_not_found(self, plan_controller, mock_planner_service):
        """测试获取周计划失败（未找到）"""
        # 准备
        user_id = 1
        week_start = date.today() - timedelta(days=date.today().weekday())
        mock_planner_service.generate_weekly_nutrition_plan.return_value = None

        # 执行
        result = plan_controller.get_weekly_plan(user_id, week_start)

        # 验证
        assert result is None

    def test_get_weekly_plan_exception(self, plan_controller, mock_planner_service):
        """测试获取周计划时异常"""
        # 准备
        user_id = 1
        week_start = date.today() - timedelta(days=date.today().weekday())
        mock_planner_service.generate_weekly_nutrition_plan.side_effect = Exception(
            "Database error"
        )

        # 执行
        result = plan_controller.get_weekly_plan(user_id, week_start)

        # 验证
        assert result is None

    # Tests for generate_weekly_plan
    def test_generate_weekly_plan_success(
        self, plan_controller, mock_planner_service, sample_weekly_plan
    ):
        """测试成功生成周计划（无现有计划）"""
        # 准备
        user_id = 1
        week_start = date.today() - timedelta(days=date.today().weekday())
        mock_planner_service.generate_weekly_nutrition_plan.return_value = (
            sample_weekly_plan
        )

        # 执行
        result = plan_controller.generate_weekly_plan(user_id, week_start)

        # 验证
        assert result == sample_weekly_plan
        mock_planner_service.generate_weekly_nutrition_plan.assert_called_once_with(
            user_id=user_id, week_start_date=week_start
        )
        self.mock_error_handler.show_success.assert_called_once()

    def test_generate_weekly_plan_with_existing_plans(
        self, plan_controller, mock_planner_service, sample_weekly_plan
    ):
        """测试强制生成周营养计划时删除现有计划"""
        # 准备
        user_id = 1
        week_start = date(2025, 1, 6)  # 周一

        # 模拟现有每日计划
        existing_daily = MagicMock()
        existing_daily.id = 101
        self.mock_unit_of_work.return_value.daily_nutrition.find_by_user_and_date.return_value = (
            existing_daily
        )

        # 模拟现有周计划
        existing_weekly = MagicMock()
        existing_weekly.id = 201
        self.mock_unit_of_work.return_value.weekly_nutrition.find_by_user_and_week.return_value = (
            existing_weekly
        )

        mock_planner_service.generate_weekly_nutrition_plan.return_value = (
            sample_weekly_plan
        )

        # 执行
        result = plan_controller.generate_weekly_plan(user_id, week_start)

        # 验证
        assert result == sample_weekly_plan
        # 验证删除了现有计划
        self.mock_unit_of_work.return_value.daily_nutrition.delete.assert_called()
        self.mock_unit_of_work.return_value.weekly_nutrition.delete.assert_called()
        self.mock_unit_of_work.return_value.commit.assert_called()
        mock_planner_service.generate_weekly_nutrition_plan.assert_called_once()
        self.mock_error_handler.show_success.assert_called_once()

    def test_generate_weekly_plan_failure(self, plan_controller, mock_planner_service):
        """测试生成周计划失败"""
        # 准备
        user_id = 1
        week_start = date.today() - timedelta(days=date.today().weekday())
        mock_planner_service.generate_weekly_nutrition_plan.return_value = None

        # 执行
        result = plan_controller.generate_weekly_plan(user_id, week_start)

        # 验证
        assert result is None

    def test_generate_weekly_plan_exception(
        self, plan_controller, mock_planner_service
    ):
        """测试生成周计划时异常"""
        # 准备
        user_id = 1
        week_start = date.today() - timedelta(days=date.today().weekday())
        mock_planner_service.generate_weekly_nutrition_plan.side_effect = Exception(
            "Database error"
        )

        # 执行
        result = plan_controller.generate_weekly_plan(user_id, week_start)

        # 验证
        assert result is None

    # Tests for update_daily_plan
    def test_update_daily_plan_success(
        self, plan_controller, mock_planner_service, sample_daily_plan
    ):
        """测试成功更新每日计划"""
        # 准备
        user_id = 1
        plan_date = date.today()
        exercise_minutes = 60
        adjustment_units = 0
        mock_planner_service.generate_daily_nutrition_plan.return_value = (
            sample_daily_plan
        )

        # 执行
        result = plan_controller.update_daily_plan(
            user_id, plan_date, exercise_minutes, adjustment_units
        )

        # 验证
        assert result == sample_daily_plan
        mock_planner_service.generate_daily_nutrition_plan.assert_called_once()

    def test_update_daily_plan_validation_error(
        self, plan_controller, mock_planner_service
    ):
        """测试更新每日计划时验证错误"""
        # 执行
        result = plan_controller.update_daily_plan(
            user_id=1,
            plan_date=date.today(),
            exercise_minutes=400,  # 超过最大值
            adjustment_units=0,
        )

        # 验证
        assert result is None

    def test_update_daily_plan_exception(self, plan_controller, mock_planner_service):
        """测试更新每日计划时异常"""
        # 准备
        mock_planner_service.generate_daily_nutrition_plan.side_effect = Exception(
            "Database error"
        )

        # 执行
        result = plan_controller.update_daily_plan(
            user_id=1, plan_date=date.today(), exercise_minutes=60, adjustment_units=0
        )

        # 验证
        assert result is None

    # Tests for get_user_by_id
    def test_get_user_by_id_success(self, plan_controller):
        """测试成功获取用户"""
        # 准备
        user = TestDataFactory.create_user_profile(id=1)
        self.mock_unit_of_work.return_value.users.get_by_id.return_value = user

        # 执行
        result = plan_controller.get_user_by_id(1)

        # 验证
        assert result == user

    def test_get_user_by_id_not_found(self, plan_controller):
        """测试获取不存在的用户"""
        # 准备
        self.mock_unit_of_work.return_value.users.get_by_id.return_value = None

        # 执行
        result = plan_controller.get_user_by_id(999)

        # 验证
        assert result is None

    def test_get_user_by_id_exception(self, plan_controller):
        """测试获取用户时异常"""
        # 准备
        self.mock_unit_of_work.return_value.users.get_by_id.side_effect = Exception(
            "Database error"
        )

        # 执行
        result = plan_controller.get_user_by_id(1)

        # 验证
        assert result is None

    # Tests for get_all_users
    def test_get_all_users_success(self, plan_controller):
        """测试成功获取所有用户"""
        # 准备
        users = [
            TestDataFactory.create_user_profile(id=1, name="用户1"),
            TestDataFactory.create_user_profile(id=2, name="用户2"),
        ]
        self.mock_unit_of_work.return_value.users.get_all.return_value = users

        # 执行
        result = plan_controller.get_all_users()

        # 验证
        assert len(result) == 2
        assert result[0].name == "用户1"

    def test_get_all_users_empty(self, plan_controller):
        """测试获取空用户列表"""
        # 准备
        self.mock_unit_of_work.return_value.users.get_all.return_value = []

        # 执行
        result = plan_controller.get_all_users()

        # 验证
        assert len(result) == 0

    def test_get_all_users_exception(self, plan_controller):
        """测试获取用户时异常"""
        # 准备
        self.mock_unit_of_work.return_value.users.get_all.side_effect = Exception(
            "Database error"
        )

        # 执行
        result = plan_controller.get_all_users()

        # 验证
        assert result == []

    # Tests for get_daily_plans_for_week
    def test_get_daily_plans_for_week_success(self, plan_controller, sample_daily_plan):
        """测试成功获取一周每日计划"""
        # 准备
        user_id = 1
        week_start = date(2025, 1, 6)  # 周一
        self.mock_unit_of_work.return_value.daily_nutrition.find_by_user_and_date.return_value = (
            sample_daily_plan
        )

        # 执行
        result = plan_controller.get_daily_plans_for_week(user_id, week_start)

        # 验证
        assert len(result) == 7
        assert all(plan is not None for plan in result.values())

    def test_get_daily_plans_for_week_empty(self, plan_controller):
        """测试获取一周每日计划（无计划）"""
        # 准备
        user_id = 1
        week_start = date(2025, 1, 6)
        self.mock_unit_of_work.return_value.daily_nutrition.find_by_user_and_date.return_value = (
            None
        )

        # 执行
        result = plan_controller.get_daily_plans_for_week(user_id, week_start)

        # 验证
        assert len(result) == 7
        assert all(plan is None for plan in result.values())

    def test_get_daily_plans_for_week_exception(self, plan_controller):
        """测试获取每日计划时异常"""
        # 准备
        user_id = 1
        week_start = date(2025, 1, 6)
        self.mock_unit_of_work.return_value.daily_nutrition.find_by_user_and_date.side_effect = Exception(
            "Database error"
        )

        # 执行
        result = plan_controller.get_daily_plans_for_week(user_id, week_start)

        # 验证
        assert result == {}

    # Tests for get_available_weeks
    def test_get_available_weeks_success(self, plan_controller):
        """测试成功获取可用周列表"""
        # 准备
        user_id = 1
        week_start_1 = date(2025, 1, 6)
        week_start_2 = date(2025, 1, 13)

        weekly_plans = [
            MagicMock(week_start_date=week_start_1),
            MagicMock(week_start_date=week_start_2),
        ]
        self.mock_unit_of_work.return_value.weekly_nutrition.find_by_user_id.return_value = (
            weekly_plans
        )

        # 执行
        result = plan_controller.get_available_weeks(user_id)

        # 验证
        assert len(result) == 2
        assert week_start_1 in result
        assert week_start_2 in result
        # 应该按降序排列
        assert result[0] > result[1]

    def test_get_available_weeks_empty(self, plan_controller):
        """测试获取空周列表"""
        # 准备
        user_id = 1
        self.mock_unit_of_work.return_value.weekly_nutrition.find_by_user_id.return_value = (
            []
        )

        # 执行
        result = plan_controller.get_available_weeks(user_id)

        # 验证
        assert len(result) == 0

    def test_get_available_weeks_exception(self, plan_controller):
        """测试获取周列表时异常"""
        # 准备
        user_id = 1
        self.mock_unit_of_work.return_value.weekly_nutrition.find_by_user_id.side_effect = Exception(
            "Database error"
        )

        # 执行
        result = plan_controller.get_available_weeks(user_id)

        # 验证
        assert result == []

    # Tests for format methods
    def test_format_daily_plan_summary(self, plan_controller, sample_daily_plan):
        """测试格式化每日计划摘要"""
        # 执行
        result = plan_controller.format_daily_plan_summary(sample_daily_plan)

        # 验证
        assert "日期:" in result
        assert "TDEE:" in result
        assert "蛋白质:" in result
        assert "碳水化合物:" in result
        assert "脂肪:" in result
        assert "总热量:" in result

    def test_format_daily_plan_summary_with_adjustment(
        self, plan_controller, sample_daily_plan
    ):
        """测试格式化每日计划摘要（包含调整）"""
        # 准备
        sample_daily_plan.is_adjusted = True
        sample_daily_plan.adjustment_units = 2  # 增加 60g 碳水

        # 执行
        result = plan_controller.format_daily_plan_summary(sample_daily_plan)

        # 验证
        assert "调整:" in result
        assert "增加" in result
        assert "60g" in result

    def test_format_weekly_plan_summary(self, plan_controller, sample_weekly_plan):
        """测试格式化周计划摘要"""
        # 执行
        result = plan_controller.format_weekly_plan_summary(sample_weekly_plan)

        # 验证
        assert "周计划:" in result
        assert "周总计:" in result
        assert "每日计划:" in result
        assert "碳水化合物:" in result
        assert "蛋白质:" in result
        assert "脂肪:" in result

    def test_export_weekly_plan_to_text(self, plan_controller, sample_weekly_plan):
        """测试导出周计划为文本"""
        # 执行
        result = plan_controller.export_weekly_plan_to_text(sample_weekly_plan)

        # 验证
        assert "=" * 50 in result
        assert "Fatloss Planner - 周营养计划" in result
        assert "周计划:" in result
        assert "每日营养计划:" in result

    def test_export_weekly_plan_to_text_with_adjustment(
        self, plan_controller, sample_weekly_plan
    ):
        """测试导出周计划为文本（包含调整）"""
        # 准备
        sample_weekly_plan.daily_plans[0].is_adjusted = True
        sample_weekly_plan.daily_plans[0].adjustment_units = -1  # 减少 30g 碳水

        # 执行
        result = plan_controller.export_weekly_plan_to_text(sample_weekly_plan)

        # 验证
        assert "调整:" in result
        assert "-30g" in result

    # Tests for _validate_plan_input
    def test_validate_plan_input_valid(self, plan_controller):
        """测试验证有效的计划输入"""
        # 执行和验证 - 不应抛出异常
        plan_controller._validate_plan_input(60, 0)

    def test_validate_plan_input_invalid_exercise_minutes_low(self, plan_controller):
        """测试验证训练分钟数过低"""
        with pytest.raises(ValueError) as exc_info:
            plan_controller._validate_plan_input(-10, 0)

        assert "训练分钟数必须在" in str(exc_info.value)

    def test_validate_plan_input_invalid_exercise_minutes_high(self, plan_controller):
        """测试验证训练分钟数过高"""
        with pytest.raises(ValueError) as exc_info:
            plan_controller._validate_plan_input(400, 0)

        assert "训练分钟数必须在" in str(exc_info.value)

    def test_validate_plan_input_invalid_adjustment_units_low(self, plan_controller):
        """测试验证调整单位过低"""
        with pytest.raises(ValueError) as exc_info:
            plan_controller._validate_plan_input(60, -20)

        assert "调整单位必须在" in str(exc_info.value)

    def test_validate_plan_input_invalid_adjustment_units_high(self, plan_controller):
        """测试验证调整单位过高"""
        with pytest.raises(ValueError) as exc_info:
            plan_controller._validate_plan_input(60, 20)

        assert "调整单位必须在" in str(exc_info.value)
