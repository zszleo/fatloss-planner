"""体重记录Repository实现。

体重记录数据访问层。
"""

from datetime import date
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from fatloss.models.weight_record import WeightRecord
from fatloss.repository.mapper import (
    weight_record_from_model,
    weight_record_to_model,
)
from fatloss.repository.models import WeightRecordModel
from fatloss.repository.sqlalchemy_repository import SQLAlchemyDateRangeRepository


class WeightRepository(
    SQLAlchemyDateRangeRepository[WeightRecord, WeightRecordModel, int]
):
    """体重记录Repository"""

    def __init__(self, session: Session):
        """初始化体重Repository。

        Args:
            session: SQLAlchemy会话
        """
        super().__init__(session, WeightRecordModel, date_column="record_date")

    def _to_model(self, entity: WeightRecord) -> WeightRecordModel:
        """将WeightRecord转换为WeightRecordModel"""
        return weight_record_to_model(entity)

    def _to_pydantic(self, model: WeightRecordModel) -> WeightRecord:
        """将WeightRecordModel转换为WeightRecord"""
        return weight_record_from_model(model)

    def find_by_user_id(self, user_id: int) -> list[WeightRecord]:
        """根据用户ID查找体重记录。

        Args:
            user_id: 用户ID

        Returns:
            体重记录列表（按日期倒序）
        """
        models = (
            self.session.query(WeightRecordModel)
            .filter(WeightRecordModel.user_id == user_id)
            .order_by(desc(WeightRecordModel.record_date))
            .all()
        )
        return [self._to_pydantic(model) for model in models]

    def find_latest_by_user_id(self, user_id: int) -> Optional[WeightRecord]:
        """查找用户最新的体重记录。

        Args:
            user_id: 用户ID

        Returns:
            最新的体重记录，如果不存在则返回None
        """
        model = (
            self.session.query(WeightRecordModel)
            .filter(WeightRecordModel.user_id == user_id)
            .order_by(desc(WeightRecordModel.record_date))
            .first()
        )

        if model is None:
            return None
        return self._to_pydantic(model)

    def find_previous_by_user_id(
        self, user_id: int, current_date: date
    ) -> Optional[WeightRecord]:
        """查找用户指定日期之前的最近一次体重记录。

        Args:
            user_id: 用户ID
            current_date: 当前日期

        Returns:
            前一次体重记录，如果不存在则返回None
        """
        model = (
            self.session.query(WeightRecordModel)
            .filter(
                WeightRecordModel.user_id == user_id,
                WeightRecordModel.record_date < current_date,
            )
            .order_by(desc(WeightRecordModel.record_date))
            .first()
        )

        if model is None:
            return None
        return self._to_pydantic(model)

    def calculate_weight_change(
        self, user_id: int, start_date: date, end_date: date
    ) -> Optional[float]:
        """计算用户在指定时间段内的体重变化。

        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            体重变化（千克），正值表示增重，负值表示减重
            如果缺少数据则返回None
        """
        start_record = (
            self.session.query(WeightRecordModel)
            .filter(
                WeightRecordModel.user_id == user_id,
                WeightRecordModel.record_date >= start_date,
            )
            .order_by(WeightRecordModel.record_date)
            .first()
        )

        end_record = (
            self.session.query(WeightRecordModel)
            .filter(
                WeightRecordModel.user_id == user_id,
                WeightRecordModel.record_date <= end_date,
            )
            .order_by(desc(WeightRecordModel.record_date))
            .first()
        )

        if start_record is None or end_record is None:
            return None

        return end_record.weight_kg - start_record.weight_kg

    def calculate_average_weight(
        self, user_id: int, start_date: date, end_date: date
    ) -> Optional[float]:
        """计算用户在指定时间段内的平均体重。

        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            平均体重（千克），如果无数据则返回None
        """
        records = self.find_by_date_range(
            start_date=start_date, end_date=end_date, user_id=user_id
        )

        if not records:
            return None

        total = sum(record.weight_kg for record in records)
        return total / len(records)
