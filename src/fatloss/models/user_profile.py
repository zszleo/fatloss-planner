"""用户档案数据模型"""

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, field_validator, ConfigDict


class Gender(str, Enum):
    """性别"""

    MALE = "male"
    FEMALE = "female"


class ActivityLevel(str, Enum):
    """活动水平"""

    SEDENTARY = "sedentary"  # 久坐
    LIGHT = "light"  # 轻度活动
    MODERATE = "moderate"  # 中度活动
    ACTIVE = "active"  # 活跃
    VERY_ACTIVE = "very_active"  # 非常活跃


class UserProfile(BaseModel):
    """用户档案"""

    id: int | None = Field(default=None, description="用户ID")
    name: str = Field(..., min_length=1, max_length=100, description="用户姓名")
    gender: Gender = Field(..., description="性别")
    birth_date: date = Field(..., description="出生日期")
    height_cm: float = Field(..., gt=0, le=300, description="身高（厘米）")
    initial_weight_kg: float = Field(..., gt=0, le=300, description="初始体重（千克）")
    activity_level: ActivityLevel = Field(
        default=ActivityLevel.MODERATE, description="活动水平"
    )
    created_at: date = Field(default_factory=date.today, description="创建日期")
    updated_at: date = Field(default_factory=date.today, description="更新日期")
    model_config = ConfigDict(
        use_enum_values=True, json_encoders={date: lambda d: d.isoformat()}
    )

    @field_validator("height_cm", mode="before")
    def validate_height(cls, v):
        """验证身高"""
        if not (100 <= v <= 250):
            raise ValueError("身高必须在100-250厘米之间")
        return v

    @field_validator("initial_weight_kg", mode="before")
    def validate_weight(cls, v):
        """验证体重"""
        if not (30 <= v <= 200):
            raise ValueError("体重必须在30-200千克之间")
        return v

    @property
    def age(self) -> int:
        """计算年龄（岁）"""
        today = date.today()
        age = today.year - self.birth_date.year
        # 调整生日是否已过
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            age -= 1
        return age
