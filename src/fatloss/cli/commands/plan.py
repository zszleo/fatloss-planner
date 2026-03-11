#!/usr/bin/env python3
"""计划命令模块。

生成每日或每周减脂营养计划。
"""

from datetime import date
from typing import Optional

import click

from fatloss.models.enums import Gender, ActivityLevel
from fatloss.planner.planner_service import PlannerService, NutritionPlanRequest


@click.group()
def plan():
    """生成减脂营养计划。"""
    pass


@plan.command()
@click.option(
    "--user-id",
    "-u",
    type=int,
    help="用户ID（如果已存在用户）",
)
@click.option(
    "--name",
    "-n",
    type=str,
    help="用户姓名（创建新用户时必需）",
)
@click.option(
    "--gender",
    "-g",
    type=click.Choice([e.value for e in Gender], case_sensitive=False),
    help="性别（创建新用户时必需）",
)
@click.option(
    "--birth-date",
    "-b",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="出生日期，格式：YYYY-MM-DD（创建新用户时必需）",
)
@click.option(
    "--height",
    type=float,
    help="身高（厘米）（创建新用户时必需）",
)
@click.option(
    "--weight",
    "-w",
    type=float,
    help="体重（千克）（创建新用户时必需）",
)
@click.option(
    "--activity-level",
    "-a",
    type=click.Choice([e.value for e in ActivityLevel], case_sensitive=False),
    default=ActivityLevel.MODERATE.value,
    show_default=True,
    help="活动水平",
)
@click.option(
    "--plan-date",
    "-d",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=str(date.today()),
    show_default=True,
    help="计划日期，格式：YYYY-MM-DD",
)
@click.option(
    "--exercise",
    "-e",
    type=float,
    default=60.0,
    show_default=True,
    help="训练时间（分钟）",
)
@click.option(
    "--adjustment",
    type=int,
    default=0,
    show_default=True,
    help="碳水化合物调整单位（正数增加，负数减少）",
)
def daily(
    user_id: Optional[int],
    name: Optional[str],
    gender: Optional[str],
    birth_date: Optional[date],
    height: Optional[float],
    weight: Optional[float],
    activity_level: str,
    plan_date: date,
    exercise: float,
    adjustment: int,
):
    """生成每日营养计划。

    必须提供用户ID（对于现有用户）或创建新用户所需的所有信息。
    """
    # 初始化Planner服务
    planner = PlannerService()

    # 确定用户ID
    target_user_id = user_id

    if target_user_id is None:
        # 创建新用户
        if not all([name, gender, birth_date, height, weight]):
            missing = []
            if not name:
                missing.append("--name")
            if not gender:
                missing.append("--gender")
            if not birth_date:
                missing.append("--birth-date")
            if not height:
                missing.append("--height")
            if not weight:
                missing.append("--weight")

            raise click.BadParameter(
                f"创建新用户需要以下参数：{', '.join(missing)}"
            )

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

        # 创建用户档案
        user = planner.create_user_profile(
            name=name,
            gender=gender_enum,
            birth_date=birth_date.date(),
            height_cm=height,
            initial_weight_kg=weight,
            activity_level=activity_level_enum,
        )

        target_user_id = user.id
        click.echo(f"✅ 创建新用户：{user.name} (ID: {user.id})")

    # 生成每日营养计划
    request = NutritionPlanRequest(
        user_id=target_user_id,
        plan_date=plan_date.date(),
        exercise_minutes=exercise,
        adjustment_units=adjustment,
    )

    try:
        daily_plan = planner.generate_daily_nutrition_plan(request)
    except Exception as e:
        raise click.ClickException(f"生成营养计划失败：{e}")

    # 显示结果
    click.echo("📅 每日营养计划")
    click.echo("=" * 40)
    click.echo(f"👤 用户ID: {target_user_id}")
    click.echo(f"📅 计划日期: {daily_plan.plan_date}")
    click.echo()

    click.echo(f"🔥 TDEE目标: {daily_plan.target_tdee} 大卡/天")
    click.echo()

    nutrition = daily_plan.nutrition
    click.echo(f"🍽️  三大营养素分配")
    click.echo(f"   碳水化合物: {nutrition.carbohydrates_g} g")
    click.echo(f"   蛋白质: {nutrition.protein_g} g")
    click.echo(f"   脂肪: {nutrition.fat_g} g")
    click.echo(f"   总热量: {nutrition.total_calories} 大卡")
    click.echo()

    if daily_plan.is_adjusted:
        adjustment_text = "增加" if daily_plan.adjustment_units > 0 else "减少"
        click.echo(f"⚖️  碳水化合物已调整：{adjustment_text} {abs(daily_plan.adjustment_units) * 30}g")
    else:
        click.echo("⚖️  碳水化合物未调整（基础分配）")

    click.echo("=" * 40)
    click.echo(f"💾 计划已保存到数据库（计划ID: {daily_plan.id})")


@plan.command()
@click.option(
    "--user-id",
    "-u",
    type=int,
    required=True,
    help="用户ID",
)
@click.option(
    "--week-start",
    "-w",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=str(date.today()),
    show_default=True,
    help="周开始日期（周一），格式：YYYY-MM-DD",
)
def weekly(user_id: int, week_start: date):
    """生成每周营养计划。"""
    planner = PlannerService()

    try:
        weekly_plan = planner.generate_weekly_nutrition_plan(
            user_id=user_id,
            week_start_date=week_start.date(),
        )
    except Exception as e:
        raise click.ClickException(f"生成每周营养计划失败：{e}")

    if weekly_plan is None:
        click.echo("⚠️  无法生成每周营养计划（可能缺少每日计划数据）")
        return

    # 显示结果
    click.echo("📅 每周营养计划")
    click.echo("=" * 40)
    click.echo(f"👤 用户ID: {user_id}")
    click.echo(f"📅 周开始日期: {weekly_plan.week_start_date}")
    click.echo(f"📅 周结束日期: {weekly_plan.week_end_date}")
    click.echo()

    click.echo(f"📊 计划统计")
    daily_plan_count = len(weekly_plan.daily_plans)
    if daily_plan_count > 0:
        average_tdee = sum(p.target_tdee for p in weekly_plan.daily_plans) / daily_plan_count
        average_carb = sum(p.nutrition.carbohydrates_g for p in weekly_plan.daily_plans) / daily_plan_count
        average_protein = sum(p.nutrition.protein_g for p in weekly_plan.daily_plans) / daily_plan_count
        average_fat = sum(p.nutrition.fat_g for p in weekly_plan.daily_plans) / daily_plan_count
    else:
        average_tdee = average_carb = average_protein = average_fat = 0.0
    
    click.echo(f"   每日计划数量: {daily_plan_count}")
    click.echo(f"   平均TDEE: {average_tdee:.1f} 大卡/天")
    click.echo(f"   平均碳水化合物: {average_carb:.1f} g/天")
    click.echo(f"   平均蛋白质: {average_protein:.1f} g/天")
    click.echo(f"   平均脂肪: {average_fat:.1f} g/天")
    click.echo()

    click.echo("📈 每日计划摘要")
    for daily_plan in weekly_plan.daily_plans:
        adjusted = "⚖️" if daily_plan.is_adjusted else "  "
        click.echo(f"   {daily_plan.plan_date}: {daily_plan.target_tdee:.0f} 大卡 {adjusted}")

    click.echo("=" * 40)
    click.echo(f"💾 每周计划已保存到数据库（计划ID: {weekly_plan.id})")