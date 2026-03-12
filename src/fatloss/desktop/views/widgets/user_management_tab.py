"""用户管理标签页。

提供用户档案的列表、创建、编辑和删除功能。
"""

from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableView,
    QPushButton,
    QLabel,
    QMessageBox,
    QInputDialog,
    QLineEdit,
    QToolBar,
    QAction,
    QApplication,
    QHeaderView,
)

from fatloss.models.user_profile import UserProfile
from fatloss.desktop.controllers.user_controller import UserController
from fatloss.desktop.models.user_table_model import UserTableModel
from fatloss.desktop.views.dialogs.user_dialog import UserDialog
from fatloss.desktop.utils.error_handler import ErrorHandler


class UserManagementTab(QWidget):
    """用户管理标签页，提供完整的用户档案管理功能。"""
    
    # 信号定义
    user_selected = pyqtSignal(UserProfile)  # 用户被选中
    user_created = pyqtSignal(UserProfile)   # 用户被创建
    user_updated = pyqtSignal(UserProfile)   # 用户被更新
    user_deleted = pyqtSignal(int)           # 用户被删除（传递用户ID）
    
    # 常量定义
    TABLE_MIN_HEIGHT = 300
    BUTTON_HEIGHT = 30
    BUTTON_SPACING = 5
    
    def __init__(self, user_controller: UserController, parent=None):
        """初始化用户管理标签页。
        
        Args:
            user_controller: 用户控制器实例
            parent: 父窗口部件
        """
        super().__init__(parent)
        
        self.user_controller = user_controller
        self.table_model = None
        self.current_selection = None
        
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
        
        # 用户列表表格
        self._create_user_table()
        main_layout.addWidget(self.user_table, 1)  # 1表示拉伸因子
        
        # 底部状态栏
        status_bar = self._create_status_bar()
        main_layout.addWidget(status_bar)
        
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
        
        # 新建用户按钮
        new_user_action = QAction("新建用户", self)
        new_user_action.setToolTip("创建新用户档案")
        new_user_action.triggered.connect(self._on_new_user)
        toolbar.addAction(new_user_action)
        
        toolbar.addSeparator()
        
        # 编辑用户按钮
        edit_user_action = QAction("编辑用户", self)
        edit_user_action.setToolTip("编辑选中的用户档案")
        edit_user_action.triggered.connect(self._on_edit_user)
        toolbar.addAction(edit_user_action)
        
        # 删除用户按钮
        delete_user_action = QAction("删除用户", self)
        delete_user_action.setToolTip("删除选中的用户档案")
        delete_user_action.triggered.connect(self._on_delete_user)
        toolbar.addAction(delete_user_action)
        
        toolbar.addSeparator()
        
        # 刷新按钮
        refresh_action = QAction("刷新", self)
        refresh_action.setToolTip("刷新用户列表")
        refresh_action.triggered.connect(self._load_users)
        toolbar.addAction(refresh_action)
        
        # 搜索框
        toolbar.addWidget(QLabel("搜索:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入姓名搜索...")
        self.search_edit.setMaximumWidth(200)
        self.search_edit.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self.search_edit)
        
        return toolbar
    
    def _create_user_table(self) -> None:
        """创建用户表格。"""
        self.user_table = QTableView()
        self.user_table.setMinimumHeight(self.TABLE_MIN_HEIGHT)
        
        # 设置选择行为
        self.user_table.setSelectionBehavior(QTableView.SelectRows)
        self.user_table.setSelectionMode(QTableView.SingleSelection)
        
        # 设置列宽调整策略
        self.user_table.horizontalHeader().setStretchLastSection(True)
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # 连接选择变化信号
        selection_model = self.user_table.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self._on_selection_changed)
    
    def _create_status_bar(self) -> QWidget:
        """创建状态栏。
        
        Returns:
            状态栏部件
        """
        status_widget = QWidget()
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 5, 0, 5)
        
        self.status_label = QLabel("就绪")
        self.user_count_label = QLabel("用户总数: 0")
        
        status_layout.addWidget(self.status_label, 1)
        status_layout.addWidget(self.user_count_label)
        
        status_widget.setLayout(status_layout)
        return status_widget
    
    def _load_users(self, search_query: Optional[str] = None) -> None:
        """加载用户列表。
        
        Args:
            search_query: 搜索查询字符串
        """
        try:
            # 获取用户列表
            if search_query and search_query.strip():
                users = self.user_controller.search_users(name_query=search_query.strip())
            else:
                users = self.user_controller.get_all_users()
            
            # 创建或更新表格模型
            if self.table_model is None:
                self.table_model = UserTableModel(users)
                self.user_table.setModel(self.table_model)
            else:
                self.table_model.set_users(users)
            
            # 更新状态
            self._update_status(len(users))
            
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)
    
    def _update_status(self, user_count: int) -> None:
        """更新状态栏。
        
        Args:
            user_count: 用户数量
        """
        self.user_count_label.setText(f"用户总数: {user_count}")
        
        if user_count == 0:
            self.status_label.setText("没有用户记录")
        else:
            self.status_label.setText(f"加载了 {user_count} 个用户")
    
    def _on_selection_changed(self) -> None:
        """处理表格选择变化。"""
        selected_rows = self.user_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            user = self.table_model.get_user_at(row)
            if user:
                self.current_selection = user
                self.user_selected.emit(user)
    
    def _on_new_user(self) -> None:
        """处理新建用户操作。"""
        user = UserDialog.create_user(self)
        if user:
            # 调用控制器创建用户
            created_user = self.user_controller.create_user(
                name=user.name,
                gender=user.gender,
                birth_date=user.birth_date,
                height_cm=user.height_cm,
                initial_weight_kg=user.initial_weight_kg,
                activity_level=user.activity_level,
                parent_widget=self
            )
            
            if created_user:
                # 刷新列表
                self._load_users()
                self.user_created.emit(created_user)
    
    def _on_edit_user(self) -> None:
        """处理编辑用户操作。"""
        if not self.current_selection:
            ErrorHandler.show_warning("请先选择一个用户", self)
            return
        
        user = UserDialog.edit_user(self.current_selection, self)
        if user:
            # 调用控制器更新用户
            updated_user = self.user_controller.update_user(
                user_id=user.id,
                name=user.name,
                gender=user.gender,
                birth_date=user.birth_date,
                height_cm=user.height_cm,
                initial_weight_kg=user.initial_weight_kg,
                activity_level=user.activity_level,
                parent_widget=self
            )
            
            if updated_user:
                # 刷新列表
                self._load_users()
                self.user_updated.emit(updated_user)
    
    def _on_delete_user(self) -> None:
        """处理删除用户操作。"""
        if not self.current_selection:
            ErrorHandler.show_warning("请先选择一个用户", self)
            return
        
        # 确认对话框
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除用户 '{self.current_selection.name}' 吗？\n\n此操作不可撤销，将删除该用户的所有相关数据。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.user_controller.delete_user(
                user_id=self.current_selection.id,
                parent_widget=self
            )
            
            if success:
                # 刷新列表
                self._load_users()
                self.user_deleted.emit(self.current_selection.id)
                self.current_selection = None
    
    def _on_search_changed(self, text: str) -> None:
        """处理搜索文本变化。
        
        Args:
            text: 搜索文本
        """
        self._load_users(text)
    
    def refresh(self) -> None:
        """刷新用户列表。"""
        self._load_users()
    
    def get_selected_user(self) -> Optional[UserProfile]:
        """获取当前选中的用户。
        
        Returns:
            选中的用户对象，如果没有选中则为None
        """
        return self.current_selection
    
    def show_user_details(self, user_id: int) -> bool:
        """显示指定用户的详细信息。
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否成功显示
        """
        user = self.user_controller.get_user_by_id(user_id)
        if user:
            # 在表格中选中该用户
            if self.table_model:
                for row in range(self.table_model.rowCount()):
                    model_user = self.table_model.get_user_at(row)
                    if model_user and model_user.id == user_id:
                        index = self.table_model.index(row, 0)
                        self.user_table.selectRow(row)
                        self.user_table.scrollTo(index)
                        return True
        return False