#!/usr/bin/env python3
"""用户管理命令模块。"""

from datetime import date
import click

from fatloss.models.enums import Gender, ActivityLevel
from fatloss.planner.planner_service import PlannerService
from fatloss.repository.unit_of_work import unit_of_work


@click.group()
def user():
    """用户管理。"""
    pass


@user.command()
@click.option(
    "--name",
    "-n",
    required=True,
    help="用户姓名",
)
@click.option(
    "--gender",
    "-g",
    type=click.Choice([e.value for e in Gender], case_sensitive=False),
    required=True,
    help="性别：male（男）或 female（女）",
)
@click.option(
    "--birth-date",
    "-b",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    required=True,
    help="出生日期，格式：YYYY-MM-DD",
)
@click.option(
    "--height",
    type=float,
    required=True,
    help="身高（厘米）",
)
@click.option(
    "--weight",
    "-w",
    type=float,
    required=True,
    help="初始体重（千克）",
)
@click.option(
    "--activity-level",
    "-a",
    type=click.Choice([e.value for e in ActivityLevel], case_sensitive=False),
    default=ActivityLevel.MODERATE.value,
    show_default=True,
    help="活动水平",
)
def create(name, gender, birth_date, height, weight, activity_level):
    """创建新用户档案。"""
    planner = PlannerService()
    
    # 转换性别字符串为枚举
    try:
        gender_enum = Gender(gender.lower())
    except (AttributeError, ValueError):
        raise click.BadParameter(f"无效的性别：{gender}，必须是 {[e.value for e in Gender]}")
    
    # 转换活动水平字符串为枚举
    try:
        activity_level_enum = ActivityLevel(activity_level.lower())
    except (AttributeError, ValueError):
        raise click.BadParameter(f"无效的活动水平：{activity_level}，必须是 {[e.value for e in ActivityLevel]}")
    
    try:
        user_profile = planner.create_user_profile(
            name=name,
            gender=gender_enum,
            birth_date=birth_date.date(),
            height_cm=height,
            initial_weight_kg=weight,
            activity_level=activity_level_enum,
        )
        
        click.echo(f"✅ 用户创建成功！")
        click.echo(f"👤 用户ID: {user_profile.id}")
        click.echo(f"📛 姓名: {user_profile.name}")
        click.echo(f"⚧️  性别: {user_profile.gender}")
        click.echo(f"🎂 年龄: {user_profile.age} 岁")
        click.echo(f"📏 身高: {user_profile.height_cm} cm")
        click.echo(f"⚖️  初始体重: {user_profile.initial_weight_kg} kg")
        click.echo(f"🏃 活动水平: {user_profile.activity_level}")
        
    except Exception as e:
        raise click.ClickException(f"创建用户失败：{e}")


@user.command()
@click.option(
    "--limit",
    "-l",
    type=int,
    default=20,
    show_default=True,
    help="显示用户数量限制",
)
def list(limit):
    """列出所有用户。"""
    planner = PlannerService()
    
    try:
        with unit_of_work(planner.database_url) as uow:
            users = uow.users.get_all(limit=limit)
            
            if not users:
                click.echo("📭 没有用户")
                return
            
            click.echo(f"📋 用户列表（共 {len(users)} 个）")
            click.echo("=" * 60)
            
            for user in users:
                # 获取最新体重
                latest_weight = uow.weights.find_latest_by_user_id(user.id)
                weight_str = f"{latest_weight.weight_kg} kg" if latest_weight else "无记录"
                
                click.echo(f"👤 ID: {user.id:3d} | 姓名: {user.name:20s} | 性别: {user.gender:6s} | 年龄: {user.age:3d} 岁 | 体重: {weight_str}")
            
            click.echo("=" * 60)
            
    except Exception as e:
        raise click.ClickException(f"列出用户失败：{e}")


@user.command()
@click.option(
    "--user-id",
    "-u",
    type=int,
    required=True,
    help="用户ID",
)
def show(user_id):
    """显示用户详细信息。"""
    planner = PlannerService()
    
    try:
        with unit_of_work(planner.database_url) as uow:
            user = uow.users.get_by_id(user_id)
            if user is None:
                raise click.ClickException(f"用户不存在：{user_id}")
            
            # 获取最新体重
            latest_weight = uow.weights.find_latest_by_user_id(user_id)
            
            # 获取体重记录数量
            weight_count = uow.weights.count_by_user_id(user_id) if hasattr(uow.weights, 'count_by_user_id') else "未知"
            
            # 获取营养计划数量
            daily_plan_count = uow.daily_nutrition.count_by_user_id(user_id) if hasattr(uow.daily_nutrition, 'count_by_user_id') else "未知"
            weekly_plan_count = uow.weekly_nutrition.count_by_user_id(user_id) if hasattr(uow.weekly_nutrition, 'count_by_user_id') else "未知"
            
            click.echo(f"👤 用户详情")
            click.echo("=" * 40)
            click.echo(f"📛 姓名: {user.name}")
            click.echo(f"🆔 用户ID: {user.id}")
            click.echo(f"⚧️  性别: {user.gender}")
            click.echo(f"🎂 出生日期: {user.birth_date} (年龄: {user.age} 岁)")
            click.echo(f"📏 身高: {user.height_cm} cm")
            click.echo(f"⚖️  初始体重: {user.initial_weight_kg} kg")
            click.echo(f"🏃 活动水平: {user.activity_level}")
            click.echo(f"📅 创建时间: {user.created_at}")
            click.echo()
            
            click.echo(f"📊 统计数据")
            click.echo(f"   体重记录: {weight_count} 条")
            if latest_weight:
                click.echo(f"   最新体重: {latest_weight.weight_kg} kg ({latest_weight.record_date})")
            click.echo(f"   每日营养计划: {daily_plan_count} 条")
            click.echo(f"   每周营养计划: {weekly_plan_count} 条")
            click.echo("=" * 40)
            
    except Exception as e:
        raise click.ClickException(f"显示用户失败：{e}")