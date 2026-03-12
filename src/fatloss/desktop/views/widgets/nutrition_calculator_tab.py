"""营养计算标签页。

提供营养计算器界面和历史记录查看功能。
"""

from typing import Optional
from datetime import date

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableView,
    QHeaderView,
    QSplitter,
    QGroupBox,
    QFormLayout,
    QComboBox,
    QDoubleSpinBox,
    QSpinBox,
    QDateEdit,
    QTextEdit,
    QApplication,
    QMessageBox,
    QToolBar,
    QAction,
    QSizePolicy,
)

from fatloss.models.user_profile import UserProfile
from fatloss.models.nutrition_plan import DailyNutritionPlan
from fatloss.desktop.controllers.nutrition_controller import NutritionController
from fatloss.desktop.views.dialogs.nutrition_dialog import NutritionDialog
from fatloss.desktop.utils.error_handler import ErrorHandler
from fatloss.desktop.models.nutrition_table_model import NutritionTableModel


class NutritionCalculatorTab(QWidget):
    """营养计算标签页，提供完整的营养计算和历史记录功能。"""
    
    # 信号定义
    calculation_performed = pyqtSignal(DailyNutritionPlan)  # 计算完成
    
    # 常量定义
    MIN_EXERCISE_MINUTES = 0.0
    MAX_EXERCISE_MINUTES = 300.0
    MIN_ADJUSTMENT_UNITS = -10
    MAX_ADJUSTMENT_UNITS = 10
    
    DEFAULT_EXERCISE_MINUTES = 60.0
    DEFAULT_ADJUSTMENT_UNITS = 0
    
    def __init__(self, nutrition_controller: NutritionController, parent=None):
        """初始化营养计算标签页。
        
        Args:
            nutrition_controller: 营养计算控制器实例
            parent: 父窗口部件
        """
        super().__init__(parent)
        
        self.nutrition_controller = nutrition_controller
        self.table_model = None
        self.current_selection = None
        self.selected_user = None
        
        self._init_ui()
        self._load_users()
    
    def _init_ui(self) -> None:
        """初始化用户界面。"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 顶部工具栏
        toolbar = self._create_toolbar()
        main_layout.addWidget(toolbar)
        
        # 创建分割器：左侧计算器，右侧历史记录
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧计算器面板
        calculator_widget = self._create_calculator_panel()
        splitter.addWidget(calculator_widget)
        
        # 右侧历史记录面板
        history_widget = self._create_history_panel()
        splitter.addWidget(history_widget)
        
        # 设置分割器比例
        splitter.setSizes([400, 600])
        
        main_layout.addWidget(splitter, 1)  # 1表示拉伸因子
        
        self.setLayout(main_layout)
    
    def _create_toolbar(self) -> QToolBar:
        """创建工具栏。
        
        Returns:
            工具栏实例
        """
        toolbar = QToolBar()
        toolbar.setIconSize(QApplication.style().standardIcon(
            QApplication.style().SP_TitleBarMenuButton
        ).actualSize(QApplication.style().standardIcon(
            QApplication.style().SP_TitleBarMenuButton
        ).availableSizes()[0]))
        
        # 快速计算按钮
        quick_calc_action = QAction("快速计算", self)
        quick_calc_action.setToolTip("打开营养计算对话框")
        quick_calc_action.triggered.connect(self._on_quick_calculate)
        toolbar.addAction(quick_calc_action)
        
        toolbar.addSeparator()
        
        # 保存计划按钮
        save_action = QAction("保存计划", self)
        save_action.setToolTip("保存当前计算结果")
        save_action.triggered.connect(self._on_save_plan)
        toolbar.addAction(save_action)
        
        # 刷新历史按钮
        refresh_action = QAction("刷新历史", self)
        refresh_action.setToolTip("刷新历史记录")
        refresh_action.triggered.connect(self._load_history)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # 用户选择下拉框
        toolbar.addWidget(QLabel("用户:"))
        self.user_combo = QComboBox()
        self.user_combo.setMinimumWidth(200)
        self.user_combo.currentIndexChanged.connect(self._on_user_selected)
        toolbar.addWidget(self.user_combo)
        
        return toolbar
    
    def _create_calculator_panel(self) -> QWidget:
        """创建计算器面板。
        
        Returns:
            计算器面板部件
        """
        panel = QWidget()
        layout = QVBoxLayout()
        
        # 计算器组
        calculator_group = QGroupBox("营养计算器")
        calculator_layout = QVBoxLayout()
        
        # 用户信息
        self.user_info_label = QLabel("请先选择一个用户")
        self.user_info_label.setWordWrap(True)
        self.user_info_label.setStyleSheet("padding: 8px; background-color: #f0f8ff; border-radius: 4px;")
        calculator_layout.addWidget(self.user_info_label)
        
        # 计算参数表单
        params_form = QFormLayout()
        
        # 计划日期
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(date.today())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        params_form.addRow("计划日期:", self.date_edit)
        
        # 训练分钟数
        self.exercise_spin = QDoubleSpinBox()
        self.exercise_spin.setRange(self.MIN_EXERCISE_MINUTES, self.MAX_EXERCISE_MINUTES)
        self.exercise_spin.setValue(self.DEFAULT_EXERCISE_MINUTES)
        self.exercise_spin.setSuffix(" 分钟")
        self.exercise_spin.setDecimals(0)
        self.exercise_spin.setSingleStep(10)
        params_form.addRow("训练时间:", self.exercise_spin)
        
        # 碳水化合物调整
        self.adjustment_spin = QSpinBox()
        self.adjustment_spin.setRange(self.MIN_ADJUSTMENT_UNITS, self.MAX_ADJUSTMENT_UNITS)
        self.adjustment_spin.setValue(self.DEFAULT_ADJUSTMENT_UNITS)
        self.adjustment_spin.setSuffix(" 单位 (±30g)")
        self.adjustment_spin.setSingleStep(1)
        params_form.addRow("碳水调整:", self.adjustment_spin)
        
        calculator_layout.addLayout(params_form)
        
        # 计算按钮
        self.calculate_btn = QPushButton("计算营养计划")
        self.calculate_btn.setEnabled(False)
        self.calculate_btn.clicked.connect(self._on_calculate)
        self.calculate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        calculator_layout.addWidget(self.calculate_btn)
        
        # 分隔线
        calculator_layout.addWidget(QLabel(""))
        
        # 结果展示
        result_group = QGroupBox("计算结果")
        result_layout = QVBoxLayout()
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("计算结果将显示在这里...")
        self.result_text.setMaximumHeight(200)
        result_layout.addWidget(self.result_text)
        
        result_group.setLayout(result_layout)
        calculator_layout.addWidget(result_group)
        
        calculator_group.setLayout(calculator_layout)
        layout.addWidget(calculator_group)
        
        layout.addStretch()
        
        panel.setLayout(layout)
        return panel
    
    def _create_history_panel(self) -> QWidget:
        """创建历史记录面板。
        
        Returns:
            历史记录面板部件
        """
        panel = QWidget()
        layout = QVBoxLayout()
        
        # 历史记录组
        history_group = QGroupBox("历史记录")
        history_layout = QVBoxLayout()
        
        # 历史记录表格
        self.history_table = QTableView()
        self.history_table.setSelectionBehavior(QTableView.SelectRows)
        self.history_table.setSelectionMode(QTableView.SingleSelection)
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # 连接选择变化信号
        selection_model = self.history_table.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self._on_history_selection_changed)
        
        history_layout.addWidget(self.history_table)
        
        # 历史记录详情
        detail_group = QGroupBox("计划详情")
        detail_layout = QVBoxLayout()
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setPlaceholderText("选择一条记录查看详情...")
        self.detail_text.setMaximumHeight(150)
        detail_layout.addWidget(self.detail_text)
        
        detail_group.setLayout(detail_layout)
        history_layout.addWidget(detail_group)
        
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        layout.addStretch()
        
        panel.setLayout(layout)
        return panel
    
    def _load_users(self) -> None:
        """加载用户列表到下拉框。"""
        try:
            users = self.nutrition_controller.get_all_users()
            self.user_combo.clear()
            
            # 添加占位项
            self.user_combo.addItem("-- 请选择用户 --", None)
            
            for user in users:
                display_text = f"{user.name} ({user.age}岁)"
                self.user_combo.addItem(display_text, user.id)
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
    
    def _on_user_selected(self, index: int) -> None:
        """处理用户选择变化。
        
        Args:
            index: 当前选中索引
        """
        user_id = self.user_combo.itemData(index)
        
        if user_id is None:
            self.user_info_label.setText("请先选择一个用户")
            self.selected_user = None
            self.calculate_btn.setEnabled(False)
            self._clear_calculator()
            return
        
        # 获取用户信息
        user = self.nutrition_controller.get_user_by_id(user_id)
        if user:
            self.selected_user = user
            
            # 更新用户信息显示
            gender = user.gender.value if hasattr(user.gender, 'value') else user.gender
            activity = user.activity_level.value if hasattr(user.activity_level, 'value') else user.activity_level
            info_text = f"""
            <b>{user.name}</b>
            <br>性别: {gender}
            <br>年龄: {user.age}岁
            <br>身高: {user.height_cm}cm
            <br>活动水平: {activity}
            """
            self.user_info_label.setText(info_text)
            
            # 启用计算按钮
            self.calculate_btn.setEnabled(True)
            
            # 加载该用户的历史记录
            self._load_history()
    
    def _load_history(self) -> None:
        """加载当前用户的历史记录。"""
        if not self.selected_user:
            return
        
        try:
            # 获取历史记录
            plans = self.nutrition_controller.get_user_nutrition_history(
                user_id=self.selected_user.id,
                limit=20
            )
            
            # 创建或更新表格模型
            if self.table_model is None:
                self.table_model = NutritionTableModel(plans)
                self.history_table.setModel(self.table_model)
            else:
                self.table_model.set_plans(plans)
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
    
    def _on_calculate(self) -> None:
        """处理计算按钮点击。"""
        if not self.selected_user:
            ErrorHandler.show_warning("请先选择一个用户", self)
            return
        
        try:
            # 获取输入参数
            plan_date_qdate = self.date_edit.date()
            plan_date = date(
                plan_date_qdate.year(),
                plan_date_qdate.month(),
                plan_date_qdate.day()
            )
            
            exercise_minutes = self.exercise_spin.value()
            adjustment_units = self.adjustment_spin.value()
            
            # 计算营养计划
            plan = self.nutrition_controller.calculate_nutrition_plan(
                user_id=self.selected_user.id,
                plan_date=plan_date,
                exercise_minutes=exercise_minutes,
                adjustment_units=adjustment_units,
                parent_widget=self
            )
            
            if plan:
                # 显示结果
                summary = self.nutrition_controller.format_nutrition_summary(plan)
                self.result_text.setPlainText(summary)
                
                # 发出信号
                self.calculation_performed.emit(plan)
                
                # 刷新历史记录
                self._load_history()
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
    
    def _on_quick_calculate(self) -> None:
        """处理快速计算按钮点击。"""
        plan = NutritionDialog.calculate_nutrition(
            nutrition_controller=self.nutrition_controller,
            parent=self,
            user=self.selected_user
        )
        
        if plan:
            # 刷新历史记录
            self._load_history()
            
            # 显示成功消息
            ErrorHandler.show_success("营养计划计算完成", self)
    
    def _on_save_plan(self) -> None:
        """处理保存计划按钮点击。"""
        if not self.current_selection:
            ErrorHandler.show_warning("请先选择一条历史记录", self)
            return
        
        # 这里可以添加保存逻辑，比如导出为PDF或JSON
        reply = QMessageBox.question(
            self,
            "保存计划",
            "确定要保存选中的营养计划吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            ErrorHandler.show_info("保存功能将在后续版本中实现", self)
    
    def _on_history_selection_changed(self) -> None:
        """处理历史记录选择变化。"""
        selected_rows = self.history_table.selectionModel().selectedRows()
        if selected_rows and self.table_model:
            row = selected_rows[0].row()
            plan = self.table_model.get_plan_at(row)
            if plan:
                self.current_selection = plan
                
                # 显示计划详情
                detail_text = self.nutrition_controller.format_nutrition_summary(plan)
                self.detail_text.setPlainText(detail_text)
    
    def _clear_calculator(self) -> None:
        """清空计算器内容。"""
        self.result_text.clear()
        self.detail_text.clear()
        self.current_selection = None
        
        # 重置输入值为默认值
        self.date_edit.setDate(date.today())
        self.exercise_spin.setValue(self.DEFAULT_EXERCISE_MINUTES)
        self.adjustment_spin.setValue(self.DEFAULT_ADJUSTMENT_UNITS)
    
    def refresh(self) -> None:
        """刷新标签页内容。"""
        self._load_users()
        if self.selected_user:
            self._load_history()
    
    def set_selected_user(self, user: UserProfile) -> None:
        """设置选中的用户。
        
        Args:
            user: 用户对象
        """
        self.selected_user = user
        self._select_user_in_combo(user.id)
        self._on_user_selected(self.user_combo.currentIndex())
    
    def _select_user_in_combo(self, user_id: int) -> None:
        """在下拉框中选中指定用户。
        
        Args:
            user_id: 用户ID
        """
        for index in range(self.user_combo.count()):
            if self.user_combo.itemData(index) == user_id:
                self.user_combo.setCurrentIndex(index)
                break