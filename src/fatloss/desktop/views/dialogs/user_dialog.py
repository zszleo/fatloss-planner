"""用户对话框模块。

提供新建/编辑用户档案的对话框。
"""

from datetime import date, datetime
from typing import Optional

from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QDialogButtonBox,
    QMessageBox,
    QLabel,
    QHBoxLayout,
    QWidget,
)

from fatloss.models.user_profile import UserProfile
from fatloss.models.enums import Gender, ActivityLevel
from fatloss.desktop.utils.error_handler import ErrorHandler


class UserDialog(QDialog):
    """用户对话框，用于新建或编辑用户档案。"""

    # 常量定义
    MIN_HEIGHT_CM = 100.0
    MAX_HEIGHT_CM = 250.0
    MIN_WEIGHT_KG = 30.0
    MAX_WEIGHT_KG = 200.0
    MAX_NAME_LENGTH = 100
    MIN_BIRTH_YEAR = 1900
    DEFAULT_AGE_YEARS = 30
    DEFAULT_HEIGHT_CM = 170.0
    DEFAULT_WEIGHT_KG = 70.0
    MIN_DIALOG_WIDTH = 400
    HEIGHT_STEP = 0.5
    WEIGHT_STEP = 0.1

    def __init__(
        self, user: Optional[UserProfile] = None, parent=None, mode: str = "create"
    ):
        """初始化用户对话框。

        Args:
            user: 要编辑的用户对象，新建时为None
            parent: 父窗口部件
            mode: 模式，"create"为新建，"edit"为编辑
        """
        super().__init__(parent)

        self.user = user
        self.mode = mode
        self.result_user = None

        self.setWindowTitle("新建用户档案" if mode == "create" else "编辑用户档案")
        self.setMinimumWidth(self.MIN_DIALOG_WIDTH)

        self._init_ui()
        self._populate_fields()

    def _init_ui(self) -> None:
        """初始化用户界面。"""
        layout = QVBoxLayout()

        # 表单布局
        form_layout = QFormLayout()

        # 姓名输入
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入用户姓名")
        self.name_edit.setMaxLength(self.MAX_NAME_LENGTH)
        form_layout.addRow("姓名*:", self.name_edit)

        # 性别选择
        self.gender_combo = QComboBox()
        self.gender_combo.addItems([g.value for g in Gender])
        form_layout.addRow("性别*:", self.gender_combo)

        # 出生日期
        self.birth_date_edit = QDateEdit()
        self.birth_date_edit.setCalendarPopup(True)
        self.birth_date_edit.setDateRange(
            QDate(self.MIN_BIRTH_YEAR, 1, 1), QDate.currentDate()
        )
        self.birth_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.birth_date_edit.setDate(
            QDate.currentDate().addYears(-self.DEFAULT_AGE_YEARS)
        )  # 默认30岁
        form_layout.addRow("出生日期*:", self.birth_date_edit)

        # 身高输入
        height_layout = QHBoxLayout()
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(self.MIN_HEIGHT_CM, self.MAX_HEIGHT_CM)
        self.height_spin.setValue(self.DEFAULT_HEIGHT_CM)
        self.height_spin.setSuffix(" cm")
        self.height_spin.setDecimals(1)
        self.height_spin.setSingleStep(self.HEIGHT_STEP)
        height_layout.addWidget(self.height_spin)
        height_layout.addStretch()
        form_layout.addRow("身高*:", height_layout)

        # 体重输入
        weight_layout = QHBoxLayout()
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(self.MIN_WEIGHT_KG, self.MAX_WEIGHT_KG)
        self.weight_spin.setValue(self.DEFAULT_WEIGHT_KG)
        self.weight_spin.setSuffix(" kg")
        self.weight_spin.setDecimals(1)
        self.weight_spin.setSingleStep(self.WEIGHT_STEP)
        weight_layout.addWidget(self.weight_spin)
        weight_layout.addStretch()
        form_layout.addRow("体重*:", weight_layout)

        # 活动水平选择
        self.activity_combo = QComboBox()
        self.activity_combo.addItems([a.value for a in ActivityLevel])
        self.activity_combo.setCurrentText(ActivityLevel.MODERATE.value)
        form_layout.addRow("活动水平:", self.activity_combo)

        layout.addLayout(form_layout)

        # 分隔线
        layout.addWidget(QLabel(""))

        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def _populate_fields(self) -> None:
        """填充字段数据（编辑模式）。"""
        if self.user is not None:
            self.name_edit.setText(self.user.name)

            # 设置性别
            gender = self.user.gender
            gender_value = gender.value if hasattr(gender, 'value') else gender
            gender_index = self.gender_combo.findText(gender_value)
            if gender_index >= 0:
                self.gender_combo.setCurrentIndex(gender_index)

            # 设置出生日期
            birth_date = self.user.birth_date
            qdate = QDate(birth_date.year, birth_date.month, birth_date.day)
            self.birth_date_edit.setDate(qdate)

            # 设置身高体重
            self.height_spin.setValue(self.user.height_cm)
            self.weight_spin.setValue(self.user.initial_weight_kg)

            # 设置活动水平
            activity = self.user.activity_level
            activity_value = activity.value if hasattr(activity, 'value') else activity
            activity_index = self.activity_combo.findText(activity_value)
            if activity_index >= 0:
                self.activity_combo.setCurrentIndex(activity_index)

    def _validate_and_accept(self) -> None:
        """验证输入并接受对话框。"""
        try:
            # 收集表单数据
            name = self.name_edit.text().strip()
            if not name:
                raise ValueError("姓名不能为空")

            gender = Gender(self.gender_combo.currentText())

            birth_date_qdate = self.birth_date_edit.date()
            birth_date = date(
                birth_date_qdate.year(),
                birth_date_qdate.month(),
                birth_date_qdate.day(),
            )

            height_cm = self.height_spin.value()
            initial_weight_kg = self.weight_spin.value()
            activity_level = ActivityLevel(self.activity_combo.currentText())

            # 创建或更新用户对象
            if self.mode == "create" or self.user is None:
                user_data = {
                    "name": name,
                    "gender": gender,
                    "birth_date": birth_date,
                    "height_cm": height_cm,
                    "initial_weight_kg": initial_weight_kg,
                    "activity_level": activity_level,
                }
                self.result_user = UserProfile(**user_data)
            else:
                # 编辑模式，保留原始ID和时间戳
                user_data = {
                    "id": self.user.id,
                    "name": name,
                    "gender": gender,
                    "birth_date": birth_date,
                    "height_cm": height_cm,
                    "initial_weight_kg": initial_weight_kg,
                    "activity_level": activity_level,
                    "created_at": self.user.created_at,
                    "updated_at": date.today(),
                }
                self.result_user = UserProfile(**user_data)

            # 验证通过，接受对话框
            self.accept()

        except ValueError as e:
            ErrorHandler.show_warning(str(e), self)
        except Exception as e:
            ErrorHandler.handle_service_error(e, self)

    def get_user(self) -> Optional[UserProfile]:
        """获取对话框创建的用户对象。

        Returns:
            用户对象，如果对话框被取消则为None
        """
        return self.result_user

    @staticmethod
    def create_user(parent=None) -> Optional[UserProfile]:
        """静态方法：创建新用户。

        Args:
            parent: 父窗口部件

        Returns:
            创建的用户对象，如果取消则为None
        """
        dialog = UserDialog(parent=parent, mode="create")
        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_user()
        return None

    @staticmethod
    def edit_user(user: UserProfile, parent=None) -> Optional[UserProfile]:
        """静态方法：编辑现有用户。

        Args:
            user: 要编辑的用户对象
            parent: 父窗口部件

        Returns:
            更新后的用户对象，如果取消则为None
        """
        dialog = UserDialog(user=user, parent=parent, mode="edit")
        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_user()
        return None
