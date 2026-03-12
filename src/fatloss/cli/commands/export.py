#!/usr/bin/env python3
"""导出命令模块。

导出用户数据为JSON或CSV格式。
"""

import json
import csv
from datetime import date
from pathlib import Path
import click

from fatloss.planner.planner_service import PlannerService
from fatloss.repository.unit_of_work import unit_of_work


@click.command()
@click.option(
    "--user-id",
    "-u",
    type=int,
    required=True,
    help="用户ID",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "csv"], case_sensitive=False),
    default="json",
    show_default=True,
    help="导出格式",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, writable=True),
    help="输出文件路径（默认：./fatloss_export_{user_id}_{date}.{format}）",
)
@click.option(
    "--include-weight-records",
    is_flag=True,
    help="包含体重记录",
)
@click.option(
    "--include-nutrition-plans",
    is_flag=True,
    help="包含营养计划",
)
def export(user_id, format, output, include_weight_records, include_nutrition_plans):
    """导出用户数据为JSON或CSV格式。

    示例：
      fatloss-planner export --user-id 1 --format json
      fatloss-planner export --user-id 1 --format csv --include-weight-records
    """
    planner = PlannerService()
    
    # 生成默认输出文件名
    if output is None:
        timestamp = date.today().isoformat()
        output = f"./fatloss_export_{user_id}_{timestamp}.{format}"
    
    output_path = Path(output)
    
    try:
        with unit_of_work(planner.database_url) as uow:
            # 获取用户信息
            user = uow.users.get_by_id(user_id)
            if user is None:
                raise click.ClickException(f"用户不存在：{user_id}")
            
            # 获取用户配置
            config = uow.app_configs.get_by_user_id(user_id)
            if config is None:
                config_data = {}
            else:
                config_data = config.model_dump()
            
            # 构建导出数据结构
            export_data = {
                "user": user.model_dump(),
                "config": config_data,
                "export_date": date.today().isoformat(),
                "export_format": format,
            }
            
            # 包含体重记录
            if include_weight_records:
                weight_records = uow.weights.find_by_user_id(user_id)
                export_data["weight_records"] = [
                    record.model_dump() for record in weight_records
                ]
            
            # 包含营养计划
            if include_nutrition_plans:
                daily_plans = uow.daily_nutrition.find_by_user_id(user_id)
                weekly_plans = uow.weekly_nutrition.find_by_user_id(user_id)
                
                export_data["daily_nutrition_plans"] = [
                    plan.model_dump() for plan in daily_plans
                ]
                export_data["weekly_nutrition_plans"] = [
                    plan.model_dump() for plan in weekly_plans
                ]
            
            # 导出到文件
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(
                        export_data,
                        f,
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    )
            elif format == "csv":
                # CSV导出简化：只导出体重记录（如果包含）
                if include_weight_records and "weight_records" in export_data:
                    weight_records = export_data["weight_records"]
                    if weight_records:
                        with open(output_path, "w", newline="", encoding="utf-8") as f:
                            writer = csv.DictWriter(f, fieldnames=weight_records[0].keys())
                            writer.writeheader()
                            writer.writerows(weight_records)
                    else:
                        # 如果没有体重记录，创建空文件
                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write("No weight records to export\n")
                else:
                    # 如果没有选择体重记录，导出基本用户信息
                    with open(output_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow(["Field", "Value"])
                        writer.writerow(["User ID", user.id])
                        writer.writerow(["User Name", user.name])
                        writer.writerow(["Gender", user.gender])
                        writer.writerow(["Birth Date", user.birth_date])
                        writer.writerow(["Height (cm)", user.height_cm])
                        writer.writerow(["Initial Weight (kg)", user.initial_weight_kg])
                        writer.writerow(["Activity Level", user.activity_level])
            
            click.echo(f"✅ 数据已导出到：{output_path}")
            click.echo(f"📊 导出内容：")
            click.echo(f"   • 用户信息: ✓")
            click.echo(f"   • 配置信息: ✓")
            if include_weight_records:
                weight_count = len(export_data.get("weight_records", []))
                click.echo(f"   • 体重记录: {weight_count} 条")
            if include_nutrition_plans:
                daily_count = len(export_data.get("daily_nutrition_plans", []))
                weekly_count = len(export_data.get("weekly_nutrition_plans", []))
                click.echo(f"   • 每日营养计划: {daily_count} 条")
                click.echo(f"   • 每周营养计划: {weekly_count} 条")
            
    except Exception as e:
        raise click.ClickException(f"导出失败：{e}")