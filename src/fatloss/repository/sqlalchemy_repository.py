"""SQLAlchemy Repository实现。

基于SQLAlchemy的通用Repository实现。
"""

from datetime import date
from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

from fatloss.repository.abstract_repository import (
    BaseRepository,
    DateRangeRepository,
    FilterableRepository,
)
from fatloss.repository.database import Base

T = TypeVar("T")  # Pydantic模型类型
M = TypeVar("M", bound=Base)  # SQLAlchemy模型类型
ID = TypeVar("ID")  # ID类型


class SQLAlchemyRepository(BaseRepository[T, ID], Generic[T, M, ID]):
    """基于SQLAlchemy的Repository基类。

    Args:
        T: Pydantic模型类型
        M: SQLAlchemy模型类型
        ID: ID类型
    """

    def __init__(self, session: Session, model_class: Type[M]):
        """初始化Repository。

        Args:
            session: SQLAlchemy会话
            model_class: SQLAlchemy模型类
        """
        self.session = session
        self.model_class = model_class

    def get_by_id(self, id: ID) -> Optional[T]:
        """根据ID获取实体。

        Args:
            id: 实体ID

        Returns:
            实体对象，如果不存在则返回None
        """
        model = self.session.get(self.model_class, id)
        if model is None:
            return None
        return self._to_pydantic(model)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """获取所有实体。

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            实体列表
        """
        query = (
            self.session.query(self.model_class)
            .order_by(self.model_class.id)
            .offset(skip)
            .limit(limit)
        )
        results = []
        for model in query.yield_per(50):  # 分批处理，每批50条记录
            results.append(self._to_pydantic(model))
        return results

    def create(self, entity: T) -> T:
        """创建新实体。

        Args:
            entity: 要创建的实体

        Returns:
            创建后的实体（包含生成的ID等）
        """
        model = self._to_model(entity)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_pydantic(model)

    def update(self, id: ID, entity: T) -> Optional[T]:
        """更新实体。

        Args:
            id: 实体ID
            entity: 包含更新数据的实体

        Returns:
            更新后的实体，如果不存在则返回None
        """
        model = self.session.get(self.model_class, id)
        if model is None:
            return None

        # 更新模型属性
        updated_model = self._to_model(entity)
        for column in self.model_class.__table__.columns:
            if column.name != "id":  # 不更新ID
                setattr(model, column.name, getattr(updated_model, column.name))

        self.session.commit()
        self.session.refresh(model)
        return self._to_pydantic(model)

    def delete(self, id: ID) -> bool:
        """删除实体。

        Args:
            id: 实体ID

        Returns:
            是否成功删除
        """
        model = self.session.get(self.model_class, id)
        if model is None:
            return False

        self.session.delete(model)
        self.session.commit()
        return True

    def count(self) -> int:
        """统计实体总数。

        Returns:
            实体总数
        """
        return self.session.query(self.model_class).count()

    def _to_model(self, entity: T) -> M:
        """将Pydantic实体转换为SQLAlchemy模型。

        子类必须实现此方法。

        Args:
            entity: Pydantic实体

        Returns:
            SQLAlchemy模型
        """
        raise NotImplementedError("子类必须实现此方法")

    def _to_pydantic(self, model: M) -> T:
        """将SQLAlchemy模型转换为Pydantic实体。

        子类必须实现此方法。

        Args:
            model: SQLAlchemy模型

        Returns:
            Pydantic实体
        """
        raise NotImplementedError("子类必须实现此方法")


class SQLAlchemyFilterableRepository(
    SQLAlchemyRepository[T, M, ID], FilterableRepository[T, ID]
):
    """支持过滤查询的SQLAlchemy Repository。"""

    def find_by_filter(self, **filters: Any) -> List[T]:
        """根据过滤条件查找实体。

        Args:
            **filters: 过滤条件

        Returns:
            匹配过滤条件的实体列表
        """
        query = self.session.query(self.model_class)

        for key, value in filters.items():
            if hasattr(self.model_class, key):
                if isinstance(value, list):
                    # 处理IN查询
                    column = getattr(self.model_class, key)
                    query = query.filter(column.in_(value))
                else:
                    # 处理等值查询
                    query = query.filter(getattr(self.model_class, key) == value)

        models = query.all()
        return [self._to_pydantic(model) for model in models]

    def find_one_by_filter(self, **filters: Any) -> Optional[T]:
        """根据过滤条件查找单个实体。

        Args:
            **filters: 过滤条件

        Returns:
            匹配过滤条件的实体，如果不存在则返回None
        """
        query = self.session.query(self.model_class)

        for key, value in filters.items():
            if hasattr(self.model_class, key):
                query = query.filter(getattr(self.model_class, key) == value)

        model = query.first()
        if model is None:
            return None
        return self._to_pydantic(model)


class SQLAlchemyDateRangeRepository(
    SQLAlchemyFilterableRepository[T, M, ID], DateRangeRepository[T, ID]
):
    """支持日期范围查询的SQLAlchemy Repository。"""

    def __init__(
        self, session: Session, model_class: Type[M], date_column: str = "date"
    ):
        """初始化日期范围Repository。

        Args:
            session: SQLAlchemy会话
            model_class: SQLAlchemy模型类
            date_column: 日期列名
        """
        super().__init__(session, model_class)
        self.date_column = date_column

    def find_by_date_range(
        self, start_date: date, end_date: date, **additional_filters: Any
    ) -> List[T]:
        """查找指定日期范围内的实体。

        Args:
            start_date: 开始日期（包含）
            end_date: 结束日期（包含）
            **additional_filters: 附加过滤条件

        Returns:
            匹配条件的实体列表
        """
        query = self.session.query(self.model_class)

        # 添加日期范围过滤
        date_column = getattr(self.model_class, self.date_column)
        query = query.filter(date_column >= start_date, date_column <= end_date)

        # 添加附加过滤条件
        for key, value in additional_filters.items():
            if hasattr(self.model_class, key):
                query = query.filter(getattr(self.model_class, key) == value)

        # 按日期排序
        query = query.order_by(date_column)

        models = query.all()
        return [self._to_pydantic(model) for model in models]

    def find_latest_by_date(self, **filters: Any) -> Optional[T]:
        """查找指定条件下的最新实体（按日期）。

        Args:
            **filters: 过滤条件

        Returns:
            最新的实体，如果不存在则返回None
        """
        query = self.session.query(self.model_class)

        # 添加过滤条件
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                query = query.filter(getattr(self.model_class, key) == value)

        # 按日期降序排序，获取最新的
        date_column = getattr(self.model_class, self.date_column)
        query = query.order_by(desc(date_column))

        model = query.first()
        if model is None:
            return None
        return self._to_pydantic(model)
