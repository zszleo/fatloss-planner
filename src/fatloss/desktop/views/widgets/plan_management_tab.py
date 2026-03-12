"""计划管理标签页。

提供周计划日历视图、每日营养计划详情和计划管理功能。
"""

from typing import Optional, Dict, Any
from datetime import date, timedelta

from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QCalendarWidget,
    QGroupBox,
    QTextEdit,
    QFormLayout,
    QSpinBox,
    QDoubleSpinBox,
    QToolBar,
    QAction,
    QSplitter,
    QTabWidget,
    QMessageBox,
    QFileDialog,
    QScrollArea,
    QGridLayout,
    QSizePolicy,
)

from fatloss.models.user_profile import UserProfile
from fatloss.models.nutrition_plan import DailyNutritionPlan, WeeklyNutritionPlan
from fatloss.desktop.controllers.plan_controller import PlanController
from fatloss.desktop.utils.error_handler import ErrorHandler


class PlanManagementTab(QWidget):
    """计划管理标签页，提供周计划日历视图和计划管理功能。"""
    
    # 信号定义
    user_selected = pyqtSignal(UserProfile)          # 用户被选中
    plan_generated = pyqtSignal(WeeklyNutritionPlan) # 计划生成
    plan_updated = pyqtSignal(DailyNutritionPlan)    # 计划更新
    
    # 常量定义
    WEEK_DAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    
    def __init__(self, plan_controller: PlanController, parent=None):
        """初始化计划管理标签页。
        
        Args:
            plan_controller: 计划管理控制器实例
            parent: 父窗口部件
        """
        super().__init__(parent)
        
        self.plan_controller = plan_controller
        self.selected_user = None
        self.selected_date = date.today()
        self.selected_week_start = self._get_monday(self.selected_date)
        self.current_weekly_plan = None
        
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
        
        # 创建分割器（左侧日历，右侧详情）
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：日历和计划管理区域
        left_widget = self._create_left_widget()
        splitter.addWidget(left_widget)
        
        # 右侧：计划详情和操作区域
        right_widget = self._create_right_widget()
        splitter.addWidget(right_widget)
        
        # 设置分割器初始比例
        splitter.setSizes([400, 600])
        
        main_layout.addWidget(splitter, 1)  # 拉伸因子
        
        self.setLayout(main_layout)
    
    def _create_toolbar(self) -> QToolBar:
        """创建工具栏。
        
        Returns:
            工具栏实例
        """
        toolbar = QToolBar()
        
        # 刷新按钮
        refresh_action = QAction("🔄 刷新", self)
        refresh_action.setToolTip("刷新计划数据")
        refresh_action.triggered.connect(self._refresh_data)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # 用户选择下拉框
        toolbar.addWidget(QLabel("用户:"))
        self.user_combo = QComboBox()
        self.user_combo.setMinimumWidth(200)
        self.user_combo.currentIndexChanged.connect(self._on_user_selected)
        toolbar.addWidget(self.user_combo)
        
        toolbar.addSeparator()
        
        # 周选择
        toolbar.addWidget(QLabel("周:"))
        self.week_combo = QComboBox()
        self.week_combo.setMinimumWidth(150)
        self.week_combo.currentIndexChanged.connect(self._on_week_selected)
        toolbar.addWidget(self.week_combo)
        
        # 跳转到本周按钮
        go_to_week_action = QAction("📅 本周", self)
        go_to_week_action.setToolTip("跳转到本周")
        go_to_week_action.triggered.connect(self._go_to_current_week)
        toolbar.addAction(go_to_week_action)
        
        toolbar.addSeparator()
        
        # 生成周计划按钮
        generate_action = QAction("🚀 生成周计划", self)
        generate_action.setToolTip("生成新的周营养计划")
        generate_action.triggered.connect(self._generate_weekly_plan)
        toolbar.addAction(generate_action)
        
        return toolbar
    
    def _create_left_widget(self) -> QWidget:
        """创建左侧部件（日历和计划概览）。
        
        Returns:
            左侧部件
        """
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)
        
        # 日历控件
        calendar_group = QGroupBox("日历")
        calendar_layout = QVBoxLayout()
        
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setFirstDayOfWeek(Qt.Monday)  # 设置周一为第一天
        self.calendar.clicked.connect(self._on_calendar_date_selected)
        
        calendar_layout.addWidget(self.calendar)
        calendar_group.setLayout(calendar_layout)
        left_layout.addWidget(calendar_group)
        
        # 周计划概览
        weekly_summary_group = QGroupBox("周计划概览")
        weekly_summary_layout = QVBoxLayout()
        
        self.weekly_summary_text = QTextEdit()
        self.weekly_summary_text.setReadOnly(True)
        self.weekly_summary_text.setMaximumHeight(150)
        self.weekly_summary_text.setStyleSheet("""
            QTextEdit {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        
        weekly_summary_layout.addWidget(self.weekly_summary_text)
        weekly_summary_group.setLayout(weekly_summary_layout)
        left_layout.addWidget(weekly_summary_group)
        
        # 周计划操作按钮
        button_layout = QHBoxLayout()
        
        self.export_weekly_btn = QPushButton("📤 导出周计划")
        self.export_weekly_btn.setToolTip("导出周计划为文本文件")
        self.export_weekly_btn.clicked.connect(self._export_weekly_plan)
        self.export_weekly_btn.setEnabled(False)
        button_layout.addWidget(self.export_weekly_btn)
        
        self.print_weekly_btn = QPushButton("🖨️ 打印周计划")
        self.print_weekly_btn.setToolTip("打印周计划")
        self.print_weekly_btn.clicked.connect(self._print_weekly_plan)
        self.print_weekly_btn.setEnabled(False)
        button_layout.addWidget(self.print_weekly_btn)
        
        left_layout.addLayout(button_layout)
        
        left_widget.setLayout(left_layout)
        return left_widget
    
    def _create_right_widget(self) -> QWidget:
        """创建右侧部件（每日计划详情和操作）。
        
        Returns:
            右侧部件
        """
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)
        
        # 创建标签页容器
        self.tab_widget = QTabWidget()
        
        # 标签页1：每日计划详情
        daily_plan_tab = self._create_daily_plan_tab()
        self.tab_widget.addTab(daily_plan_tab, "每日计划详情")
        
        # 标签页2：周计划表格
        weekly_table_tab = self._create_weekly_table_tab()
        self.tab_widget.addTab(weekly_table_tab, "周计划表格")
        
        right_layout.addWidget(self.tab_widget)
        
        right_widget.setLayout(right_layout)
        return right_widget
    
    def _create_daily_plan_tab(self) -> QWidget:
        """创建每日计划详情标签页。
        
        Returns:
            每日计划详情标签页
        """
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # 日期标题
        self.date_header_label = QLabel("请选择日期")
        self.date_header_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.date_header_label)
        
        # 计划详情显示区域
        plan_display_group = QGroupBox("营养计划详情")
        plan_display_layout = QVBoxLayout()
        
        self.plan_display_text = QTextEdit()
        self.plan_display_text.setReadOnly(True)
        self.plan_display_text.setMinimumHeight(200)
        self.plan_display_text.setStyleSheet("""
            QTextEdit {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                font-family: monospace;
            }
        """)
        
        plan_display_layout.addWidget(self.plan_display_text)
        plan_display_group.setLayout(plan_display_layout)
        layout.addWidget(plan_display_group)
        
        # 计划编辑区域
        edit_group = QGroupBox("编辑每日计划")
        edit_layout = QFormLayout()
        
        # 训练分钟数
        self.exercise_minutes_spin = QDoubleSpinBox()
        self.exercise_minutes_spin.setRange(0, 300)
        self.exercise_minutes_spin.setValue(60.0)
        self.exercise_minutes_spin.setSuffix(" 分钟")
        edit_layout.addRow("训练分钟数:", self.exercise_minutes_spin)
        
        # 碳水化合物调整单位
        self.adjustment_units_spin = QSpinBox()
        self.adjustment_units_spin.setRange(-10, 10)
        self.adjustment_units_spin.setValue(0)
        self.adjustment_units_spin.setSuffix(" 单位 (每单位30g)")
        edit_layout.addRow("碳水调整:", self.adjustment_units_spin)
        
        # 备注
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("输入计划备注...")
        edit_layout.addRow("备注:", self.notes_edit)
        
        edit_group.setLayout(edit_layout)
        layout.addWidget(edit_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.save_daily_btn = QPushButton("💾 保存计划")
        self.save_daily_btn.setToolTip("保存每日营养计划")
        self.save_daily_btn.clicked.connect(self._save_daily_plan)
        self.save_daily_btn.setEnabled(False)
        button_layout.addWidget(self.save_daily_btn)
        
        self.clear_daily_btn = QPushButton("🗑️ 删除计划")
        self.clear_daily_btn.setToolTip("删除每日营养计划")
        self.clear_daily_btn.clicked.connect(self._delete_daily_plan)
        self.clear_daily_btn.setEnabled(False)
        button_layout.addWidget(self.clear_daily_btn)
        
        layout.addLayout(button_layout)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def _create_weekly_table_tab(self) -> QWidget:
        """创建周计划表格标签页。
        
        Returns:
            周计划表格标签页
        """
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 表格区域
        table_group = QGroupBox("周计划表格")
        table_layout = QVBoxLayout()
        
        # 使用滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        self.weekly_table_widget = QWidget()
        self.weekly_table_layout = QGridLayout()
        self.weekly_table_layout.setSpacing(5)
        self.weekly_table_layout.setContentsMargins(10, 10, 10, 10)
        
        self.weekly_table_widget.setLayout(self.weekly_table_layout)
        scroll_area.setWidget(self.weekly_table_widget)
        
        table_layout.addWidget(scroll_area)
        table_group.setLayout(table_layout)
        
        layout.addWidget(table_group)
        
        tab.setLayout(layout)
        return tab
    
    def _load_users(self) -> None:
        """加载用户列表到下拉框。"""
        try:
            users = self.plan_controller.get_all_users()
            self.user_combo.clear()
            
            # 添加占位项
            self.user_combo.addItem("-- 请选择用户 --", None)
            
            for user in users:
                display_text = f"{user.name} ({user.age}岁)"
                self.user_combo.addItem(display_text, user.id)
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
    
    def _load_available_weeks(self) -> None:
        """加载可用周列表到下拉框。"""
        if not self.selected_user:
            return
        
        try:
            available_weeks = self.plan_controller.get_available_weeks(self.selected_user.id)
            self.week_combo.clear()
            
            # 添加占位项和新建选项
            self.week_combo.addItem("-- 选择周 --", None)
            self.week_combo.addItem("新建周计划...", "new")
            
            for week_start in available_weeks:
                week_end = week_start + timedelta(days=6)
                display_text = f"{week_start} 至 {week_end}"
                self.week_combo.addItem(display_text, week_start)
            
            # 默认选中当前周
            current_week_start = self._get_monday(date.today())
            for index in range(self.week_combo.count()):
                if self.week_combo.itemData(index) == current_week_start:
                    self.week_combo.setCurrentIndex(index)
                    break
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
    
    def _load_weekly_plan(self, week_start_date: date) -> None:
        """加载周计划数据。
        
        Args:
            week_start_date: 周开始日期
        """
        if not self.selected_user:
            return
        
        try:
            self.current_weekly_plan = self.plan_controller.get_weekly_plan(
                user_id=self.selected_user.id,
                week_start_date=week_start_date,
                parent_widget=self
            )
            
            if self.current_weekly_plan:
                # 更新周计划概览
                summary = self.plan_controller.format_weekly_plan_summary(self.current_weekly_plan)
                self.weekly_summary_text.setPlainText(summary)
                
                # 启用导出按钮
                self.export_weekly_btn.setEnabled(True)
                self.print_weekly_btn.setEnabled(True)
                
                # 更新周计划表格
                self._update_weekly_table()
                
                # 发出信号
                self.plan_generated.emit(self.current_weekly_plan)
            else:
                self.weekly_summary_text.setPlainText("暂无周计划数据")
                self.export_weekly_btn.setEnabled(False)
                self.print_weekly_btn.setEnabled(False)
                self._clear_weekly_table()
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
    
    def _load_daily_plan(self, plan_date: date) -> None:
        """加载每日计划数据。
        
        Args:
            plan_date: 计划日期
        """
        if not self.selected_user:
            return
        
        try:
            # 更新日期标题
            day_name = self.WEEK_DAY_NAMES[plan_date.weekday()]
            self.date_header_label.setText(f"{day_name} ({plan_date})")
            
            # 获取该日的计划
            weekly_plans = self.plan_controller.get_daily_plans_for_week(
                user_id=self.selected_user.id,
                week_start_date=self.selected_week_start
            )
            
            daily_plan = weekly_plans.get(plan_date)
            
            if daily_plan:
                # 显示计划详情
                summary = self.plan_controller.format_daily_plan_summary(daily_plan)
                self.plan_display_text.setPlainText(summary)
                
                # 设置编辑控件
                self.exercise_minutes_spin.setValue(60.0)  # 默认值，实际应该从计划中获取
                self.adjustment_units_spin.setValue(daily_plan.adjustment_units)
                self.notes_edit.setPlainText(daily_plan.notes)
                
                # 启用按钮
                self.save_daily_btn.setEnabled(True)
                self.clear_daily_btn.setEnabled(True)
            else:
                self.plan_display_text.setPlainText("该日暂无营养计划")
                self.exercise_minutes_spin.setValue(60.0)
                self.adjustment_units_spin.setValue(0)
                self.notes_edit.clear()
                self.save_daily_btn.setEnabled(True)  # 允许创建新计划
                self.clear_daily_btn.setEnabled(False)
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
    
    def _update_weekly_table(self) -> None:
        """更新周计划表格。"""
        # 清空现有表格
        while self.weekly_table_layout.count():
            item = self.weekly_table_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.current_weekly_plan:
            return
        
        # 创建表头
        headers = ["日期", "星期", "TDEE (kcal)", "蛋白质 (g)", "碳水 (g)", "脂肪 (g)", "总热量 (kcal)", "调整"]
        
        for col, header in enumerate(headers):
            label = QLabel(f"<b>{header}</b>")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("background-color: #e0e0e0; padding: 5px;")
            self.weekly_table_layout.addWidget(label, 0, col)
        
        # 添加数据行
        daily_plans = self.current_weekly_plan.daily_plans
        daily_plans.sort(key=lambda p: p.plan_date)
        
        for row, daily_plan in enumerate(daily_plans, 1):
            nutrition = daily_plan.nutrition
            day_name = self.WEEK_DAY_NAMES[daily_plan.plan_date.weekday()]
            
            # 日期
            date_label = QLabel(str(daily_plan.plan_date))
            date_label.setAlignment(Qt.AlignCenter)
            self.weekly_table_layout.addWidget(date_label, row, 0)
            
            # 星期
            day_label = QLabel(day_name)
            day_label.setAlignment(Qt.AlignCenter)
            self.weekly_table_layout.addWidget(day_label, row, 1)
            
            # TDEE
            tdee_label = QLabel(f"{daily_plan.target_tdee:.0f}")
            tdee_label.setAlignment(Qt.AlignCenter)
            self.weekly_table_layout.addWidget(tdee_label, row, 2)
            
            # 蛋白质
            protein_label = QLabel(f"{nutrition.protein_g:.1f}")
            protein_label.setAlignment(Qt.AlignCenter)
            self.weekly_table_layout.addWidget(protein_label, row, 3)
            
            # 碳水化合物
            carbs_label = QLabel(f"{nutrition.carbohydrates_g:.1f}")
            carbs_label.setAlignment(Qt.AlignCenter)
            self.weekly_table_layout.addWidget(carbs_label, row, 4)
            
            # 脂肪
            fat_label = QLabel(f"{nutrition.fat_g:.1f}")
            fat_label.setAlignment(Qt.AlignCenter)
            self.weekly_table_layout.addWidget(fat_label, row, 5)
            
            # 总热量
            calories_label = QLabel(f"{nutrition.total_calories:.0f}")
            calories_label.setAlignment(Qt.AlignCenter)
            self.weekly_table_layout.addWidget(calories_label, row, 6)
            
            # 调整
            if daily_plan.is_adjusted:
                adjustment = daily_plan.adjustment_units * 30
                adjustment_label = QLabel(f"{adjustment:+d}g")
                adjustment_label.setAlignment(Qt.AlignCenter)
                color = "#4CAF50" if adjustment > 0 else "#F44336"
                adjustment_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            else:
                adjustment_label = QLabel("无")
                adjustment_label.setAlignment(Qt.AlignCenter)
            
            self.weekly_table_layout.addWidget(adjustment_label, row, 7)
    
    def _clear_weekly_table(self) -> None:
        """清空周计划表格。"""
        while self.weekly_table_layout.count():
            item = self.weekly_table_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 添加提示信息
        info_label = QLabel("暂无周计划数据")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 16px; color: #666; padding: 50px;")
        self.weekly_table_layout.addWidget(info_label, 0, 0)
    
    def _refresh_data(self) -> None:
        """刷新数据。"""
        self._load_users()
        if self.selected_user:
            self._load_available_weeks()
            if self.selected_week_start:
                self._load_weekly_plan(self.selected_week_start)
            if self.selected_date:
                self._load_daily_plan(self.selected_date)
    
    def _on_user_selected(self, index: int) -> None:
        """处理用户选择变化。
        
        Args:
            index: 当前选中索引
        """
        user_id = self.user_combo.itemData(index)
        
        if user_id is None:
            self.selected_user = None
            self._clear_display()
            return
        
        # 获取用户信息
        user = self.plan_controller.get_user_by_id(user_id)
        if user:
            self.selected_user = user
            self.user_selected.emit(user)
            
            # 加载可用周列表
            self._load_available_weeks()
            
            # 加载当前周计划
            self._load_weekly_plan(self.selected_week_start)
            
            # 加载当前日计划
            self._load_daily_plan(self.selected_date)
    
    def _on_week_selected(self, index: int) -> None:
        """处理周选择变化。
        
        Args:
            index: 当前选中索引
        """
        week_data = self.week_combo.itemData(index)
        
        if week_data is None:
            return
        
        if week_data == "new":
            # 创建新的周计划
            self._generate_weekly_plan()
        else:
            # 选择现有周
            self.selected_week_start = week_data
            self._load_weekly_plan(self.selected_week_start)
            
            # 更新日历选中日期
            qdate = QDate(
                self.selected_week_start.year,
                self.selected_week_start.month,
                self.selected_week_start.day
            )
            self.calendar.setSelectedDate(qdate)
    
    def _on_calendar_date_selected(self, qdate: QDate) -> None:
        """处理日历日期选择。
        
        Args:
            qdate: 选中的QDate对象
        """
        self.selected_date = date(qdate.year(), qdate.month(), qdate.day())
        self._load_daily_plan(self.selected_date)
    
    def _generate_weekly_plan(self) -> None:
        """生成周计划。"""
        if not self.selected_user:
            QMessageBox.warning(self, "警告", "请先选择用户")
            return
        
        # 获取周开始日期（默认选中当前周）
        week_start = self.selected_week_start
        
        # 确认对话框
        reply = QMessageBox.question(
            self,
            "生成周计划",
            f"确定要生成 {week_start} 开始的周计划吗？\n（如果已有该周计划，将被覆盖）",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 生成周计划
            weekly_plan = self.plan_controller.generate_weekly_plan(
                user_id=self.selected_user.id,
                week_start_date=week_start,
                parent_widget=self
            )
            
            if weekly_plan:
                # 重新加载周列表
                self._load_available_weeks()
                
                # 加载新生成的周计划
                self._load_weekly_plan(week_start)
    
    def _save_daily_plan(self) -> None:
        """保存每日计划。"""
        if not self.selected_user:
            QMessageBox.warning(self, "警告", "请先选择用户")
            return
        
        if not self.selected_date:
            QMessageBox.warning(self, "警告", "请先选择日期")
            return
        
        # 获取输入值
        exercise_minutes = self.exercise_minutes_spin.value()
        adjustment_units = self.adjustment_units_spin.value()
        
        # 更新每日计划
        daily_plan = self.plan_controller.update_daily_plan(
            user_id=self.selected_user.id,
            plan_date=self.selected_date,
            exercise_minutes=exercise_minutes,
            adjustment_units=adjustment_units,
            parent_widget=self
        )
        
        if daily_plan:
            # 重新加载每日计划
            self._load_daily_plan(self.selected_date)
            
            # 重新加载周计划（因为每日计划已更新）
            self._load_weekly_plan(self.selected_week_start)
            
            # 发出信号
            self.plan_updated.emit(daily_plan)
    
    def _delete_daily_plan(self) -> None:
        """删除每日计划。"""
        if not self.selected_user:
            return
        
        if not self.selected_date:
            return
        
        # 确认对话框
        reply = QMessageBox.question(
            self,
            "删除计划",
            f"确定要删除 {self.selected_date} 的营养计划吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                from fatloss.repository.unit_of_work import unit_of_work
                
                with unit_of_work(self.plan_controller.planner_service.database_url) as uow:
                    # 查找并删除每日计划
                    daily_plan = uow.daily_nutrition.find_by_user_and_date(
                        self.selected_user.id, self.selected_date
                    )
                    
                    if daily_plan:
                        uow.daily_nutrition.delete(daily_plan.id)
                        uow.commit()
                        
                        ErrorHandler.show_success(f"{self.selected_date} 的营养计划已删除", self)
                        
                        # 重新加载显示
                        self._load_daily_plan(self.selected_date)
                        self._load_weekly_plan(self.selected_week_start)
                        
            except Exception as e:
                ErrorHandler.handle_service_error(e, self)
    
    def _export_weekly_plan(self) -> None:
        """导出周计划。"""
        if not self.current_weekly_plan:
            return
        
        # 选择文件保存位置
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出周计划",
            f"fatloss_weekly_plan_{self.current_weekly_plan.week_start_date}.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                # 获取导出文本
                export_text = self.plan_controller.export_weekly_plan_to_text(
                    self.current_weekly_plan
                )
                
                # 写入文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(export_text)
                
                ErrorHandler.show_success(f"周计划已导出到: {file_path}", self)
                
            except Exception as e:
                ErrorHandler.handle_service_error(e, self)
    
    def _print_weekly_plan(self) -> None:
        """打印周计划。"""
        if not self.current_weekly_plan:
            return
        
        # 显示打印预览（简化版：显示在消息框中）
        export_text = self.plan_controller.export_weekly_plan_to_text(
            self.current_weekly_plan
        )
        
        # 创建打印预览对话框
        preview_dialog = QMessageBox(self)
        preview_dialog.setWindowTitle("打印预览")
        preview_dialog.setText("周计划打印预览")
        preview_dialog.setDetailedText(export_text)
        preview_dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        preview_dialog.setDefaultButton(QMessageBox.Ok)
        
        if preview_dialog.exec_() == QMessageBox.Ok:
            # 在实际应用中，这里应该调用打印API
            QMessageBox.information(
                self, 
                "打印", 
                "打印功能将在未来版本中实现。\n您可以使用导出功能将计划保存为文本文件。"
            )
    
    def _go_to_current_week(self) -> None:
        """跳转到本周。"""
        current_week_start = self._get_monday(date.today())
        self.selected_week_start = current_week_start
        
        # 更新周选择下拉框
        for index in range(self.week_combo.count()):
            if self.week_combo.itemData(index) == current_week_start:
                self.week_combo.setCurrentIndex(index)
                break
        
        # 更新日历
        qdate = QDate.today()
        self.calendar.setSelectedDate(qdate)
        self.selected_date = date.today()
        self._load_daily_plan(self.selected_date)
    
    def _clear_display(self) -> None:
        """清空显示。"""
        self.weekly_summary_text.clear()
        self.plan_display_text.clear()
        self.date_header_label.setText("请选择日期")
        self.export_weekly_btn.setEnabled(False)
        self.print_weekly_btn.setEnabled(False)
        self.save_daily_btn.setEnabled(False)
        self.clear_daily_btn.setEnabled(False)
        self._clear_weekly_table()
    
    def _get_monday(self, d: date) -> date:
        """获取给定日期所在周的周一日期。
        
        Args:
            d: 日期对象
            
        Returns:
            周一日期
        """
        return d - timedelta(days=d.weekday())
    
    def refresh(self) -> None:
        """刷新标签页内容。"""
        self._refresh_data()
    
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