"""Tests for SettingsTab."""

import pytest
from unittest.mock import MagicMock, Mock, patch

from PyQt5.QtWidgets import QApplication

from fatloss.desktop.views.widgets.settings_tab import SettingsTab
from fatloss.desktop.controllers.settings_controller import SettingsController
from fatloss.models.app_config import AppConfig
from fatloss.models.enums import UnitSystem, Theme


@pytest.fixture
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def mock_settings_controller():
    """Create a mock settings controller."""
    controller = MagicMock(spec=SettingsController)
    controller.get_all_users.return_value = []
    controller.get_user_by_id.return_value = None
    controller.get_config.return_value = None
    controller.get_database_info.return_value = {
        "path": "/test/db.db",
        "exists": True,
        "size_mb": 1.5,
        "table_count": 10,
        "total_records": 100,
        "last_modified": 1234567890
    }
    return controller


@pytest.fixture
def settings_tab(mock_settings_controller, qapp):
    """Create SettingsTab instance for testing."""
    tab = SettingsTab(mock_settings_controller)
    return tab


@pytest.fixture
def sample_config():
    """Create a sample AppConfig for testing."""
    return AppConfig(
        user_id=1,
        unit_system=UnitSystem.METRIC,
        theme=Theme.LIGHT,
        language="zh-CN",
        weekly_check_day=1,
        carb_adjustment_unit_g=30,
        monthly_loss_percentage=0.05,
        exercise_calories_per_minute=10,
        enable_notifications=True,
        data_retention_days=365
    )


class TestSettingsTabInitialization:
    """Tests for tab initialization."""

    def test_initialization(self, settings_tab, mock_settings_controller):
        """Test that tab initializes correctly."""
        assert settings_tab.settings_controller == mock_settings_controller
        assert settings_tab.selected_user is None
        assert settings_tab.current_config is None
        
        # Check UI components exist
        assert settings_tab.user_combo is not None
        assert settings_tab.tab_widget is not None

    def test_load_users_empty(self, settings_tab, mock_settings_controller):
        """Test loading users when no users exist."""
        mock_settings_controller.get_all_users.return_value = []
        
        settings_tab._load_users()
        
        # Should have placeholder item
        assert settings_tab.user_combo.count() == 1
        assert settings_tab.user_combo.itemText(0) == "-- 请选择用户 --"

    def test_load_users_with_data(self, settings_tab, mock_settings_controller):
        """Test loading users with data."""
        mock_user = {"id": 1, "name": "Test User", "age": 30}
        mock_settings_controller.get_all_users.return_value = [mock_user]
        
        settings_tab._load_users()
        
        # Should have placeholder + user items
        assert settings_tab.user_combo.count() == 2
        assert settings_tab.user_combo.itemText(0) == "-- 请选择用户 --"
        assert "Test User" in settings_tab.user_combo.itemText(1)


class TestSettingsTabUserSelection:
    """Tests for user selection functionality."""

    def test_on_user_selected_none(self, settings_tab, mock_settings_controller):
        """Test selecting placeholder item."""
        settings_tab.user_combo.setCurrentIndex(0)
        settings_tab._on_user_selected(0)
        
        assert settings_tab.selected_user is None

    def test_on_user_selected_valid(self, settings_tab, mock_settings_controller):
        """Test selecting a valid user."""
        mock_user = {"id": 1, "name": "Test User", "age": 30}
        mock_settings_controller.get_user_by_id.return_value = mock_user
        mock_settings_controller.get_config.return_value = Mock(spec=AppConfig)
        
        # First load users
        settings_tab.user_combo.addItem("Test User (30岁)", 1)
        settings_tab.user_combo.setCurrentIndex(1)
        
        settings_tab._on_user_selected(1)
        
        assert settings_tab.selected_user == mock_user


class TestSettingsTabConfigManagement:
    """Tests for configuration management."""

    def test_save_config_no_user(self, settings_tab):
        """Test saving config without user selected."""
        settings_tab.selected_user = None
        settings_tab._save_config()
        
        # Should not proceed with saving
        mock_settings_controller = settings_tab.settings_controller
        mock_settings_controller.save_config.assert_not_called()

    def test_save_config_with_user(self, settings_tab, mock_settings_controller, sample_config):
        """Test saving config with user selected."""
        mock_user = {"id": 1, "name": "Test User", "age": 30}
        mock_settings_controller.save_config.return_value = sample_config
        
        settings_tab.selected_user = mock_user
        
        # Connect to signal
        signal_emitted = []
        settings_tab.config_saved.connect(lambda config: signal_emitted.append(config))
        
        settings_tab._save_config()
        
        mock_settings_controller.save_config.assert_called()
        assert len(signal_emitted) == 1
        assert signal_emitted[0] == sample_config

    def test_reset_to_defaults_no_user(self, settings_tab):
        """Test resetting to defaults without user selected."""
        settings_tab.selected_user = None
        settings_tab._reset_to_defaults()
        
        # Should not proceed with resetting
        mock_settings_controller = settings_tab.settings_controller
        mock_settings_controller.save_config.assert_not_called()


class TestSettingsTabDatabaseManagement:
    """Tests for database management functionality."""

    def test_backup_database_no_path(self, settings_tab):
        """Test backup without path selected."""
        settings_tab.backup_path_edit.setText("")
        settings_tab._backup_database()
        
        # Should not proceed with backup
        mock_settings_controller = settings_tab.settings_controller
        mock_settings_controller.backup_database.assert_not_called()

    def test_restore_database_no_path(self, settings_tab):
        """Test restore without path selected."""
        settings_tab.restore_path_edit.setText("")
        settings_tab._restore_database()
        
        # Should not proceed with restore
        mock_settings_controller = settings_tab.settings_controller
        mock_settings_controller.restore_database.assert_not_called()


class TestSettingsTabExport:
    """Tests for data export functionality."""

    def test_export_user_data_no_user(self, settings_tab):
        """Test exporting data without user selected."""
        settings_tab.selected_user = None
        settings_tab._export_user_data()
        
        # Should not proceed with export
        mock_settings_controller = settings_tab.settings_controller
        mock_settings_controller.export_user_data.assert_not_called()

    def test_export_user_data_no_path(self, settings_tab):
        """Test exporting data without path selected."""
        mock_user = {"id": 1, "name": "Test User", "age": 30}
        settings_tab.selected_user = mock_user
        settings_tab.export_path_edit.setText("")
        
        settings_tab._export_user_data()
        
        # Should not proceed with export
        mock_settings_controller = settings_tab.settings_controller
        mock_settings_controller.export_user_data.assert_not_called()


class TestSettingsTabSignals:
    """Tests for signal emissions."""

    def test_config_saved_signal(self, settings_tab, mock_settings_controller, sample_config):
        """Test that config_saved signal is emitted."""
        mock_user = {"id": 1, "name": "Test User", "age": 30}
        mock_settings_controller.save_config.return_value = sample_config
        
        settings_tab.selected_user = mock_user
        
        # Connect to signal
        signal_emitted = []
        settings_tab.config_saved.connect(lambda config: signal_emitted.append(config))
        
        settings_tab._save_config()
        
        assert len(signal_emitted) == 1
        assert signal_emitted[0] == sample_config


class TestSettingsTabRefresh:
    """Tests for refresh functionality."""

    def test_refresh(self, settings_tab, mock_settings_controller):
        """Test refresh method."""
        mock_user = {"id": 1, "name": "Test User", "age": 30}
        mock_settings_controller.get_all_users.return_value = [mock_user]
        
        # Set selected user
        settings_tab.selected_user = mock_user
        
        settings_tab.refresh()
        
        # Verify controllers were called
        mock_settings_controller.get_all_users.assert_called()


class TestSettingsTabEdgeCases:
    """Tests for edge cases."""

    def test_user_selection_with_exception(self, settings_tab, mock_settings_controller):
        """Test error handling when loading users fails."""
        mock_settings_controller.get_all_users.side_effect = Exception("Database error")
        
        # Should not raise exception
        settings_tab._load_users()
        
        # Should have only placeholder item
        assert settings_tab.user_combo.count() == 1

    def test_load_config_with_exception(self, settings_tab, mock_settings_controller):
        """Test error handling when loading config fails."""
        mock_user = {"id": 1, "name": "Test User", "age": 30}
        mock_settings_controller.get_config.side_effect = Exception("Database error")
        
        settings_tab.selected_user = mock_user
        
        # Should not raise exception
        settings_tab._load_config()
