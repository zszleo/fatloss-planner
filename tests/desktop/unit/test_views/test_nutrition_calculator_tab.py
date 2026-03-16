"""Tests for NutritionCalculatorTab."""

import pytest
from datetime import date
from unittest.mock import MagicMock, Mock, patch

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from fatloss.desktop.views.widgets.nutrition_calculator_tab import NutritionCalculatorTab
from fatloss.desktop.controllers.nutrition_controller import NutritionController
from fatloss.models.user_profile import UserProfile
from fatloss.models.nutrition_plan import DailyNutritionPlan


# Use qapp fixture from conftest.py (automatic via pytest-qt)


@pytest.fixture
def mock_nutrition_controller():
    """Create a mock nutrition controller."""
    controller = MagicMock(spec=NutritionController)
    controller.get_all_users.return_value = []
    controller.get_user_by_id.return_value = None
    controller.get_user_nutrition_history.return_value = []
    return controller


@pytest.fixture
def nutrition_tab(mock_nutrition_controller, qapp):
    """Create NutritionCalculatorTab instance for testing."""
    tab = NutritionCalculatorTab(mock_nutrition_controller)
    return tab


class TestNutritionCalculatorTabInitialization:
    """Tests for tab initialization."""

    def test_initialization(self, nutrition_tab, mock_nutrition_controller):
        """Test that tab initializes correctly."""
        assert nutrition_tab.nutrition_controller == mock_nutrition_controller
        assert nutrition_tab.table_model is None
        assert nutrition_tab.current_selection is None
        assert nutrition_tab.selected_user is None
        
        # Check UI components exist
        assert nutrition_tab.user_combo is not None
        assert nutrition_tab.calculate_btn is not None
        assert nutrition_tab.result_text is not None

    def test_load_users_empty(self, nutrition_tab, mock_nutrition_controller):
        """Test loading users when no users exist."""
        mock_nutrition_controller.get_all_users.return_value = []
        
        nutrition_tab._load_users()
        
        # Should have placeholder item
        assert nutrition_tab.user_combo.count() == 1
        assert nutrition_tab.user_combo.itemText(0) == "-- 请选择用户 --"

    def test_load_users_with_data(self, nutrition_tab, mock_nutrition_controller):
        """Test loading users with data."""
        mock_user = Mock(spec=UserProfile)
        mock_user.name = "Test User"
        mock_user.age = 30
        mock_user.id = 1
        mock_nutrition_controller.get_all_users.return_value = [mock_user]
        
        nutrition_tab._load_users()
        
        # Should have placeholder + user items
        assert nutrition_tab.user_combo.count() == 2
        assert nutrition_tab.user_combo.itemText(0) == "-- 请选择用户 --"
        assert "Test User" in nutrition_tab.user_combo.itemText(1)

    def test_on_user_selected_none(self, nutrition_tab, mock_nutrition_controller):
        """Test selecting placeholder item."""
        nutrition_tab.user_combo.setCurrentIndex(0)
        nutrition_tab._on_user_selected(0)
        
        assert nutrition_tab.selected_user is None
        assert not nutrition_tab.calculate_btn.isEnabled()

    def test_on_user_selected_valid(self, nutrition_tab, mock_nutrition_controller):
        """Test selecting a valid user."""
        mock_user = Mock(spec=UserProfile)
        mock_user.name = "Test User"
        mock_user.age = 30
        mock_user.id = 1
        mock_user.gender = Mock(value="Male")
        mock_user.activity_level = Mock(value="Moderate")
        mock_user.height_cm = 175
        mock_nutrition_controller.get_user_by_id.return_value = mock_user
        
        # First load users
        nutrition_tab.user_combo.addItem("Test User (30岁)", 1)
        nutrition_tab.user_combo.setCurrentIndex(1)
        
        nutrition_tab._on_user_selected(1)
        
        assert nutrition_tab.selected_user == mock_user
        assert nutrition_tab.calculate_btn.isEnabled()

    def test_calculate_button_disabled_without_user(self, nutrition_tab):
        """Test calculate button is disabled when no user selected."""
        assert not nutrition_tab.calculate_btn.isEnabled()

    def test_clear_calculator(self, nutrition_tab):
        """Test clearing calculator content."""
        nutrition_tab.result_text.setPlainText("Test result")
        nutrition_tab.detail_text.setPlainText("Test detail")
        nutrition_tab.current_selection = Mock()
        
        nutrition_tab._clear_calculator()
        
        assert nutrition_tab.result_text.toPlainText() == ""
        assert nutrition_tab.detail_text.toPlainText() == ""
        assert nutrition_tab.current_selection is None


class TestNutritionCalculatorTabCalculations:
    """Tests for nutrition calculation functionality."""

    def test_calculate_button_enabled_with_user(self, nutrition_tab, mock_nutrition_controller):
        """Test that calculate button is enabled when user is selected."""
        mock_user = Mock(spec=UserProfile)
        mock_user.id = 1
        mock_user.name = "Test User"
        mock_user.age = 30
        mock_user.gender = Mock(value="Male")
        mock_user.activity_level = Mock(value="Moderate")
        mock_user.height_cm = 175
        mock_nutrition_controller.get_user_by_id.return_value = mock_user
        
        # Simulate user selection
        nutrition_tab.user_combo.addItem("Test User (30岁)", 1)
        nutrition_tab.user_combo.setCurrentIndex(1)
        nutrition_tab._on_user_selected(1)
        
        assert nutrition_tab.calculate_btn.isEnabled()

    def test_on_calculate_without_user(self, nutrition_tab):
        """Test calculation attempt without user selected."""
        nutrition_tab._on_calculate()
        
        # Should not proceed with calculation
        assert nutrition_tab.result_text.toPlainText() == ""

    def test_on_calculate_with_user(self, nutrition_tab, mock_nutrition_controller):
        """Test calculation with user selected."""
        mock_user = Mock(spec=UserProfile)
        mock_user.id = 1
        mock_user.name = "Test User"
        mock_user.age = 30
        mock_user.gender = Mock(value="Male")
        mock_user.activity_level = Mock(value="Moderate")
        mock_user.height_cm = 175
        mock_nutrition_controller.get_user_by_id.return_value = mock_user
        
        mock_plan = Mock(spec=DailyNutritionPlan)
        mock_nutrition_controller.calculate_nutrition_plan.return_value = mock_plan
        mock_nutrition_controller.format_nutrition_summary.return_value = "Test Summary"
        
        # Simulate user selection
        nutrition_tab.user_combo.addItem("Test User (30岁)", 1)
        nutrition_tab.user_combo.setCurrentIndex(1)
        nutrition_tab._on_user_selected(1)
        
        # Verify selected_user is set
        assert nutrition_tab.selected_user == mock_user
        
        # Trigger calculation
        nutrition_tab._on_calculate()
        
        # Verify calculation was called
        mock_nutrition_controller.calculate_nutrition_plan.assert_called()
        assert nutrition_tab.result_text.toPlainText() == "Test Summary"


class TestNutritionCalculatorTabSignals:
    """Tests for signal emissions."""

    def test_calculation_performed_signal(self, nutrition_tab, mock_nutrition_controller):
        """Test that calculation_performed signal is emitted."""
        mock_user = Mock(spec=UserProfile)
        mock_user.id = 1
        mock_user.name = "Test User"
        mock_user.age = 30
        mock_user.gender = Mock(value="Male")
        mock_user.activity_level = Mock(value="Moderate")
        mock_user.height_cm = 175
        mock_nutrition_controller.get_user_by_id.return_value = mock_user
        
        # Create a mock plan that is a valid DailyNutritionPlan instance
        from datetime import date
        from fatloss.calculator.nutrition_calculator import NutritionDistribution
        
        mock_plan = DailyNutritionPlan(
            user_id=1,
            plan_date=date.today(),
            target_tdee=2000.0,
            nutrition=NutritionDistribution(
                protein_g=150.0,
                carbohydrates_g=200.0,
                fat_g=50.0,
                total_calories=2000.0
            ),
            adjustment_units=0,
            notes="Test plan"
        )
        mock_nutrition_controller.calculate_nutrition_plan.return_value = mock_plan
        mock_nutrition_controller.format_nutrition_summary.return_value = "Test"
        mock_nutrition_controller.get_user_nutrition_history.return_value = []  # Mock history call
        
        # Connect to signal
        signal_emitted = []
        nutrition_tab.calculation_performed.connect(lambda plan: signal_emitted.append(plan))
        
        # Simulate user selection
        nutrition_tab.user_combo.addItem("Test User (30岁)", 1)
        nutrition_tab.user_combo.setCurrentIndex(1)
        nutrition_tab._on_user_selected(1)
        
        # Verify selected_user is set
        assert nutrition_tab.selected_user == mock_user
        
        # Trigger calculation
        nutrition_tab._on_calculate()
        
        assert len(signal_emitted) == 1
        assert signal_emitted[0] == mock_plan


class TestNutritionCalculatorTabRefresh:
    """Tests for refresh functionality."""

    def test_refresh(self, nutrition_tab, mock_nutrition_controller):
        """Test refresh method."""
        mock_user = Mock(spec=UserProfile)
        mock_user.id = 1
        mock_user.name = "Test User"
        mock_user.age = 30
        mock_user.gender = Mock(value="Male")
        mock_user.activity_level = Mock(value="Moderate")
        mock_user.height_cm = 175
        mock_nutrition_controller.get_user_by_id.return_value = mock_user
        mock_nutrition_controller.get_all_users.return_value = [mock_user]
        
        # Set selected user
        nutrition_tab.selected_user = mock_user
        
        # Mock history
        mock_plan = Mock(spec=DailyNutritionPlan)
        mock_nutrition_controller.get_user_nutrition_history.return_value = [mock_plan]
        
        nutrition_tab.refresh()
        
        # Verify controllers were called
        mock_nutrition_controller.get_all_users.assert_called()
        # refresh() calls _load_users() which clears the combo, so _on_user_selected isn't called
        # with the selected user anymore. The history won't be loaded unless a user is selected again.

    def test_set_selected_user(self, nutrition_tab, mock_nutrition_controller):
        """Test setting selected user."""
        mock_user = Mock(spec=UserProfile)
        mock_user.id = 1
        mock_user.name = "Test User"
        mock_user.age = 30
        mock_user.gender = Mock(value="Male")
        mock_user.activity_level = Mock(value="Moderate")
        mock_user.height_cm = 175
        mock_nutrition_controller.get_user_by_id.return_value = mock_user
        
        # Add user to combo
        nutrition_tab.user_combo.addItem("Test User (30岁)", 1)
        
        nutrition_tab.set_selected_user(mock_user)
        
        assert nutrition_tab.selected_user == mock_user


class TestNutritionCalculatorTabHistory:
    """Tests for history functionality."""

    def test_load_history_no_user(self, nutrition_tab):
        """Test loading history without user selected."""
        nutrition_tab.selected_user = None
        nutrition_tab._load_history()
        
        # Should not call controller
        mock_nutrition_controller = nutrition_tab.nutrition_controller
        mock_nutrition_controller.get_user_nutrition_history.assert_not_called()

    def test_load_history_with_user(self, nutrition_tab, mock_nutrition_controller):
        """Test loading history with user selected."""
        from datetime import date
        from fatloss.calculator.nutrition_calculator import NutritionDistribution
        
        mock_user = Mock(spec=UserProfile)
        mock_user.id = 1
        mock_nutrition_controller.get_user_by_id.return_value = mock_user
        
        # Create a proper mock DailyNutritionPlan with all required attributes
        mock_plan = Mock(spec=DailyNutritionPlan)
        mock_plan.plan_date = date(2026, 3, 12)
        mock_plan.target_tdee = 2000.0
        mock_plan.is_adjusted = False
        mock_plan.adjustment_units = 0
        mock_plan.nutrition = NutritionDistribution(
            carbohydrates_g=250.0,
            protein_g=150.0,
            fat_g=44.0,
            total_calories=2000.0
        )
        
        mock_nutrition_controller.get_user_nutrition_history.return_value = [mock_plan]
        
        # Set selected user
        nutrition_tab.selected_user = mock_user
        
        nutrition_tab._load_history()
        
        mock_nutrition_controller.get_user_nutrition_history.assert_called_with(
            user_id=1, limit=20
        )


class TestNutritionCalculatorTabEdgeCases:
    """Tests for edge cases."""

    def test_user_selection_with_exception(self, nutrition_tab, mock_nutrition_controller):
        """Test error handling when loading users fails."""
        mock_nutrition_controller.get_all_users.side_effect = Exception("Database error")
        
        # Should not raise exception
        nutrition_tab._load_users()
        
        # Should have only placeholder item
        assert nutrition_tab.user_combo.count() == 1

    def test_clear_calculator_with_none_values(self, nutrition_tab):
        """Test clearing calculator with None values."""
        nutrition_tab.result_text.setPlainText("")
        nutrition_tab.detail_text.setPlainText("")
        nutrition_tab.current_selection = None
        
        # Should not raise exception
        nutrition_tab._clear_calculator()
        
        assert nutrition_tab.result_text.toPlainText() == ""
        assert nutrition_tab.detail_text.toPlainText() == ""
        assert nutrition_tab.current_selection is None

    def test_load_history_exception_handling(self, nutrition_tab, mock_nutrition_controller, mocker):
        """Test exception handling in _load_history method."""
        # Mock controller to raise exception
        mock_nutrition_controller.get_user_nutrition_history.side_effect = Exception("Database error")
        
        # Mock ErrorHandler
        mock_error_handler = mocker.patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.ErrorHandler')
        
        # Set selected user
        nutrition_tab.selected_user = Mock(id=1)
        
        # Call method
        nutrition_tab._load_history()
        
        # Verify ErrorHandler was called
        mock_error_handler.handle_service_error.assert_called_once()

    def test_on_quick_calculate_with_plan(self, nutrition_tab, mock_nutrition_controller, mocker):
        """Test _on_quick_calculate when NutritionDialog returns a plan."""
        # Mock NutritionDialog.calculate_nutrition to return a plan
        mock_plan = Mock(spec=DailyNutritionPlan)
        mock_dialog = mocker.patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.NutritionDialog')
        mock_dialog.calculate_nutrition.return_value = mock_plan
        
        # Mock _load_history
        mock_load_history = mocker.patch.object(nutrition_tab, '_load_history')
        
        # Mock ErrorHandler.show_success
        mock_show_success = mocker.patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.ErrorHandler.show_success')
        
        # Set selected user
        nutrition_tab.selected_user = Mock()
        
        # Call method
        nutrition_tab._on_quick_calculate()
        
        # Verify dialog was called
        mock_dialog.calculate_nutrition.assert_called_once()
        # Verify _load_history was called
        mock_load_history.assert_called_once()
        # Verify success message was shown
        mock_show_success.assert_called_once()

    def test_on_quick_calculate_without_plan(self, nutrition_tab, mock_nutrition_controller, mocker):
        """Test _on_quick_calculate when NutritionDialog returns None."""
        # Mock NutritionDialog.calculate_nutrition to return None
        mock_dialog = mocker.patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.NutritionDialog')
        mock_dialog.calculate_nutrition.return_value = None
        
        # Mock _load_history
        mock_load_history = mocker.patch.object(nutrition_tab, '_load_history')
        
        # Set selected user
        nutrition_tab.selected_user = Mock()
        
        # Call method
        nutrition_tab._on_quick_calculate()
        
        # Verify dialog was called
        mock_dialog.calculate_nutrition.assert_called_once()
        # Verify _load_history was NOT called
        mock_load_history.assert_not_called()

    def test_on_save_plan_no_selection(self, nutrition_tab, mocker):
        """Test _on_save_plan with no selection."""
        # Mock ErrorHandler.show_warning
        mock_show_warning = mocker.patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.ErrorHandler.show_warning')
        
        # Set no current selection
        nutrition_tab.current_selection = None
        
        # Call method
        nutrition_tab._on_save_plan()
        
        # Verify warning was shown
        mock_show_warning.assert_called_once()

    def test_on_save_plan_with_selection_user_cancels(self, nutrition_tab, mocker):
        """Test _on_save_plan when user cancels the save dialog."""
        # Mock QMessageBox
        mock_qmessagebox = mocker.patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QMessageBox')
        mock_qmessagebox.question.return_value = mock_qmessagebox.No
        
        # Mock ErrorHandler.show_info
        mock_show_info = mocker.patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.ErrorHandler.show_info')
        
        # Set current selection
        nutrition_tab.current_selection = Mock()
        
        # Call method
        nutrition_tab._on_save_plan()
        
        # Verify QMessageBox was called
        mock_qmessagebox.question.assert_called_once()
        # Verify show_info was NOT called (user cancelled)
        mock_show_info.assert_not_called()

    def test_on_save_plan_with_selection_user_confirms(self, nutrition_tab, mocker):
        """Test _on_save_plan when user confirms the save dialog."""
        # Mock QMessageBox
        mock_qmessagebox = mocker.patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QMessageBox')
        mock_qmessagebox.question.return_value = mock_qmessagebox.Yes
        
        # Mock ErrorHandler.show_info
        mock_show_info = mocker.patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.ErrorHandler.show_info')
        
        # Set current selection
        nutrition_tab.current_selection = Mock()
        
        # Call method
        nutrition_tab._on_save_plan()
        
        # Verify QMessageBox was called
        mock_qmessagebox.question.assert_called_once()
        # Verify show_info was called
        mock_show_info.assert_called_once()

    def test_on_history_selection_changed_with_selection(self, nutrition_tab, mocker):
        """Test _on_history_selection_changed with a valid selection."""
        # Mock selection model
        mock_selection_model = Mock()
        mock_selected_row = Mock()
        mock_selected_row.row.return_value = 0
        mock_selection_model.selectedRows.return_value = [mock_selected_row]
        
        # Mock table model
        mock_table_model = Mock()
        mock_plan = Mock()
        mock_table_model.get_plan_at.return_value = mock_plan
        nutrition_tab.table_model = mock_table_model
        
        # Mock history_table
        nutrition_tab.history_table = Mock()
        nutrition_tab.history_table.selectionModel.return_value = mock_selection_model
        
        # Mock nutrition_controller.format_nutrition_summary
        mock_format = mocker.patch.object(nutrition_tab.nutrition_controller, 'format_nutrition_summary')
        mock_format.return_value = "Plan details"
        
        # Mock detail_text
        nutrition_tab.detail_text = Mock()
        
        # Call method
        nutrition_tab._on_history_selection_changed()
        
        # Verify current_selection was set
        assert nutrition_tab.current_selection == mock_plan
        # Verify format_nutrition_summary was called
        mock_format.assert_called_once_with(mock_plan)
        # Verify detail_text was updated
        nutrition_tab.detail_text.setPlainText.assert_called_once_with("Plan details")

    def test_on_history_selection_changed_no_selection(self, nutrition_tab, mocker):
        """Test _on_history_selection_changed with no selection."""
        # Mock selection model with empty selection
        mock_selection_model = Mock()
        mock_selection_model.selectedRows.return_value = []
        
        # Mock history_table
        nutrition_tab.history_table = Mock()
        nutrition_tab.history_table.selectionModel.return_value = mock_selection_model
        
        # Mock detail_text
        nutrition_tab.detail_text = Mock()
        
        # Call method
        nutrition_tab._on_history_selection_changed()
        
        # Verify detail_text was NOT updated
        nutrition_tab.detail_text.setPlainText.assert_not_called()

    def test_on_history_selection_changed_no_table_model(self, nutrition_tab, mocker):
        """Test _on_history_selection_changed when table_model is None."""
        # Mock selection model
        mock_selection_model = Mock()
        mock_selected_row = Mock()
        mock_selected_row.row.return_value = 0
        mock_selection_model.selectedRows.return_value = [mock_selected_row]
        
        # Set table_model to None
        nutrition_tab.table_model = None
        
        # Mock history_table
        nutrition_tab.history_table = Mock()
        nutrition_tab.history_table.selectionModel.return_value = mock_selection_model
        
        # Mock detail_text
        nutrition_tab.detail_text = Mock()
        
        # Call method
        nutrition_tab._on_history_selection_changed()
        
        # Verify detail_text was NOT updated
        nutrition_tab.detail_text.setPlainText.assert_not_called()

    def test_refresh_with_selected_user(self, nutrition_tab, mocker):
        """Test refresh method when a user is selected."""
        # Mock _load_users and _load_history
        mock_load_users = mocker.patch.object(nutrition_tab, '_load_users')
        mock_load_history = mocker.patch.object(nutrition_tab, '_load_history')
        
        # Set selected user
        nutrition_tab.selected_user = Mock()
        
        # Call refresh
        nutrition_tab.refresh()
        
        # Verify both methods were called
        mock_load_users.assert_called_once()
        mock_load_history.assert_called_once()

    def test_refresh_without_selected_user(self, nutrition_tab, mocker):
        """Test refresh method when no user is selected."""
        # Mock _load_users and _load_history
        mock_load_users = mocker.patch.object(nutrition_tab, '_load_users')
        mock_load_history = mocker.patch.object(nutrition_tab, '_load_history')
        
        # Set selected user to None
        nutrition_tab.selected_user = None
        
        # Call refresh
        nutrition_tab.refresh()
        
        # Verify only _load_users was called
        mock_load_users.assert_called_once()
        mock_load_history.assert_not_called()

    def test_selection_model_connection_when_exists(self, mocker):
        """Test that selection model signal is connected when selection_model exists."""
        # Mock the QTableView to return a non-None selectionModel
        mock_selection_model = mocker.Mock()
        mock_qtableview_instance = mocker.Mock()
        mock_qtableview_instance.selectionModel.return_value = mock_selection_model
        
        # Mock other UI components
        mock_groupbox = mocker.Mock()
        mock_groupbox.setLayout = mocker.Mock()
        mock_label = mocker.Mock()
        mock_toolbar = mocker.Mock()
        mock_toolbar.addWidget = mocker.Mock()
        mock_toolbar.addAction = mocker.Mock()
        mock_toolbar.addSeparator = mocker.Mock()
        
        with patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QGroupBox', return_value=mock_groupbox), \
             patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QVBoxLayout', return_value=mocker.Mock()), \
             patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QTextEdit', return_value=mocker.Mock()), \
             patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QWidget', return_value=mocker.Mock()), \
             patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QDateEdit', return_value=mocker.Mock()), \
             patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QDoubleSpinBox', return_value=mocker.Mock()), \
             patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QSpinBox', return_value=mocker.Mock()), \
             patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QPushButton', return_value=mocker.Mock()), \
             patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QLabel', return_value=mock_label), \
             patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QToolBar', return_value=mock_toolbar), \
             patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QTableView', return_value=mock_qtableview_instance):
             
            # Create mock controller
            mock_controller = mocker.Mock()
            mock_controller.get_all_users.return_value = []
             
            # Create NutritionCalculatorTab instance
            from fatloss.desktop.views.widgets.nutrition_calculator_tab import NutritionCalculatorTab
            tab = NutritionCalculatorTab(mock_controller)
             
            # Verify selectionModel was called (line 256)
            mock_qtableview_instance.selectionModel.assert_called_once()
            # Verify connect was called (line 258)
            mock_selection_model.selectionChanged.connect.assert_called_once_with(tab._on_history_selection_changed)

    def test_selection_model_connection_when_none(self, mocker):
        """Test that no connection is attempted when selection_model is None."""
        # Mock the QTableView to return None selectionModel
        mock_qtableview_instance = mocker.Mock()
        mock_qtableview_instance.selectionModel.return_value = None
        
        # Mock other UI components
        mock_groupbox = mocker.Mock()
        mock_groupbox.setLayout = mocker.Mock()
        mock_label = mocker.Mock()
        mock_toolbar = mocker.Mock()
        mock_toolbar.addWidget = mocker.Mock()
        mock_toolbar.addAction = mocker.Mock()
        mock_toolbar.addSeparator = mocker.Mock()
        
        with patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QGroupBox', return_value=mock_groupbox), \
             patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QVBoxLayout', return_value=mocker.Mock()), \
             patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QTextEdit', return_value=mocker.Mock()), \
             patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QWidget', return_value=mocker.Mock()), \
             patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QDateEdit', return_value=mocker.Mock()), \
             patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QDoubleSpinBox', return_value=mocker.Mock()), \
             patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QSpinBox', return_value=mocker.Mock()), \
             patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QPushButton', return_value=mocker.Mock()), \
             patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QLabel', return_value=mock_label), \
             patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QToolBar', return_value=mock_toolbar), \
             patch('fatloss.desktop.views.widgets.nutrition_calculator_tab.QTableView', return_value=mock_qtableview_instance):
             
            # Create mock controller
            mock_controller = mocker.Mock()
            mock_controller.get_all_users.return_value = []
             
            # Create NutritionCalculatorTab instance
            from fatloss.desktop.views.widgets.nutrition_calculator_tab import NutritionCalculatorTab
            tab = NutritionCalculatorTab(mock_controller)
             
            # Verify selectionModel was called (line 256)
            mock_qtableview_instance.selectionModel.assert_called_once()
            # Verify connect was NOT called (line 258) because selection_model is None
            mock_qtableview_instance.selectionModel().selectionChanged.connect.assert_not_called()
