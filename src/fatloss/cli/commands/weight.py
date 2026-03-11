#!/usr/bin/env python3
"""体重记录管理命令模块。"""

from datetime import date
import click

from fatloss.planner.planner_service import PlannerService
from fatloss.repository.unit_of_work import unit_of_work


@click.group()
def weight():
    """体重记录管理。"""
    pass


@weight.command()
@click.option(
    "--user-id",
    "-u",
    type=int,
    required=True,
    help="用户ID",
)
@click.option(
    "--weight",
    "-w",
    type=float,
    required=True,
    help="体重（千克）",
)
@click.option(
    "--date",
    "-d",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="记录日期，格式：YYYY-MM-DD（默认：今天）",
)
@click.option(
    "--notes",
    "-n",
    help="备注",
)
def record(user_id, weight, date, notes):
    """记录体重。"""
    planner = PlannerService()
    
    # 避免参数名冲突，重新导入date类
    from datetime import date as date_class
    record_date = date.date() if date else date_class.today()
    
    try:
        weight_record = planner.record_weight(
            user_id=user_id,
            weight_kg=weight,
            record_date=record_date,
            notes=notes or "",
        )
        
        click.echo(f"✅ 体重记录成功！")
        click.echo(f"👤 用户ID: {user_id}")
        click.echo(f"⚖️  体重: {weight} kg")
        click.echo(f"📅 记录日期: {record_date}")
        if notes:
            click.echo(f"📝 备注: {notes}")
        click.echo(f"🆔 记录ID: {weight_record.id}")
        
    except Exception as e:
        raise click.ClickException(f"记录体重失败：{e}")


@weight.command()
@click.option(
    "--user-id",
    "-u",
    type=int,
    required=True,
    help="用户ID",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=10,
    show_default=True,
    help="显示记录数量限制",
)
@click.option(
    "--reverse",
    "-r",
    is_flag=True,
    help="反向排序（从旧到新）",
)
def history(user_id, limit, reverse):
    """查看体重历史记录。"""
    planner = PlannerService()
    
    try:
        with unit_of_work(planner.database_url) as uow:
            # 获取用户
            user = uow.users.get_by_id(user_id)
            if user is None:
                raise click.ClickException(f"用户不存在：{user_id}")
            
            # 获取体重记录
            weight_records = uow.weights.find_all_by_user_id(user_id)
            if not weight_records:
                click.echo(f"📭 用户 {user.name} 没有体重记录")
                return
            
            # 排序
            weight_records = sorted(
                weight_records,
                key=lambda x: x.record_date,
                reverse=not reverse,
            )
            
            # 限制数量
            if limit > 0:
                weight_records = weight_records[:limit]
            
            click.echo(f"📈 体重历史记录 - {user.name}")
            click.echo(f"📊 总记录数: {len(uow.weights.find_all_by_user_id(user_id))}")
            click.echo("=" * 50)
            
            # 计算变化
            previous_weight = None
            for i, record in enumerate(weight_records):
                change = ""
                if previous_weight is not None:
                    diff = record.weight_kg - previous_weight
                    if diff > 0:
                        change = f"(+{diff:.1f} kg)"
                    elif diff < 0:
                        change = f"({diff:.1f} kg)"
                    else:
                        change = "(0 kg)"
                
                notes_str = f" - {record.notes}" if record.notes else ""
                click.echo(f"{i+1:2d}. {record.record_date}: {record.weight_kg:6.1f} kg {change:10s}{notes_str}")
                previous_weight = record.weight_kg
            
            # 显示统计信息
            if len(weight_records) >= 2:
                first = weight_records[0].weight_kg
                last = weight_records[-1].weight_kg
                total_change = last - first
                days_diff = (weight_records[-1].record_date - weight_records[0].record_date).days
                
                click.echo("=" * 50)
                click.echo(f"📊 统计信息")
                click.echo(f"   初始体重: {first:.1f} kg ({weight_records[0].record_date})")
                click.echo(f"   最新体重: {last:.1f} kg ({weight_records[-1].record_date})")
                click.echo(f"   总变化: {total_change:+.1f} kg")
                if days_diff > 0:
                    avg_daily_change = total_change / days_diff
                    click.echo(f"   平均每日变化: {avg_daily_change:+.3f} kg/天")
            
            click.echo("=" * 50)
            
    except Exception as e:
        raise click.ClickException(f"获取体重历史失败：{e}")


@weight.command()
@click.option(
    "--user-id",
    "-u",
    type=int,
    required=True,
    help="用户ID",
)
@click.option(
    "--target",
    "-t",
    type=float,
    help="目标体重（千克）",
)
def progress(user_id, target):
    """查看减脂进度。"""
    planner = PlannerService()
    
    try:
        # 如果没有提供目标体重，使用用户初始体重减去5%作为默认目标
        if target is None:
            with unit_of_work(planner.database_url) as uow:
                user = uow.users.get_by_id(user_id)
                if user is None:
                    raise click.ClickException(f"用户不存在：{user_id}")
                
                target = user.initial_weight_kg * 0.95  # 减5%
                click.echo(f"ℹ️  使用默认目标体重: {target:.1f} kg (初始体重的95%)")
        
        # 计算减脂进度
        progress_info = planner.calculate_weight_loss_progress(
            user_id=user_id,
            target_weight_kg=target,
        )
        
        click.echo(f"🎯 减脂进度报告")
        click.echo("=" * 50)
        click.echo(f"👤 用户ID: {user_id}")
        click.echo(f"⚖️  当前体重: {progress_info.current_weight_kg:.1f} kg")
        click.echo(f"🎯 目标体重: {progress_info.target_weight_kg:.1f} kg")
        click.echo(f"📉 需要减重: {progress_info.total_loss_kg:.1f} kg")
        click.echo(f"📊 进度: {progress_info.progress_percentage:.1f}%")
        click.echo(f"📅 预计完成日期: {progress_info.estimated_completion_date}")
        
        # 调整建议
        if progress_info.weekly_adjustment_needed > 0:
            click.echo(f"💡 建议: 增加 {progress_info.weekly_adjustment_needed} 单位碳水化合物摄入")
        elif progress_info.weekly_adjustment_needed < 0:
            click.echo(f"💡 建议: 减少 {abs(progress_info.weekly_adjustment_needed)} 单位碳水化合物摄入")
        else:
            click.echo(f"💡 建议: 无需调整，保持当前计划")
        
        # 进度条可视化
        progress_percent = min(100, max(0, progress_info.progress_percentage))
        bar_length = 30
        filled = int(bar_length * progress_percent / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        click.echo()
        click.echo(f"📈 进度条: [{bar}] {progress_percent:.1f}%")
        
        click.echo("=" * 50)
        
    except Exception as e:
        raise click.ClickException(f"获取减脂进度失败：{e}")