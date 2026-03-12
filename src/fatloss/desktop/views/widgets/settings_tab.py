"""配置设置标签页。

提供应用程序配置管理功能，包括营养比例、调整策略、界面主题和数据库管理。
"""

from typing import Optional, Dict, Any
from datetime import date

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QGroupBox,
    QFormLayout,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QTabWidget,
    QMessageBox,
    QFileDialog,
    QLineEdit,
    QTextEdit,
    QProgressBar,
    QToolBar,
    QAction,
    QScrollArea,
    QSplitter,
    QSizePolicy,
    QApplication,
)

from fatloss.models.app_config import AppConfig
from fatloss.models.enums import UnitSystem, Theme
from fatloss.models.user_profile import UserProfile
from fatloss.desktop.controllers.settings_controller import SettingsController
from fatloss.desktop.utils.error_handler import ErrorHandler


class SettingsTab(QWidget):
    """配置设置标签页，提供应用程序配置管理功能。"""
    
    # 信号定义
    config_saved = pyqtSignal(AppConfig)          # 配置保存
    theme_changed = pyqtSignal(Theme)             # 主题改变
    database_backed_up = pyqtSignal(str)          # 数据库备份
    database_restored = pyqtSignal(str)           # 数据库恢复
    
    def __init__(self, settings_controller: SettingsController, parent=None):
        """初始化配置设置标签页。
        
        Args:
            settings_controller: 配置设置控制器实例
            parent: 父窗口部件
        """
        super().__init__(parent)
        
        self.settings_controller = settings_controller
        self.selected_user = None
        self.current_config = None
        
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
        
        # 创建标签页容器
        self.tab_widget = QTabWidget()
        
        # 标签页1：基本设置
        basic_settings_tab = self._create_basic_settings_tab()
        self.tab_widget.addTab(basic_settings_tab, "基本设置")
        
        # 标签页2：营养策略
        nutrition_settings_tab = self._create_nutrition_settings_tab()
        self.tab_widget.addTab(nutrition_settings_tab, "营养策略")
        
        # 标签页3：数据库管理
        database_tab = self._create_database_tab()
        self.tab_widget.addTab(database_tab, "数据库管理")
        
        # 标签页4：数据导出
        export_tab = self._create_export_tab()
        self.tab_widget.addTab(export_tab, "数据导出")
        
        # 标签页5：关于
        about_tab = self._create_about_tab()
        self.tab_widget.addTab(about_tab, "关于")
        
        main_layout.addWidget(self.tab_widget, 1)  # 拉伸因子
        
        self.setLayout(main_layout)
    
    def _create_toolbar(self) -> QToolBar:
        """创建工具栏。
        
        Returns:
            工具栏实例
        """
        toolbar = QToolBar()
        
        # 刷新按钮
        refresh_action = QAction("🔄 刷新", self)
        refresh_action.setToolTip("刷新配置数据")
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
        
        # 保存配置按钮
        save_action = QAction("💾 保存配置", self)
        save_action.setToolTip("保存当前配置")
        save_action.triggered.connect(self._save_config)
        toolbar.addAction(save_action)
        
        # 重置配置按钮
        reset_action = QAction("🔄 重置默认", self)
        reset_action.setToolTip("重置为默认配置")
        reset_action.triggered.connect(self._reset_to_defaults)
        toolbar.addAction(reset_action)
        
        return toolbar
    
    def _create_basic_settings_tab(self) -> QWidget:
        """创建基本设置标签页。
        
        Returns:
            基本设置标签页
        """
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # 使用滚动区域以适应内容
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(20)
        
        # 单位制设置
        unit_group = QGroupBox("单位制设置")
        unit_layout = QFormLayout()
        
        self.unit_system_combo = QComboBox()
        self.unit_system_combo.addItem("公制 (千克, 厘米)", UnitSystem.METRIC)
        self.unit_system_combo.addItem("英制 (磅, 英尺)", UnitSystem.IMPERIAL)
        unit_layout.addRow("单位制:", self.unit_system_combo)
        
        unit_group.setLayout(unit_layout)
        scroll_layout.addWidget(unit_group)
        
        # 界面设置
        interface_group = QGroupBox("界面设置")
        interface_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("浅色", Theme.LIGHT)
        self.theme_combo.addItem("深色", Theme.DARK)
        self.theme_combo.addItem("自动 (跟随系统)", Theme.AUTO)
        interface_layout.addRow("主题:", self.theme_combo)
        
        self.language_combo = QComboBox()
        self.language_combo.addItem("简体中文", "zh-CN")
        self.language_combo.addItem("English", "en-US")
        interface_layout.addRow("语言:", self.language_combo)
        
        interface_group.setLayout(interface_layout)
        scroll_layout.addWidget(interface_group)
        
        # 通知设置
        notification_group = QGroupBox("通知设置")
        notification_layout = QFormLayout()
        
        self.enable_notifications_check = QCheckBox("启用通知")
        notification_layout.addRow(self.enable_notifications_check)
        
        notification_group.setLayout(notification_layout)
        scroll_layout.addWidget(notification_group)
        
        # 周计划设置
        weekly_group = QGroupBox("周计划设置")
        weekly_layout = QFormLayout()
        
        self.weekly_check_day_combo = QComboBox()
        self.weekly_check_day_combo.addItem("周日", 0)
        self.weekly_check_day_combo.addItem("周一", 1)
        self.weekly_check_day_combo.addItem("周二", 2)
        self.weekly_check_day_combo.addItem("周三", 3)
        self.weekly_check_day_combo.addItem("周四", 4)
        self.weekly_check_day_combo.addItem("周五", 5)
        self.weekly_check_day_combo.addItem("周六", 6)
        weekly_layout.addRow("周检查日:", self.weekly_check_day_combo)
        
        weekly_group.setLayout(weekly_layout)
        scroll_layout.addWidget(weekly_group)
        
        # 数据保留设置
        data_group = QGroupBox("数据保留设置")
        data_layout = QFormLayout()
        
        self.data_retention_days_spin = QSpinBox()
        self.data_retention_days_spin.setRange(30, 3650)
        self.data_retention_days_spin.setValue(365)
        self.data_retention_days_spin.setSuffix(" 天")
        data_layout.addRow("数据保留天数:", self.data_retention_days_spin)
        
        data_group.setLayout(data_layout)
        scroll_layout.addWidget(data_group)
        
        scroll_layout.addStretch()
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        
        layout.addWidget(scroll_area)
        tab.setLayout(layout)
        return tab
    
    def _create_nutrition_settings_tab(self) -> QWidget:
        """创建营养策略标签页。
        
        Returns:
            营养策略标签页
        """
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # 使用滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(20)
        
        # 碳水化合物调整设置
        carb_group = QGroupBox("碳水化合物调整设置")
        carb_layout = QFormLayout()
        
        self.carb_adjustment_unit_spin = QSpinBox()
        self.carb_adjustment_unit_spin.setRange(10, 100)
        self.carb_adjustment_unit_spin.setValue(30)
        self.carb_adjustment_unit_spin.setSuffix(" 克/单位")
        self.carb_adjustment_unit_spin.setToolTip("每次调整碳水化合物的克数")
        carb_layout.addRow("碳水调整单位:", self.carb_adjustment_unit_spin)
        
        carb_group.setLayout(carb_layout)
        scroll_layout.addWidget(carb_group)
        
        # 减脂目标设置
        loss_group = QGroupBox("减脂目标设置")
        loss_layout = QFormLayout()
        
        self.monthly_loss_percentage_spin = QDoubleSpinBox()
        self.monthly_loss_percentage_spin.setRange(1.0, 10.0)
        self.monthly_loss_percentage_spin.setValue(5.0)
        self.monthly_loss_percentage_spin.setSuffix(" %")
        self.monthly_loss_percentage_spin.setToolTip("每月减脂目标百分比")
        loss_layout.addRow("每月减脂目标:", self.monthly_loss_percentage_spin)
        
        loss_group.setLayout(loss_layout)
        scroll_layout.addWidget(loss_group)
        
        # 训练消耗设置
        exercise_group = QGroupBox("训练消耗设置")
        exercise_layout = QFormLayout()
        
        self.exercise_calories_spin = QDoubleSpinBox()
        self.exercise_calories_spin.setRange(5.0, 20.0)
        self.exercise_calories_spin.setValue(10.0)
        self.exercise_calories_spin.setSuffix(" 大卡/分钟")
        self.exercise_calories_spin.setToolTip("每分钟训练消耗的热量")
        exercise_layout.addRow("训练消耗:", self.exercise_calories_spin)
        
        exercise_group.setLayout(exercise_layout)
        scroll_layout.addWidget(exercise_group)
        
        # 营养比例说明
        info_group = QGroupBox("营养比例说明")
        info_layout = QVBoxLayout()
        
        info_text = QLabel(
            "当前营养比例采用5:3:2分配策略：\n"
            "• 碳水化合物: 50% (提供能量)\n"
            "• 蛋白质: 30% (维持肌肉)\n"
            "• 脂肪: 20% (激素健康)\n\n"
            "此比例适用于大多数减脂场景，\n"
            "如需个性化调整请咨询营养师。"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("padding: 10px; background-color: #f9f9f9; border-radius: 4px;")
        info_layout.addWidget(info_text)
        
        info_group.setLayout(info_layout)
        scroll_layout.addWidget(info_group)
        
        scroll_layout.addStretch()
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        
        layout.addWidget(scroll_area)
        tab.setLayout(layout)
        return tab
    
    def _create_database_tab(self) -> QWidget:
        """创建数据库管理标签页。
        
        Returns:
            数据库管理标签页
        """
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # 数据库信息显示
        info_group = QGroupBox("数据库信息")
        info_layout = QFormLayout()
        
        self.db_path_label = QLabel("加载中...")
        self.db_path_label.setWordWrap(True)
        info_layout.addRow("数据库路径:", self.db_path_label)
        
        self.db_size_label = QLabel("加载中...")
        info_layout.addRow("数据库大小:", self.db_size_label)
        
        self.db_tables_label = QLabel("加载中...")
        info_layout.addRow("数据表数量:", self.db_tables_label)
        
        self.db_records_label = QLabel("加载中...")
        info_layout.addRow("总记录数:", self.db_records_label)
        
        self.db_modified_label = QLabel("加载中...")
        info_layout.addRow("最后修改:", self.db_modified_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 数据库操作按钮
        operation_group = QGroupBox("数据库操作")
        operation_layout = QVBoxLayout()
        
        # 备份数据库
        backup_layout = QHBoxLayout()
        self.backup_path_edit = QLineEdit()
        self.backup_path_edit.setPlaceholderText("选择备份文件保存路径...")
        backup_layout.addWidget(self.backup_path_edit, 1)
        
        browse_backup_btn = QPushButton("浏览...")
        browse_backup_btn.clicked.connect(self._browse_backup_path)
        backup_layout.addWidget(browse_backup_btn)
        
        operation_layout.addLayout(backup_layout)
        
        backup_btn = QPushButton("💾 备份数据库")
        backup_btn.clicked.connect(self._backup_database)
        operation_layout.addWidget(backup_btn)
        
        operation_layout.addSpacing(10)
        
        # 恢复数据库
        restore_layout = QHBoxLayout()
        self.restore_path_edit = QLineEdit()
        self.restore_path_edit.setPlaceholderText("选择备份文件恢复路径...")
        restore_layout.addWidget(self.restore_path_edit, 1)
        
        browse_restore_btn = QPushButton("浏览...")
        browse_restore_btn.clicked.connect(self._browse_restore_path)
        restore_layout.addWidget(browse_restore_btn)
        
        operation_layout.addLayout(restore_layout)
        
        restore_btn = QPushButton("🔄 恢复数据库")
        restore_btn.clicked.connect(self._restore_database)
        operation_layout.addWidget(restore_btn)
        
        operation_layout.addSpacing(10)
        
        # 数据库维护
        maintenance_btn = QPushButton("🔧 优化数据库")
        maintenance_btn.setToolTip("优化数据库性能")
        maintenance_btn.clicked.connect(self._optimize_database)
        operation_layout.addWidget(maintenance_btn)
        
        operation_group.setLayout(operation_layout)
        layout.addWidget(operation_group)
        
        # 状态信息
        self.db_status_label = QLabel("就绪")
        self.db_status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.db_status_label)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def _create_export_tab(self) -> QWidget:
        """创建数据导出标签页。
        
        Returns:
            数据导出标签页
        """
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # 使用滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(20)
        
        # 导出设置
        export_group = QGroupBox("导出设置")
        export_layout = QFormLayout()
        
        # 导出格式选择
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItem("JSON格式", "json")
        self.export_format_combo.addItem("CSV格式", "csv")
        export_layout.addRow("导出格式:", self.export_format_combo)
        
        # 包含体重记录
        self.include_weight_check = QCheckBox("包含体重记录")
        self.include_weight_check.setChecked(True)
        export_layout.addRow(self.include_weight_check)
        
        # 包含营养计划
        self.include_nutrition_check = QCheckBox("包含营养计划")
        self.include_nutrition_check.setChecked(True)
        export_layout.addRow(self.include_nutrition_check)
        
        export_group.setLayout(export_layout)
        scroll_layout.addWidget(export_group)
        
        # 导出文件路径
        path_group = QGroupBox("导出文件路径")
        path_layout = QVBoxLayout()
        
        path_input_layout = QHBoxLayout()
        self.export_path_edit = QLineEdit()
        self.export_path_edit.setPlaceholderText("选择导出文件保存路径...")
        path_input_layout.addWidget(self.export_path_edit, 1)
        
        browse_export_btn = QPushButton("浏览...")
        browse_export_btn.clicked.connect(self._browse_export_path)
        path_input_layout.addWidget(browse_export_btn)
        
        path_layout.addLayout(path_input_layout)
        
        # 默认文件名提示
        default_path_label = QLabel(
            "默认文件名格式: fatloss_export_{用户ID}_{日期}.{格式}\n"
            "例如: fatloss_export_1_2026-03-12.json"
        )
        default_path_label.setStyleSheet("color: #666; font-size: 12px;")
        path_layout.addWidget(default_path_label)
        
        path_group.setLayout(path_layout)
        scroll_layout.addWidget(path_group)
        
        # 导出操作按钮
        operation_group = QGroupBox("导出操作")
        operation_layout = QVBoxLayout()
        
        # 导出按钮
        export_btn = QPushButton("📤 导出数据")
        export_btn.setToolTip("导出选中的数据")
        export_btn.clicked.connect(self._export_user_data)
        operation_layout.addWidget(export_btn)
        
        operation_group.setLayout(operation_layout)
        scroll_layout.addWidget(operation_group)
        
        # 导出状态信息
        self.export_status_label = QLabel("就绪")
        self.export_status_label.setStyleSheet("color: #666; font-style: italic;")
        scroll_layout.addWidget(self.export_status_label)
        
        # 导出统计信息显示区域
        self.export_stats_text = QTextEdit()
        self.export_stats_text.setReadOnly(True)
        self.export_stats_text.setMaximumHeight(150)
        self.export_stats_text.setPlaceholderText("导出统计信息将显示在这里...")
        scroll_layout.addWidget(self.export_stats_text)
        
        scroll_layout.addStretch()
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        
        layout.addWidget(scroll_area)
        tab.setLayout(layout)
        return tab
    
    def _browse_export_path(self) -> None:
        """浏览导出文件保存路径。"""
        if not self.selected_user:
            QMessageBox.warning(self, "警告", "请先选择用户")
            return
        
        user_id = self.selected_user['id']
        default_filename = f"fatloss_export_{user_id}_{date.today()}.json"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择导出文件保存位置",
            default_filename,
            "JSON Files (*.json);;CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self.export_path_edit.setText(file_path)
            # 根据文件扩展名自动选择格式
            if file_path.lower().endswith('.csv'):
                self.export_format_combo.setCurrentIndex(1)  # CSV格式
            else:
                self.export_format_combo.setCurrentIndex(0)  # JSON格式
    
    def _export_user_data(self) -> None:
        """导出用户数据。"""
        if not self.selected_user:
            QMessageBox.warning(self, "警告", "请先选择用户")
            return
        
        export_path = self.export_path_edit.text().strip()
        
        if not export_path:
            QMessageBox.warning(self, "警告", "请先选择导出文件路径")
            return
        
        # 获取导出设置
        export_format = self.export_format_combo.currentData()
        include_weight_records = self.include_weight_check.isChecked()
        include_nutrition_plans = self.include_nutrition_check.isChecked()
        
        user_id = self.selected_user['id']
        
        # 确认对话框
        reply = QMessageBox.question(
            self,
            "导出数据",
            f"确定要导出用户数据吗？\n\n"
            f"用户: {self.selected_user['name']}\n"
            f"格式: {export_format.upper()}\n"
            f"包含体重记录: {'是' if include_weight_records else '否'}\n"
            f"包含营养计划: {'是' if include_nutrition_plans else '否'}\n"
            f"保存到: {export_path}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 显示导出中状态
                self.export_status_label.setText("导出中...")
                self.export_status_label.setStyleSheet("color: #0066cc; font-weight: bold;")
                QApplication.processEvents()  # 更新UI
                
                # 调用控制器导出数据
                stats = self.settings_controller.export_user_data(
                    user_id=user_id,
                    export_format=export_format,
                    output_path=export_path,
                    include_weight_records=include_weight_records,
                    include_nutrition_plans=include_nutrition_plans,
                    parent_widget=self
                )
                
                # 显示导出成功
                self.export_status_label.setText("导出成功 ✓")
                self.export_status_label.setStyleSheet("color: #009933; font-weight: bold;")
                
                # 显示统计信息
                stats_text = f"""✅ 数据导出成功！

📁 导出文件: {stats['output_path']}
📊 导出格式: {stats['export_format'].upper()}

📈 导出内容统计:
   • 用户信息: ✓
   • 配置信息: ✓
   • 体重记录: {stats['weight_records_count']} 条
   • 每日营养计划: {stats['daily_nutrition_plans_count']} 条
   • 每周营养计划: {stats['weekly_nutrition_plans_count']} 条

💾 导出已完成，文件已保存到指定位置。"""
                
                self.export_stats_text.setText(stats_text)
                
                # 显示成功消息
                QMessageBox.information(
                    self,
                    "导出成功",
                    f"数据已成功导出到:\n{export_path}\n\n"
                    f"共导出:\n"
                    f"• 体重记录: {stats['weight_records_count']} 条\n"
                    f"• 每日营养计划: {stats['daily_nutrition_plans_count']} 条\n"
                    f"• 每周营养计划: {stats['weekly_nutrition_plans_count']} 条"
                )
                
            except Exception as e:
                # 显示导出失败
                self.export_status_label.setText("导出失败 ✗")
                self.export_status_label.setStyleSheet("color: #cc0000; font-weight: bold;")
                
                error_text = f"""❌ 导出失败！

错误信息: {str(e)}

请检查:
1. 文件路径是否可写
2. 用户数据是否完整
3. 磁盘空间是否充足"""
                
                self.export_stats_text.setText(error_text)
                ErrorHandler.handle_service_error(e, self)
    
    def _create_about_tab(self) -> QWidget:
        """创建关于标签页。
        
        Returns:
            关于标签页
        """
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # 应用信息
        app_group = QGroupBox("应用信息")
        app_layout = QVBoxLayout()
        
        app_name = QLabel("Fatloss Planner")
        app_name.setStyleSheet("font-size: 24px; font-weight: bold;")
        app_layout.addWidget(app_name, 0, Qt.AlignmentFlag.AlignCenter)
        
        version_label = QLabel("版本: 1.0.0")
        app_layout.addWidget(version_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        description = QLabel(
            "科学减脂计划工具\n"
            "基于BMR/TDEE计算和营养学原理，\n"
            "帮助您制定科学的减脂计划。"
        )
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)
        app_layout.addWidget(description)
        
        app_group.setLayout(app_layout)
        layout.addWidget(app_group)
        
        # 技术信息
        tech_group = QGroupBox("技术信息")
        tech_layout = QFormLayout()
        
        tech_layout.addRow("开发语言:", QLabel("Python 3.9+"))
        tech_layout.addRow("GUI框架:", QLabel("PyQt5"))
        tech_layout.addRow("数据库:", QLabel("SQLite"))
        tech_layout.addRow("架构:", QLabel("MVC分层架构"))
        
        tech_group.setLayout(tech_layout)
        layout.addWidget(tech_group)
        
        # 版权信息
        copyright_group = QGroupBox("版权信息")
        copyright_layout = QVBoxLayout()
        
        copyright_text = QLabel(
            "© 2026 Fatloss Planner Team\n\n"
            "本软件遵循MIT开源协议。\n"
            "仅供学习和研究使用。\n"
            "商业使用请联系作者。"
        )
        copyright_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_text.setWordWrap(True)
        copyright_layout.addWidget(copyright_text)
        
        copyright_group.setLayout(copyright_layout)
        layout.addWidget(copyright_group)
        
        # 检查更新按钮
        check_update_btn = QPushButton("🔄 检查更新")
        check_update_btn.clicked.connect(self._check_for_updates)
        layout.addWidget(check_update_btn)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def _load_users(self) -> None:
        """加载用户列表到下拉框。"""
        try:
            users = self.settings_controller.get_all_users()
            self.user_combo.clear()
            
            # 添加占位项
            self.user_combo.addItem("-- 请选择用户 --", None)
            
            for user in users:
                display_text = f"{user['name']} ({user['age']}岁)"
                self.user_combo.addItem(display_text, user['id'])
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
    
    def _load_config(self) -> None:
        """加载用户配置。"""
        if not self.selected_user:
            return
        
        try:
            self.current_config = self.settings_controller.get_config(self.selected_user['id'])
            
            if self.current_config:
                # 更新UI控件
                self._update_config_ui(self.current_config)
                
                # 更新数据库信息
                self._update_database_info()
            else:
                # 使用默认配置
                default_config = AppConfig(user_id=self.selected_user['id'])
                self._update_config_ui(default_config)
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
    
    def _update_config_ui(self, config: AppConfig) -> None:
        """更新配置UI控件。
        
        Args:
            config: 应用配置对象
        """
        # 单位制
        for index in range(self.unit_system_combo.count()):
            if self.unit_system_combo.itemData(index) == config.unit_system:
                self.unit_system_combo.setCurrentIndex(index)
                break
        
        # 主题
        for index in range(self.theme_combo.count()):
            if self.theme_combo.itemData(index) == config.theme:
                self.theme_combo.setCurrentIndex(index)
                break
        
        # 语言
        for index in range(self.language_combo.count()):
            if self.language_combo.itemData(index) == config.language:
                self.language_combo.setCurrentIndex(index)
                break
        
        # 通知
        self.enable_notifications_check.setChecked(config.enable_notifications)
        
        # 周检查日
        for index in range(self.weekly_check_day_combo.count()):
            if self.weekly_check_day_combo.itemData(index) == config.weekly_check_day:
                self.weekly_check_day_combo.setCurrentIndex(index)
                break
        
        # 数据保留天数
        self.data_retention_days_spin.setValue(config.data_retention_days)
        
        # 营养策略
        self.carb_adjustment_unit_spin.setValue(config.carb_adjustment_unit_g)
        self.monthly_loss_percentage_spin.setValue(config.monthly_loss_percentage * 100)  # 转换为百分比
        self.exercise_calories_spin.setValue(config.exercise_calories_per_minute)
    
    def _update_database_info(self) -> None:
        """更新数据库信息显示。"""
        try:
            db_info = self.settings_controller.get_database_info()
            
            self.db_path_label.setText(db_info["path"])
            
            if db_info["exists"]:
                self.db_size_label.setText(f"{db_info['size_mb']:.2f} MB")
                self.db_tables_label.setText(str(db_info["table_count"]))
                self.db_records_label.setText(str(db_info["total_records"]))
                
                import datetime
                if db_info["last_modified"]:
                    dt = datetime.datetime.fromtimestamp(db_info["last_modified"])
                    self.db_modified_label.setText(dt.strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    self.db_modified_label.setText("未知")
            else:
                self.db_size_label.setText("数据库不存在")
                self.db_tables_label.setText("0")
                self.db_records_label.setText("0")
                self.db_modified_label.setText("未知")
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
    
    def _refresh_data(self) -> None:
        """刷新数据。"""
        self._load_users()
        if self.selected_user:
            self._load_config()
    
    def _on_user_selected(self, index: int) -> None:
        """处理用户选择变化。
        
        Args:
            index: 当前选中索引
        """
        user_id = self.user_combo.itemData(index)
        
        if user_id is None:
            self.selected_user = None
            return
        
        # 获取用户信息
        user_info = self.settings_controller.get_user_by_id(user_id)
        if user_info:
            self.selected_user = user_info
            
            # 加载配置
            self._load_config()
    
    def _save_config(self) -> None:
        """保存配置。"""
        if not self.selected_user:
            QMessageBox.warning(self, "警告", "请先选择用户")
            return
        
        try:
            # 获取UI中的配置值
            unit_system = self.unit_system_combo.currentData()
            theme = self.theme_combo.currentData()
            language = self.language_combo.currentData()
            weekly_check_day = self.weekly_check_day_combo.currentData()
            carb_adjustment_unit_g = self.carb_adjustment_unit_spin.value()
            monthly_loss_percentage = self.monthly_loss_percentage_spin.value() / 100.0  # 转换为小数
            exercise_calories_per_minute = self.exercise_calories_spin.value()
            enable_notifications = self.enable_notifications_check.isChecked()
            data_retention_days = self.data_retention_days_spin.value()
            
            # 保存配置
            saved_config = self.settings_controller.save_config(
                user_id=self.selected_user['id'],
                unit_system=unit_system,
                theme=theme,
                language=language,
                weekly_check_day=weekly_check_day,
                carb_adjustment_unit_g=carb_adjustment_unit_g,
                monthly_loss_percentage=monthly_loss_percentage,
                exercise_calories_per_minute=exercise_calories_per_minute,
                enable_notifications=enable_notifications,
                data_retention_days=data_retention_days,
                parent_widget=self
            )
            
            if saved_config:
                self.current_config = saved_config
                self.config_saved.emit(saved_config)
                
                # 如果主题改变，发出主题改变信号
                if theme != self.current_config.theme:
                    self.theme_changed.emit(theme)
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
    
    def _reset_to_defaults(self) -> None:
        """重置为默认配置。"""
        if not self.selected_user:
            QMessageBox.warning(self, "警告", "请先选择用户")
            return
        
        # 确认对话框
        reply = QMessageBox.question(
            self,
            "重置配置",
            "确定要重置为默认配置吗？\n当前配置将丢失。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 创建默认配置
            default_config = AppConfig(user_id=self.selected_user['id'])
            
            # 更新UI
            self._update_config_ui(default_config)
            
            # 保存配置
            self._save_config()
    
    def _browse_backup_path(self) -> None:
        """浏览备份文件保存路径。"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择备份文件保存位置",
            f"fatloss_backup_{date.today()}.db",
            "Database Files (*.db);;All Files (*)"
        )
        
        if file_path:
            self.backup_path_edit.setText(file_path)
    
    def _browse_restore_path(self) -> None:
        """浏览备份文件恢复路径。"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择备份文件",
            "",
            "Database Files (*.db);;All Files (*)"
        )
        
        if file_path:
            self.restore_path_edit.setText(file_path)
    
    def _backup_database(self) -> None:
        """备份数据库。"""
        backup_path = self.backup_path_edit.text().strip()
        
        if not backup_path:
            QMessageBox.warning(self, "警告", "请先选择备份文件保存路径")
            return
        
        # 确认对话框
        reply = QMessageBox.question(
            self,
            "备份数据库",
            f"确定要备份数据库到:\n{backup_path}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.settings_controller.backup_database(
                backup_path=backup_path,
                parent_widget=self
            )
            
            if success:
                self.database_backed_up.emit(backup_path)
                self._update_database_info()
                self.db_status_label.setText("数据库备份完成")
    
    def _restore_database(self) -> None:
        """恢复数据库。"""
        restore_path = self.restore_path_edit.text().strip()
        
        if not restore_path:
            QMessageBox.warning(self, "警告", "请先选择备份文件")
            return
        
        # 警告对话框
        reply = QMessageBox.warning(
            self,
            "恢复数据库",
            f"⚠️ 警告: 这将覆盖当前数据库!\n\n"
            f"从: {restore_path}\n"
            f"恢复后将无法撤销。\n\n"
            f"确定要继续吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.settings_controller.restore_database(
                backup_path=restore_path,
                parent_widget=self
            )
            
            if success:
                self.database_restored.emit(restore_path)
                self._update_database_info()
                self.db_status_label.setText("数据库恢复完成")
    
    def _optimize_database(self) -> None:
        """优化数据库。"""
        try:
            import sqlite3
            import os
            from pathlib import Path
            
            # 获取数据库文件路径
            db_info = self.settings_controller.get_database_info()
            db_path = db_info["path"]
            
            if not os.path.exists(db_path):
                ErrorHandler.show_warning(f"数据库文件不存在: {db_path}", self)
                return
            
            # 执行VACUUM命令优化数据库
            conn = sqlite3.connect(db_path)
            conn.execute("VACUUM")
            conn.close()
            
            ErrorHandler.show_success("数据库优化完成", self)
            self.db_status_label.setText("数据库优化完成")
            self._update_database_info()
            
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
    
    def _check_for_updates(self) -> None:
        """检查更新。"""
        QMessageBox.information(
            self,
            "检查更新",
            "当前已是最新版本: 1.0.0\n\n"
            "自动更新功能将在未来版本中实现。\n"
            "请关注项目更新。"
        )
    
    def refresh(self) -> None:
        """刷新标签页内容。"""
        self._refresh_data()
    
    def set_selected_user(self, user_info: Dict[str, Any]) -> None:
        """设置选中的用户。
        
        Args:
            user_info: 用户信息字典
        """
        self.selected_user = user_info
        self._select_user_in_combo(user_info['id'])
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