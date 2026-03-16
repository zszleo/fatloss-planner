"""Tests for PlanManagementTab."""

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, Mock, patch

from PyQt5.QtWidgets import QApplication

from fatloss.desktop.views.widgets.plan_management_tab import PlanManagementTab
from fatloss.desktop.controllers.plan_controller import PlanController
from fatloss.models.user_profile import UserProfile, Gender, ActivityLevel
from fatloss.models.nutrition_plan import DailyNutritionPlan, WeeklyNutritionPlan


@pytest.fixture
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def mock_plan_controller():
    """Create a mock plan controller."""
    controller = MagicMock(spec=PlanController)
    controller.get_all_users.return_value = []
    controller.get_user_by_id.return_value = None
    controller.get_available_weeks.return_value = []
    return controller


@pytest.fixture
def plan_tab(mock_plan_controller, qapp):
    """Create PlanManagementTab instance for testing."""
    tab = PlanManagementTab(mock_plan_controller)
    return tab


@pytest.fixture
def sample_user():
    """Create a sample UserProfile for testing."""
    return UserProfile(
        id=1,
        name="Test User",
        gender=Gender.MALE,
        birth_date=date(1990, 1, 1),
        height_cm=175.0,
        initial_weight_kg=70.0,
        activity_level=ActivityLevel.MODERATE
    )


class TestPlanManagementTabInitialization:
    """Tests for tab initialization."""

    def test_initialization(self, plan_tab, mock_plan_controller):
        """Test that tab initializes correctly."""
        assert plan_tab.plan_controller == mock_plan_controller
        assert plan_tab.selected_user is None
        assert plan_tab.selected_date is not None
        
        # Check UI components exist
        assert plan_tab.user_combo is not None
        assert plan_tab.week_combo is not None
        assert plan_tab.calendar is not None

    def test_load_users_empty(self, plan_tab, mock_plan_controller):
        """Test loading users when no users exist."""
        mock_plan_controller.get_all_users.return_value = []
        
        plan_tab._load_users()
        
        # Should have placeholder item
        assert plan_tab.user_combo.count() == 1
        assert plan_tab.user_combo.itemText(0) == "-- 请选择用户 --"

    def test_load_users_with_data(self, plan_tab, mock_plan_controller):
        """Test loading users with data."""
        mock_user = Mock(spec=UserProfile)
        mock_user.name = "Test User"
        mock_user.age = 30
        mock_user.id = 1
        mock_plan_controller.get_all_users.return_value = [mock_user]
        
        plan_tab._load_users()
        
        # Should have placeholder + user items
        assert plan_tab.user_combo.count() == 2
        assert plan_tab.user_combo.itemText(0) == "-- 请选择用户 --"
        assert "Test User" in plan_tab.user_combo.itemText(1)

    def test_on_user_selected_none(self, plan_tab, mock_plan_controller):
        """Test selecting placeholder item."""
        plan_tab.user_combo.setCurrentIndex(0)
        plan_tab._on_user_selected(0)
        
        assert plan_tab.selected_user is None

    def test_on_user_selected_valid(self, plan_tab, mock_plan_controller, sample_user):
        """Test selecting a valid user."""
        mock_plan_controller.get_user_by_id.return_value = sample_user
        
        # First load users
        plan_tab.user_combo.addItem("Test User (30岁)", 1)
        plan_tab.user_combo.setCurrentIndex(1)
        
        plan_tab._on_user_selected(1)
        
        assert plan_tab.selected_user == sample_user

    def test_get_monday(self, plan_tab):
        """Test getting Monday of a week."""
        # Test with Wednesday
        wednesday = date(2026, 3, 12)  # Thursday actually, but let's test logic
        # Actually let's use a known Monday
        known_monday = date(2026, 3, 9)  # Monday
        test_date = date(2026, 3, 11)  # Wednesday
        
        monday = plan_tab._get_monday(test_date)
        assert monday == known_monday


class TestPlanManagementTabWeekManagement:
    """Tests for week management functionality."""

    def test_load_available_weeks_no_user(self, plan_tab):
        """Test loading available weeks without user selected."""
        plan_tab.selected_user = None
        plan_tab._load_available_weeks()
        
        # Should not call controller
        mock_plan_controller = plan_tab.plan_controller
        mock_plan_controller.get_available_weeks.assert_not_called()

    def test_load_available_weeks_with_user(self, plan_tab, mock_plan_controller, sample_user):
        """Test loading available weeks with user selected."""
        mock_plan_controller.get_user_by_id.return_value = sample_user
        
        # Mock available weeks
        week_start = date(2026, 3, 9)  # Monday
        mock_plan_controller.get_available_weeks.return_value = [week_start]
        
        # Set selected user
        plan_tab.selected_user = sample_user
        
        plan_tab._load_available_weeks()
        
        mock_plan_controller.get_available_weeks.assert_called_with(1)

    def test_on_week_selected_none(self, plan_tab):
        """Test selecting placeholder week."""
        plan_tab.week_combo.setCurrentIndex(0)
        plan_tab._on_week_selected(0)
        
        # Should not change selected week
        assert plan_tab.selected_week_start is not None

    def test_on_week_selected_new(self, plan_tab, mock_plan_controller):
        """Test selecting 'new week' option."""
        mock_user = Mock(spec=UserProfile)
        mock_user.id = 1
        mock_plan_controller.get_user_by_id.return_value = mock_user
        mock_plan_controller.generate_weekly_plan.return_value = Mock()
        
        # Simulate user selection and week selection
        plan_tab.selected_user = mock_user
        plan_tab.week_combo.addItem("新建周计划...", "new")
        plan_tab.week_combo.setCurrentIndex(1)
        
        # This would trigger _generate_weekly_plan which shows a dialog
        # We can't test the dialog interaction easily, but we can verify no exception
        plan_tab._on_week_selected(1)


class TestPlanManagementTabPlanManagement:
    """Tests for plan management functionality."""

    def test_generate_weekly_plan_no_user(self, plan_tab):
        """Test generating weekly plan without user selected."""
        plan_tab.selected_user = None
        plan_tab._generate_weekly_plan()
        
        # Should not proceed with generation
        mock_plan_controller = plan_tab.plan_controller
        mock_plan_controller.generate_weekly_plan.assert_not_called()

    def test_save_daily_plan_no_user(self, plan_tab):
        """Test saving daily plan without user selected."""
        plan_tab.selected_user = None
        plan_tab._save_daily_plan()
        
        # Should not proceed with saving
        mock_plan_controller = plan_tab.plan_controller
        mock_plan_controller.update_daily_plan.assert_not_called()


class TestPlanManagementTabSignals:
    """Tests for signal emissions."""

    def test_user_selected_signal(self, plan_tab, mock_plan_controller, sample_user):
        """Test that user_selected signal is emitted."""
        mock_plan_controller.get_user_by_id.return_value = sample_user
        
        # Connect to signal
        signal_emitted = []
        plan_tab.user_selected.connect(lambda user: signal_emitted.append(user))
        
        # Simulate user selection by directly calling _on_user_selected
        # We need to set the user_combo itemData first
        plan_tab.user_combo.clear()
        plan_tab.user_combo.addItem("-- 请选择用户 --", None)
        plan_tab.user_combo.addItem("Test User (30岁)", sample_user.id)
        
        # Simulate user selection by directly calling _on_user_selected
        # (not through combo box signal which would trigger it twice)
        plan_tab._on_user_selected(1)  # Index 1 (after placeholder at index 0)
        
        assert len(signal_emitted) == 1
        assert signal_emitted[0] == sample_user


class TestPlanManagementTabRefresh:
    """Tests for refresh functionality."""

    def test_refresh(self, plan_tab, mock_plan_controller, sample_user):
        """Test refresh method."""
        mock_plan_controller.get_user_by_id.return_value = sample_user
        mock_plan_controller.get_all_users.return_value = [sample_user]
        
        # Set selected user
        plan_tab.selected_user = sample_user
        
        plan_tab.refresh()
        
        # Verify controllers were called
        mock_plan_controller.get_all_users.assert_called()


class TestPlanManagementTabEdgeCases:
    """Tests for edge cases."""

    def test_user_selection_with_exception(self, plan_tab, mock_plan_controller):
        """Test error handling when loading users fails."""
        mock_plan_controller.get_all_users.side_effect = Exception("Database error")
        
        # Should not raise exception
        plan_tab._load_users()
        
        # Should have only placeholder item
        assert plan_tab.user_combo.count() == 1

    def test_load_daily_plan_no_user(self, plan_tab):
        """Test loading daily plan without user selected."""
        plan_tab.selected_user = None
        plan_tab._load_daily_plan(date.today())
        
        # Should not call controller
        mock_plan_controller = plan_tab.plan_controller
        mock_plan_controller.get_daily_plans_for_week.assert_not_called()
