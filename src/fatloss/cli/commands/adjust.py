#!/usr/bin/env python3
"""调整命令模块。

基于体重变化提供营养调整建议。
"""

import click
from datetime import date

from fatloss.planner.planner_service import PlannerService


@click.command()
@click.option(
    "--user-id",
    "-u",
    type=int,
    required=True,
    help="用户ID",
)
@click.option(
    "--manual-adjustment",
    "-m",
    type=int,
    help="手动调整单位数（正数增加碳水，负数减少碳水）",
)
@click.option(
    "--apply",
    "-a",
    is_flag=True,
    help="应用调整到今日营养计划",
)
def adjust(user_id, manual_adjustment, apply):
    """基于体重变化调整营养计划。

    提供自动调整建议或应用手动调整。
    
    示例：
      fatloss-planner adjust --user-id 1
      fatloss-planner adjust --user-id 1 --manual-adjustment 1 --apply
    """
    planner = PlannerService()
    
    if manual_adjustment is not None:
        # 手动调整模式
        if manual_adjustment > 0:
            direction = "增加"
        elif manual_adjustment < 0:
            direction = "减少"
        else:
            direction = "无"
        
        click.echo("🔧 手动调整模式")
        click.echo(f"   调整单位数: {manual_adjustment}")
        click.echo(f"   调整方向: {direction}碳水化合物摄入")
        
        if apply:
            # 应用调整到今日计划
            try:
                from fatloss.planner.planner_service import NutritionPlanRequest
                
                request = NutritionPlanRequest(
                    user_id=user_id,
                    plan_date=date.today(),
                    exercise_minutes=60.0,
                    adjustment_units=manual_adjustment,
                )
                
                daily_plan = planner.generate_daily_nutrition_plan(request)
                
                click.echo(f"✅ 已应用调整到今日营养计划（计划ID: {daily_plan.id})")
                click.echo(f"   调整后碳水化合物: {daily_plan.nutrition.carbohydrates_g} g")
                
            except Exception as e:
                raise click.ClickException(f"应用调整失败：{e}")
        else:
            click.echo("ℹ️  使用 --apply 标志将调整应用到今日营养计划")
            
    else:
        # 自动调整建议模式
        click.echo("📊 分析体重变化数据...")
        
        try:
            adjustment, message = planner.get_weekly_adjustment_recommendation(user_id)
        except Exception as e:
            raise click.ClickException(f"获取调整建议失败：{e}")
        
        click.echo("💡 每周调整建议")
        click.echo("=" * 40)
        click.echo(f"👤 用户ID: {user_id}")
        click.echo(f"📅 分析日期: {date.today()}")
        click.echo()
        
        if adjustment > 0:
            click.echo(f"✅ 建议: 增加 {adjustment} 单位碳水化合物摄入")
            click.echo(f"   📝 {message}")
        elif adjustment < 0:
            click.echo(f"✅ 建议: 减少 {abs(adjustment)} 单位碳水化合物摄入")
            click.echo(f"   📝 {message}")
        else:
            click.echo(f"✅ 建议: 无需调整")
            click.echo(f"   📝 {message}")
        
        click.echo()
        click.echo("📋 调整单位说明:")
        click.echo("   • 1单位 = 30g 碳水化合物")
        click.echo("   • 正数: 增加碳水摄入（体重下降过快）")
        click.echo("   • 负数: 减少碳水摄入（体重下降过慢）")
        click.echo("   • 0: 无需调整（体重变化正常）")
        
        if adjustment != 0:
            click.echo()
            click.echo("🔧 应用建议调整:")
            click.echo(f"   fatloss-planner adjust --user-id {user_id} --manual-adjustment {adjustment} --apply")
        
        click.echo("=" * 40)