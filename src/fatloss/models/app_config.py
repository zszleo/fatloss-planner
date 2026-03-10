"""应用程序配置模型"""

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class UnitSystem(str, Enum):
    """单位制"""

    METRIC = "metric"  # 公制（千克，厘米）
    IMPERIAL = "imperial"  # 英制（磅，英尺）


class Theme(str, Enum):
    """主题"""

    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class AppConfig(BaseModel):
    """应用程序配置"""

    id: int | None = Field(default=None, description="配置ID")
    user_id: int = Field(..., gt=0, description="用户ID")
    unit_system: UnitSystem = Field(default=UnitSystem.METRIC, description="单位制")
    theme: Theme = Field(default=Theme.AUTO, description="主题")
    language: str = Field(
        default="zh-CN", min_length=2, max_length=10, description="语言"
    )
    weekly_check_day: int = Field(
        default=1, ge=0, le=6, description="周检查日（0=周日，1=周一，...）"
    )
    carb_adjustment_unit_g: int = Field(
        default=30, gt=0, le=100, description="碳水化合物调整单位（克）"
    )
    monthly_loss_percentage: float = Field(
        default=0.05, gt=0, le=0.1, description="每月减脂百分比"
    )
    exercise_calories_per_minute: float = Field(
        default=10, gt=0, le=20, description="每分钟训练消耗热量"
    )
    enable_notifications: bool = Field(default=True, description="启用通知")
    data_retention_days: int = Field(default=365, gt=0, description="数据保留天数")
    created_at: date = Field(default_factory=date.today, description="创建日期")
    updated_at: date = Field(default_factory=date.today, description="更新日期")

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={date: lambda d: d.isoformat()}
    )
