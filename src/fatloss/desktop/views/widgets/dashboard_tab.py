"""仪表盘标签页。

提供关键指标概览、数据可视化和减脂进度跟踪。
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
    QGridLayout,
    QGroupBox,
    QFrame,
    QApplication,
    QToolBar,
    QAction,
    QSizePolicy,
    QScrollArea,
)

# 尝试导入matplotlib
try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    FigureCanvas = None
    Figure = None

from fatloss.models.user_profile import UserProfile
from fatloss.desktop.controllers.dashboard_controller import DashboardController
from fatloss.desktop.utils.error_handler import ErrorHandler


class DashboardTab(QWidget):
    """仪表盘标签页，提供关键指标概览和数据可视化。"""
    
    # 信号定义
    user_selected = pyqtSignal(UserProfile)  # 用户被选中
    data_updated = pyqtSignal()              # 数据更新
    
    # 常量定义
    CARD_MIN_HEIGHT = 100
    CHART_MIN_HEIGHT = 300
    
    DEFAULT_CHART_DAYS = 30
    CHART_DAYS_OPTIONS = [7, 14, 30, 60, 90]
    
    # 颜色定义
    COLOR_PRIMARY = "#4CAF50"      # 绿色
    COLOR_SECONDARY = "#2196F3"    # 蓝色
    COLOR_WARNING = "#FF9800"      # 橙色
    COLOR_DANGER = "#F44336"       # 红色
    COLOR_INFO = "#9C27B0"         # 紫色
    
    def __init__(self, dashboard_controller: DashboardController, parent=None):
        """初始化仪表盘标签页。
        
        Args:
            dashboard_controller: 仪表盘控制器实例
            parent: 父窗口部件
        """
        super().__init__(parent)
        
        self.dashboard_controller = dashboard_controller
        self.selected_user = None
        self.dashboard_data = None
        
        # 图表相关
        self.weight_chart_canvas = None
        self.weight_chart_figure = None
        self.nutrition_chart_canvas = None
        self.nutrition_chart_figure = None
        
        self._init_ui()
        self._load_users()
    
    def _init_ui(self) -> None:
        """初始化用户界面。"""
        # 使用滚动区域以适应内容
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # 顶部工具栏
        toolbar = self._create_toolbar()
        main_layout.addWidget(toolbar)
        
        # 用户信息栏
        user_info_bar = self._create_user_info_bar()
        main_layout.addWidget(user_info_bar)
        
        # 关键指标卡片
        metrics_section = self._create_metrics_section()
        main_layout.addWidget(metrics_section)
        
        # 图表区域
        charts_section = self._create_charts_section()
        main_layout.addWidget(charts_section)
        
        # 建议和活动区域
        bottom_section = self._create_bottom_section()
        main_layout.addWidget(bottom_section)
        
        main_layout.addStretch()
        
        main_widget.setLayout(main_layout)
        scroll_area.setWidget(main_widget)
        
        # 设置主布局
        final_layout = QVBoxLayout()
        final_layout.addWidget(scroll_area)
        self.setLayout(final_layout)
    
    def _create_toolbar(self) -> QToolBar:
        """创建工具栏。
        
        Returns:
            工具栏实例
        """
        toolbar = QToolBar()
        
        # 刷新按钮
        refresh_action = QAction("刷新", self)
        refresh_action.setToolTip("刷新仪表盘数据")
        refresh_action.triggered.connect(self._load_dashboard_data)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
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
        if self.DEFAULT_CHART_DAYS in self.CHART_DAYS_OPTIONS:
            default_index = self.CHART_DAYS_OPTIONS.index(self.DEFAULT_CHART_DAYS)
            self.chart_days_combo.setCurrentIndex(default_index)
        
        self.chart_days_combo.currentIndexChanged.connect(self._on_chart_days_changed)
        toolbar.addWidget(self.chart_days_combo)
        
        return toolbar
    
    def _create_user_info_bar(self) -> QWidget:
        """创建用户信息栏。
        
        Returns:
            用户信息栏部件
        """
        bar = QWidget()
        bar.setStyleSheet("""
            QWidget {
                background-color: #f0f8ff;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout()
        
        # 用户头像占位符
        avatar_label = QLabel("👤")
        avatar_label.setStyleSheet("font-size: 40px;")
        layout.addWidget(avatar_label)
        
        # 用户信息
        self.user_info_widget = QWidget()
        user_info_layout = QVBoxLayout()
        
        self.user_name_label = QLabel("请选择一个用户")
        self.user_name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        user_info_layout.addWidget(self.user_name_label)
        
        self.user_details_label = QLabel("")
        self.user_details_label.setWordWrap(True)
        user_info_layout.addWidget(self.user_details_label)
        
        self.user_info_widget.setLayout(user_info_layout)
        layout.addWidget(self.user_info_widget, 1)  # 拉伸因子
        
        # 健康评分
        self.health_score_widget = QWidget()
        health_score_layout = QVBoxLayout()
        health_score_layout.setAlignment(Qt.AlignCenter)
        
        self.health_score_label = QLabel("--")
        self.health_score_label.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #4CAF50;
        """)
        health_score_layout.addWidget(self.health_score_label)
        
        health_score_text = QLabel("健康评分")
        health_score_text.setAlignment(Qt.AlignCenter)
        health_score_layout.addWidget(health_score_text)
        
        self.health_score_widget.setLayout(health_score_layout)
        layout.addWidget(self.health_score_widget)
        
        bar.setLayout(layout)
        return bar
    
    def _create_metrics_section(self) -> QWidget:
        """创建关键指标卡片区域。
        
        Returns:
            指标卡片区域部件
        """
        section = QGroupBox("关键指标")
        section_layout = QGridLayout()
        
        # 创建6个指标卡片
        self.metric_cards = []
        
        card_titles = [
            "当前体重", "目标体重", "减脂进度",
            "TDEE", "体重变化(30天)", "记录数量"
        ]
        
        card_keys = [
            "current_weight", "target_weight", "progress_percentage",
            "tdee", "weight_change_30d", "weight_records_count"
        ]
        
        card_colors = [
            self.COLOR_PRIMARY, self.COLOR_SECONDARY, self.COLOR_INFO,
            self.COLOR_WARNING, self.COLOR_DANGER, self.COLOR_PRIMARY
        ]
        
        card_icons = ["⚖️", "🎯", "📊", "🔥", "🔄", "📈"]
        
        for i in range(6):
            card = self._create_metric_card(
                title=card_titles[i],
                value_key=card_keys[i],
                color=card_colors[i],
                icon=card_icons[i]
            )
            self.metric_cards.append(card)
            
            # 添加到网格布局（2行3列）
            row = i // 3
            col = i % 3
            section_layout.addWidget(card, row, col)
        
        section.setLayout(section_layout)
        return section
    
    def _create_metric_card(self, title: str, value_key: str, color: str, icon: str) -> QWidget:
        """创建单个指标卡片。
        
        Args:
            title: 卡片标题
            value_key: 数据键名
            color: 卡片颜色
            icon: 图标
            
        Returns:
            指标卡片部件
        """
        card = QFrame()
        card.setFrameStyle(QFrame.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        card.setMinimumHeight(self.CARD_MIN_HEIGHT)
        
        layout = QVBoxLayout()
        
        # 标题行
        title_layout = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        title_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {color};
        """)
        title_layout.addWidget(title_label, 1)  # 拉伸因子
        
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 数值显示
        value_label = QLabel("--")
        value_label.setObjectName(f"metric_{value_key}")  # 用于后续更新
        value_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #333333;
        """)
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label, 1)  # 拉伸因子
        
        # 单位/说明
        unit_label = QLabel(self._get_metric_unit(value_key))
        unit_label.setStyleSheet("font-size: 12px; color: #666666;")
        unit_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(unit_label)
        
        card.setLayout(layout)
        return card
    
    def _create_charts_section(self) -> QWidget:
        """创建图表区域。
        
        Returns:
            图表区域部件
        """
        section = QGroupBox("数据可视化")
        section_layout = QHBoxLayout()
        
        # 左侧：体重趋势图
        weight_chart_group = QGroupBox("体重趋势")
        weight_chart_layout = QVBoxLayout()
        
        if MATPLOTLIB_AVAILABLE:
            self.weight_chart_figure = Figure(figsize=(6, 4), dpi=100)
            self.weight_chart_canvas = FigureCanvas(self.weight_chart_figure)
            self.weight_chart_canvas.setMinimumHeight(self.CHART_MIN_HEIGHT)
            weight_chart_layout.addWidget(self.weight_chart_canvas)
        else:
            warning_label = QLabel("matplotlib未安装，无法显示图表")
            warning_label.setAlignment(Qt.AlignCenter)
            warning_label.setStyleSheet("color: #ff0000; font-weight: bold;")
            weight_chart_layout.addWidget(warning_label)
        
        weight_chart_group.setLayout(weight_chart_layout)
        section_layout.addWidget(weight_chart_group, 1)  # 拉伸因子
        
        # 右侧：营养比例图
        nutrition_chart_group = QGroupBox("营养比例")
        nutrition_chart_layout = QVBoxLayout()
        
        if MATPLOTLIB_AVAILABLE:
            self.nutrition_chart_figure = Figure(figsize=(4, 4), dpi=100)
            self.nutrition_chart_canvas = FigureCanvas(self.nutrition_chart_figure)
            self.nutrition_chart_canvas.setMinimumHeight(self.CHART_MIN_HEIGHT)
            nutrition_chart_layout.addWidget(self.nutrition_chart_canvas)
        else:
            warning_label = QLabel("matplotlib未安装，无法显示图表")
            warning_label.setAlignment(Qt.AlignCenter)
            warning_label.setStyleSheet("color: #ff0000; font-weight: bold;")
            nutrition_chart_layout.addWidget(warning_label)
        
        nutrition_chart_group.setLayout(nutrition_chart_layout)
        section_layout.addWidget(nutrition_chart_group, 1)  # 拉伸因子
        
        section.setLayout(section_layout)
        return section
    
    def _create_bottom_section(self) -> QWidget:
        """创建底部区域（建议和活动）。
        
        Returns:
            底部区域部件
        """
        section = QWidget()
        section_layout = QHBoxLayout()
        
        # 左侧：调整建议
        suggestion_group = QGroupBox("调整建议")
        suggestion_layout = QVBoxLayout()
        
        self.suggestion_text = QLabel("选择用户后显示调整建议...")
        self.suggestion_text.setWordWrap(True)
        self.suggestion_text.setStyleSheet("""
            font-size: 14px;
            padding: 10px;
            background-color: #f9f9f9;
            border-radius: 4px;
        """)
        suggestion_layout.addWidget(self.suggestion_text)
        
        suggestion_group.setLayout(suggestion_layout)
        section_layout.addWidget(suggestion_group, 1)  # 拉伸因子
        
        # 右侧：最近活动
        activity_group = QGroupBox("最近活动")
        activity_layout = QVBoxLayout()
        
        self.activity_text = QLabel("暂无活动记录")
        self.activity_text.setWordWrap(True)
        self.activity_text.setStyleSheet("""
            font-size: 12px;
            padding: 10px;
            background-color: #f9f9f9;
            border-radius: 4px;
        """)
        activity_layout.addWidget(self.activity_text)
        
        activity_group.setLayout(activity_layout)
        section_layout.addWidget(activity_group, 1)  # 拉伸因子
        
        section.setLayout(section_layout)
        return section
    
    def _load_users(self) -> None:
        """加载用户列表到下拉框。"""
        try:
            users = self.dashboard_controller.get_all_users()
            self.user_combo.clear()
            
            # 添加占位项
            self.user_combo.addItem("-- 请选择用户 --", None)
            
            for user in users:
                display_text = f"{user.name} ({user.age}岁)"
                self.user_combo.addItem(display_text, user.id)
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
    
    def _load_dashboard_data(self) -> None:
        """加载仪表盘数据。"""
        if not self.selected_user:
            return
        
        try:
            # 获取仪表盘数据
            self.dashboard_data = self.dashboard_controller.get_dashboard_data(
                user_id=self.selected_user.id,
                parent_widget=self
            )
            
            if self.dashboard_data:
                # 更新UI
                self._update_user_info()
                self._update_metrics()
                self._update_charts()
                self._update_suggestions()
                self._update_activities()
                
                # 发出数据更新信号
                self.data_updated.emit()
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
    
    def _update_user_info(self) -> None:
        """更新用户信息显示。"""
        if not self.dashboard_data or "user" not in self.dashboard_data:
            return
        
        user = self.dashboard_data["user"]
        
        # 更新用户名
        self.user_name_label.setText(user.name)
        
        # 更新用户详情
        gender = user.gender.value if hasattr(user.gender, 'value') else user.gender
        activity = user.activity_level.value if hasattr(user.activity_level, 'value') else user.activity_level
        details = f"""
         性别: {gender}
         年龄: {user.age}岁
         身高: {user.height_cm}cm
         活动水平: {activity}
        """
        self.user_details_label.setText(details)
        
        # 更新健康评分
        if "dashboard_metrics" in self.dashboard_data:
            metrics = self.dashboard_data["dashboard_metrics"]
            health_score = metrics.get("health_score", 0)
            self.health_score_label.setText(f"{health_score}")
            
            # 根据分数设置颜色
            if health_score >= 80:
                color = "#4CAF50"  # 绿色
            elif health_score >= 60:
                color = "#FF9800"  # 橙色
            else:
                color = "#F44336"  # 红色
            
            self.health_score_label.setStyleSheet(f"""
                font-size: 32px;
                font-weight: bold;
                color: {color};
            """)
    
    def _update_metrics(self) -> None:
        """更新指标卡片。"""
        if not self.dashboard_data:
            return
        
        metrics = self.dashboard_data.get("dashboard_metrics", {})
        
        # 更新每个指标卡片
        for card in self.metric_cards:
            # 找到卡片中的值标签
            value_label = card.findChild(QLabel, "metric_*")
            if value_label:
                # 提取指标键名
                metric_key = value_label.objectName().replace("metric_", "")
                
                # 获取值
                value = metrics.get(metric_key)
                
                # 格式化显示
                if value is None:
                    display_value = "--"
                elif metric_key == "progress_percentage":
                    display_value = f"{value:.1f}%"
                elif metric_key in ["current_weight", "target_weight", "weight_change_30d"]:
                    display_value = f"{value:.1f}"
                elif metric_key == "tdee":
                    display_value = f"{int(value)}"
                elif metric_key == "weight_records_count":
                    display_value = f"{int(value)}"
                else:
                    display_value = str(value)
                
                value_label.setText(display_value)
    
    def _update_charts(self) -> None:
        """更新图表。"""
        if not MATPLOTLIB_AVAILABLE or not self.dashboard_data:
            return
        
        # 更新体重趋势图
        self._update_weight_chart()
        
        # 更新营养比例图
        self._update_nutrition_chart()
    
    def _update_weight_chart(self) -> None:
        """更新体重趋势图。"""
        if not self.weight_chart_figure:
            return
        
        # 获取图表天数
        chart_days = self.chart_days_combo.currentData()
        if chart_days is None:
            chart_days = self.DEFAULT_CHART_DAYS
        
        # 清空图表
        self.weight_chart_figure.clear()
        
        # 创建子图
        ax = self.weight_chart_figure.add_subplot(111)
        
        # 检查是否有图表数据
        chart_data = self.dashboard_data.get("chart_data", {})
        
        if chart_data.get("has_data", False) and chart_data.get("dates") and chart_data.get("weights"):
            dates = chart_data["dates"]
            weights = chart_data["weights"]
            trend = chart_data.get("trend", [])
            
            # 绘制折线图
            ax.plot(dates, weights, 'b-', linewidth=2, marker='o', markersize=4, label='体重')
            
            # 绘制趋势线
            if trend:
                ax.plot(dates, trend, 'r--', linewidth=1.5, label='趋势线')
            
            # 添加标题和标签
            ax.set_title(f'体重趋势图（最近{chart_days}天）', fontsize=14, fontweight='bold')
            ax.set_xlabel('日期', fontsize=12)
            ax.set_ylabel('体重 (kg)', fontsize=12)
            
            # 设置网格
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # 自动调整刻度标签
            self.weight_chart_figure.autofmt_xdate()
            
            # 添加图例
            ax.legend()
            
        else:
            # 没有数据
            ax.text(0.5, 0.5, '暂无体重记录数据', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
        
        # 调整布局
        self.weight_chart_figure.tight_layout()
        
        # 刷新画布
        if self.weight_chart_canvas:
            self.weight_chart_canvas.draw()
    
    def _update_nutrition_chart(self) -> None:
        """更新营养比例图。"""
        if not self.nutrition_chart_figure:
            return
        
        # 清空图表
        self.nutrition_chart_figure.clear()
        
        # 创建子图
        ax = self.nutrition_chart_figure.add_subplot(111)
        
        # 检查是否有营养数据
        nutrition = self.dashboard_data.get("nutrition")
        
        if nutrition:
            # 营养比例数据
            labels = ['蛋白质', '碳水化合物', '脂肪']
            
            # 计算克数比例
            protein_g = nutrition.protein_g
            carbs_g = nutrition.carbohydrates_g
            fat_g = nutrition.fat_g
            total_g = protein_g + carbs_g + fat_g
            
            if total_g > 0:
                sizes = [protein_g, carbs_g, fat_g]
                colors = ['#FF6384', '#36A2EB', '#FFCE56']
                
                # 绘制饼图
                wedges, texts, autotexts = ax.pie(
                    sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                    startangle=90, shadow=False
                )
                
                # 设置标题
                ax.set_title('营养比例', fontsize=14, fontweight='bold')
                
                # 添加图例
                ax.legend(wedges, labels, title="营养素", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
                
                # 设置纵横比使饼图为圆形
                ax.axis('equal')
            else:
                # 没有营养数据
                ax.text(0.5, 0.5, '暂无营养数据', 
                       horizontalalignment='center', verticalalignment='center',
                       transform=ax.transAxes, fontsize=14)
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.axis('off')
        else:
            # 没有营养数据
            ax.text(0.5, 0.5, '暂无营养数据', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
        
        # 调整布局
        self.nutrition_chart_figure.tight_layout()
        
        # 刷新画布
        if self.nutrition_chart_canvas:
            self.nutrition_chart_canvas.draw()
    
    def _update_suggestions(self) -> None:
        """更新调整建议。"""
        if not self.selected_user:
            return
        
        try:
            # 获取调整建议
            recommendation = self.dashboard_controller.get_weekly_adjustment_recommendation(
                user_id=self.selected_user.id,
                parent_widget=self
            )
            
            if recommendation:
                adjustment_units = recommendation.get("adjustment_units", 0)
                recommendation_text = recommendation.get("recommendation", "")
                
                if adjustment_units > 0:
                    suggestion = f"💡 建议增加 {adjustment_units} 单位碳水化合物摄入（+{adjustment_units * 30}g）\n\n{recommendation_text}"
                elif adjustment_units < 0:
                    suggestion = f"💡 建议减少 {abs(adjustment_units)} 单位碳水化合物摄入（{adjustment_units * 30}g）\n\n{recommendation_text}"
                else:
                    suggestion = f"✅ 无需调整，保持当前计划\n\n{recommendation_text}"
                
                self.suggestion_text.setText(suggestion)
            else:
                self.suggestion_text.setText("暂无调整建议")
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
            self.suggestion_text.setText("获取调整建议时出错")
    
    def _update_activities(self) -> None:
        """更新最近活动。"""
        if not self.selected_user:
            return
        
        try:
            # 获取最近活动
            activities = self.dashboard_controller.get_recent_activities(
                user_id=self.selected_user.id,
                limit=5
            )
            
            if activities:
                activity_text = ""
                for i, activity in enumerate(activities, 1):
                    date_str = activity["date"].strftime("%m-%d")
                    description = activity["description"]
                    activity_text += f"{i}. [{date_str}] {description}\n"
                
                self.activity_text.setText(activity_text)
            else:
                self.activity_text.setText("暂无活动记录")
                
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
            self.activity_text.setText("获取活动记录时出错")
    
    def _on_user_selected(self, index: int) -> None:
        """处理用户选择变化。
        
        Args:
            index: 当前选中索引
        """
        user_id = self.user_combo.itemData(index)
        
        if user_id is None:
            self.selected_user = None
            self._clear_dashboard()
            return
        
        # 获取用户信息
        user = self.dashboard_controller.get_user_by_id(user_id)
        if user:
            self.selected_user = user
            self.user_selected.emit(user)
            
            # 加载仪表盘数据
            self._load_dashboard_data()
    
    def _on_chart_days_changed(self) -> None:
        """处理图表天数变化。"""
        if self.selected_user and self.dashboard_data:
            self._update_weight_chart()
    
    def _clear_dashboard(self) -> None:
        """清空仪表盘显示。"""
        # 清空用户信息
        self.user_name_label.setText("请选择一个用户")
        self.user_details_label.setText("")
        self.health_score_label.setText("--")
        self.health_score_label.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #4CAF50;
        """)
        
        # 清空指标卡片
        for card in self.metric_cards:
            value_label = card.findChild(QLabel, "metric_*")
            if value_label:
                value_label.setText("--")
        
        # 清空图表
        if MATPLOTLIB_AVAILABLE:
            if self.weight_chart_figure:
                self.weight_chart_figure.clear()
                self.weight_chart_canvas.draw()
            
            if self.nutrition_chart_figure:
                self.nutrition_chart_figure.clear()
                self.nutrition_chart_canvas.draw()
        
        # 清空建议和活动
        self.suggestion_text.setText("选择用户后显示调整建议...")
        self.activity_text.setText("暂无活动记录")
    
    def _get_metric_unit(self, metric_key: str) -> str:
        """获取指标的单位。
        
        Args:
            metric_key: 指标键名
            
        Returns:
            单位字符串
        """
        units = {
            "current_weight": "kg",
            "target_weight": "kg",
            "progress_percentage": "%",
            "tdee": "kcal",
            "weight_change_30d": "kg",
            "weight_records_count": "条"
        }
        
        return units.get(metric_key, "")
    
    def refresh(self) -> None:
        """刷新标签页内容。"""
        self._load_users()
        if self.selected_user:
            self._load_dashboard_data()
    
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