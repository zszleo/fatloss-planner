#!/usr/bin/env python3
"""Fatloss Planner CLI 主入口点。"""

import click

from fatloss.cli import commands


@click.group()
@click.version_option(package_name="fatloss-planner")
def cli():
    """Fatloss Planner - 科学减脂计划工具。

    基于营养计算逻辑，提供个性化的减脂计划生成、进度跟踪和调整建议。
    """
    pass


# 注册命令组
cli.add_command(commands.calculate)
cli.add_command(commands.plan)
cli.add_command(commands.adjust)
cli.add_command(commands.config)
cli.add_command(commands.export)
cli.add_command(commands.user)
cli.add_command(commands.weight)


def main():
    """CLI 入口点函数。"""
    cli()


if __name__ == "__main__":
    main()