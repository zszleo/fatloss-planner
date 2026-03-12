#!/usr/bin/env python3
"""Fatloss Planner 桌面应用主入口点。"""

import sys
from pathlib import Path

# 添加项目根目录到路径，以便导入fatloss模块
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from fatloss.desktop.views.main_window import MainWindow
from fatloss.desktop.controllers.main_controller import MainController


def main():
    """桌面应用入口点函数。"""
    # 创建QApplication实例
    app = QApplication(sys.argv)
    
    # 设置应用属性
    app.setApplicationName("Fatloss Planner")
    app.setApplicationDisplayName("Fatloss Planner - 科学减脂计划工具")
    app.setOrganizationName("Fatloss Planner Team")
    app.setOrganizationDomain("example.com")
    
    # 设置默认字体
    font = QFont()
    font.setFamily("Segoe UI" if sys.platform == "win32" else 
                  "SF Pro Text" if sys.platform == "darwin" else 
                  "Ubuntu")
    font.setPointSize(10)
    app.setFont(font)
    
    # 创建主控制器和主窗口
    controller = MainController()
    window = MainWindow(controller)
    
    # 显示窗口
    window.show()
    
    # 执行应用事件循环
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()