"""体重记录数据模型"""

from datetime import date

from pydantic import BaseModel, Field, field_validator, ConfigDict, field_serializer


class WeightRecord(BaseModel):
    """体重记录"""

    id: int | None = Field(default=None, description="记录ID")
    user_id: int = Field(..., gt=0, description="用户ID")
    weight_kg: float = Field(..., gt=0, le=300, description="体重（千克）")
    record_date: date = Field(..., description="记录日期")
    notes: str = Field(default="", max_length=500, description="备注")
    created_at: date = Field(default_factory=date.today, description="创建日期")

    @field_serializer('record_date', 'created_at')
    def serialize_date(self, value: date, _info):
        """序列化日期字段为ISO格式"""
        return value.isoformat() if value else None

    model_config = ConfigDict()

    @field_validator("weight_kg", mode="before")
    def validate_weight(cls, v):
        """验证体重"""
        if not (30 <= v <= 200):
            raise ValueError("体重必须在30-200千克之间")
        return round(v, 2)

    @field_validator("record_date", mode="before")
    def validate_record_date(cls, v):
        """验证记录日期"""
        if v > date.today():
            raise ValueError("记录日期不能是未来日期")
        return v
