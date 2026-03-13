"""桌面测试专用fixture和配置。

提供PyQt5应用实例、QtBot、模拟对象和测试数据工厂。
支持无头环境(Xvfb)下的GUI测试。
"""

import os
import sys
from unittest.mock import MagicMock, Mock

import pytest
from pytestqt.qt_compat import qt_api

from fatloss.desktop.controllers.main_controller import MainController
from fatloss.repository.database import init_database
from fatloss.repository.unit_of_work import UnitOfWork
from fatloss.planner.planner_service import PlannerService


@pytest.fixture(scope="session")
def qapp():
    """创建Qt应用实例（session作用域）。

    如果已经存在QApplication实例，则复用现有实例。
    在无头环境中自动配置offscreen平台。
    """
    # 检查是否在无头环境中运行
    if os.environ.get("DISPLAY") is None and os.environ.get("QT_QPA_PLATFORM") is None:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    
    app = qt_api.QtWidgets.QApplication.instance()
    if app is None:
        app = qt_api.QtWidgets.QApplication([])
        app.setApplicationName("FatlossPlannerTest")
        app.setOrganizationName("FatlossPlanner")
    yield app
    
    # 清理：关闭所有窗口，但不要退出应用，以免影响其他测试
    for widget in app.topLevelWidgets():
        widget.close()


@pytest.fixture
def qtbot(qapp):
    """创建QtBot用于界面测试。

    QtBot提供模拟用户交互的方法（点击、键盘输入等）。
    """
    from pytestqt.qtbot import QtBot
    return QtBot(qapp)


@pytest.fixture(scope="session")
def test_engine():
    """创建测试数据库引擎（session作用域）。"""
    from sqlalchemy import create_engine
    
    # 使用内存数据库避免文件冲突
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # 创建所有表（只执行一次）
    init_database(engine)
    
    yield engine
    
    # 清理
    engine.dispose()


@pytest.fixture
def test_session(test_engine):
    """创建测试数据库会话（function作用域）。"""
    from sqlalchemy.orm import sessionmaker
    
    Session = sessionmaker(bind=test_engine)
    session = Session()
    
    try:
        yield session
        # 测试结束后回滚，保持数据库干净
        session.rollback()
    finally:
        session.close()


@pytest.fixture
def test_uow(test_session):
    """创建测试工作单元（function作用域）。"""
    return UnitOfWork(test_session)


@pytest.fixture
def mock_planner_service():
    """模拟PlannerService依赖。

    提供常用方法的默认返回值，简化控制器测试。
    """
    service = Mock(spec=PlannerService)
    
    # 配置默认返回值
    service.calculate_bmr.return_value = 1600.0
    service.calculate_tdee.return_value = 2200.0
    service.calculate_nutrition_from_tdee.return_value = {
        "calories": 1800,
        "protein_g": 120.0,
        "carbs_g": 150.0,
        "fat_g": 50.0
    }
    service.create_nutrition_plan.return_value = Mock(
        calories=1800,
        protein_g=120.0,
        carbs_g=150.0,
        fat_g=50.0,
        created_at="2025-01-01"
    )
    
    return service


@pytest.fixture
def main_controller(mock_planner_service, test_session):
    """创建MainController实例用于测试。

    注入模拟的PlannerService和数据库会话。
    """
    controller = MainController(database_url=None)
    controller.planner_service = mock_planner_service
    controller._session = test_session
    return controller


@pytest.fixture
def qt_signal_spy():
    """创建Qt信号监视器工具函数。

    用于验证信号是否被正确发射。
    
    Usage:
        spy = qt_signal_spy(widget.signal_name)
        # 执行操作...
        assert spy.count() == 1
        assert spy[0] == expected_args
    """
    from pytestqt.wait_signal import SignalBlocker
    
    def create_spy(signal):
        return SignalBlocker(signal)
    
    return create_spy


@pytest.fixture
def sample_user_data():
    """生成示例用户测试数据。"""
    from datetime import date
    from fatloss.models.user_profile import Gender, ActivityLevel
    
    return {
        "name": "测试用户",
        "gender": Gender.MALE,
        "birth_date": date(1990, 1, 1),
        "height_cm": 175.0,
        "initial_weight_kg": 70.0,
        "target_weight_kg": 65.0,
        "activity_level": ActivityLevel.MODERATE,
        "weekly_weight_loss_kg": 0.5,
    }


@pytest.fixture
def sample_nutrition_data():
    """生成示例营养计算测试数据。"""
    return {
        "user_id": 1,
        "training_minutes": 30,
        "adjustment_unit": 0,
        "calculation_date": "2025-01-01",
    }


@pytest.fixture(autouse=True)
def mock_error_handler(request, mocker):
    """自动模拟ErrorHandler，避免GUI调用。
    
    这个fixture会在每个测试中自动执行，模拟ErrorHandler的所有静态方法，
    防止在无头环境中调用Qt的QMessageBox。
    但如果是ErrorHandler自身的测试，则跳过模拟。
    """
    # 检查是否在测试ErrorHandler本身
    if "test_error_handler" in request.module.__name__:
        # 不模拟ErrorHandler，返回None
        return None
    
    mock_handler = mocker.patch("fatloss.desktop.utils.error_handler.ErrorHandler")
    # 模拟静态方法
    mock_handler.handle_service_error = mocker.Mock()
    mock_handler.show_success = mocker.Mock()
    mock_handler.show_warning = mocker.Mock()
    mock_handler.show_info = mocker.Mock()
    return mock_handler


@pytest.fixture
def sample_weight_data():
    """生成示例体重记录测试数据。"""
    from datetime import date
    
    return {
        "user_id": 1,
        "weight_kg": 70.5,
        "record_date": date(2025, 1, 1),
        "notes": "测试记录",
    }


@pytest.fixture
def gui_test_marker():
    """标记GUI测试，提供GUI测试专用工具。

    用于需要实际界面渲染的测试（与纯单元测试区分）。
    """
    marker = Mock()
    marker.requires_display = os.environ.get("DISPLAY") is not None
    return marker