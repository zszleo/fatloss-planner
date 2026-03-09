"""Repository抽象层接口定义。

定义通用的Repository模式接口，提供数据访问的抽象层。
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Generic, List, Optional, TypeVar

T = TypeVar("T")
ID = TypeVar("ID")


class BaseRepository(Generic[T, ID], ABC):
    """Repository基类接口。

    Args:
        T: 实体类型
        ID: 实体ID类型
    """

    @abstractmethod
    def get_by_id(self, id: ID) -> Optional[T]:
        """根据ID获取实体。

        Args:
            id: 实体ID

        Returns:
            实体对象，如果不存在则返回None
        """
        pass

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """获取所有实体。

        Args:
            skip: 跳过的记录数（用于分页）
            limit: 返回的最大记录数

        Returns:
            实体列表
        """
        pass

    @abstractmethod
    def create(self, entity: T) -> T:
        """创建新实体。

        Args:
            entity: 要创建的实体

        Returns:
            创建后的实体（包含生成的ID等）
        """
        pass

    @abstractmethod
    def update(self, id: ID, entity: T) -> Optional[T]:
        """更新实体。

        Args:
            id: 实体ID
            entity: 包含更新数据的实体

        Returns:
            更新后的实体，如果不存在则返回None
        """
        pass

    @abstractmethod
    def delete(self, id: ID) -> bool:
        """删除实体。

        Args:
            id: 实体ID

        Returns:
            是否成功删除
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """统计实体总数。

        Returns:
            实体总数
        """
        pass


class FilterableRepository(BaseRepository[T, ID], ABC):
    """支持过滤查询的Repository接口。"""

    @abstractmethod
    def find_by_filter(self, **filters: Any) -> List[T]:
        """根据过滤条件查找实体。

        Args:
            **filters: 过滤条件

        Returns:
            匹配过滤条件的实体列表
        """
        pass

    @abstractmethod
    def find_one_by_filter(self, **filters: Any) -> Optional[T]:
        """根据过滤条件查找单个实体。

        Args:
            **filters: 过滤条件

        Returns:
            匹配过滤条件的实体，如果不存在则返回None
        """
        pass


class DateRangeRepository(FilterableRepository[T, ID], ABC):
    """支持日期范围查询的Repository接口。"""

    @abstractmethod
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
        pass

    @abstractmethod
    def find_latest_by_date(self, **filters: Any) -> Optional[T]:
        """查找指定条件下的最新实体（按日期）。

        Args:
            **filters: 过滤条件

        Returns:
            最新的实体，如果不存在则返回None
        """
        pass
