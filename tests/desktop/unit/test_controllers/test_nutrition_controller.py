"""NutritionController单元测试。

测试营养计算控制器的业务逻辑和数据处理。
"""

from datetime import date
from unittest.mock import Mock, MagicMock, patch
import pytest

from fatloss.desktop.controllers.nutrition_controller import NutritionController
from fatloss.models.user_profile import UserProfile, Gender, ActivityLevel
from fatloss.models.nutrition_plan import DailyNutritionPlan
from fatloss.calculator.nutrition_calculator import NutritionDistribution


class TestNutritionController:
    """NutritionController单元测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker):
        """自动设置模拟，避免GUI调用"""
        # 模拟ErrorHandler
        self.mock_error_handler = mocker.patch(
            "fatloss.desktop.controllers.nutrition_controller.ErrorHandler"
        )
        self.mock_error_handler.handle_service_error = mocker.Mock()
        self.mock_error_handler.show_success = mocker.Mock()
        # 模拟unit_of_work
        self.mock_unit_of_work = mocker.patch(
            "fatloss.desktop.controllers.nutrition_controller.unit_of_work"
        )
        mock_uow = MagicMock()
        mock_uow.__enter__.return_value = mock_uow
        mock_uow.__exit__.return_value = None
        mock_uow.daily_nutrition = MagicMock()
        mock_uow.users = MagicMock()
        mock_uow.weights = MagicMock()
        self.mock_unit_of_work.return_value = mock_uow
    
    @pytest.fixture
    def mock_planner_service(self):
        """模拟PlannerService依赖"""
        service = Mock()
        service.generate_daily_nutrition_plan.return_value = None
        service.get_user_by_id.return_value = None
        service.get_nutrition_history.return_value = []
        service.get_all_users.return_value = []
        service.database_url = "sqlite:///:memory:"
        return service
    
    @pytest.fixture
    def controller(self, mock_planner_service):
        """创建测试控制器实例"""
        return NutritionController(mock_planner_service)
    
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
    def sample_nutrition_plan(self, sample_nutrition_distribution):
        """创建示例营养计划"""
        return DailyNutritionPlan(
            id=1,
            user_id=1,
            plan_date=date.today(),
            target_tdee=2200.0,
            nutrition=sample_nutrition_distribution,
            adjustment_units=0
        )
    
    @pytest.fixture
    def sample_nutrition_distribution(self):
        """创建示例营养素分配"""
        return NutritionDistribution(
            total_calories=1800,
            protein_g=120.0,
            carbohydrates_g=150.0,
            fat_g=50.0
        )
    
    # 测试初始化
    
    def test_initialization(self, mock_planner_service):
        """测试控制器初始化"""
        # Act
        controller = NutritionController(mock_planner_service)
        
        # Assert
        assert controller.planner_service == mock_planner_service
        assert controller.MIN_EXERCISE_MINUTES == 0.0
        assert controller.MAX_EXERCISE_MINUTES == 300.0
        assert controller.MIN_ADJUSTMENT_UNITS == -10
        assert controller.MAX_ADJUSTMENT_UNITS == 10
        assert controller.DEFAULT_EXERCISE_MINUTES == 60.0
        assert controller.DEFAULT_ADJUSTMENT_UNITS == 0
    
    # 测试calculate_nutrition_plan方法
    
    def test_calculate_nutrition_plan_success(self, controller, mock_planner_service, sample_nutrition_plan):
        """测试计算营养计划成功场景"""
        # Arrange
        user_id = 1
        plan_date = date.today()
        exercise_minutes = 60.0
        adjustment_units = 0
        
        mock_planner_service.generate_daily_nutrition_plan.return_value = sample_nutrition_plan
        
        # Act
        result = controller.calculate_nutrition_plan(
            user_id=user_id,
            plan_date=plan_date,
            exercise_minutes=exercise_minutes,
            adjustment_units=adjustment_units
        )
        
        # Assert
        assert result == sample_nutrition_plan
        mock_planner_service.generate_daily_nutrition_plan.assert_called_once()
    
    def test_calculate_nutrition_plan_validation_error(self, controller, mock_planner_service):
        """测试计算营养计划 - 输入验证错误"""
        # Arrange
        user_id = 1
        plan_date = date.today()
        exercise_minutes = 400.0  # 超过最大值
        adjustment_units = 0
        
        # Act
        result = controller.calculate_nutrition_plan(
            user_id=user_id,
            plan_date=plan_date,
            exercise_minutes=exercise_minutes,
            adjustment_units=adjustment_units
        )
        
        # Assert
        assert result is None
        mock_planner_service.generate_daily_nutrition_plan.assert_not_called()
    
    def test_calculate_nutrition_plan_service_error(self, controller, mock_planner_service):
        """测试计算营养计划 - 服务错误"""
        # Arrange
        user_id = 1
        plan_date = date.today()
        exercise_minutes = 60.0
        adjustment_units = 0
        
        mock_planner_service.generate_daily_nutrition_plan.side_effect = Exception("服务错误")
        
        # Act
        result = controller.calculate_nutrition_plan(
            user_id=user_id,
            plan_date=plan_date,
            exercise_minutes=exercise_minutes,
            adjustment_units=adjustment_units
        )
        
        # Assert
        assert result is None
        mock_planner_service.generate_daily_nutrition_plan.assert_called_once()
    
    def test_calculate_nutrition_plan_with_parent_widget(self, controller, mock_planner_service, sample_nutrition_plan):
        """测试计算营养计划 - 提供父窗口部件"""
        # Arrange
        user_id = 1
        plan_date = date.today()
        exercise_minutes = 60.0
        adjustment_units = 0
        mock_parent = Mock()
        
        mock_planner_service.generate_daily_nutrition_plan.return_value = sample_nutrition_plan
        
        # Act
        result = controller.calculate_nutrition_plan(
            user_id=user_id,
            plan_date=plan_date,
            exercise_minutes=exercise_minutes,
            adjustment_units=adjustment_units,
            parent_widget=mock_parent
        )
        
        # Assert
        assert result == sample_nutrition_plan
        mock_planner_service.generate_daily_nutrition_plan.assert_called_once()
    
    # 测试get_user_nutrition_history方法
    
    def test_get_user_nutrition_history_success(self, controller, mock_planner_service, sample_nutrition_plan):
        """测试获取用户营养历史成功"""
        # Arrange
        user_id = 1
        expected_history = [sample_nutrition_plan]
        # Configure the unit_of_work mock
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.daily_nutrition.find_by_user_id.return_value = expected_history
        
        # Act
        result = controller.get_user_nutrition_history(user_id)
        
        # Assert
        assert result == expected_history
        mock_uow.daily_nutrition.find_by_user_id.assert_called_once_with(user_id)
    
    def test_get_user_nutrition_history_with_custom_limit(self, controller, mock_planner_service):
        """测试获取用户营养历史 - 自定义限制"""
        # Arrange
        user_id = 1
        limit = 5
        expected_history = []
        # Configure the unit_of_work mock
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.daily_nutrition.find_by_user_id.return_value = expected_history
        
        # Act
        result = controller.get_user_nutrition_history(user_id, limit=limit)
        
        # Assert
        mock_uow.daily_nutrition.find_by_user_id.assert_called_once_with(user_id)
        assert result == expected_history
    
    def test_get_user_nutrition_history_error(self, controller):
        """测试获取用户营养历史错误"""
        # Arrange
        user_id = 1
        # Configure the unit_of_work mock to raise an exception
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.daily_nutrition.find_by_user_id.side_effect = Exception("数据库错误")
        
        # Act
        result = controller.get_user_nutrition_history(user_id)
        
        # Assert
        assert result == []
    
    # 测试calculate_bmr_tdee方法
    
    @patch("fatloss.desktop.controllers.nutrition_controller.unit_of_work")
    @patch("fatloss.calculator.bmr_calculator.calculate_bmr")
    @patch("fatloss.calculator.tdee_calculator.calculate_tdee")
    def test_calculate_bmr_tdee_success(
        self, 
        mock_calculate_tdee,
        mock_calculate_bmr,
        mock_unit_of_work,
        controller,
        sample_user
    ):
        """测试计算BMR和TDEE成功"""
        # Arrange
        exercise_minutes = 60.0
        expected_bmr = 1600.0
        expected_tdee = 2200.0
        mock_weight = Mock(weight_kg=70.0)
        
        mock_uow = MagicMock()
        mock_uow.__enter__.return_value = mock_uow
        mock_uow.weights.find_latest_by_user_id.return_value = mock_weight
        mock_unit_of_work.return_value = mock_uow
        
        mock_calculate_bmr.return_value = expected_bmr
        mock_calculate_tdee.return_value = expected_tdee
        
        # Act
        result = controller.calculate_bmr_tdee(sample_user, exercise_minutes)
        
        # Assert
        assert result["bmr"] == expected_bmr
        assert result["tdee"] == expected_tdee
        assert result["weight_kg"] == mock_weight.weight_kg
        mock_calculate_bmr.assert_called_once_with(
            weight_kg=mock_weight.weight_kg,
            height_cm=sample_user.height_cm,
            age_years=sample_user.age,
            gender=sample_user.gender
        )
        mock_calculate_tdee.assert_called_once_with(bmr=expected_bmr, exercise_minutes=exercise_minutes)
    
    @patch("fatloss.desktop.controllers.nutrition_controller.unit_of_work")
    def test_calculate_bmr_tdee_no_weight_record(self, mock_unit_of_work, controller, sample_user):
        """测试计算BMR和TDEE - 无体重记录"""
        # Arrange
        exercise_minutes = 60.0
        
        mock_uow = MagicMock()
        mock_uow.__enter__.return_value = mock_uow
        mock_uow.weights.find_latest_by_user_id.return_value = None
        mock_unit_of_work.return_value = mock_uow
        
        # Act
        result = controller.calculate_bmr_tdee(sample_user, exercise_minutes)
        
        # Assert
        assert result["bmr"] == 0.0
        assert result["tdee"] == 0.0
        assert result["weight_kg"] == 0.0
    
    @patch("fatloss.desktop.controllers.nutrition_controller.unit_of_work")
    def test_calculate_bmr_tdee_database_error(self, mock_unit_of_work, controller, sample_user):
        """测试计算BMR和TDEE - 数据库错误"""
        # Arrange
        exercise_minutes = 60.0
        
        mock_uow = MagicMock()
        mock_uow.__enter__.return_value = mock_uow
        mock_uow.weights.find_latest_by_user_id.side_effect = Exception("数据库错误")
        mock_unit_of_work.return_value = mock_uow
        
        # Act
        result = controller.calculate_bmr_tdee(sample_user, exercise_minutes)
        
        # Assert
        assert result["bmr"] == 0.0
        assert result["tdee"] == 0.0
        assert result["weight_kg"] == 0.0
    
    # 测试calculate_nutrition_from_tdee方法
    
    @patch("fatloss.calculator.nutrition_calculator.calculate_nutrition")
    @patch("fatloss.calculator.nutrition_calculator.adjust_carbohydrates")
    def test_calculate_nutrition_from_tdee_success(
        self,
        mock_adjust_carbohydrates,
        mock_calculate_nutrition,
        controller
    ):
        """测试根据TDEE计算营养素分配成功"""
        # Arrange
        tdee = 2200.0
        adjustment_units = 2
        
        # Calculate what calculate_nutrition(tdee=2200.0) should return
        # Based on 5:3:2 ratio (carbs:protein:fat = 50%:30%:20%)
        base_carbs_g = round((tdee * 0.5) / 4.0, 2)  # 275.0g
        base_protein_g = round((tdee * 0.3) / 4.0, 2)  # 165.0g
        base_fat_g = round((tdee * 0.2) / 9.0, 2)  # 48.89g
        base_nutrition = NutritionDistribution(
            carbohydrates_g=base_carbs_g,
            protein_g=base_protein_g,
            fat_g=base_fat_g,
            total_calories=tdee
        )
    
        mock_calculate_nutrition.return_value = base_nutrition
        # When adjust_carbohydrates is called with base_carb_g=275.0 and adjustment_units=2,
        # it should return 275.0 + (2 * 30) = 335.0
        mock_adjust_carbohydrates.return_value = 335.0
    
        # Expected result after adjustment
        expected_carbs_g = 335.0
        expected_protein_g = base_protein_g  # 165.0
        expected_fat_g = base_fat_g  # 48.89
        expected_total_calories = round(expected_carbs_g * 4.0 + expected_protein_g * 4.0 + expected_fat_g * 9.0, 2)
        # 335.0*4 + 165.0*4 + 48.89*9 = 1340 + 660 + 440.01 = 2440.01
    
        # Act
        result = controller.calculate_nutrition_from_tdee(tdee, adjustment_units)
    
        # Assert
        assert result.carbohydrates_g == expected_carbs_g
        assert result.protein_g == expected_protein_g
        assert result.fat_g == expected_fat_g
        assert result.total_calories == expected_total_calories
        mock_calculate_nutrition.assert_called_once_with(tdee=tdee)
        mock_adjust_carbohydrates.assert_called_once_with(
            base_carb_g=base_carbs_g,
            adjustment_units=adjustment_units
        )
    
    @patch("fatloss.calculator.nutrition_calculator.calculate_nutrition")
    def test_calculate_nutrition_from_tdee_no_adjustment(
        self,
        mock_calculate_nutrition,
        controller,
        sample_nutrition_distribution
    ):
        """测试根据TDEE计算营养素分配 - 无调整"""
        # Arrange
        tdee = 2200.0
        adjustment_units = 0
        
        mock_calculate_nutrition.return_value = sample_nutrition_distribution
        
        # Act
        result = controller.calculate_nutrition_from_tdee(tdee, adjustment_units)
        
        # Assert
        assert result == sample_nutrition_distribution
        mock_calculate_nutrition.assert_called_once_with(tdee=tdee)
    
    @patch("fatloss.calculator.nutrition_calculator.calculate_nutrition")
    def test_calculate_nutrition_from_tdee_error(
        self,
        mock_calculate_nutrition,
        controller
    ):
        """测试根据TDEE计算营养素分配 - 计算错误"""
        # Arrange
        tdee = 2200.0
        adjustment_units = 0
        
        mock_calculate_nutrition.side_effect = Exception("计算错误")
        
        # Act
        result = controller.calculate_nutrition_from_tdee(tdee, adjustment_units)
        
        # Assert
        assert result.total_calories == tdee
        assert result.protein_g == pytest.approx(tdee * 0.3 / 4)
        assert result.carbohydrates_g == pytest.approx(tdee * 0.5 / 4)
        assert result.fat_g == pytest.approx(tdee * 0.2 / 9)
    
    # 测试_validate_calculation_input方法
    
    def test_validate_calculation_input_valid(self, controller):
        """测试验证计算输入 - 有效输入"""
        # Arrange
        exercise_minutes = 60.0
        adjustment_units = 0
        
        # Act & Assert (不应该抛出异常)
        controller._validate_calculation_input(exercise_minutes, adjustment_units)
    
    def test_validate_calculation_input_invalid_exercise_minutes_low(self, controller):
        """测试验证计算输入 - 训练分钟数过低"""
        # Arrange
        exercise_minutes = -10.0
        adjustment_units = 0
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            controller._validate_calculation_input(exercise_minutes, adjustment_units)
        
        assert "训练分钟数必须在" in str(exc_info.value)
    
    def test_validate_calculation_input_invalid_exercise_minutes_high(self, controller):
        """测试验证计算输入 - 训练分钟数过高"""
        # Arrange
        exercise_minutes = 400.0
        adjustment_units = 0
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            controller._validate_calculation_input(exercise_minutes, adjustment_units)
        
        assert "训练分钟数必须在" in str(exc_info.value)
    
    def test_validate_calculation_input_invalid_adjustment_units_low(self, controller):
        """测试验证计算输入 - 调整单位过低"""
        # Arrange
        exercise_minutes = 60.0
        adjustment_units = -15
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            controller._validate_calculation_input(exercise_minutes, adjustment_units)
        
        assert "调整单位必须在" in str(exc_info.value)
    
    def test_validate_calculation_input_invalid_adjustment_units_high(self, controller):
        """测试验证计算输入 - 调整单位过高"""
        # Arrange
        exercise_minutes = 60.0
        adjustment_units = 15
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            controller._validate_calculation_input(exercise_minutes, adjustment_units)
        
        assert "调整单位必须在" in str(exc_info.value)
    
    def test_validate_calculation_input_with_parent_widget(self, controller):
        """测试验证计算输入 - 提供父窗口部件"""
        # Arrange
        exercise_minutes = 60.0
        adjustment_units = 0
        mock_parent = Mock()
        
        # Act & Assert (不应该抛出异常)
        controller._validate_calculation_input(exercise_minutes, adjustment_units, mock_parent)
    
    # 测试format_nutrition_summary方法
    
    def test_format_nutrition_summary(self, controller, sample_nutrition_plan):
        """测试格式化营养计划摘要"""
        # Act
        result = controller.format_nutrition_summary(sample_nutrition_plan)
        
        # Assert
        assert isinstance(result, str)
        assert str(sample_nutrition_plan.nutrition.total_calories) in result
        assert str(sample_nutrition_plan.nutrition.protein_g) in result
        assert str(sample_nutrition_plan.nutrition.carbohydrates_g) in result
        assert str(sample_nutrition_plan.nutrition.fat_g) in result
    
    # 测试format_nutrition_for_table方法
    
    def test_format_nutrition_for_table(self, controller, sample_nutrition_plan):
        """测试格式化表格营养计划"""
        # Act
        result = controller.format_nutrition_for_table(sample_nutrition_plan)
        
        # Assert
        assert isinstance(result, dict)
        assert "calories" in result
        assert "protein" in result
        assert "carbs" in result
        assert "fat" in result
        assert "date" in result
        assert "adjusted" in result
        assert "adjustment" in result
    
    # 测试辅助方法
    
    def test_get_user_by_id_success(self, controller, mock_planner_service, sample_user):
        """测试根据ID获取用户"""
        # Arrange
        user_id = 1
        # Configure the unit_of_work mock
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.users.get_by_id.return_value = sample_user
        
        # Act
        result = controller.get_user_by_id(user_id)
        
        # Assert
        assert result == sample_user
        mock_uow.users.get_by_id.assert_called_once_with(user_id)
    
    def test_get_user_by_id_not_found(self, controller):
        """测试根据ID获取用户 - 未找到"""
        # Arrange
        user_id = 999
        # Configure the unit_of_work mock
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.users.get_by_id.return_value = None
    
        # Act
        result = controller.get_user_by_id(user_id)
    
        # Assert
        assert result is None
    
    def test_get_all_users_success(self, controller):
        """测试获取所有用户"""
        # Arrange
        sample_user = UserProfile(
            id=1,
            name="测试用户",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=70.0,
            activity_level=ActivityLevel.MODERATE
        )
        expected_users = [sample_user]
        # Configure the unit_of_work mock
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.users.get_all.return_value = expected_users
    
        # Act
        result = controller.get_all_users()
    
        # Assert
        assert result == expected_users
        mock_uow.users.get_all.assert_called_once()
    
    def test_get_all_users_error(self, controller):
        """测试获取所有用户错误"""
        # Arrange
        # Configure the unit_of_work mock to raise an exception
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.users.get_all.side_effect = Exception("数据库错误")
    
        # Act
        result = controller.get_all_users()
    
        # Assert
        assert result == []