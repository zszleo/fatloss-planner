#!/usr/bin/env python3
"""计算命令模块。

计算基础代谢率（BMR）、每日总能量消耗（TDEE）和营养分配。
"""

import click

from fatloss.models.enums import Gender
from fatloss.calculator.bmr_calculator import calculate_bmr
from fatloss.calculator.nutrition_calculator import (
    NutritionDistribution,
    calculate_nutrition,
)
from fatloss.calculator.tdee_calculator import calculate_tdee


@click.command()
@click.option(
    "--weight",
    "-w",
    type=float,
    required=True,
    help="体重（千克），范围：30-200kg",
)
@click.option(
    "--height",
    "-h",
    type=float,
    required=True,
    help="身高（厘米），范围：100-250cm",
)
@click.option(
    "--age",
    "-a",
    type=int,
    required=True,
    help="年龄（岁），范围：18-80岁",
)
@click.option(
    "--gender",
    "-g",
    type=click.Choice([e.value for e in Gender], case_sensitive=False),
    required=True,
    help="性别：male（男）或 female（女）",
)
@click.option(
    "--exercise",
    "-e",
    type=float,
    default=60.0,
    show_default=True,
    help="每日训练时间（分钟），范围：0-300分钟",
)
def calculate(weight, height, age, gender, exercise):
    """计算基础代谢率（BMR）、每日总能量消耗（TDEE）和营养分配。

    示例：
      fatloss-planner calculate --weight 70 --height 175 --age 30 --gender male
    """
    # 转换性别字符串为枚举
    try:
        gender_enum = Gender(gender.lower())
    except (AttributeError, ValueError):
        raise click.BadParameter(f"无效的性别：{gender}，必须是 {[e.value for e in Gender]}")

    # 执行计算
    try:
        bmr = calculate_bmr(
            weight_kg=weight,
            height_cm=height,
            age_years=age,
            gender=gender_enum,
        )

        tdee = calculate_tdee(bmr=bmr, exercise_minutes=exercise)

        nutrition = calculate_nutrition(tdee=tdee)

    except ValueError as e:
        raise click.BadParameter(str(e))

    # 格式化输出
    click.echo("📊 减脂计算器结果")
    click.echo("=" * 40)
    click.echo(f"📏 输入参数")
    click.echo(f"   体重: {weight} kg")
    click.echo(f"   身高: {height} cm")
    click.echo(f"   年龄: {age} 岁")
    click.echo(f"   性别: {gender}")
    click.echo(f"   训练时间: {exercise} 分钟/天")
    click.echo()

    click.echo(f"🔥 基础代谢率（BMR）")
    click.echo(f"   {bmr} 大卡/天")
    click.echo()

    click.echo(f"⚡ 每日总能量消耗（TDEE）")
    click.echo(f"   {tdee} 大卡/天")
    click.echo()

    click.echo(f"🍽️  三大营养素分配（5:3:2比例）")
    click.echo(f"   碳水化合物: {nutrition.carbohydrates_g} g")
    click.echo(f"   蛋白质: {nutrition.protein_g} g")
    click.echo(f"   脂肪: {nutrition.fat_g} g")
    click.echo(f"   总热量: {nutrition.total_calories} 大卡")
    click.echo("=" * 40)