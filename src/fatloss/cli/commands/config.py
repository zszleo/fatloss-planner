#!/usr/bin/env python3
"""配置命令模块。

管理应用程序配置。
"""

import click
import sqlalchemy.exc

from fatloss.planner.planner_service import PlannerService
from fatloss.models.app_config import AppConfig, UnitSystem, Theme
from fatloss.repository.unit_of_work import unit_of_work


@click.group()
def config():
    """管理应用程序配置。"""
    pass


@config.command()
@click.option(
    "--user-id",
    "-u",
    type=int,
    required=True,
    help="用户ID",
)
def show(user_id):
    """显示用户配置。"""
    planner = PlannerService()
    
    try:
        with unit_of_work(planner.database_url) as uow:
            config = uow.app_configs.get_by_user_id(user_id)
    except sqlalchemy.exc.SQLAlchemyError as e:
        raise click.ClickException(f"数据库错误：{e}")
    except KeyError as e:
        raise click.ClickException(f"配置不存在：{e}")
    
    if config is None:
        click.echo(f"⚠️  用户 {user_id} 没有配置，使用默认配置")
        config = AppConfig(user_id=user_id)
    
    click.echo("⚙️  应用程序配置")
    click.echo("=" * 40)
    click.echo(f"👤 用户ID: {user_id}")
    click.echo()
    
    unit_system_str = config.unit_system
    theme_str = config.theme
    
    click.echo(f"📏 单位制: {unit_system_str} ({'公制' if unit_system_str == 'metric' else '英制'})")
    click.echo(f"🎨 主题: {theme_str}")
    click.echo(f"🌐 语言: {config.language}")
    click.echo(f"📅 周检查日: {config.weekly_check_day} ({'周一' if config.weekly_check_day == 1 else '周日' if config.weekly_check_day == 0 else f'星期{config.weekly_check_day}'})")
    click.echo(f"⚖️  碳水化合物调整单位: {config.carb_adjustment_unit_g} g")
    click.echo(f"📉 每月减脂百分比: {config.monthly_loss_percentage * 100:.1f}%")
    click.echo(f"🔥 每分钟训练消耗热量: {config.exercise_calories_per_minute} 大卡")
    click.echo(f"🔔 启用通知: {'是' if config.enable_notifications else '否'}")
    click.echo(f"💾 数据保留天数: {config.data_retention_days} 天")
    click.echo(f"📅 创建时间: {config.created_at}")
    click.echo(f"🔄 更新时间: {config.updated_at}")
    click.echo("=" * 40)


@config.command()
@click.option(
    "--user-id",
    "-u",
    type=int,
    required=True,
    help="用户ID",
)
@click.option(
    "--unit-system",
    type=click.Choice(["metric", "imperial"], case_sensitive=False),
    help="单位制：metric（公制）或 imperial（英制）",
)
@click.option(
    "--theme",
    type=click.Choice(["light", "dark", "auto"], case_sensitive=False),
    help="主题：light（浅色）、dark（深色）或 auto（自动）",
)
@click.option(
    "--language",
    help="语言代码（如 zh-CN, en-US）",
)
@click.option(
    "--weekly-check-day",
    type=click.IntRange(0, 6),
    help="周检查日（0=周日，1=周一，...，6=周六）",
)
@click.option(
    "--carb-adjustment-unit",
    type=click.IntRange(10, 100),
    help="碳水化合物调整单位（克），范围：10-100",
)
@click.option(
    "--monthly-loss-percentage",
    type=click.FloatRange(0.01, 0.1),
    help="每月减脂百分比，范围：1%-10%",
)
@click.option(
    "--exercise-calories-per-minute",
    type=click.FloatRange(5, 20),
    help="每分钟训练消耗热量，范围：5-20大卡",
)
@click.option(
    "--enable-notifications/--disable-notifications",
    default=None,
    help="启用或禁用通知",
)
@click.option(
    "--data-retention-days",
    type=click.IntRange(30, 3650),
    help="数据保留天数，范围：30-3650",
)
def update(
    user_id,
    unit_system,
    theme,
    language,
    weekly_check_day,
    carb_adjustment_unit,
    monthly_loss_percentage,
    exercise_calories_per_minute,
    enable_notifications,
    data_retention_days,
):
    """更新用户配置。"""
    planner = PlannerService()
    
    try:
        with unit_of_work(planner.database_url) as uow:
            # 获取现有配置或创建新配置
            existing_config = uow.app_configs.get_by_user_id(user_id)
            
            if existing_config is None:
                config = AppConfig(user_id=user_id)
                click.echo(f"ℹ️  为用户 {user_id} 创建新配置")
            else:
                config = existing_config
            
            # 更新配置字段（如果提供了新值）
            if unit_system is not None:
                config.unit_system = UnitSystem(unit_system)
            if theme is not None:
                config.theme = Theme(theme)
            if language is not None:
                config.language = language
            if weekly_check_day is not None:
                config.weekly_check_day = weekly_check_day
            if carb_adjustment_unit is not None:
                config.carb_adjustment_unit_g = carb_adjustment_unit
            if monthly_loss_percentage is not None:
                config.monthly_loss_percentage = monthly_loss_percentage
            if exercise_calories_per_minute is not None:
                config.exercise_calories_per_minute = exercise_calories_per_minute
            if enable_notifications is not None:
                config.enable_notifications = enable_notifications
            if data_retention_days is not None:
                config.data_retention_days = data_retention_days
            
            # 保存配置
            if existing_config is None:
                saved_config = uow.app_configs.create(config)
            else:
                saved_config = uow.app_configs.update(config)
            
            click.echo(f"✅ 配置已更新（配置ID: {saved_config.id})")
            
    except sqlalchemy.exc.SQLAlchemyError as e:
        raise click.ClickException(f"数据库错误：{e}")
    except (KeyError, ValueError) as e:
        raise click.ClickException(f"配置错误：{e}")