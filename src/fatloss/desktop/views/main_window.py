"""主窗口模块。

包含桌面应用的主窗口类。
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtWidgets import (
    QMainWindow,
    QAction,
    QMenuBar,
    QToolBar,
    QStatusBar,
    QLabel,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QMessageBox,
)

from fatloss.desktop.controllers.main_controller import MainController
from fatloss.desktop.controllers.user_controller import UserController
from fatloss.desktop.controllers.nutrition_controller import NutritionController
from fatloss.desktop.controllers.weight_controller import WeightController
from fatloss.desktop.controllers.dashboard_controller import DashboardController
from fatloss.desktop.views.widgets.user_management_tab import UserManagementTab
from fatloss.desktop.views.widgets.nutrition_calculator_tab import NutritionCalculatorTab
from fatloss.desktop.views.widgets.weight_tracking_tab import WeightTrackingTab
from fatloss.desktop.views.widgets.dashboard_tab import DashboardTab


class MainWindow(QMainWindow):
    """主窗口类，提供应用的主要用户界面。"""
    
    def __init__(self, controller: MainController):
        """初始化主窗口。
        
        Args:
            controller: 主控制器实例
        """
        super().__init__()
        self.controller = controller
        self.user_controller = UserController(controller.planner_service)
        self.nutrition_controller = NutritionController(controller.planner_service)
        self.weight_controller = WeightController(controller.planner_service)
        self.dashboard_controller = DashboardController(controller.planner_service)
        
        # 窗口属性
        self.setWindowTitle("Fatloss Planner - 科学减脂计划工具")
        self.setMinimumSize(1024, 768)
        
        # 初始化UI
        self._init_ui()
        
    def _init_ui(self) -> None:
        """初始化用户界面。"""
        # 创建菜单栏
        self._create_menu_bar()
        
        # 创建工具栏
        self._create_tool_bar()
        
        # 创建状态栏
        self._create_status_bar()
        
        # 创建中央部件
        self._create_central_widget()
        
    def _create_menu_bar(self) -> None:
        """创建菜单栏。"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        new_user_action = QAction("新建用户(&N)", self)
        new_user_action.setShortcut(QKeySequence.New)
        new_user_action.triggered.connect(self._on_new_user)
        file_menu.addAction(new_user_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")
        
        preferences_action = QAction("首选项(&P)...", self)
        preferences_action.triggered.connect(self._on_preferences)
        edit_menu.addAction(preferences_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")
        
        calculate_action = QAction("营养计算(&C)", self)
        calculate_action.triggered.connect(self._on_calculate_nutrition)
        tools_menu.addAction(calculate_action)
        
        tools_menu.addSeparator()
        
        database_action = QAction("数据库管理(&D)...", self)
        database_action.triggered.connect(self._on_database_management)
        tools_menu.addAction(database_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        about_action = QAction("关于(&A)...", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
        
    def _create_tool_bar(self) -> None:
        """创建工具栏。"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # 添加工具按钮（占位符）
        new_user_btn = QAction("新建用户", self)
        new_user_btn.triggered.connect(self._on_new_user)
        toolbar.addAction(new_user_btn)
        
        toolbar.addSeparator()
        
        calculate_btn = QAction("营养计算", self)
        calculate_btn.triggered.connect(self._on_calculate_nutrition)
        toolbar.addAction(calculate_btn)
        
    def _create_status_bar(self) -> None:
        """创建状态栏。"""
        statusbar = QStatusBar()
        self.setStatusBar(statusbar)
        
        # 左侧状态标签
        self.status_label = QLabel("就绪")
        statusbar.addWidget(self.status_label, 1)
        
        # 右侧数据库状态标签
        db_status = self.controller.test_database_connection()
        db_text = "数据库: 已连接" if db_status else "数据库: 未连接"
        self.db_status_label = QLabel(db_text)
        statusbar.addPermanentWidget(self.db_status_label)
        
    def _create_central_widget(self) -> None:
        """创建中央部件。"""
        # 创建标签页容器
        self.tab_widget = QTabWidget()
        
        # 创建标签页
        self._create_tabs()
        
        # 设置中央部件
        self.setCentralWidget(self.tab_widget)
        
    def _create_tabs(self) -> None:
        """创建主窗口标签页。"""
        # 仪表盘标签页
        dashboard_tab = DashboardTab(self.dashboard_controller)
        self.tab_widget.addTab(dashboard_tab, "仪表盘")
        
        # 用户管理标签页
        user_tab = UserManagementTab(self.user_controller)
        self.tab_widget.addTab(user_tab, "用户管理")
        
        # 营养计算标签页
        nutrition_tab = NutritionCalculatorTab(self.nutrition_controller)
        self.tab_widget.addTab(nutrition_tab, "营养计算")
        
        # 计划管理标签页
        plan_tab = QWidget()
        plan_layout = QVBoxLayout()
        plan_layout.addWidget(QLabel("<h2>计划管理</h2><p>生成和管理周营养计划。</p><p>功能将在阶段2实现。</p>"))
        plan_tab.setLayout(plan_layout)
        self.tab_widget.addTab(plan_tab, "计划管理")
        
        # 体重跟踪标签页
        weight_tab = WeightTrackingTab(self.weight_controller)
        self.tab_widget.addTab(weight_tab, "体重跟踪")
        
        # 配置设置标签页
        settings_tab = QWidget()
        settings_layout = QVBoxLayout()
        settings_layout.addWidget(QLabel("<h2>配置设置</h2><p>配置营养比例、调整策略和界面主题。</p><p>功能将在阶段2实现。</p>"))
        settings_tab.setLayout(settings_layout)
        self.tab_widget.addTab(settings_tab, "配置设置")
        
    # 事件处理函数
    def _on_new_user(self) -> None:
        """处理新建用户操作。"""
        QMessageBox.information(self, "功能提示", "新建用户功能将在阶段2实现。")
        
    def _on_calculate_nutrition(self) -> None:
        """处理营养计算操作。"""
        QMessageBox.information(self, "功能提示", "营养计算功能将在阶段2实现。")
        
    def _on_preferences(self) -> None:
        """处理首选项操作。"""
        QMessageBox.information(self, "功能提示", "首选项功能将在阶段3实现。")
        
    def _on_database_management(self) -> None:
        """处理数据库管理操作。"""
        user_count = self.controller.get_user_count()
        QMessageBox.information(
            self, 
            "数据库信息", 
            f"数据库连接状态: {'正常' if self.controller.test_database_connection() else '异常'}\n"
            f"用户数量: {user_count}"
        )
        
    def _on_about(self) -> None:
        """处理关于操作。"""
        info = self.controller.get_application_info()
        about_text = f"""
        <h2>{info['name']}</h2>
        <p>版本: {info['version']}</p>
        <p>{info['description']}</p>
        <p>作者: {info['author']}</p>
        <p>© 2026 Fatloss Planner Team</p>
        """
        QMessageBox.about(self, "关于 Fatloss Planner", about_text)
        
    def closeEvent(self, event):
        """处理窗口关闭事件。"""
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出Fatloss Planner吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()