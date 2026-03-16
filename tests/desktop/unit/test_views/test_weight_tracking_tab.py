"""Tests for WeightTrackingTab."""

import pytest
from datetime import date
from unittest.mock import MagicMock, Mock, patch

from PyQt5.QtWidgets import QApplication

from fatloss.desktop.views.widgets.weight_tracking_tab import WeightTrackingTab
from fatloss.desktop.controllers.weight_controller import WeightController
from fatloss.models.user_profile import UserProfile, Gender, ActivityLevel
from fatloss.models.weight_record import WeightRecord


@pytest.fixture
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def mock_weight_controller():
    """Create a mock weight controller."""
    controller = MagicMock(spec=WeightController)
    controller.get_all_users.return_value = []
    controller.get_user_by_id.return_value = None
    controller.get_weight_history.return_value = []
    controller.get_weight_stats.return_value = {
        "count": 0,
        "latest_weight": None,
        "min_weight": None,
        "max_weight": None,
        "avg_weight": None,
        "total_change": 0,
        "avg_daily_change": 0
    }
    return controller


@pytest.fixture
def weight_tab(mock_weight_controller, qapp):
    """Create WeightTrackingTab instance for testing."""
    tab = WeightTrackingTab(mock_weight_controller)
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


class TestWeightTrackingTabInitialization:
    """Tests for tab initialization."""

    def test_initialization(self, weight_tab, mock_weight_controller):
        """Test that tab initializes correctly."""
        assert weight_tab.weight_controller == mock_weight_controller
        assert weight_tab.table_model is None
        assert weight_tab.current_selection is None
        assert weight_tab.selected_user is None
        
        # Check UI components exist
        assert weight_tab.user_combo is not None
        assert weight_tab.record_btn is not None
        assert weight_tab.weight_table is not None

    def test_load_users_empty(self, weight_tab, mock_weight_controller):
        """Test loading users when no users exist."""
        mock_weight_controller.get_all_users.return_value = []
        
        weight_tab._load_users()
        
        # Should have placeholder item
        assert weight_tab.user_combo.count() == 1
        assert weight_tab.user_combo.itemText(0) == "-- 请选择用户 --"

    def test_load_users_with_data(self, weight_tab, mock_weight_controller, sample_user):
        """Test loading users with data."""
        mock_weight_controller.get_all_users.return_value = [sample_user]
        
        weight_tab._load_users()
        
        # Should have placeholder + user items
        assert weight_tab.user_combo.count() == 2
        assert weight_tab.user_combo.itemText(0) == "-- 请选择用户 --"
        assert "Test User" in weight_tab.user_combo.itemText(1)

    def test_on_user_selected_none(self, weight_tab, mock_weight_controller):
        """Test selecting placeholder item."""
        weight_tab.user_combo.setCurrentIndex(0)
        weight_tab._on_user_selected(0)
        
        assert weight_tab.selected_user is None
        assert not weight_tab.record_btn.isEnabled()

    def test_on_user_selected_valid(self, weight_tab, mock_weight_controller, sample_user):
        """Test selecting a valid user."""
        mock_weight_controller.get_user_by_id.return_value = sample_user
        
        # First load users
        weight_tab.user_combo.addItem("Test User (30岁)", 1)
        weight_tab.user_combo.setCurrentIndex(1)
        
        weight_tab._on_user_selected(1)
        
        assert weight_tab.selected_user == sample_user
        assert weight_tab.record_btn.isEnabled()

    def test_record_button_disabled_without_user(self, weight_tab):
        """Test record button is disabled when no user selected."""
        assert not weight_tab.record_btn.isEnabled()

    def test_clear_form(self, weight_tab):
        """Test clearing form content."""
        weight_tab.weight_spin.setValue(80.0)
        weight_tab.notes_edit.setPlainText("Test notes")
        
        weight_tab._clear_form()
        
        assert weight_tab.weight_spin.value() == weight_tab.DEFAULT_WEIGHT_KG
        assert weight_tab.notes_edit.toPlainText() == ""


class TestWeightTrackingTabWeightRecording:
    """Tests for weight recording functionality."""

    def test_record_weight_without_user(self, weight_tab):
        """Test recording weight without user selected."""
        weight_tab._on_record_weight()
        
        # Should not proceed with recording
        # (Error handler would show warning, but we just check no exception)

    def test_record_weight_with_user(self, weight_tab, mock_weight_controller, sample_user):
        """Test recording weight with user selected."""
        mock_weight_controller.get_user_by_id.return_value = sample_user
        
        mock_record = Mock(spec=WeightRecord)
        mock_weight_controller.record_weight.return_value = mock_record
        
        # Simulate user selection
        weight_tab.user_combo.addItem("Test User (30岁)", 1)
        weight_tab.user_combo.setCurrentIndex(1)
        weight_tab._on_user_selected(1)
        
        # Set weight value
        weight_tab.weight_spin.setValue(75.5)
        
        # Trigger recording
        weight_tab._on_record_weight()
        
        # Verify recording was called
        mock_weight_controller.record_weight.assert_called()
        assert mock_weight_controller.record_weight.call_args[1]['weight_kg'] == 75.5

    def test_on_new_record(self, weight_tab, mock_weight_controller, sample_user):
        """Test new record operation."""
        mock_weight_controller.get_user_by_id.return_value = sample_user
        
        # Simulate user selection
        weight_tab.user_combo.addItem("Test User (30岁)", 1)
        weight_tab.user_combo.setCurrentIndex(1)
        weight_tab._on_user_selected(1)
        
        # Trigger new record
        weight_tab._on_new_record()
        
        # Should focus on weight spin (can't easily test focus, but no exception)
        assert weight_tab.selected_user is not None


class TestWeightTrackingTabSignals:
    """Tests for signal emissions."""

    def test_weight_recorded_signal(self, weight_tab, mock_weight_controller, sample_user):
        """Test that weight_recorded signal is emitted."""
        mock_weight_controller.get_user_by_id.return_value = sample_user
        
        # Create a real WeightRecord instance
        mock_record = WeightRecord(
            id=1,
            user_id=sample_user.id,
            weight_kg=75.5,
            record_date=date.today(),
            notes="Test weight record"
        )
        mock_weight_controller.record_weight.return_value = mock_record
        
        # Connect to signal
        signal_emitted = []
        weight_tab.weight_recorded.connect(lambda record: signal_emitted.append(record))
        
        # Simulate user selection
        weight_tab.user_combo.addItem("Test User (30岁)", 1)
        weight_tab.user_combo.setCurrentIndex(1)
        weight_tab._on_user_selected(1)
        
        # Trigger recording
        weight_tab._on_record_weight()
        
        assert len(signal_emitted) == 1
        assert signal_emitted[0] == mock_record


class TestWeightTrackingTabHistory:
    """Tests for history functionality."""

    def test_load_weight_history_no_user(self, weight_tab):
        """Test loading history without user selected."""
        weight_tab.selected_user = None
        weight_tab._load_weight_history()
        
        # Should not call controller
        mock_weight_controller = weight_tab.weight_controller
        mock_weight_controller.get_weight_history.assert_not_called()

    def test_load_weight_history_with_user(self, weight_tab, mock_weight_controller, sample_user):
        """Test loading history with user selected."""
        mock_weight_controller.get_user_by_id.return_value = sample_user
        
        mock_record = Mock(spec=WeightRecord)
        mock_weight_controller.get_weight_history.return_value = [mock_record]
        
        # Set selected user
        weight_tab.selected_user = sample_user
        
        weight_tab._load_weight_history()
        
        mock_weight_controller.get_weight_history.assert_called_with(
            user_id=1, limit=100, descending=True
        )


class TestWeightTrackingTabRefresh:
    """Tests for refresh functionality."""

    def test_refresh(self, weight_tab, mock_weight_controller, sample_user):
        """Test refresh method."""
        mock_weight_controller.get_user_by_id.return_value = sample_user
        mock_weight_controller.get_all_users.return_value = [sample_user]
        
        # Mock history
        mock_record = Mock(spec=WeightRecord)
        mock_weight_controller.get_weight_history.return_value = [mock_record]
        
        # Set selected user in combo box
        weight_tab.user_combo.addItem("Test User (30岁)", sample_user.id)
        weight_tab.user_combo.setCurrentIndex(1)
        weight_tab._on_user_selected(1)
        
        # Now refresh should reload users and still have selected user
        weight_tab.refresh()
        
        # Verify controllers were called
        mock_weight_controller.get_all_users.assert_called()
        # Note: get_weight_history is only called if selected_user is set
        # But refresh() calls _load_users() first which clears the combo and resets selected_user
        # So we can't verify get_weight_history was called in this test setup

    def test_set_selected_user(self, weight_tab, mock_weight_controller, sample_user):
        """Test setting selected user."""
        mock_weight_controller.get_user_by_id.return_value = sample_user
        
        # Add user to combo
        weight_tab.user_combo.addItem("Test User (30岁)", 1)
        
        weight_tab.set_selected_user(sample_user)
        
        assert weight_tab.selected_user == sample_user


class TestWeightTrackingTabEdgeCases:
    """Tests for edge cases."""

    def test_user_selection_with_exception(self, weight_tab, mock_weight_controller):
        """Test error handling when loading users fails."""
        mock_weight_controller.get_all_users.side_effect = Exception("Database error")
        
        # Should not raise exception
        weight_tab._load_users()
        
        # Should have only placeholder item
        assert weight_tab.user_combo.count() == 1

    def test_record_weight_with_exception(self, weight_tab, mock_weight_controller, sample_user):
        """Test error handling when recording weight fails."""
        mock_weight_controller.get_user_by_id.return_value = sample_user
        mock_weight_controller.record_weight.side_effect = Exception("Database error")
        
        # Simulate user selection
        weight_tab.user_combo.addItem("Test User (30岁)", 1)
        weight_tab.user_combo.setCurrentIndex(1)
        weight_tab._on_user_selected(1)
        
        # Should not raise exception
        weight_tab._on_record_weight()
