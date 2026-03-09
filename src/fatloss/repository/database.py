"""数据库配置和SQLAlchemy基类。

提供数据库连接配置和SQLAlchemy ORM基类。
"""

import os
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

Base = declarative_base()

# 默认数据库路径
DEFAULT_DATABASE_URL = "sqlite:///./data/fatloss.db"


def get_database_url() -> str:
    """获取数据库连接URL。

    Returns:
        数据库连接URL
    """
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def create_engine_from_url(database_url: Optional[str] = None):
    """创建SQLAlchemy引擎。

    Args:
        database_url: 数据库连接URL，如果为None则使用默认URL

    Returns:
        SQLAlchemy引擎
    """
    if database_url is None:
        database_url = get_database_url()

    # 如果是SQLite内存数据库，使用StaticPool避免连接问题
    if database_url.startswith("sqlite:///:memory:"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )

    # 如果是SQLite文件数据库
    if database_url.startswith("sqlite:///"):
        return create_engine(
            database_url, connect_args={"check_same_thread": False}, echo=False
        )

    # 其他数据库
    return create_engine(database_url, echo=False)


def create_session_factory(engine):
    """创建会话工厂。

    Args:
        engine: SQLAlchemy引擎

    Returns:
        会话工厂
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database(engine) -> None:
    """初始化数据库，创建所有表。

    Args:
        engine: SQLAlchemy引擎
    """
    Base.metadata.create_all(bind=engine)


def get_session(engine) -> Session:
    """获取数据库会话。

    Args:
        engine: SQLAlchemy引擎

    Returns:
        数据库会话
    """
    SessionLocal = create_session_factory(engine)
    return SessionLocal()
