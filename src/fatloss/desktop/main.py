#!/usr/bin/env python3
"""Fatloss Planner 桌面应用主入口点。"""

import sys
from pathlib import Path

# 添加项目根目录到路径，以便导入fatloss模块
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置matplotlib支持中文显示
try:
    import matplotlib
    matplotlib.use('Qt5Agg')  # 确保使用Qt5后端
    
    import matplotlib.pyplot as plt
    from matplotlib import rcParams
    from matplotlib.font_manager import FontProperties
    import platform
    
    # 根据操作系统选择字体列表
    system = platform.system().lower()
    
    if system == 'windows':
        # Windows系统中的中文字体（按优先级排序）
        chinese_fonts = [
            'Microsoft YaHei',      # 微软雅黑 (Windows Vista+) - 最常用
            'SimHei',               # 黑体 - 所有Windows版本都有
            'SimSun',               # 宋体 - 所有Windows版本都有
            'NSimSun',              # 新宋体
            'FangSong',             # 仿宋
            'KaiTi',                # 楷体
            'Microsoft JhengHei',   # 微软正黑体
        ]
                
        # Windows特定字体路径
        windows_font_paths = [
            'C:/Windows/Fonts/msyh.ttc',      # 微软雅黑
            'C:/Windows/Fonts/simhei.ttf',    # 黑体
            'C:/Windows/Fonts/simsun.ttc',    # 宋体
        ]
        
    elif system == 'darwin':
        # macOS系统中的中文字体
        chinese_fonts = [
            'PingFang SC',          # 苹方-简 (macOS 10.11+)
            'Hiragino Sans GB',     # 冬青黑体简体中文
            'STHeiti',              # 华文黑体
            'STXihei',              # 华文细黑
            'STKaiti',              # 华文楷体
            'STSong',               # 华文宋体
            'Apple LiGothic',       # 苹果俪黑体
            'Apple LiSung',         # 苹果俪宋体
        ]
        print(f"macOS系统: 配置macOS中文字体")
        
    else:
        # Linux/Unix系统中的中文字体
        chinese_fonts = [
            'Noto Sans CJK SC',     # Google思源黑体简体
            'Noto Sans CJK TC',     # Google思源黑体繁体
            'WenQuanYi Micro Hei',  # 文泉驿微米黑
            'WenQuanYi Zen Hei',    # 文泉驿正黑
            'AR PL UMing CN',       # AR PL 明体
            'AR PL UKai CN',        # AR PL 楷体
            'DejaVu Sans',          # 备用
        ]
        print(f"{system.capitalize()}系统: 配置Linux中文字体")
    
    # 获取当前字体配置
    current_fonts = rcParams.get('font.sans-serif', [])
    
    # 首先清理现有字体列表，移除重复项
    clean_fonts = []
    for font in current_fonts:
        if font not in clean_fonts:
            clean_fonts.append(font)
    
    # 将中文字体插入到列表最前面（保持优先级）
    for font in reversed(chinese_fonts):
        if font in clean_fonts:
            clean_fonts.remove(font)
        clean_fonts.insert(0, font)
    
    # 设置新的字体配置
    rcParams['font.sans-serif'] = clean_fonts
    rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
    
    # 强制指定字体族，确保使用sans-serif
    rcParams['font.family'] = 'sans-serif'
    
except ImportError:
    # matplotlib不可用，图表功能将受限
    print("警告: matplotlib未安装，图表功能不可用")

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