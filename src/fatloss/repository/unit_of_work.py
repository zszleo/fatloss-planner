"""工作单元模式实现。

协调多个Repository和事务管理。
"""

from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy.orm import Session

from fatloss.repository.app_config_repository import AppConfigRepository
from fatloss.repository.database import create_engine_from_url, get_session
from fatloss.repository.nutrition_repository import (
    DailyNutritionRepository,
    WeeklyNutritionRepository,
)
from fatloss.repository.user_repository import UserRepository
from fatloss.repository.weight_repository import WeightRepository


class UnitOfWork:
    """工作单元，协调多个Repository和事务。

    提供对所有Repository的访问，并管理数据库事务。
    """

    def __init__(self, session: Session):
        """初始化工作单元。

        Args:
            session: SQLAlchemy会话
        """
        self.session = session
        self._initialize_repositories()

    def _initialize_repositories(self) -> None:
        """初始化所有Repository。"""
        self.users = UserRepository(self.session)
        self.weights = WeightRepository(self.session)
        self.daily_nutrition = DailyNutritionRepository(self.session)
        self.weekly_nutrition = WeeklyNutritionRepository(self.session)
        self.app_configs = AppConfigRepository(self.session)

    def commit(self) -> None:
        """提交当前事务。"""
        self.session.commit()

    def rollback(self) -> None:
        """回滚当前事务。"""
        self.session.rollback()

    def close(self) -> None:
        """关闭会话。"""
        self.session.close()


@contextmanager
def unit_of_work(
    database_url: Optional[str] = None, session: Optional[Session] = None
) -> Generator[UnitOfWork, None, None]:
    """工作单元上下文管理器。

    自动管理事务：成功时提交，异常时回滚。

    Args:
        database_url: 数据库连接URL，如果为None则使用默认URL
        session: 已有会话，如果为None则创建新会话

    Yields:
        UnitOfWork实例

    Examples:
        >>> with unit_of_work() as uow:
        ...     user = uow.users.get_by_id(1)
        ...     user.name = "New Name"
        ...     uow.users.update(user.id, user)
        ...     uow.commit()
    """
    if session is None:
        # 创建新引擎和会话
        engine = create_engine_from_url(database_url)
        session = get_session(engine)

    uow = UnitOfWork(session)

    try:
        yield uow
        uow.commit()
    except Exception:
        uow.rollback()
        raise
    finally:
        uow.close()


class DatabaseContext:
    """数据库上下文，提供简单的数据库操作接口。

    这是UnitOfWork的简化版本，适合简单场景。
    """

    def __init__(self, database_url: Optional[str] = None):
        """初始化数据库上下文。

        Args:
            database_url: 数据库连接URL，如果为None则使用默认URL
        """
        self.database_url = database_url
        self.engine = create_engine_from_url(database_url)

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """会话作用域上下文管理器。

        Yields:
            SQLAlchemy会话

        Examples:
            >>> db = DatabaseContext()
            >>> with db.session_scope() as session:
            ...     user = session.get(UserProfileModel, 1)
            ...     user.name = "New Name"
        """
        session = get_session(self.engine)
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def uow_scope(self) -> Generator[UnitOfWork, None, None]:
        """工作单元作用域上下文管理器。

        Yields:
            UnitOfWork实例

        Examples:
            >>> db = DatabaseContext()
            >>> with db.uow_scope() as uow:
            ...     user = uow.users.get_by_id(1)
            ...     user.name = "New Name"
            ...     uow.users.update(user.id, user)
        """
        with unit_of_work(session=get_session(self.engine)) as uow:
            yield uow
