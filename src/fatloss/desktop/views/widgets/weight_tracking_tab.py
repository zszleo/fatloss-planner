"""体重跟踪标签页。

提供体重记录的表格、图表和CRUD功能。
"""

from typing import Optional, List
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
    QDoubleSpinBox,
    QDateEdit,
    QTextEdit,
    QComboBox,
    QApplication,
    QMessageBox,
    QToolBar,
    QAction,
    QSizePolicy,
    QTabWidget,
)

# 尝试导入matplotlib
try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    FigureCanvas = None
    Figure = None

from fatloss.models.weight_record import WeightRecord
from fatloss.models.user_profile import UserProfile
from fatloss.desktop.controllers.weight_controller import WeightController
from fatloss.desktop.models.weight_table_model import WeightTableModel
from fatloss.desktop.utils.error_handler import ErrorHandler


class WeightTrackingTab(QWidget):
    """体重跟踪标签页，提供完整的体重记录管理和可视化功能。"""
    
    # 信号定义
    weight_recorded = pyqtSignal(WeightRecord)  # 体重记录被创建
    weight_updated = pyqtSignal(WeightRecord)   # 体重记录被更新
    weight_deleted = pyqtSignal(int)            # 体重记录被删除（传递记录ID）
    
    # 常量定义
    TABLE_MIN_HEIGHT = 200
    CHART_MIN_HEIGHT = 300
    FORM_MIN_WIDTH = 300
    
    MIN_WEIGHT_KG = 30.0
    MAX_WEIGHT_KG = 200.0
    DEFAULT_WEIGHT_KG = 70.0
    
    CHART_DAYS_OPTIONS = [7, 14, 30, 60, 90]
    DEFAULT_CHART_DAYS = 30
    
    def __init__(self, weight_controller: WeightController, parent=None):
        """初始化体重跟踪标签页。
        
        Args:
            weight_controller: 体重控制器实例
            parent: 父窗口部件
        """
        super().__init__(parent)
        
        self.weight_controller = weight_controller
        self.table_model = None
        self.current_selection = None
        self.selected_user = None
        
        # 图表相关
        self.chart_canvas = None
        self.chart_figure = None
        
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
        
        # 创建主分割器：左侧表单和统计，右侧表格和图表
        main_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板（表单和统计）
        left_panel = self._create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # 右侧面板（表格和图表）
        right_panel = self._create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # 设置分割器比例
        main_splitter.setSizes([400, 600])
        
        main_layout.addWidget(main_splitter, 1)  # 1表示拉伸因子
        
        self.setLayout(main_layout)
    
    def _create_toolbar(self) -> QToolBar:
        """创建工具栏。
        
        Returns:
            工具栏实例
        """
        toolbar = QToolBar()
        
        # 新建记录按钮
        new_record_action = QAction("新建记录", self)
        new_record_action.setToolTip("记录新体重")
        new_record_action.triggered.connect(self._on_new_record)
        toolbar.addAction(new_record_action)
        
        toolbar.addSeparator()
        
        # 编辑记录按钮
        edit_record_action = QAction("编辑记录", self)
        edit_record_action.setToolTip("编辑选中的体重记录")
        edit_record_action.triggered.connect(self._on_edit_record)
        toolbar.addAction(edit_record_action)
        
        # 删除记录按钮
        delete_record_action = QAction("删除记录", self)
        delete_record_action.setToolTip("删除选中的体重记录")
        delete_record_action.triggered.connect(self._on_delete_record)
        toolbar.addAction(delete_record_action)
        
        toolbar.addSeparator()
        
        # 刷新按钮
        refresh_action = QAction("刷新", self)
        refresh_action.setToolTip("刷新体重记录")
        refresh_action.triggered.connect(self._load_weight_history)
        toolbar.addAction(refresh_action)
        
        # 用户选择下拉框
        toolbar.addWidget(QLabel("用户:"))
        self.user_combo = QComboBox()
        self.user_combo.setMinimumWidth(200)
        self.user_combo.currentIndexChanged.connect(self._on_user_selected)
        toolbar.addWidget(self.user_combo)
        
        # 图表天数选择
        toolbar.addWidget(QLabel("图表天数:"))
        self.chart_days_combo = QComboBox()
        self.chart_days_combo.setMinimumWidth(100)
        for days in self.CHART_DAYS_OPTIONS:
            self.chart_days_combo.addItem(f"{days}天", days)
        
        # 设置默认值
        default_index = self.CHART_DAYS_OPTIONS.index(self.DEFAULT_CHART_DAYS)
        self.chart_days_combo.setCurrentIndex(default_index)
        self.chart_days_combo.currentIndexChanged.connect(self._on_chart_days_changed)
        toolbar.addWidget(self.chart_days_combo)
        
        return toolbar
    
    def _create_left_panel(self) -> QWidget:
        """创建左侧面板（表单和统计）。
        
        Returns:
            左侧面板部件
        """
        panel = QWidget()
        layout = QVBoxLayout()
        
        # 记录表单组
        form_group = QGroupBox("记录体重")
        form_layout = QVBoxLayout()
        
        # 用户信息
        self.user_info_label = QLabel("请先选择一个用户")
        self.user_info_label.setWordWrap(True)
        self.user_info_label.setStyleSheet("padding: 8px; background-color: #f0f8ff; border-radius: 4px;")
        form_layout.addWidget(self.user_info_label)
        
        # 记录表单
        record_form = QFormLayout()
        
        # 体重输入
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(self.MIN_WEIGHT_KG, self.MAX_WEIGHT_KG)
        self.weight_spin.setValue(self.DEFAULT_WEIGHT_KG)
        self.weight_spin.setSuffix(" kg")
        self.weight_spin.setDecimals(2)
        self.weight_spin.setSingleStep(0.1)
        record_form.addRow("体重:", self.weight_spin)
        
        # 日期输入
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(date.today())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        record_form.addRow("记录日期:", self.date_edit)
        
        # 备注输入
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("可选备注...")
        record_form.addRow("备注:", self.notes_edit)
        
        form_layout.addLayout(record_form)
        
        # 记录按钮
        self.record_btn = QPushButton("记录体重")
        self.record_btn.setEnabled(False)
        self.record_btn.clicked.connect(self._on_record_weight)
        self.record_btn.setStyleSheet("""
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
        form_layout.addWidget(self.record_btn)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # 统计信息组
        stats_group = QGroupBox("统计信息")
        stats_layout = QVBoxLayout()
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setPlaceholderText("选择用户后显示统计信息...")
        self.stats_text.setMaximumHeight(150)
        stats_layout.addWidget(self.stats_text)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        layout.addStretch()
        
        panel.setLayout(layout)
        return panel
    
    def _create_right_panel(self) -> QWidget:
        """创建右侧面板（表格和图表）。
        
        Returns:
            右侧面板部件
        """
        panel = QWidget()
        layout = QVBoxLayout()
        
        # 创建标签页：表格和图表
        self.right_tabs = QTabWidget()
        
        # 表格标签页
        table_tab = QWidget()
        table_layout = QVBoxLayout()
        
        self.weight_table = QTableView()
        self.weight_table.setMinimumHeight(self.TABLE_MIN_HEIGHT)
        self.weight_table.setSelectionBehavior(QTableView.SelectRows)
        self.weight_table.setSelectionMode(QTableView.SingleSelection)
        self.weight_table.horizontalHeader().setStretchLastSection(True)
        self.weight_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # 连接选择变化信号
        selection_model = self.weight_table.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self._on_selection_changed)
        
        table_layout.addWidget(self.weight_table)
        table_tab.setLayout(table_layout)
        
        self.right_tabs.addTab(table_tab, "体重记录")
        
        # 图表标签页（如果matplotlib可用）
        if MATPLOTLIB_AVAILABLE:
            chart_tab = QWidget()
            chart_layout = QVBoxLayout()
            
            # 创建matplotlib图表
            self.chart_figure = Figure(figsize=(8, 4), dpi=100)
            self.chart_canvas = FigureCanvas(self.chart_figure)
            self.chart_canvas.setMinimumHeight(self.CHART_MIN_HEIGHT)
            
            chart_layout.addWidget(self.chart_canvas)
            chart_tab.setLayout(chart_layout)
            
            self.right_tabs.addTab(chart_tab, "体重趋势")
        else:
            # 如果matplotlib不可用，显示提示
            chart_tab = QWidget()
            chart_layout = QVBoxLayout()
            
            warning_label = QLabel(
                "matplotlib未安装，无法显示图表。\n"
                "请安装matplotlib以启用图表功能。\n"
                "安装命令: pip install matplotlib"
            )
            warning_label.setAlignment(Qt.AlignCenter)
            warning_label.setStyleSheet("color: #ff0000; font-weight: bold;")
            chart_layout.addWidget(warning_label)
            
            chart_tab.setLayout(chart_layout)
            self.right_tabs.addTab(chart_tab, "体重趋势（需安装matplotlib）")
        
        layout.addWidget(self.right_tabs)
        
        # 记录详情
        detail_group = QGroupBox("记录详情")
        detail_layout = QVBoxLayout()
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setPlaceholderText("选择一条记录查看详情...")
        self.detail_text.setMaximumHeight(100)
        detail_layout.addWidget(self.detail_text)
        
        detail_group.setLayout(detail_layout)
        layout.addWidget(detail_group)
        
        panel.setLayout(layout)
        return panel
    
    def _load_users(self) -> None:
        """加载用户列表到下拉框。"""
        try:
            users = self.weight_controller.get_all_users()
            self.user_combo.clear()
            
            # 添加占位项
            self.user_combo.addItem("-- 请选择用户 --", None)
            
            for user in users:
                display_text = f"{user.name} ({user.age}岁)"
                self.user_combo.addItem(display_text, user.id)
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
    
    def _load_weight_history(self) -> None:
        """加载当前用户的体重历史记录。"""
        if not self.selected_user:
            return
        
        try:
            # 获取体重记录
            records = self.weight_controller.get_weight_history(
                user_id=self.selected_user.id,
                limit=100,
                descending=True
            )
            
            # 创建或更新表格模型
            if self.table_model is None:
                self.table_model = WeightTableModel(records)
                self.weight_table.setModel(self.table_model)
            else:
                self.table_model.set_weight_records(records)
            
            # 更新统计信息
            self._update_stats()
            
            # 更新图表
            self._update_chart()
            
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
    
    def _update_stats(self) -> None:
        """更新统计信息显示。"""
        if not self.selected_user:
            return
        
        try:
            # 获取统计信息
            stats = self.weight_controller.get_weight_stats(
                user_id=self.selected_user.id,
                days=30
            )
            
            stats_text = ""
            
            if stats["count"] == 0:
                stats_text = "暂无体重记录"
            else:
                stats_text += f"📊 统计信息（最近30天）\n"
                stats_text += f"📈 记录数量: {stats['count']} 条\n"
                
                if stats["latest_weight"]:
                    stats_text += f"⚖️  最新体重: {stats['latest_weight'].weight_kg:.2f} kg\n"
                
                if stats["min_weight"] is not None:
                    stats_text += f"📉 最低体重: {stats['min_weight']:.2f} kg\n"
                
                if stats["max_weight"] is not None:
                    stats_text += f"📈 最高体重: {stats['max_weight']:.2f} kg\n"
                
                if stats["avg_weight"] is not None:
                    stats_text += f"📊 平均体重: {stats['avg_weight']:.2f} kg\n"
                
                if stats["total_change"] != 0:
                    change_text = f"+{stats['total_change']:.2f}" if stats['total_change'] > 0 else f"{stats['total_change']:.2f}"
                    stats_text += f"🔄 总变化: {change_text} kg\n"
                
                if stats["avg_daily_change"] != 0:
                    change_text = f"+{stats['avg_daily_change']:.3f}" if stats['avg_daily_change'] > 0 else f"{stats['avg_daily_change']:.3f}"
                    stats_text += f"📅 平均每日变化: {change_text} kg/天\n"
            
            self.stats_text.setPlainText(stats_text)
            
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
    
    def _update_chart(self) -> None:
        """更新体重趋势图表。"""
        if not MATPLOTLIB_AVAILABLE or not self.selected_user:
            return
        
        try:
            # 获取图表天数
            chart_days = self.chart_days_combo.currentData()
            if chart_days is None:
                chart_days = self.DEFAULT_CHART_DAYS
            
            # 获取图表数据
            chart_data = self.weight_controller.get_chart_data(
                user_id=self.selected_user.id,
                days=chart_days
            )
            
            # 清空图表
            self.chart_figure.clear()
            
            # 创建子图
            ax = self.chart_figure.add_subplot(111)
            
            if chart_data["dates"] and chart_data["weights"]:
                # 绘制折线图
                dates = chart_data["dates"]
                weights = chart_data["weights"]
                
                ax.plot(dates, weights, 'b-', linewidth=2, marker='o', markersize=4, label='体重')
                
                # 添加标题和标签
                ax.set_title(f'体重趋势图（最近{chart_days}天）', fontsize=14, fontweight='bold')
                ax.set_xlabel('日期', fontsize=12)
                ax.set_ylabel('体重 (kg)', fontsize=12)
                
                # 设置网格
                ax.grid(True, linestyle='--', alpha=0.7)
                
                # 自动调整刻度标签
                self.chart_figure.autofmt_xdate()
                
                # 添加图例
                ax.legend()
                
                # 调整布局
                self.chart_figure.tight_layout()
            
            else:
                # 没有数据
                ax.text(0.5, 0.5, '暂无体重记录数据', 
                       horizontalalignment='center', verticalalignment='center',
                       transform=ax.transAxes, fontsize=14)
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.axis('off')
            
            # 刷新画布
            self.chart_canvas.draw()
            
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
            self.record_btn.setEnabled(False)
            self._clear_form()
            return
        
        # 获取用户信息
        user = self.weight_controller.get_user_by_id(user_id)
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
            
            # 启用记录按钮
            self.record_btn.setEnabled(True)
            
            # 加载该用户的体重记录
            self._load_weight_history()
    
    def _on_record_weight(self) -> None:
        """处理记录体重按钮点击。"""
        if not self.selected_user:
            ErrorHandler.show_warning("请先选择一个用户", self)
            return
        
        try:
            # 获取输入值
            weight_kg = self.weight_spin.value()
            
            date_qdate = self.date_edit.date()
            record_date = date(
                date_qdate.year(),
                date_qdate.month(),
                date_qdate.day()
            )
            
            notes = self.notes_edit.toPlainText()
            
            # 记录体重
            weight_record = self.weight_controller.record_weight(
                user_id=self.selected_user.id,
                weight_kg=weight_kg,
                record_date=record_date,
                notes=notes,
                parent_widget=self
            )
            
            if weight_record:
                # 刷新记录列表
                self._load_weight_history()
                
                # 发出信号
                self.weight_recorded.emit(weight_record)
                
                # 重置表单
                self._clear_form()
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
    
    def _on_new_record(self) -> None:
        """处理新建记录操作（工具栏按钮）。"""
        if not self.selected_user:
            ErrorHandler.show_warning("请先选择一个用户", self)
            return
        
        # 聚焦到表单
        self.weight_spin.setFocus()
    
    def _on_edit_record(self) -> None:
        """处理编辑记录操作。"""
        if not self.current_selection:
            ErrorHandler.show_warning("请先选择一条体重记录", self)
            return
        
        # 将当前选中记录的值填充到表单
        self.weight_spin.setValue(self.current_selection.weight_kg)
        
        date_qdate = self.date_edit.dateFromString(
            self.current_selection.record_date.strftime("%Y-%m-%d")
        )
        self.date_edit.setDate(date_qdate)
        
        self.notes_edit.setPlainText(self.current_selection.notes)
        
        # 更改按钮文本和功能
        original_text = self.record_btn.text()
        original_slot = self.record_btn.clicked
        
        self.record_btn.setText("更新记录")
        self.record_btn.clicked.disconnect()
        self.record_btn.clicked.connect(self._on_update_record)
        
        # 保存原始状态以便恢复
        self._original_record_btn_state = (original_text, original_slot)
    
    def _on_update_record(self) -> None:
        """处理更新记录操作。"""
        if not self.current_selection:
            ErrorHandler.show_warning("请先选择一条体重记录", self)
            return
        
        try:
            # 获取输入值
            weight_kg = self.weight_spin.value()
            
            date_qdate = self.date_edit.date()
            record_date = date(
                date_qdate.year(),
                date_qdate.month(),
                date_qdate.day()
            )
            
            notes = self.notes_edit.toPlainText()
            
            # 更新体重记录
            updated_record = self.weight_controller.update_weight(
                weight_id=self.current_selection.id,
                weight_kg=weight_kg,
                record_date=record_date,
                notes=notes,
                parent_widget=self
            )
            
            if updated_record:
                # 刷新记录列表
                self._load_weight_history()
                
                # 发出信号
                self.weight_updated.emit(updated_record)
                
                # 恢复按钮状态
                self._restore_record_btn()
                
                # 清除当前选择
                self.current_selection = None
                self.detail_text.clear()
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
    
    def _on_delete_record(self) -> None:
        """处理删除记录操作。"""
        if not self.current_selection:
            ErrorHandler.show_warning("请先选择一条体重记录", self)
            return
        
        # 确认对话框
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除 {self.current_selection.record_date} 的体重记录 ({self.current_selection.weight_kg} kg) 吗？\n\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.weight_controller.delete_weight(
                weight_id=self.current_selection.id,
                parent_widget=self
            )
            
            if success:
                # 刷新记录列表
                self._load_weight_history()
                
                # 发出信号
                self.weight_deleted.emit(self.current_selection.id)
                
                # 清除当前选择
                self.current_selection = None
                self.detail_text.clear()
                
                # 恢复按钮状态（如果正在编辑）
                if hasattr(self, '_original_record_btn_state'):
                    self._restore_record_btn()
    
    def _on_selection_changed(self) -> None:
        """处理表格选择变化。"""
        selected_rows = self.weight_table.selectionModel().selectedRows()
        if selected_rows and self.table_model:
            row = selected_rows[0].row()
            record = self.table_model.get_record_at(row)
            if record:
                self.current_selection = record
                
                # 显示记录详情
                detail_text = f"""
                📅 日期: {record.record_date}
                ⚖️  体重: {record.weight_kg:.2f} kg
                📝 备注: {record.notes if record.notes else "无"}
                🆔 记录ID: {record.id}
                """
                self.detail_text.setPlainText(detail_text)
    
    def _on_chart_days_changed(self) -> None:
        """处理图表天数变化。"""
        if self.selected_user:
            self._update_chart()
    
    def _clear_form(self) -> None:
        """清空表单内容。"""
        # 重置为默认值
        self.weight_spin.setValue(self.DEFAULT_WEIGHT_KG)
        self.date_edit.setDate(date.today())
        self.notes_edit.clear()
        
        # 确保按钮状态正确
        if hasattr(self, '_original_record_btn_state'):
            self._restore_record_btn()
    
    def _restore_record_btn(self) -> None:
        """恢复记录按钮的原始状态。"""
        if hasattr(self, '_original_record_btn_state'):
            original_text, original_slot = self._original_record_btn_state
            self.record_btn.setText(original_text)
            self.record_btn.clicked.disconnect()
            self.record_btn.clicked.connect(original_slot)
            delattr(self, '_original_record_btn_state')
    
    def refresh(self) -> None:
        """刷新标签页内容。"""
        self._load_users()
        if self.selected_user:
            self._load_weight_history()
    
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
    
    def show_record_details(self, record_id: int) -> bool:
        """显示指定体重记录的详细信息。
        
        Args:
            record_id: 体重记录ID
            
        Returns:
            是否成功显示
        """
        record = self.weight_controller.get_weight_by_id(record_id)
        if record and self.table_model:
            # 在表格中选中该记录
            for row in range(self.table_model.rowCount()):
                model_record = self.table_model.get_record_at(row)
                if model_record and model_record.id == record_id:
                    self.weight_table.selectRow(row)
                    self.weight_table.scrollTo(self.table_model.index(row, 0))
                    return True
        return False