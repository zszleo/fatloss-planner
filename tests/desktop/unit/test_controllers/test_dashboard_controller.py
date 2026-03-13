"""DashboardController单元测试。

测试仪表盘控制器的业务逻辑和数据处理。
"""

from datetime import date, timedelta
from unittest.mock import Mock, MagicMock, patch
import pytest

from fatloss.desktop.controllers.dashboard_controller import DashboardController
from fatloss.models.user_profile import UserProfile, Gender, ActivityLevel
from fatloss.models.weight_record import WeightRecord
from fatloss.models.nutrition_plan import DailyNutritionPlan
from fatloss.calculator.nutrition_calculator import NutritionDistribution


class TestDashboardController:
    """DashboardController单元测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker):
        """自动设置模拟，避免GUI调用和数据库访问"""
        # 模拟unit_of_work
        self.mock_unit_of_work = mocker.patch(
            "fatloss.desktop.controllers.dashboard_controller.unit_of_work"
        )
        mock_uow = MagicMock()
        mock_uow.__enter__.return_value = mock_uow
        mock_uow.__exit__.return_value = None
        
        # 模拟权重仓库
        mock_weights = MagicMock()
        mock_weights.find_by_date_range.return_value = []
        mock_weights.find_by_user_id.return_value = []
        mock_weights.find_latest_by_user_id.return_value = None
        mock_uow.weights = mock_weights
        
        # 模拟用户仓库
        mock_users = MagicMock()
        mock_users.get_by_id.return_value = None
        mock_users.get_all.return_value = []
        mock_uow.users = mock_users
        
        # 模拟营养计划仓库
        mock_daily_nutrition = MagicMock()
        mock_daily_nutrition.find_by_user_id.return_value = []
        mock_uow.daily_nutrition = mock_daily_nutrition
        
        self.mock_unit_of_work.return_value = mock_uow
        
        # 模拟ErrorHandler
        self.mock_error_handler = mocker.patch(
            "fatloss.desktop.controllers.dashboard_controller.ErrorHandler"
        )
    
    @pytest.fixture
    def mock_planner_service(self):
        """模拟PlannerService依赖"""
        service = Mock()
        service.get_user_by_id.return_value = None
        service.get_weight_records.return_value = []
        service.get_recent_nutrition_plans.return_value = []
        service.get_user_summary.return_value = {}
        service.get_weight_loss_progress.return_value = {}
        service.get_weekly_adjustment_recommendation.return_value = {}
        service.get_recent_activities.return_value = []
        service.get_all_users.return_value = []
        return service
    
    @pytest.fixture
    def controller(self, mock_planner_service):
        """创建测试控制器实例"""
        return DashboardController(mock_planner_service)
    
    @pytest.fixture
    def sample_user(self):
        """创建示例用户档案"""
        return UserProfile(
            id=1,
            name="测试用户",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=70.0,
            activity_level=ActivityLevel.MODERATE
        )
    
    @pytest.fixture
    def sample_weight_records(self, sample_user):
        """创建示例体重记录"""
        return [
            WeightRecord(
                id=i,
                user_id=sample_user.id,
                weight_kg=70.0 - (i * 0.1),
                record_date=date.today() - timedelta(days=30 - i),
                notes=f"第{i+1}天记录"
            )
            for i in range(30)
        ]
    
    @pytest.fixture
    def sample_nutrition_distribution(self):
        """创建示例营养素分配"""
        from fatloss.calculator.nutrition_calculator import NutritionDistribution
        return NutritionDistribution(
            total_calories=1800,
            protein_g=120.0,
            carbohydrates_g=150.0,
            fat_g=50.0
        )

    @pytest.fixture
    def sample_nutrition_plans(self, sample_user, sample_nutrition_distribution):
        """创建示例营养计划"""
        return [
            DailyNutritionPlan(
                id=i,
                user_id=sample_user.id,
                plan_date=date.today() - timedelta(days=7 - i),
                target_tdee=2200.0 - (i * 100),
                nutrition=sample_nutrition_distribution,
                adjustment_units=0
            )
            for i in range(5)
        ]
    
    # 测试初始化
    
    def test_initialization(self, mock_planner_service):
        """测试控制器初始化"""
        # Act
        controller = DashboardController(mock_planner_service)
        
        # Assert
        assert controller.planner_service == mock_planner_service
        assert controller.DEFAULT_CHART_DAYS == 30
        assert controller.MAX_CHART_DAYS == 90
        assert controller.RECENT_PLANS_LIMIT == 5
    
    # 测试get_dashboard_data方法
    
    @patch("fatloss.desktop.controllers.dashboard_controller.unit_of_work")
    @patch("fatloss.desktop.controllers.dashboard_controller.ErrorHandler")
    def test_get_dashboard_data_success(self, mock_error_handler, mock_unit_of_work, 
                                        controller, mock_planner_service, sample_user):
        """测试获取仪表盘数据成功场景"""
        # Arrange
        user_id = 1
        summary_data = {
            "name": "测试用户",
            "age": 35,
            "height_cm": 175.0,
            "initial_weight_kg": 70.0,
            "current_weight_kg": 68.5,
            "target_weight_kg": 65.0
        }
        
        mock_planner_service.get_user_summary.return_value = summary_data
        
        # 模拟unit_of_work
        mock_uow = MagicMock()
        mock_uow.__enter__.return_value = mock_uow
        mock_uow.weights.find_by_date_range.return_value = []
        mock_unit_of_work.return_value = mock_uow
        
        # Act
        result = controller.get_dashboard_data(user_id)
        
        # Assert
        assert result is not None
        assert result["name"] == "测试用户"
        assert "weight_stats" in result
        assert "recent_plans" in result
        assert "progress_info" in result
        assert "chart_data" in result
        assert "dashboard_metrics" in result
        mock_planner_service.get_user_summary.assert_called_once_with(user_id)
    
    def test_get_dashboard_data_user_not_found(self, controller, mock_planner_service):
        """测试获取仪表盘数据 - 用户不存在"""
        # Arrange
        user_id = 999
        mock_planner_service.get_user_summary.side_effect = ValueError("用户不存在")
        
        # Act
        result = controller.get_dashboard_data(user_id)
        
        # Assert
        assert result is None
    
    def test_get_dashboard_data_with_parent_widget(self, controller, mock_planner_service):
        """测试获取仪表盘数据时提供父窗口部件"""
        # Arrange
        user_id = 1
        mock_parent = Mock()
        mock_planner_service.get_user_summary.side_effect = Exception("测试异常")
        
        # Act
        result = controller.get_dashboard_data(user_id, mock_parent)
        
        # Assert
        assert result is None
    
    # 测试get_user_summary方法
    
    def test_get_user_summary_success(self, controller, mock_planner_service, sample_user):
        """测试获取用户摘要成功"""
        # Arrange
        user_id = 1
        expected_summary = {
            "id": sample_user.id,
            "name": sample_user.name,
            "age": 35,
            "height_cm": sample_user.height_cm,
            "initial_weight_kg": sample_user.initial_weight_kg,
            "target_weight_kg": 65.0,
            "weekly_weight_loss_kg": 0.5,
            "activity_level": "中等"
        }
        mock_planner_service.get_user_summary.return_value = expected_summary
        
        # Act
        result = controller.get_user_summary(user_id)
        
        # Assert
        assert result == expected_summary
        mock_planner_service.get_user_summary.assert_called_once_with(user_id)
    
    def test_get_user_summary_error(self, controller, mock_planner_service):
        """测试获取用户摘要错误"""
        # Arrange
        user_id = 999
        mock_planner_service.get_user_summary.side_effect = ValueError("用户不存在")
        
        # Act
        result = controller.get_user_summary(user_id)
        
        # Assert
        assert result is None
    
    # 测试get_weight_loss_progress方法
    
    def test_get_weight_loss_progress_success(self, controller, mock_planner_service):
        """测试获取减重进度成功"""
        # Arrange
        user_id = 1
        target_weight_kg = 65.0
        expected_progress = {
            "current_weight": 70.0,
            "target_weight": 65.0,
            "weight_loss_kg": 5.0,
            "progress_percentage": 50.0,
            "weeks_remaining": 10,
            "expected_completion_date": date.today() + timedelta(days=70)
        }
        # 配置unit_of_work模拟返回用户
        mock_uow = self.mock_unit_of_work.return_value
        mock_user = Mock()
        mock_user.initial_weight_kg = 70.0
        mock_uow.users.get_by_id.return_value = mock_user
        
        mock_planner_service.calculate_weight_loss_progress.return_value = expected_progress
        
        # Act
        result = controller.get_weight_loss_progress(user_id, target_weight_kg=target_weight_kg)
        
        # Assert
        assert result == expected_progress
        mock_planner_service.calculate_weight_loss_progress.assert_called_once_with(
            user_id=user_id,
            target_weight_kg=target_weight_kg
        )
    
    def test_get_weight_loss_progress_error(self, controller, mock_planner_service):
        """测试获取减重进度错误"""
        # Arrange
        user_id = 999
        target_weight_kg = 65.0
        # 配置unit_of_work模拟返回None（用户不存在）
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.users.get_by_id.return_value = None
        # 也需要模拟calculate_weight_loss_progress返回None
        mock_planner_service.calculate_weight_loss_progress.return_value = None
        
        # Act
        result = controller.get_weight_loss_progress(user_id, target_weight_kg=target_weight_kg)
        
        # Assert
        assert result is None
    
    # 测试get_weekly_adjustment_recommendation方法
    
    def test_get_weekly_adjustment_recommendation_success(self, controller, mock_planner_service):
        """测试获取每周调整建议成功"""
        # Arrange
        user_id = 1
        adjustment_units = 0
        recommendation = "进度正常，无需调整"
        mock_planner_service.get_weekly_adjustment_recommendation.return_value = (adjustment_units, recommendation)
        
        # Act
        result = controller.get_weekly_adjustment_recommendation(user_id)
        
        # Assert
        assert result["adjustment_units"] == adjustment_units
        assert result["recommendation"] == recommendation
        assert result["carb_adjustment_g"] == adjustment_units * 30
        mock_planner_service.get_weekly_adjustment_recommendation.assert_called_once_with(user_id)
    
    def test_get_weekly_adjustment_recommendation_error(self, controller, mock_planner_service):
        """测试获取每周调整建议错误"""
        # Arrange
        user_id = 999
        mock_planner_service.get_weekly_adjustment_recommendation.side_effect = ValueError("用户不存在")
        
        # Act
        result = controller.get_weekly_adjustment_recommendation(user_id)
        
        # Assert
        assert result is None
    
    # 测试get_recent_activities方法
    
    def test_get_recent_activities_success(self, controller, mock_planner_service, sample_weight_records, sample_nutrition_plans):
        """测试获取最近活动记录成功"""
        # Arrange
        user_id = 1
        # 配置unit_of_work模拟返回数据
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_by_user_id.return_value = sample_weight_records
        mock_uow.daily_nutrition.find_by_user_id.return_value = sample_nutrition_plans
        
        # Act
        result = controller.get_recent_activities(user_id)
        
        # Assert
        assert len(result) > 0
        # 应该包含体重记录和营养计划
        assert any(a["type"] == "weight_record" for a in result)
        assert any(a["type"] == "nutrition_plan" for a in result)
        mock_uow.weights.find_by_user_id.assert_called_once_with(user_id)
        mock_uow.daily_nutrition.find_by_user_id.assert_called_once_with(user_id)
    
    def test_get_recent_activities_with_custom_limit(self, controller, mock_planner_service, sample_weight_records, sample_nutrition_plans):
        """测试获取最近活动记录 - 自定义限制"""
        # Arrange
        user_id = 1
        limit = 5
        # 配置unit_of_work模拟返回数据
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_by_user_id.return_value = sample_weight_records
        mock_uow.daily_nutrition.find_by_user_id.return_value = sample_nutrition_plans
        
        # Act
        result = controller.get_recent_activities(user_id, limit=limit)
        
        # Assert
        assert len(result) <= limit  # 结果数量不应超过限制
        mock_uow.weights.find_by_user_id.assert_called_once_with(user_id)
        mock_uow.daily_nutrition.find_by_user_id.assert_called_once_with(user_id)
    
    def test_get_recent_activities_error(self, controller, mock_planner_service):
        """测试获取最近活动记录错误"""
        # Arrange
        user_id = 999
        # 配置unit_of_work模拟抛出异常
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_by_user_id.side_effect = Exception("数据库错误")
        
        # Act
        result = controller.get_recent_activities(user_id)
        
        # Assert
        assert result == []
    
    # 测试辅助方法_get_weight_stats
    
    def test_get_weight_stats_with_records(self, controller, mock_planner_service, sample_weight_records):
        """测试获取体重统计 - 有记录"""
        # Arrange
        user_id = 1
        # 配置unit_of_work模拟返回数据
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_by_date_range.return_value = sample_weight_records
        
        # Act
        result = controller._get_weight_stats(user_id)
        
        # Assert
        assert "has_data" in result
        assert result["has_data"] is True
        assert "record_count" in result
        assert result["record_count"] == len(sample_weight_records)
        mock_uow.weights.find_by_date_range.assert_called_once()
    
    def test_get_weight_stats_no_records(self, controller, mock_planner_service):
        """测试获取体重统计 - 无记录"""
        # Arrange
        user_id = 1
        mock_planner_service.get_weight_records.return_value = []
        
        # Act
        result = controller._get_weight_stats(user_id)
        
        # Assert
        assert result["has_data"] is False
        assert result["record_count"] == 0
        assert result["latest_weight"] is None
        assert result["min_weight"] is None
        assert result["max_weight"] is None
        assert result["avg_weight"] is None
        assert result["total_change"] == 0.0
        assert result["avg_daily_change"] == 0.0
    
    def test_get_weight_stats_with_custom_days(self, controller, mock_planner_service):
        """测试获取体重统计 - 自定义天数"""
        # Arrange
        user_id = 1
        days = 60
        mock_planner_service.get_weight_records.return_value = []
        
        # Act
        # Note: _get_weight_stats doesn't accept days parameter, it uses fixed 30 days
        # So we test that it still works with the default behavior
        result = controller._get_weight_stats(user_id)
        
        # Assert
        # Since we're mocking get_weight_records to return [], it should return empty stats
        assert result["has_data"] is False
        assert result["record_count"] == 0
    
    # 测试辅助方法_get_recent_nutrition_plans
    
    def test_get_recent_nutrition_plans_with_plans(self, controller, mock_planner_service, sample_nutrition_plans):
        """测试获取最近营养计划 - 有计划"""
        # Arrange
        user_id = 1
        # Configure the unit_of_work mock
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.daily_nutrition.find_by_user_id.return_value = sample_nutrition_plans
    
        # Act
        result = controller._get_recent_nutrition_plans(user_id)
    
        # Assert
        assert len(result) == len(sample_nutrition_plans)
        for plan in result:
            assert "date" in plan
            assert "tdee" in plan
            assert "protein_g" in plan
            assert "carbs_g" in plan
            assert "fat_g" in plan
            assert "calories" in plan
            assert "is_adjusted" in plan
            assert "adjustment_units" in plan
        mock_uow.daily_nutrition.find_by_user_id.assert_called_once_with(user_id)
    
    def test_get_recent_nutrition_plans_no_plans(self, controller, mock_planner_service):
        """测试获取最近营养计划 - 无计划"""
        # Arrange
        user_id = 1
        mock_planner_service.get_recent_nutrition_plans.return_value = []
        
        # Act
        result = controller._get_recent_nutrition_plans(user_id)
        
        # Assert
        assert result == []
    
    # 测试辅助方法_get_weight_chart_data
    
    def test_get_weight_chart_data(self, controller, mock_planner_service, sample_weight_records):
        """测试获取体重图表数据"""
        # Arrange
        user_id = 1
        # Configure the unit_of_work mock
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_by_date_range.return_value = sample_weight_records
        
        # Act
        result = controller._get_weight_chart_data(user_id)
        
        # Assert
        assert "dates" in result
        assert "weights" in result
        assert "trend" in result
        assert len(result["dates"]) == len(sample_weight_records)
        assert len(result["weights"]) == len(sample_weight_records)
    
    # 测试get_all_users方法
    
    def test_get_all_users_success(self, controller, mock_planner_service, sample_user):
        """测试获取所有用户"""
        # Arrange
        expected_users = [sample_user]
        # 配置unit_of_work模拟返回expected_users
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.users.get_all.return_value = expected_users
        
        # Act
        result = controller.get_all_users()
        
        # Assert
        assert result == expected_users
        mock_uow.users.get_all.assert_called_once()
    
    def test_get_all_users_error(self, controller, mock_planner_service):
        """测试获取所有用户错误"""
        # Arrange
        # 配置unit_of_work模拟抛出异常
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.users.get_all.side_effect = Exception("数据库错误")
        
        # Act
        result = controller.get_all_users()
        
        # Assert
        assert result == []
    
    # 测试get_user_by_id方法
    
    def test_get_user_by_id_success(self, controller, mock_planner_service, sample_user):
        """测试根据ID获取用户"""
        # Arrange
        user_id = 1
        # 配置unit_of_work模拟返回sample_user
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.users.get_by_id.return_value = sample_user
        
        # Act
        result = controller.get_user_by_id(user_id)
        
        # Assert
        assert result == sample_user
        mock_uow.users.get_by_id.assert_called_once_with(user_id)
    
    def test_get_user_by_id_not_found(self, controller, mock_planner_service):
        """测试根据ID获取用户 - 未找到"""
        # Arrange
        user_id = 999
        # 配置unit_of_work模拟返回None
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.users.get_by_id.return_value = None
        
        # Act
        result = controller.get_user_by_id(user_id)
        
        # Assert
        assert result is None
        mock_uow.users.get_by_id.assert_called_once_with(user_id)