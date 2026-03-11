#!/usr/bin/env python3
"""数据库初始化和管理脚本"""

import os
import sys
from pathlib import Path
from datetime import date

import click
from sqlalchemy import inspect

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from fatloss.repository.database import (
    create_engine_from_url,
    get_database_url,
    init_database,
    Base,
)
from fatloss.repository.models import (
    UserProfileModel,
    WeightRecordModel,
    DailyNutritionPlanModel,
    WeeklyNutritionPlanModel,
    AppConfigModel,
    GenderEnum,
    ActivityLevelEnum,
    UnitSystemEnum,
    ThemeEnum,
)


@click.group()
def cli():
    """数据库管理命令"""
    pass


@cli.command()
@click.option("--url", default=None, help="数据库URL，默认使用环境变量DATABASE_URL")
@click.option("--force", is_flag=True, help="强制覆盖现有数据库")
def init(url, force):
    """初始化数据库，创建所有表"""
    database_url = url or get_database_url()
    click.echo(f"📊 使用数据库URL: {database_url}")

    # 如果是SQLite文件数据库，确保目录存在
    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "")
        if db_path != ":memory:":
            db_file = Path(db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)

            # 检查文件是否存在
            if db_file.exists() and not force:
                click.echo(f"⚠️  数据库文件已存在: {db_file}")
                if not click.confirm("是否继续？将保留现有数据"):
                    return

    engine = create_engine_from_url(database_url)
    init_database(engine)
    click.echo("✅ 数据库表创建完成")


@cli.command()
@click.option("--url", default=None, help="数据库URL")
def drop(url):
    """删除所有表（危险操作）"""
    database_url = url or get_database_url()
    click.echo(f"📊 使用数据库URL: {database_url}")

    if click.confirm("⚠️  确定要删除所有表吗？所有数据将永久丢失！"):
        engine = create_engine_from_url(database_url)
        Base.metadata.drop_all(bind=engine)
        click.echo("🗑️  所有表已删除")


@cli.command()
@click.option("--url", default=None, help="数据库URL")
def reset(url):
    """重置数据库：删除所有表并重新创建"""
    database_url = url or get_database_url()
    click.echo(f"📊 使用数据库URL: {database_url}")

    if click.confirm("⚠️  确定要重置数据库吗？所有数据将丢失！"):
        engine = create_engine_from_url(database_url)
        Base.metadata.drop_all(bind=engine)
        click.echo("🗑️  所有表已删除")
        Base.metadata.create_all(bind=engine)
        click.echo("✅ 数据库重置完成")


@cli.command()
@click.option("--url", default=None, help="数据库URL")
def seed(url):
    """添加示例数据"""
    database_url = url or get_database_url()
    engine = create_engine_from_url(database_url)

    from sqlalchemy.orm import Session

    session = Session(engine)

    try:
        # 创建示例用户
        user = UserProfileModel(
            name="示例用户",
            gender=GenderEnum.MALE,
            birth_date=date(1990, 1, 1),
            height_cm=175.0,
            initial_weight_kg=70.0,
            activity_level=ActivityLevelEnum.MODERATE,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # 创建体重记录
        weight_record = WeightRecordModel(
            user_id=user.id,
            weight_kg=70.0,
            record_date=date.today(),
            notes="初始体重",
        )
        session.add(weight_record)

        # 创建应用配置
        app_config = AppConfigModel(
            user_id=user.id,
            unit_system=UnitSystemEnum.METRIC,
            theme=ThemeEnum.AUTO,
            language="zh-CN",
            weekly_check_day=1,
        )
        session.add(app_config)

        session.commit()
        click.echo(f"✅ 示例数据已添加（用户ID: {user.id}）")

    except Exception as e:
        session.rollback()
        click.echo(f"❌ 添加示例数据失败: {e}")
    finally:
        session.close()


@cli.command()
@click.option("--url", default=None, help="数据库URL")
def status(url):
    """显示数据库状态"""
    database_url = url or get_database_url()
    click.echo(f"📊 数据库URL: {database_url}")

    try:
        engine = create_engine_from_url(database_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        click.echo(f"📋 已创建的表 ({len(tables)}):")
        for table in sorted(tables):
            columns = inspector.get_columns(table)
            click.echo(f"  - {table} ({len(columns)}列)")

        # 显示表大小（仅SQLite）
        if database_url.startswith("sqlite:///"):
            db_path = database_url.replace("sqlite:///", "")
            if db_path != ":memory:" and Path(db_path).exists():
                size = Path(db_path).stat().st_size
                click.echo(f"💾 数据库文件大小: {size:,} 字节 ({size/1024:.1f} KB)")

    except Exception as e:
        click.echo(f"❌ 获取状态失败: {e}")


@cli.command()
@click.option("--url", default=None, help="数据库URL")
@click.option("--output", default="schema.sql", help="输出文件路径")
def dump_schema(url, output):
    """导出数据库Schema为SQL文件"""
    database_url = url or get_database_url()
    engine = create_engine_from_url(database_url)

    # 生成创建表的SQL
    from sqlalchemy.schema import CreateTable

    schema_sql = []

    for table in Base.metadata.sorted_tables:
        schema_sql.append(str(CreateTable(table).compile(engine)))

    sql_content = "\n\n".join(schema_sql)

    with open(output, "w", encoding="utf-8") as f:
        f.write(f"-- Fatloss Planner 数据库Schema\n")
        f.write(f"-- 生成时间: {date.today()}\n")
        f.write(f"-- 数据库: {database_url}\n\n")
        f.write(sql_content)

    click.echo(f"✅ Schema已导出到: {output}")


if __name__ == "__main__":
    cli()
