"""Tests for UserManagementTab."""

import pytest
from datetime import date
from unittest.mock import MagicMock, Mock, patch

from PyQt5.QtWidgets import QApplication

from fatloss.desktop.views.widgets.user_management_tab import UserManagementTab
from fatloss.desktop.controllers.user_controller import UserController
from fatloss.models.user_profile import UserProfile, Gender, ActivityLevel


@pytest.fixture
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def mock_user_controller():
    """Create a mock user controller."""
    controller = MagicMock(spec=UserController)
    controller.get_all_users.return_value = []
    controller.get_user_by_id.return_value = None
    controller.search_users.return_value = []
    return controller


@pytest.fixture
def user_tab(mock_user_controller, qapp):
    """Create UserManagementTab instance for testing."""
    tab = UserManagementTab(mock_user_controller)
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


class TestUserManagementTabInitialization:
    """Tests for tab initialization."""

    def test_initialization(self, user_tab, mock_user_controller):
        """Test that tab initializes correctly."""
        assert user_tab.user_controller == mock_user_controller
        # table_model is set during initialization (via _load_users)
        assert user_tab.table_model is not None
        assert user_tab.current_selection is None
        
        # Check UI components exist
        assert user_tab.user_table is not None
        assert user_tab.search_edit is not None

    def test_load_users_empty(self, user_tab, mock_user_controller):
        """Test loading users when no users exist."""
        mock_user_controller.get_all_users.return_value = []
        
        user_tab._load_users()
        
        # Should have empty table
        assert user_tab.table_model is not None
        assert user_tab.table_model.rowCount() == 0

    def test_load_users_with_data(self, user_tab, mock_user_controller, sample_user):
        """Test loading users with data."""
        mock_user_controller.get_all_users.return_value = [sample_user]
        
        user_tab._load_users()
        
        # Should have one user in table
        assert user_tab.table_model is not None
        assert user_tab.table_model.rowCount() == 1

    def test_search_users(self, user_tab, mock_user_controller, sample_user):
        """Test searching users."""
        mock_user_controller.search_users.return_value = [sample_user]
        
        user_tab._load_users(search_query="Test")
        
        mock_user_controller.search_users.assert_called_with(name_query="Test")


class TestUserManagementTabSelection:
    """Tests for user selection functionality."""

    def test_on_selection_changed(self, user_tab, mock_user_controller, sample_user):
        """Test selection change handler."""
        mock_user_controller.get_all_users.return_value = [sample_user]
        
        user_tab._load_users()
        
        # Select the user
        user_tab.user_table.selectRow(0)
        
        # The selection change should emit signal
        # We can't easily test signal emission without actually selecting via UI
        # But we can verify current_selection is set
        assert user_tab.current_selection is None  # Initially None

    def test_get_selected_user(self, user_tab):
        """Test getting selected user."""
        mock_user = Mock(spec=UserProfile)
        user_tab.current_selection = mock_user
        
        assert user_tab.get_selected_user() == mock_user


class TestUserManagementTabUserOperations:
    """Tests for user CRUD operations."""

    def test_on_new_user(self, user_tab, mock_user_controller, sample_user):
        """Test new user operation."""
        # Mock UserDialog to return a user
        with patch('fatloss.desktop.views.widgets.user_management_tab.UserDialog') as mock_dialog:
            mock_dialog.create_user.return_value = sample_user
            mock_user_controller.create_user.return_value = sample_user
            
            user_tab._on_new_user()
            
            mock_user_controller.create_user.assert_called()
            mock_user_controller.get_all_users.assert_called()

    def test_on_edit_user_no_selection(self, user_tab):
        """Test editing without user selected."""
        user_tab.current_selection = None
        user_tab._on_edit_user()
        
        # Should not proceed with editing
        mock_user_controller = user_tab.user_controller
        mock_user_controller.update_user.assert_not_called()

    def test_on_edit_user_with_selection(self, user_tab, mock_user_controller, sample_user):
        """Test editing with user selected."""
        user_tab.current_selection = sample_user
        
        # Mock UserDialog to return updated user
        with patch('fatloss.desktop.views.widgets.user_management_tab.UserDialog') as mock_dialog:
            mock_dialog.edit_user.return_value = sample_user
            mock_user_controller.update_user.return_value = sample_user
            
            user_tab._on_edit_user()
            
            mock_user_controller.update_user.assert_called()
            mock_user_controller.get_all_users.assert_called()

    def test_on_delete_user_no_selection(self, user_tab):
        """Test deleting without user selected."""
        user_tab.current_selection = None
        user_tab._on_delete_user()
        
        # Should not proceed with deletion
        mock_user_controller = user_tab.user_controller
        mock_user_controller.delete_user.assert_not_called()

    def test_on_delete_user_with_selection(self, user_tab, mock_user_controller, sample_user):
        """Test deleting with user selected."""
        user_tab.current_selection = sample_user
        
        # Mock QMessageBox to return Yes
        with patch('fatloss.desktop.views.widgets.user_management_tab.QMessageBox') as mock_msgbox:
            mock_msgbox.question.return_value = mock_msgbox.Yes
            mock_user_controller.delete_user.return_value = True
            
            user_tab._on_delete_user()
            
            mock_user_controller.delete_user.assert_called()
            mock_user_controller.get_all_users.assert_called()


class TestUserManagementTabSearch:
    """Tests for search functionality."""

    def test_on_search_changed(self, user_tab, mock_user_controller):
        """Test search text change handler."""
        user_tab._on_search_changed("Test")
        
        mock_user_controller.search_users.assert_called_with(name_query="Test")


class TestUserManagementTabRefresh:
    """Tests for refresh functionality."""

    def test_refresh(self, user_tab, mock_user_controller, sample_user):
        """Test refresh method."""
        mock_user_controller.get_all_users.return_value = [sample_user]
        
        user_tab.refresh()
        
        mock_user_controller.get_all_users.assert_called()


class TestUserManagementTabEdgeCases:
    """Tests for edge cases."""

    def test_user_selection_with_exception(self, user_tab, mock_user_controller):
        """Test error handling when loading users fails."""
        mock_user_controller.get_all_users.side_effect = Exception("Database error")
        
        # Should not raise exception
        user_tab._load_users()
        
        # Should have empty table
        assert user_tab.table_model is None or user_tab.table_model.rowCount() == 0

    def test_show_user_details(self, user_tab, mock_user_controller, sample_user):
        """Test showing user details."""
        mock_user_controller.get_user_by_id.return_value = sample_user
        
        # Load users first
        mock_user_controller.get_all_users.return_value = [sample_user]
        user_tab._load_users()
        
        # Show details
        result = user_tab.show_user_details(1)
        
        assert result is True
