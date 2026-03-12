"""营养计算对话框模块。

提供营养计算参数的输入和结果显示。
"""

from typing import Optional, List
from datetime import date

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QComboBox,
    QDoubleSpinBox,
    QSpinBox,
    QDateEdit,
    QTextEdit,
    QLabel,
    QPushButton,
    QDialogButtonBox,
    QGroupBox,
    QGridLayout,
    QWidget,
    QApplication,
    QFrame,
    QSplitter,
)

from fatloss.models.user_profile import UserProfile
from fatloss.models.nutrition_plan import DailyNutritionPlan
from fatloss.desktop.controllers.nutrition_controller import NutritionController
from fatloss.desktop.utils.error_handler import ErrorHandler


class NutritionDialog(QDialog):
    """营养计算对话框，用于输入计算参数并显示结果。"""
    
    # 信号定义
    calculation_completed = pyqtSignal(DailyNutritionPlan)  # 计算完成
    
    # 常量定义
    MIN_EXERCISE_MINUTES = 0.0
    MAX_EXERCISE_MINUTES = 300.0
    MIN_ADJUSTMENT_UNITS = -10
    MAX_ADJUSTMENT_UNITS = 10
    
    DEFAULT_EXERCISE_MINUTES = 60.0
    DEFAULT_ADJUSTMENT_UNITS = 0
    
    def __init__(
        self,
        nutrition_controller: NutritionController,
        parent=None,
        user: Optional[UserProfile] = None
    ):
        """初始化营养计算对话框。
        
        Args:
            nutrition_controller: 营养计算控制器实例
            parent: 父窗口部件
            user: 预选用户，如果为None则允许选择
        """
        super().__init__(parent)
        
        self.nutrition_controller = nutrition_controller
        self.selected_user = user
        self.result_plan = None
        
        self.setWindowTitle("营养计算器")
        self.setMinimumSize(700, 600)
        
        self._init_ui()
        self._load_users()
        
        if user:
            self._select_user(user.id)
    
    def _init_ui(self) -> None:
        """初始化用户界面。"""
        main_layout = QVBoxLayout()
        
        # 创建分割器，左侧输入，右侧结果
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧输入面板
        input_widget = self._create_input_panel()
        splitter.addWidget(input_widget)
        
        # 右侧结果面板
        result_widget = self._create_result_panel()
        splitter.addWidget(result_widget)
        
        # 设置分割器初始比例
        splitter.setSizes([300, 400])
        
        main_layout.addWidget(splitter)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Calculate | QDialogButtonBox.Close
        )
        calculate_btn = button_box.button(QDialogButtonBox.Calculate)
        calculate_btn.setText("计算")
        calculate_btn.clicked.connect(self._on_calculate)
        
        close_btn = button_box.button(QDialogButtonBox.Close)
        close_btn.setText("关闭")
        close_btn.clicked.connect(self.reject)
        
        main_layout.addWidget(button_box)
        
        self.setLayout(main_layout)
    
    def _create_input_panel(self) -> QWidget:
        """创建输入面板。
        
        Returns:
            输入面板部件
        """
        panel = QWidget()
        layout = QVBoxLayout()
        
        # 用户选择组
        user_group = QGroupBox("用户选择")
        user_layout = QVBoxLayout()
        
        self.user_combo = QComboBox()
        self.user_combo.setMinimumWidth(200)
        self.user_combo.currentIndexChanged.connect(self._on_user_changed)
        user_layout.addWidget(self.user_combo)
        
        # 用户信息标签
        self.user_info_label = QLabel("请选择一个用户")
        self.user_info_label.setWordWrap(True)
        self.user_info_label.setStyleSheet("padding: 5px; background-color: #f0f0f0; border-radius: 3px;")
        user_layout.addWidget(self.user_info_label)
        
        user_group.setLayout(user_layout)
        layout.addWidget(user_group)
        
        # 计算参数组
        params_group = QGroupBox("计算参数")
        params_layout = QFormLayout()
        
        # 计划日期
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QApplication.instance().activeWindow().date() if QApplication.instance().activeWindow() else date.today())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        params_layout.addRow("计划日期:", self.date_edit)
        
        # 训练分钟数
        self.exercise_spin = QDoubleSpinBox()
        self.exercise_spin.setRange(self.MIN_EXERCISE_MINUTES, self.MAX_EXERCISE_MINUTES)
        self.exercise_spin.setValue(self.DEFAULT_EXERCISE_MINUTES)
        self.exercise_spin.setSuffix(" 分钟")
        self.exercise_spin.setDecimals(0)
        self.exercise_spin.setSingleStep(10)
        params_layout.addRow("训练时间:", self.exercise_spin)
        
        # 碳水化合物调整
        self.adjustment_spin = QSpinBox()
        self.adjustment_spin.setRange(self.MIN_ADJUSTMENT_UNITS, self.MAX_ADJUSTMENT_UNITS)
        self.adjustment_spin.setValue(self.DEFAULT_ADJUSTMENT_UNITS)
        self.adjustment_spin.setSuffix(" 单位 (±30g)")
        self.adjustment_spin.setSingleStep(1)
        params_layout.addRow("碳水调整:", self.adjustment_spin)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        layout.addStretch()
        
        panel.setLayout(layout)
        return panel
    
    def _create_result_panel(self) -> QWidget:
        """创建结果面板。
        
        Returns:
            结果面板部件
        """
        panel = QWidget()
        layout = QVBoxLayout()
        
        # 计算结果组
        result_group = QGroupBox("计算结果")
        result_layout = QVBoxLayout()
        
        # 基本信息
        info_layout = QGridLayout()
        
        self.bmr_label = QLabel("BMR: --")
        self.tdee_label = QLabel("TDEE: --")
        self.weight_label = QLabel("当前体重: --")
        
        info_layout.addWidget(QLabel("<b>基础代谢:</b>"), 0, 0)
        info_layout.addWidget(self.bmr_label, 0, 1)
        info_layout.addWidget(QLabel("<b>总消耗:</b>"), 1, 0)
        info_layout.addWidget(self.tdee_label, 1, 1)
        info_layout.addWidget(QLabel("<b>体重:</b>"), 2, 0)
        info_layout.addWidget(self.weight_label, 2, 1)
        
        result_layout.addLayout(info_layout)
        
        # 分隔线
        result_layout.addWidget(QLabel(""))
        
        # 营养素详情
        nutrition_layout = QGridLayout()
        
        self.protein_label = QLabel("蛋白质: --")
        self.carbs_label = QLabel("碳水化合物: --")
        self.fat_label = QLabel("脂肪: --")
        self.calories_label = QLabel("总热量: --")
        
        nutrition_layout.addWidget(QLabel("<b>🥩 蛋白质:</b>"), 0, 0)
        nutrition_layout.addWidget(self.protein_label, 0, 1)
        nutrition_layout.addWidget(QLabel("<b>🍚 碳水化合物:</b>"), 1, 0)
        nutrition_layout.addWidget(self.carbs_label, 1, 1)
        nutrition_layout.addWidget(QLabel("<b>🥑 脂肪:</b>"), 2, 0)
        nutrition_layout.addWidget(self.fat_label, 2, 1)
        nutrition_layout.addWidget(QLabel("<b>🔥 总热量:</b>"), 3, 0)
        nutrition_layout.addWidget(self.calories_label, 3, 1)
        
        result_layout.addLayout(nutrition_layout)
        
        # 分隔线
        result_layout.addWidget(QLabel(""))
        
        # 详细文本
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(150)
        self.result_text.setPlaceholderText("计算结果将显示在这里...")
        result_layout.addWidget(self.result_text)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
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
                display_text = f"{user.name} ({user.age}岁, {user.height_cm}cm)"
                self.user_combo.addItem(display_text, user.id)
            
            # 如果有预选用户，选中它
            if self.selected_user:
                self._select_user(self.selected_user.id)
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
    
    def _select_user(self, user_id: int) -> None:
        """选择指定用户。
        
        Args:
            user_id: 用户ID
        """
        for index in range(self.user_combo.count()):
            if self.user_combo.itemData(index) == user_id:
                self.user_combo.setCurrentIndex(index)
                break
    
    def _on_user_changed(self, index: int) -> None:
        """处理用户选择变化。
        
        Args:
            index: 当前选中索引
        """
        user_id = self.user_combo.itemData(index)
        
        if user_id is None:
            self.user_info_label.setText("请选择一个用户")
            self.selected_user = None
            return
        
        # 获取用户信息
        user = self.nutrition_controller.get_user_by_id(user_id)
        if user:
            self.selected_user = user
            
            # 更新用户信息显示
            gender = user.gender.value if hasattr(user.gender, 'value') else user.gender
            activity = user.activity_level.value if hasattr(user.activity_level, 'value') else user.activity_level
            info_text = f"""
            <b>{user.name}</b><br>
            性别: {gender}<br>
            年龄: {user.age}岁<br>
            身高: {user.height_cm}cm<br>
            活动水平: {activity}
            """
            self.user_info_label.setText(info_text)
            
            # 清空之前的计算结果
            self._clear_results()
    
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
            
            # 计算BMR和TDEE
            bmr_tdee_result = self.nutrition_controller.calculate_bmr_tdee(
                user=self.selected_user,
                exercise_minutes=exercise_minutes
            )
            
            # 更新基础信息显示
            self.bmr_label.setText(f"{bmr_tdee_result['bmr']:.0f} kcal")
            self.tdee_label.setText(f"{bmr_tdee_result['tdee']:.0f} kcal")
            self.weight_label.setText(f"{bmr_tdee_result['weight_kg']:.1f} kg")
            
            # 计算营养素分配
            nutrition = self.nutrition_controller.calculate_nutrition_from_tdee(
                tdee=bmr_tdee_result['tdee'],
                adjustment_units=adjustment_units
            )
            
            # 更新营养素显示
            self.protein_label.setText(f"{nutrition.protein_g:.1f} g")
            self.carbs_label.setText(f"{nutrition.carbohydrates_g:.1f} g")
            self.fat_label.setText(f"{nutrition.fat_g:.1f} g")
            self.calories_label.setText(f"{nutrition.calories_kcal:.0f} kcal")
            
            # 计算完整的营养计划
            plan = self.nutrition_controller.calculate_nutrition_plan(
                user_id=self.selected_user.id,
                plan_date=plan_date,
                exercise_minutes=exercise_minutes,
                adjustment_units=adjustment_units,
                parent_widget=self
            )
            
            if plan:
                self.result_plan = plan
                
                # 显示详细结果
                summary = self.nutrition_controller.format_nutrition_summary(plan)
                self.result_text.setPlainText(summary)
                
                # 发出信号
                self.calculation_completed.emit(plan)
                
                # 更新按钮文本
                calculate_btn = self.findChild(QDialogButtonBox).button(QDialogButtonBox.Calculate)
                calculate_btn.setText("重新计算")
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
    
    def _clear_results(self) -> None:
        """清空计算结果。"""
        self.bmr_label.setText("BMR: --")
        self.tdee_label.setText("TDEE: --")
        self.weight_label.setText("当前体重: --")
        
        self.protein_label.setText("蛋白质: --")
        self.carbs_label.setText("碳水化合物: --")
        self.fat_label.setText("脂肪: --")
        self.calories_label.setText("总热量: --")
        
        self.result_text.clear()
        self.result_plan = None
        
        # 重置按钮文本
        calculate_btn = self.findChild(QDialogButtonBox).button(QDialogButtonBox.Calculate)
        calculate_btn.setText("计算")
    
    def get_result(self) -> Optional[DailyNutritionPlan]:
        """获取计算结果。
        
        Returns:
            营养计划对象，如果未计算则为None
        """
        return self.result_plan
    
    @staticmethod
    def calculate_nutrition(
        nutrition_controller: NutritionController,
        parent=None,
        user: Optional[UserProfile] = None
    ) -> Optional[DailyNutritionPlan]:
        """静态方法：打开营养计算对话框。
        
        Args:
            nutrition_controller: 营养计算控制器实例
            parent: 父窗口部件
            user: 预选用户
            
        Returns:
            营养计划对象，如果取消则为None
        """
        dialog = NutritionDialog(
            nutrition_controller=nutrition_controller,
            parent=parent,
            user=user
        )
        
        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_result()
        return None