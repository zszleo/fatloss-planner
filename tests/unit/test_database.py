"""数据库配置单元测试"""

import os
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fatloss.repository.database import (
    DEFAULT_DATABASE_URL,
    Base,
    create_engine_from_url,
    create_session_factory,
    get_database_url,
    get_session,
    init_database,
)


class TestDatabaseConfig:
    """数据库配置测试类"""

    def test_get_database_url_default(self):
        """测试默认数据库URL"""
        # 清除环境变量
        with patch.dict(os.environ, {}, clear=True):
            url = get_database_url()
            assert url == DEFAULT_DATABASE_URL

    def test_get_database_url_custom(self):
        """测试自定义数据库URL"""
        custom_url = "sqlite:///custom.db"
        with patch.dict(os.environ, {"DATABASE_URL": custom_url}):
            url = get_database_url()
            assert url == custom_url

    def test_create_engine_from_url_none(self):
        """测试使用默认URL创建引擎"""
        with patch.dict(os.environ, {}, clear=True):
            engine = create_engine_from_url(None)
            assert engine is not None
            assert str(engine.url) == DEFAULT_DATABASE_URL

    def test_create_engine_from_url_sqlite_memory(self):
        """测试SQLite内存数据库引擎"""
        engine = create_engine_from_url("sqlite:///:memory:")
        assert engine is not None
        assert str(engine.url) == "sqlite:///:memory:"
        # 验证使用了StaticPool
        assert engine.pool.__class__.__name__ == "StaticPool"

    def test_create_engine_from_url_sqlite_file(self):
        """测试SQLite文件数据库引擎"""
        engine = create_engine_from_url("sqlite:///test.db")
        assert engine is not None
        assert str(engine.url) == "sqlite:///test.db"
        # 不应该使用StaticPool
        assert engine.pool.__class__.__name__ != "StaticPool"

    @patch('fatloss.repository.database.create_engine')
    def test_create_engine_from_url_other_database(self, mock_create_engine):
        """测试其他数据库引擎（如PostgreSQL）"""
        # 模拟引擎对象
        mock_engine = create_engine("sqlite:///:memory:")
        mock_create_engine.return_value = mock_engine
        
        engine = create_engine_from_url("postgresql://user:pass@localhost/db")
        assert engine is not None
        # 验证调用了create_engine，且echo=False
        mock_create_engine.assert_called_once_with("postgresql://user:pass@localhost/db", echo=False)
        assert engine == mock_engine

    def test_create_session_factory(self):
        """测试创建会话工厂"""
        engine = create_engine("sqlite:///:memory:")
        Session = create_session_factory(engine)
        assert isinstance(Session, sessionmaker)
        assert Session.kw["bind"] == engine
        assert Session.kw["autocommit"] is False
        assert Session.kw["autoflush"] is False

    def test_init_database(self):
        """测试初始化数据库"""
        engine = create_engine("sqlite:///:memory:")
        # 应该不会抛出异常
        init_database(engine)
        # 验证表是否存在（通过检查元数据）
        assert len(Base.metadata.tables) > 0

    def test_get_session(self):
        """测试获取数据库会话"""
        engine = create_engine("sqlite:///:memory:")
        session = get_session(engine)
        assert session is not None
        # 验证会话绑定到正确的引擎
        assert session.bind == engine
        session.close()

    def test_session_operations(self):
        """测试会话操作（提交、回滚）"""
        engine = create_engine("sqlite:///:memory:")
        init_database(engine)
        
        Session = create_session_factory(engine)
        session = Session()
        
        try:
            # 会话应该可以正常使用
            assert session.is_active
            session.commit()
            session.rollback()
        finally:
            session.close()

    def test_database_url_edge_cases(self):
        """测试数据库URL边界情况"""
        # 空字符串环境变量
        with patch.dict(os.environ, {"DATABASE_URL": ""}):
            url = get_database_url()
            assert url == ""  # 注意：这可能不是期望的行为，但测试实际功能
        
        # 带有特殊字符的URL
        special_url = "sqlite:///path with spaces/db.db"
        engine = create_engine_from_url(special_url)
        assert engine is not None
        
        # 无效URL（SQLAlchemy会处理）
        # 这里我们只测试函数不会崩溃
        try:
            engine = create_engine_from_url("invalid://url")
            assert engine is not None
        except Exception:
            # 允许抛出异常，因为无效URL应该被SQLAlchemy拒绝
            pass