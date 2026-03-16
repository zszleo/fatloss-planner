"""WeightController单元测试。

测试体重控制器的业务逻辑和数据处理。
"""

from datetime import date, timedelta
from unittest.mock import Mock, MagicMock, patch
import pytest

from fatloss.desktop.controllers.weight_controller import WeightController
from fatloss.models.weight_record import WeightRecord
from fatloss.models.user_profile import UserProfile
from fatloss.models.enums import Gender, ActivityLevel


class TestWeightController:
    """WeightController单元测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker):
        """自动设置模拟，避免GUI调用和数据库访问"""
        # 模拟unit_of_work
        self.mock_unit_of_work = mocker.patch(
            "fatloss.desktop.controllers.weight_controller.unit_of_work"
        )
        mock_uow = MagicMock()
        mock_uow.__enter__.return_value = mock_uow
        mock_uow.__exit__.return_value = None
        
        # 模拟权重仓库
        mock_weights = MagicMock()
        mock_weights.find_by_user_id.return_value = []
        mock_weights.find_by_date_range.return_value = []
        mock_weights.find_latest_by_user_id.return_value = None
        mock_weights.find_all.return_value = []
        mock_uow.weights = mock_weights
        
        # 模拟用户仓库
        mock_users = MagicMock()
        mock_users.get_by_id.return_value = None
        mock_users.get_all.return_value = []
        mock_uow.users = mock_users
        
        self.mock_unit_of_work.return_value = mock_uow
        
        # 模拟ErrorHandler
        self.mock_error_handler = mocker.patch(
            "fatloss.desktop.controllers.weight_controller.ErrorHandler"
        )
    
    @pytest.fixture
    def mock_planner_service(self):
        """模拟PlannerService依赖"""
        service = Mock()
        service.record_weight.return_value = None
        service.calculate_weight_loss_progress.return_value = None
        return service
    
    @pytest.fixture
    def controller(self, mock_planner_service):
        """创建测试控制器实例"""
        return WeightController(mock_planner_service)
    
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
    def sample_weight_record(self, sample_user):
        """创建示例体重记录"""
        return WeightRecord(
            id=1,
            user_id=sample_user.id,
            weight_kg=70.0,
            record_date=date.today(),
            notes="测试记录"
        )
    
    @pytest.fixture
    def sample_weight_records(self, sample_user):
        """创建示例体重记录列表"""
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
    
    # 测试初始化
    
    def test_initialization(self, mock_planner_service):
        """测试控制器初始化"""
        # Act
        controller = WeightController(mock_planner_service)
        
        # Assert
        assert controller.planner_service == mock_planner_service
        assert controller.MIN_WEIGHT_KG == 30.0
        assert controller.MAX_WEIGHT_KG == 200.0
        assert controller.DEFAULT_CHART_DAYS == 30
        assert controller.MAX_CHART_DAYS == 365
    
    # 测试record_weight方法
    
    @patch("fatloss.desktop.controllers.weight_controller.ErrorHandler")
    def test_record_weight_success(self, mock_error_handler, mock_planner_service, controller):
        """测试记录体重成功"""
        # Arrange
        user_id = 1
        weight_kg = 70.5
        mock_weight_record = Mock(spec=WeightRecord)
        mock_planner_service.record_weight.return_value = mock_weight_record
        
        # Act
        result = controller.record_weight(user_id, weight_kg)
        
        # Assert
        assert result == mock_weight_record
        mock_planner_service.record_weight.assert_called_once_with(
            user_id=user_id,
            weight_kg=weight_kg,
            record_date=None,
            notes=""
        )
        mock_error_handler.show_success.assert_called_once()
    
    @patch("fatloss.desktop.controllers.weight_controller.ErrorHandler")
    def test_record_weight_invalid_weight(self, mock_error_handler, controller):
        """测试记录体重 - 无效体重"""
        # Arrange
        user_id = 1
        weight_kg = 25.0  # 低于最小值
        
        # Act
        result = controller.record_weight(user_id, weight_kg)
        
        # Assert
        assert result is None
        mock_error_handler.handle_service_error.assert_called_once()
    
    @patch("fatloss.desktop.controllers.weight_controller.ErrorHandler")
    def test_record_weight_service_error(self, mock_error_handler, mock_planner_service, controller):
        """测试记录体重 - 服务错误"""
        # Arrange
        user_id = 1
        weight_kg = 70.5
        mock_planner_service.record_weight.side_effect = Exception("数据库错误")
        
        # Act
        result = controller.record_weight(user_id, weight_kg)
        
        # Assert
        assert result is None
        mock_error_handler.handle_service_error.assert_called_once()
    
    # 测试get_weight_history方法
    
    def test_get_weight_history_success(self, controller, mock_planner_service, sample_weight_records):
        """测试获取体重历史记录成功"""
        # Arrange
        user_id = 1
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_by_user_id.return_value = sample_weight_records
        
        # Act
        result = controller.get_weight_history(user_id)
        
        # Assert
        assert len(result) == 30
        assert result[0].record_date > result[1].record_date  # 降序排列
        mock_uow.weights.find_by_user_id.assert_called_once_with(user_id)
    
    def test_get_weight_history_with_limit(self, controller, mock_planner_service, sample_weight_records):
        """测试获取体重历史记录 - 带限制"""
        # Arrange
        user_id = 1
        limit = 5
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_by_user_id.return_value = sample_weight_records
        
        # Act
        result = controller.get_weight_history(user_id, limit=limit)
        
        # Assert
        assert len(result) == limit
        mock_uow.weights.find_by_user_id.assert_called_once_with(user_id)
    
    def test_get_weight_history_error(self, controller, mock_planner_service):
        """测试获取体重历史记录 - 错误"""
        # Arrange
        user_id = 1
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_by_user_id.side_effect = Exception("数据库错误")
        
        # Act
        result = controller.get_weight_history(user_id)
        
        # Assert
        assert result == []
    
    # 测试get_weight_by_id方法
    
    def test_get_weight_by_id_success(self, controller, mock_planner_service, sample_weight_record):
        """测试根据ID获取体重记录成功"""
        # Arrange
        weight_id = 1
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_all.return_value = [sample_weight_record]
        
        # Act
        result = controller.get_weight_by_id(weight_id)
        
        # Assert
        assert result == sample_weight_record
        mock_uow.weights.find_all.assert_called_once()
    
    def test_get_weight_by_id_not_found(self, controller, mock_planner_service, sample_weight_record):
        """测试根据ID获取体重记录 - 未找到"""
        # Arrange
        weight_id = 999
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_all.return_value = [sample_weight_record]
        
        # Act
        result = controller.get_weight_by_id(weight_id)
        
        # Assert
        assert result is None
        mock_uow.weights.find_all.assert_called_once()
    
    def test_get_weight_by_id_error(self, controller, mock_planner_service):
        """测试根据ID获取体重记录 - 错误"""
        # Arrange
        weight_id = 1
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_all.side_effect = Exception("数据库错误")
        
        # Act
        result = controller.get_weight_by_id(weight_id)
        
        # Assert
        assert result is None
    
    # 测试update_weight方法
    
    @patch("fatloss.desktop.controllers.weight_controller.ErrorHandler")
    def test_update_weight_success(self, mock_error_handler, mock_planner_service, controller, sample_weight_record):
        """测试更新体重记录成功"""
        # Arrange
        weight_id = 1
        weight_kg = 69.5
        record_date = date.today()
        notes = "更新记录"
        
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_all.return_value = [sample_weight_record]
        
        # Act
        result = controller.update_weight(weight_id, weight_kg, record_date, notes)
        
        # Assert
        assert result is not None
        assert result.weight_kg == weight_kg
        assert result.record_date == record_date
        assert result.notes == notes
        mock_uow.weights.update.assert_called_once()
        mock_uow.commit.assert_called_once()
        mock_error_handler.show_success.assert_called_once()
    
    @patch("fatloss.desktop.controllers.weight_controller.ErrorHandler")
    def test_update_weight_not_found(self, mock_error_handler, controller):
        """测试更新体重记录 - 记录不存在"""
        # Arrange
        weight_id = 999
        weight_kg = 69.5
        record_date = date.today()
        
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_all.return_value = []
        
        # Act
        result = controller.update_weight(weight_id, weight_kg, record_date)
        
        # Assert
        assert result is None
        mock_error_handler.show_warning.assert_called_once()
    
    @patch("fatloss.desktop.controllers.weight_controller.ErrorHandler")
    def test_update_weight_invalid_weight(self, mock_error_handler, controller):
        """测试更新体重记录 - 无效体重"""
        # Arrange
        weight_id = 1
        weight_kg = 250.0  # 超过最大值
        record_date = date.today()
        
        # Act
        result = controller.update_weight(weight_id, weight_kg, record_date)
        
        # Assert
        assert result is None
        mock_error_handler.handle_service_error.assert_called_once()
    
    # 测试delete_weight方法
    
    @patch("fatloss.desktop.controllers.weight_controller.ErrorHandler")
    def test_delete_weight_success(self, mock_error_handler, mock_planner_service, controller, sample_weight_record):
        """测试删除体重记录成功"""
        # Arrange
        weight_id = 1
        
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_all.return_value = [sample_weight_record]
        
        # Act
        result = controller.delete_weight(weight_id)
        
        # Assert
        assert result is True
        mock_uow.weights.delete.assert_called_once_with(weight_id)
        mock_uow.commit.assert_called_once()
        mock_error_handler.show_success.assert_called_once()
    
    @patch("fatloss.desktop.controllers.weight_controller.ErrorHandler")
    def test_delete_weight_not_found(self, mock_error_handler, controller):
        """测试删除体重记录 - 记录不存在"""
        # Arrange
        weight_id = 999
        
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_all.return_value = []
        
        # Act
        result = controller.delete_weight(weight_id)
        
        # Assert
        assert result is False
        mock_error_handler.show_warning.assert_called_once()

    # 缺失测试：delete_weight 异常处理
    @patch("fatloss.desktop.controllers.weight_controller.ErrorHandler")
    def test_delete_weight_error(self, mock_error_handler, controller, sample_weight_record):
        """测试删除体重记录 - 异常"""
        # Arrange
        weight_id = 1
        
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_all.return_value = [sample_weight_record]
        mock_uow.weights.delete.side_effect = Exception("Database error")
        
        # Act
        result = controller.delete_weight(weight_id)
        
        # Assert
        assert result is False
        mock_error_handler.handle_service_error.assert_called_once()
    
    # 测试get_weight_stats方法
    
    def test_get_weight_stats_success(self, controller, mock_planner_service, sample_weight_records):
        """测试获取体重统计成功"""
        # Arrange
        user_id = 1
        days = 30
        
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_by_date_range.return_value = sample_weight_records
        
        # Act
        result = controller.get_weight_stats(user_id, days)
        
        # Assert
        assert result["count"] == 30
        assert result["latest_weight"] is not None
        assert result["min_weight"] is not None
        assert result["max_weight"] is not None
        assert result["avg_weight"] is not None
        assert result["total_change"] < 0  # 应该是减重
        assert result["avg_daily_change"] < 0
        mock_uow.weights.find_by_date_range.assert_called_once()
    
    def test_get_weight_stats_no_records(self, controller, mock_planner_service):
        """测试获取体重统计 - 无记录"""
        # Arrange
        user_id = 1
        
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_by_date_range.return_value = []
        
        # Act
        result = controller.get_weight_stats(user_id)
        
        # Assert
        assert result["count"] == 0
        assert result["latest_weight"] is None
        assert result["min_weight"] is None
        assert result["max_weight"] is None
        assert result["avg_weight"] is None
        assert result["total_change"] == 0.0
        assert result["avg_daily_change"] == 0.0

    # 缺失测试：get_weight_stats avg_daily_change 计算 (days_diff <= 0)
    def test_get_weight_stats_same_date_records(self, controller, mock_planner_service, sample_user):
        """测试获取体重统计 - 同日期记录"""
        # Arrange
        user_id = 1
        today = date.today()
        
        # Create records with same date
        same_date_records = [
            WeightRecord(id=1, user_id=user_id, weight_kg=70.0, record_date=today, notes="Morning"),
            WeightRecord(id=2, user_id=user_id, weight_kg=69.5, record_date=today, notes="Evening"),
        ]
        
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_by_date_range.return_value = same_date_records
        
        # Act
        result = controller.get_weight_stats(user_id)
        
        # Assert
        assert result["count"] == 2
        assert result["avg_daily_change"] == 0.0  # days_diff = 0, so avg_daily_change = 0.0

    # 缺失测试：get_weight_stats 只有一条记录
    def test_get_weight_stats_single_record(self, controller, mock_planner_service, sample_user):
        """测试获取体重统计 - 只有一条记录"""
        # Arrange
        user_id = 1
        today = date.today()
        
        # Create single record
        single_record = [
            WeightRecord(id=1, user_id=user_id, weight_kg=70.0, record_date=today, notes="Test")
        ]
        
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_by_date_range.return_value = single_record
        
        # Act
        result = controller.get_weight_stats(user_id)
        
        # Assert
        assert result["count"] == 1
        assert result["avg_daily_change"] == 0.0  # Only one record, so no daily change

    # 缺失测试：get_weight_stats 异常处理
    @patch("fatloss.desktop.controllers.weight_controller.ErrorHandler")
    def test_get_weight_stats_error(self, mock_error_handler, controller):
        """测试获取体重统计 - 异常"""
        # Arrange
        user_id = 1
        
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_by_date_range.side_effect = Exception("Database error")
        
        # Act
        result = controller.get_weight_stats(user_id)
        
        # Assert
        assert result["count"] == 0
        mock_error_handler.handle_service_error.assert_called_once()
    
    # 测试get_latest_weight方法
    
    def test_get_latest_weight_success(self, controller, mock_planner_service, sample_weight_record):
        """测试获取最新体重记录成功"""
        # Arrange
        user_id = 1
        
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_latest_by_user_id.return_value = sample_weight_record
        
        # Act
        result = controller.get_latest_weight(user_id)
        
        # Assert
        assert result == sample_weight_record
        mock_uow.weights.find_latest_by_user_id.assert_called_once_with(user_id)
    
    def test_get_latest_weight_not_found(self, controller, mock_planner_service):
        """测试获取最新体重记录 - 未找到"""
        # Arrange
        user_id = 1
        
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_latest_by_user_id.return_value = None
        
        # Act
        result = controller.get_latest_weight(user_id)
        
        # Assert
        assert result is None

    # 缺失测试：get_latest_weight 异常处理
    @patch("fatloss.desktop.controllers.weight_controller.ErrorHandler")
    def test_get_latest_weight_error(self, mock_error_handler, controller):
        """测试获取最新体重记录 - 异常"""
        # Arrange
        user_id = 1
        
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_latest_by_user_id.side_effect = Exception("Database error")
        
        # Act
        result = controller.get_latest_weight(user_id)
        
        # Assert
        assert result is None
        mock_error_handler.handle_service_error.assert_called_once()
    
    # 测试get_chart_data方法
    
    def test_get_chart_data_success(self, controller, mock_planner_service, sample_weight_records):
        """测试获取图表数据成功"""
        # Arrange
        user_id = 1
        days = 30
        
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_by_date_range.return_value = sample_weight_records
        
        # Act
        result = controller.get_chart_data(user_id, days)
        
        # Assert
        assert "dates" in result
        assert "weights" in result
        assert "records" in result
        assert "day_count" in result
        assert len(result["dates"]) == 30
        assert len(result["weights"]) == 30
    
    def test_get_chart_data_empty(self, controller, mock_planner_service):
        """测试获取图表数据 - 空数据"""
        # Arrange
        user_id = 1
        
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_by_date_range.return_value = []
        
        # Act
        result = controller.get_chart_data(user_id)
        
        # Assert
        assert result["dates"] == []
        assert result["weights"] == []
        assert result["records"] == []

    # 缺失测试：get_chart_data 异常处理
    @patch("fatloss.desktop.controllers.weight_controller.ErrorHandler")
    def test_get_chart_data_error(self, mock_error_handler, controller):
        """测试获取图表数据 - 异常"""
        # Arrange
        user_id = 1
        
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.weights.find_by_date_range.side_effect = Exception("Database error")
        
        # Act
        result = controller.get_chart_data(user_id)
        
        # Assert
        assert result["dates"] == []
        assert result["weights"] == []
        assert result["records"] == []
        mock_error_handler.handle_service_error.assert_called_once()
    
    # 测试calculate_weight_loss_progress方法
    
    @patch("fatloss.desktop.controllers.weight_controller.ErrorHandler")
    def test_calculate_weight_loss_progress_success(self, mock_error_handler, mock_planner_service, controller):
        """测试计算减脂进度成功"""
        # Arrange
        user_id = 1
        target_weight_kg = 65.0
        expected_progress = {"progress": 50}
        
        mock_planner_service.calculate_weight_loss_progress.return_value = expected_progress
        
        # Act
        result = controller.calculate_weight_loss_progress(user_id, target_weight_kg)
        
        # Assert
        assert result == expected_progress
        mock_planner_service.calculate_weight_loss_progress.assert_called_once_with(
            user_id=user_id,
            target_weight_kg=target_weight_kg
        )
    
    @patch("fatloss.desktop.controllers.weight_controller.ErrorHandler")
    def test_calculate_weight_loss_progress_error(self, mock_error_handler, mock_planner_service, controller):
        """测试计算减脂进度 - 错误"""
        # Arrange
        user_id = 1
        target_weight_kg = 65.0
        mock_planner_service.calculate_weight_loss_progress.side_effect = Exception("计算错误")
        
        # Act
        result = controller.calculate_weight_loss_progress(user_id, target_weight_kg)
        
        # Assert
        assert result is None
        mock_error_handler.handle_service_error.assert_called_once()
    
    # 测试get_user_by_id方法
    
    def test_get_user_by_id_success(self, controller, mock_planner_service, sample_user):
        """测试根据ID获取用户成功"""
        # Arrange
        user_id = 1
        
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
        
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.users.get_by_id.return_value = None
        
        # Act
        result = controller.get_user_by_id(user_id)
        
        # Assert
        assert result is None

    # 缺失测试：get_user_by_id 异常处理
    @patch("fatloss.desktop.controllers.weight_controller.ErrorHandler")
    def test_get_user_by_id_error(self, mock_error_handler, controller):
        """测试根据ID获取用户 - 异常"""
        # Arrange
        user_id = 1
        
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.users.get_by_id.side_effect = Exception("Database error")
        
        # Act
        result = controller.get_user_by_id(user_id)
        
        # Assert
        assert result is None
        mock_error_handler.handle_service_error.assert_called_once()
    
    # 测试get_all_users方法
    
    def test_get_all_users_success(self, controller, mock_planner_service, sample_user):
        """测试获取所有用户成功"""
        # Arrange
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.users.get_all.return_value = [sample_user]
        
        # Act
        result = controller.get_all_users()
        
        # Assert
        assert len(result) == 1
        assert result[0] == sample_user
        mock_uow.users.get_all.assert_called_once()
    
    def test_get_all_users_error(self, controller, mock_planner_service):
        """测试获取所有用户 - 错误"""
        # Arrange
        mock_uow = self.mock_unit_of_work.return_value
        mock_uow.users.get_all.side_effect = Exception("数据库错误")
        
        # Act
        result = controller.get_all_users()
        
        # Assert
        assert result == []

    # 缺失测试：_validate_weight_input 验证失败 (备注过长)
    def test_validate_weight_input_notes_too_long(self, controller):
        """测试验证体重输入 - 备注过长"""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="备注长度不能超过"):
            controller._validate_weight_input(
                weight_kg=70.0,
                notes="a" * 501  # 超过 500 字符
            )
