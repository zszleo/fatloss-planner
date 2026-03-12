# Phase 4: PyQt5桌面界面实施方案

## 概述
本文档详细描述Fatloss Planner项目Phase 4：PyQt5桌面图形界面的实施方案。基于已完成的Phase 1-3（核心计算引擎、存储层、业务服务层、CLI接口），本阶段将添加现代化桌面界面，提供更直观的用户体验和数据可视化。

## 开发状态更新（2026-03-12）

✅ **阶段1：基础框架搭建（已完成）**

### 已完成的核心任务：

1. **PyQt5环境配置和依赖安装**
   - 更新了`pyproject.toml`文件，添加了完整的desktop可选依赖
   - 依赖包包括：PyQt5>=5.15.0、matplotlib>=3.7.0、pandas>=2.0.0、pyqtgraph>=0.13.0
   - 所有依赖已成功安装到虚拟环境

2. **主窗口框架和基本布局**
   - 创建了完整的桌面模块目录结构：
     ```
     src/fatloss/desktop/
     ├── __init__.py
     ├── main.py                 # 应用入口点
     ├── controllers/            # 控制器模块
     │   ├── __init__.py
     │   └── main_controller.py
     ├── views/                  # 视图模块
     │   ├── __init__.py
     │   └── main_window.py
     ├── models/                 # Qt数据模型
     ├── utils/                  # 工具函数
     │   ├── __init__.py
     │   └── error_handler.py
     ├── resources/              # 资源文件
     └── ui/                     # Qt Designer文件
     ```
   - 实现了`MainWindow`类（QMainWindow），包含：
     - 完整的菜单栏（文件、编辑、视图、工具、帮助）
     - 状态栏显示应用状态和数据库连接信息
     - 标签页框架（为6个核心功能模块预留）
     - 窗口关闭确认对话框

3. **应用启动器和配置管理**
   - 创建了`main.py`应用入口点，处理QApplication初始化和配置
   - 跨平台字体设置（Windows: Segoe UI, macOS: SF Pro Text, Linux: Ubuntu）
   - 应用程序元数据配置（名称、版本、组织信息）
   - 支持多种启动方式：`python -m fatloss.desktop.main` 或 `python src/fatloss/desktop/main.py`

4. **基础控制器和错误处理**
   - 实现了`MainController`控制器，封装现有`PlannerService`业务逻辑
   - 实现了`ErrorHandler`统一错误处理类：
     - 处理Pydantic验证错误
     - 处理SQLAlchemy数据库错误
     - 提供标准化的用户反馈（成功/警告/错误消息）
   - 修复了repository层的类型注解问题（Optional[str]支持），确保与现有代码兼容

5. **数据库兼容性**
   - 桌面应用与CLI共享相同的SQLite数据库文件（`~/.fatloss-planner/fatloss.db`）
   - 重用现有的`PlannerService`、`Repository`层和工作单元模式
   - 支持从CLI版本无缝迁移数据（自动检测现有数据）

6. **架构设计实现**
   - 采用Model-View-Controller (MVC)变体模式，适配PyQt5架构
   - 与现有五层架构无缝集成
   - 已完成所有必要的导入测试和功能验证

## 当前项目状态

### 已完成的功能
1. **核心计算引擎**：BMR、TDEE、营养分配、减脂时间预测
2. **数据模型层**：UserProfile、WeightRecord、NutritionPlan、AppConfig
3. **存储层**：Repository模式、SQLAlchemy ORM、工作单元模式
4. **业务服务层**：PlannerService统一业务逻辑
5. **CLI接口**：7个核心命令（calculate, plan, adjust, config, export, user, weight）
6. **桌面UI基础框架**：PyQt5主窗口、控制器、错误处理、配置管理（阶段1完成）
7. **测试**：92.05%覆盖率，297个测试全部通过

### 技术栈
- Python 3.9+
- Pydantic V2（数据验证）
- SQLAlchemy 2.0+（ORM）
- Click 8.0+（CLI框架）
- PyQt5>=5.15.0（桌面UI框架）
- pytest（测试框架）
- matplotlib>=3.7.0（数据可视化）

## 1. 架构设计

### 1.1 分层架构扩展
现有架构将扩展为五层：

```
┌─────────────────────────────────────────┐
│          表示层 (Presentation)           │
├─────────────────────────────────────────┤
│ 1. CLI接口 (已实现)                      │
│ 2. PyQt5桌面界面 (本阶段实现)             │
├─────────────────────────────────────────┤
│          业务服务层 (Service)            │
│          PlannerService (已实现)         │
├─────────────────────────────────────────┤
│          存储层 (Repository)             │
│          Repository模式 (已实现)          │
├─────────────────────────────────────────┤
│          数据模型层 (Model)              │
│          Pydantic模型 (已实现)           │
├─────────────────────────────────────────┤
│          计算引擎层 (Calculator)         │
│          科学计算模块 (已实现)            │
└─────────────────────────────────────────┘
```

### 1.2 视图层设计模式
采用**Model-View-Controller (MVC)**变体模式，适配PyQt5的**Model-View-Delegate**架构：

- **Model**: 现有的PlannerService和数据模型层
- **View**: PyQt5窗口和控件
- **Controller**: 自定义控制器类，协调View和Model
- **Delegate**: PyQt5委托用于自定义数据显示

### 1.3 数据流设计
```
用户界面事件 → 控制器 → PlannerService → Repository → SQLite数据库
                                     ↓
                             计算结果/数据 → 视图更新
```

### 1.4 现有组件重用策略
1. **PlannerService**: 完全重用，作为业务逻辑核心
2. **Repository层**: 通过工作单元模式重用
3. **数据模型**: Pydantic模型转换为Qt友好格式
4. **计算引擎**: 直接调用现有模块

### 1.5 与CLI的共存策略
桌面应用将与现有CLI接口完全兼容，共享相同的数据和业务逻辑：

1. **数据库共享**: 桌面应用和CLI使用相同的SQLite数据库文件
   - 默认路径: `~/.fatloss-planner/fatloss.db` (跨平台)
   - 支持自定义数据库路径配置

2. **业务逻辑共享**: 两者都调用相同的PlannerService
   - 确保计算逻辑一致性
   - 避免重复实现业务规则

3. **配置共享**: 应用配置（AppConfig）在CLI和桌面应用间同步
   - 营养比例设置
   - 调整策略参数
   - 用户偏好设置

4. **数据迁移**: 从CLI到桌面应用的无缝迁移
   - 自动检测现有CLI数据
   - 一键迁移功能
   - 迁移后CLI仍可继续使用

5. **并行使用**: 用户可同时使用CLI和桌面应用
   - 实时数据同步（通过文件锁机制）
   - 操作冲突处理（最后写入优先）
   - 状态一致性保证

这种设计确保了：
- **投资保护**: 现有CLI用户可平滑过渡到桌面应用
- **灵活性**: 用户可根据场景选择合适界面
- **维护简化**: 业务逻辑单一实现，减少维护成本
## 2. 技术选型与依赖

### 2.1 PyQt5版本
- **PyQt5>=5.15.0**（已在pyproject.toml的desktop可选依赖中定义）
- **Qt5>=5.15.0**（跨平台支持良好）

### 2.2 附加Python包
```toml
# 在pyproject.toml的desktop可选依赖中扩展
desktop = [
    "PyQt5>=5.15.0",
    "PyQt5-Qt5>=5.15.0",
    "PyQt5-sip>=12.0",
    "matplotlib>=3.7.0",  # 数据可视化
    "pandas>=2.0.0",      # 数据处理和图表
    "pyqtgraph>=0.13.0",  # 高性能绘图（可选）
]
```

### 2.3 打包工具选择
| 工具 | 优点 | 缺点 | 推荐 |
|------|------|------|------|
| **PyInstaller** | 单文件打包，跨平台，简单易用 | 包体积较大 | ✅ 首选 |
| **cx_Freeze** | 官方维护，稳定性好 | 配置较复杂 | 备选 |
| **Briefcase** | 支持移动端打包 | 成熟度较低 | 不考虑 |
| **Nuitka** | 编译为C，性能好 | 编译时间长 | 性能敏感时考虑 |

**推荐**: PyInstaller，配置简单，跨平台支持良好。

### 2.4 多平台支持策略
- **Windows**: `.exe`单文件，添加图标和版本信息
- **macOS**: `.app`捆绑包，代码签名（可选）
- **Linux**: AppImage或deb/rpm包
- **统一策略**: 使用PyInstaller的`--onefile`和`--windowed`选项

## 3. 模块设计

### 3.1 主窗口结构
```
MainWindow (QMainWindow)
├── MenuBar (QMenuBar)
│   ├── 文件(F)
│   ├── 编辑(E)
│   ├── 视图(V)
│   ├── 工具(T)
│   └── 帮助(H)
├── ToolBar (QToolBar) - 常用功能快捷入口
├── StatusBar (QStatusBar) - 状态信息和提示
├── CentralWidget (QTabWidget) - 核心功能区
│   ├── 仪表盘 (DashboardTab)
│   ├── 用户管理 (UserManagementTab)
│   ├── 营养计算 (NutritionCalculatorTab)
│   ├── 计划管理 (PlanManagementTab)
│   ├── 体重跟踪 (WeightTrackingTab)
│   └── 配置设置 (SettingsTab)
└── DockWidgets (可选停靠窗口)
    ├── 快速计算器 (QuickCalcDock)
    └── 历史记录 (HistoryDock)
```

### 3.2 核心功能模块

#### 3.2.1 仪表盘模块 (DashboardTab)
- 关键指标概览（当前体重、目标体重、进度百分比）
- 营养摄入环形图（碳水、蛋白质、脂肪比例）
- 体重变化趋势图（折线图）
- 本周计划摘要
- 调整建议卡片

#### 3.2.2 用户管理模块 (UserManagementTab)
- 用户档案列表（QTableView）
- 新建/编辑用户表单
- 用户详细信息面板
- 档案导入/导出功能

#### 3.2.3 营养计算模块 (NutritionCalculatorTab)
- BMR/TDEE计算器（表单输入+结果展示）
- 营养素分配计算
- 训练时间调整滑块
- 历史计算记录

#### 3.2.4 计划管理模块 (PlanManagementTab)
- 周计划日历视图（QCalendarWidget）
- 每日营养计划详情
- 计划生成和调整功能
- 计划导出（PDF/图片）

#### 3.2.5 体重跟踪模块 (WeightTrackingTab)
- 体重记录表格（日期、体重、变化量）
- 体重趋势图表（matplotlib集成）
- 目标进度条
- 预测完成日期

#### 3.2.6 配置设置模块 (SettingsTab)
- 营养比例配置（5:3:2比例调整）
- 调整策略设置（±30g碳水单位）
- 界面主题选择（浅色/深色）
- 数据库管理（备份/恢复）

### 3.3 对话框设计
1. **新建用户对话框** (UserDialog)
2. **体重记录对话框** (WeightRecordDialog)
3. **计算器对话框** (CalculatorDialog)
4. **计划调整对话框** (PlanAdjustmentDialog)
5. **导出选项对话框** (ExportDialog)
6. **关于对话框** (AboutDialog)

### 3.4 导航系统
- **标签页导航**: 主要功能切换
- **面包屑导航**: 当前位置提示
- **侧边栏导航**: 快速访问（可选）
- **键盘快捷键**: 常用操作快捷键

## 4. 用户界面设计

### 4.1 视觉设计原则
- **美观性**: 现代、专业的视觉设计，吸引用户使用
- **简洁性**: 减少界面元素，突出核心信息
- **一致性**: 统一控件风格和交互模式
- **反馈性**: 及时的操作反馈和状态提示
- **可访问性**: 支持键盘导航和屏幕阅读器

### 4.2 主要界面设计

#### 4.2.1 登录/启动界面
- 应用Logo和名称
- 最近用户选择
- 新建用户按钮
- 设置入口

#### 4.2.2 主仪表盘
```
┌─────────────────────────────────────────┐
│ [Logo] Fatloss Planner            [设置] │
├─────────────────────────────────────────┤
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐        │
│  │ 体重 │ │ 目标 │ │ 进度 │ │ 剩余 │        │
│  │ 75kg │ │ 65kg │ │ 67% │ │ 30天 │        │
│  └─────┘ └─────┘ └─────┘ └─────┘        │
│                                          │
│  ┌────────────────────────────┐         │
│  │  体重趋势图 (折线图)        │         │
│  │                            │         │
│  └────────────────────────────┘         │
│                                          │
│  ┌─────────────┐ ┌─────────────┐        │
│  │ 营养比例     │ │ 今日计划     │        │
│  │  饼图       │ │  表格        │        │
│  └─────────────┘ └─────────────┘        │
│                                          │
│  ┌────────────────────────────┐         │
│  │  建议：增加30g碳水化合物    │         │
│  └────────────────────────────┘         │
└─────────────────────────────────────────┘
```

#### 4.2.3 数据输入表单设计
- 使用QFormLayout进行标签-输入对齐
- 实时验证（Pydantic模型驱动）
- 错误提示和帮助文本
- 保存/取消按钮组

#### 4.2.4 数据可视化组件
1. **折线图**: 体重变化趋势（matplotlib）
2. **饼图**: 营养素比例（QPieSeries）
3. **柱状图**: 周计划对比（QBarSeries）
4. **进度环**: 减脂进度（自定义QWidget）
5. **日历热图**: 计划完成情况（QCalendarWidget定制）

### 4.3 响应式布局
- 使用QHBoxLayout、QVBoxLayout、QGridLayout组合
- 尺寸策略（QSizePolicy）
- 最小窗口尺寸限制
- 高DPI屏幕支持

### 4.4 主题支持
- **浅色主题**: 默认主题，明亮清晰
- **深色主题**: 减少视觉疲劳
- **系统主题**: 跟随操作系统主题
- 使用QPalette和样式表（QSS）实现

## 5. 与现有代码的集成

### 5.1 PlannerService调用策略
```python
# 桌面应用中的服务调用示例
class MainController:
    def __init__(self):
        self.planner_service = PlannerService()
    
    def calculate_nutrition(self, user_id: int, exercise_minutes: float):
        """调用现有PlannerService方法"""
        request = NutritionPlanRequest(
            user_id=user_id,
            plan_date=date.today(),
            exercise_minutes=exercise_minutes
        )
        return self.planner_service.create_daily_nutrition_plan(request)
```

### 5.2 数据模型转换
```python
# Pydantic ↔ PyQt5数据转换
from fatloss.models.user_profile import UserProfile

def pydantic_to_qt(user_profile: UserProfile) -> dict:
    """将Pydantic模型转换为Qt友好格式"""
    return {
        "id": user_profile.id,
        "name": user_profile.name,
        "gender": user_profile.gender.value,
        "age": calculate_age(user_profile.birth_date),
        "height": user_profile.height_cm,
        "weight": user_profile.current_weight_kg,
    }

# 使用QAbstractTableModel包装数据
class UserTableModel(QAbstractTableModel):
    def __init__(self, users: List[UserProfile]):
        super().__init__()
        self._users = users
```

### 5.3 数据库连接管理
- 重用现有的`unit_of_work`上下文管理器
- 在应用启动时初始化数据库连接
- 使用连接池管理数据库连接
- 支持多线程数据库访问（QThread）

### 5.4 错误处理与用户反馈
```python
class ErrorHandler:
    """统一错误处理"""
    
    @staticmethod
    def handle_service_error(error: Exception, parent_widget=None):
        """处理业务服务错误"""
        if isinstance(error, ValidationError):
            QMessageBox.warning(parent_widget, "输入验证错误", str(error))
        elif isinstance(error, DatabaseError):
            QMessageBox.critical(parent_widget, "数据库错误", "请检查数据库连接")
        else:
            QMessageBox.critical(parent_widget, "系统错误", f"未知错误: {error}")
    
    @staticmethod
    def show_success(message: str, parent_widget=None):
        """显示成功消息"""
        QMessageBox.information(parent_widget, "操作成功", message)
```

## 6. 开发计划

### 6.1 阶段划分（预计总工时：80-120小时，阶段1已完成）

#### ✅ 阶段1：基础框架搭建（已完成，原计划20小时）
**完成详情：**
1. **PyQt5环境配置和依赖安装**
   - 更新`pyproject.toml`文件，添加完整desktop可选依赖
   - 成功安装PyQt5>=5.15.0、matplotlib>=3.7.0、pandas>=2.0.0、pyqtgraph>=0.13.0到虚拟环境

2. **主窗口框架和基本布局**
   - 创建完整的桌面模块目录结构（controllers/, views/, models/, utils/等）
   - 实现`MainWindow`类（QMainWindow），包含完整菜单栏、状态栏、标签页框架
   - 窗口关闭确认对话框

3. **应用启动器和配置管理**
   - 创建`main.py`应用入口点，处理QApplication初始化和配置
   - 跨平台字体设置（Windows: Segoe UI, macOS: SF Pro Text, Linux: Ubuntu）
   - 应用程序元数据配置（名称、版本、组织信息）
   - 支持多种启动方式

4. **基础控制器和错误处理**
   - 实现`MainController`控制器，封装现有`PlannerService`业务逻辑
   - 实现`ErrorHandler`统一错误处理类（Pydantic验证错误、SQLAlchemy数据库错误）
   - 修复repository层类型注解问题，确保与现有代码兼容

5. **数据库兼容性**
   - 桌面应用与CLI共享相同的SQLite数据库文件（`~/.fatloss-planner/fatloss.db`）
   - 重用现有的`PlannerService`、`Repository`层和工作单元模式
   - 支持从CLI版本无缝迁移数据

6. **架构设计实现**
   - 采用Model-View-Controller (MVC)变体模式，适配PyQt5架构
   - 与现有五层架构无缝集成
   - 完成所有必要的导入测试和功能验证

#### 阶段2：核心功能模块开发（进行中，预计40小时）
- 用户管理模块（列表、表单、CRUD） - 已完成
- 营养计算模块（计算器界面） - 已完成
- 体重跟踪模块（表格和图表）
- 仪表盘模块（概览和可视化）

#### 阶段3：高级功能实现（30小时）
- 计划管理模块（日历视图）
- 配置设置模块
- 数据导出功能
- 主题和个性化设置

#### 阶段4：测试和优化（20小时）
- 单元测试和集成测试
- 界面测试（pytest-qt）
- 性能优化
- 用户体验测试

#### 阶段5：打包和部署（10小时）
- PyInstaller配置
- 多平台打包测试
- 安装程序创建
- 文档更新

### 6.2 依赖模块开发顺序
1. ✅ **基础框架**（应用入口、配置、日志） - **已完成**
2. **用户管理**（依赖现有UserProfile模型） - **立即开始**
3. **营养计算**（依赖Calculator模块）
4. **体重跟踪**（依赖WeightRecord模型）
5. **计划管理**（依赖NutritionPlan模型）
6. **仪表盘**（集成所有数据）
7. **配置和设置**

### 6.3 测试策略

#### 6.3.1 单元测试
- 使用`pytest-qt`进行Qt组件测试
- 控制器逻辑测试（Mock PlannerService）
- 数据转换函数测试

#### 6.3.2 集成测试
- 完整业务流测试（UI→Service→Database）
- 数据库操作测试
- 多窗口交互测试

#### 6.3.3 界面测试
- 控件状态验证
- 用户交互模拟
- 布局和响应测试

#### 6.3.4 测试覆盖率目标
- 整体覆盖率保持在85%以上
- 核心业务逻辑覆盖率90%以上
- 新增代码覆盖率100%

### 6.4 质量保证措施
1. **代码审查**: 每个模块完成后进行审查
2. **自动化测试**: CI/CD集成测试
3. **用户体验测试**: 真实用户操作测试
4. **性能测试**: 大数据量下的响应测试
5. **跨平台测试**: Windows/macOS/Linux兼容性测试

## 7. 打包与部署

### 7.1 应用程序打包方案

#### 7.1.1 PyInstaller配置
```python
# pyinstaller_spec.py
a = Analysis(
    ['src/fatloss/desktop/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('src/fatloss/desktop/ui/*.ui', 'ui'),
        ('src/fatloss/desktop/resources/*', 'resources'),
        ('data/', 'data')  # 包含数据库模板
    ],
    hiddenimports=[
        'fatloss.calculator',
        'fatloss.models',
        'fatloss.repository',
        'fatloss.planner',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
```

#### 7.1.2 打包命令
```bash
# Windows
pyinstaller --onefile --windowed --icon=resources/icon.ico --name="Fatloss-Planner" pyinstaller_spec.py

# macOS
pyinstaller --onefile --windowed --icon=resources/icon.icns --name="Fatloss-Planner" pyinstaller_spec.py

# Linux
pyinstaller --onefile --windowed --icon=resources/icon.png --name="fatloss-planner" pyinstaller_spec.py
```

### 7.2 安装程序创建
- **Windows**: Inno Setup创建安装程序
- **macOS**: create-dmg工具创建DMG镜像
- **Linux**: 创建AppImage或deb/rpm包

### 7.3 自动更新机制
```python
# 简化更新检查（未来可扩展）
class UpdateChecker:
    def check_for_updates(self):
        """检查更新"""
        try:
            response = requests.get("https://api.example.com/version")
            latest_version = response.json()["version"]
            current_version = __version__
            
            if latest_version > current_version:
                self.show_update_dialog(latest_version)
        except:
            pass  # 静默失败，不影响主要功能
```

### 7.4 用户数据迁移
```python
def migrate_from_cli():
    """从CLI版本迁移数据"""
    cli_db_path = Path.home() / ".fatloss-planner" / "fatloss.db"
    if cli_db_path.exists():
        # 复制数据库文件到新位置
        desktop_db_path = get_desktop_db_path()
        shutil.copy2(cli_db_path, desktop_db_path)
        QMessageBox.information(
            None, 
            "数据迁移", 
            f"已从CLI版本迁移数据到桌面版:\n{cli_db_path} → {desktop_db_path}"
        )
```

## 8. 风险与缓解

### 8.1 技术风险

#### 风险1: PyQt5版本兼容性问题
- **可能性**: 中
- **影响**: 高
- **缓解措施**:
  - 锁定PyQt5版本（~=5.15.0）
  - 在多个Python版本测试（3.9-3.12）
  - 提供虚拟环境配置脚本

#### 风险2: 打包后的文件体积过大
- **可能性**: 高
- **影响**: 中
- **缓解措施**:
  - 使用UPX压缩可执行文件
  - 排除不必要的依赖
  - 分模块打包（核心包+可选组件）

#### 风险3: 多平台兼容性问题
- **可能性**: 中
- **影响**: 高
- **缓解措施**:
  - 使用平台无关的Qt API
  - 在CI/CD中设置多平台测试
  - 提供平台特定的安装说明

### 8.2 性能考虑

#### 性能优化策略:
1. **懒加载**: 标签页内容按需加载
2. **数据分页**: 大数据集分页显示
3. **图表优化**: 限制数据点数量
4. **异步操作**: 耗时操作在后台线程执行
5. **缓存机制**: 频繁访问的数据缓存

#### 性能指标:
- 应用启动时间：<3秒
- 界面响应时间：<100毫秒
- 大数据量操作：<2秒（有进度提示）

### 8.3 维护考虑

#### 代码组织:
```
src/fatloss/desktop/
├── __init__.py
├── main.py                 # 应用入口
├── controllers/            # 控制器
│   ├── __init__.py
│   ├── main_controller.py
│   ├── user_controller.py
│   └── ...
├── views/                  # 视图
│   ├── __init__.py
│   ├── main_window.py
│   ├── dialogs/
│   └── widgets/
├── models/                 # Qt数据模型
│   ├── __init__.py
│   ├── user_table_model.py
│   └── ...
├── utils/                  # 工具函数
│   ├── __init__.py
│   ├── validators.py
│   ├── converters.py
│   └── ...
├── resources/              # 资源文件
│   ├── icons/
│   ├── styles/
│   └── translations/
└── ui/                     # Qt Designer文件
    ├── main_window.ui
    └── ...
```

#### 可测试性设计:
1. **依赖注入**: 便于Mock和测试
2. **关注点分离**: 视图、控制器、模型分离
3. **接口抽象**: 关键组件定义接口
4. **配置外部化**: 配置参数可外部调整

## 9. 成功指标

### 技术指标:
- [ ] 测试覆盖率不低于85%
- [ ] 无重大缺陷（Critical/High级别）
- [ ] 跨平台兼容性（Windows 10+, macOS 10.15+, Ubuntu 20.04+）
- [ ] 应用启动时间<3秒
- [ ] 内存占用<200MB（典型使用）

### 功能指标:
- [ ] 所有CLI功能在桌面界面中可用
- [ ] 数据可视化功能完整
- [ ] 用户数据可迁移
- [ ] 支持数据导出（JSON/CSV/PDF）

### 用户体验指标:
- [ ] 界面直观，新用户10分钟内完成首次计算
- [ ] 无崩溃或数据丢失问题
- [ ] 响应式设计，适应不同屏幕尺寸
- [ ] 提供清晰的错误提示和帮助信息

## 10. 下一步行动

### 立即行动（已完成）:
✅ 1. 更新pyproject.toml，添加完整desktop依赖  
✅ 2. 创建桌面模块基础结构  
✅ 3. 设计并实现主窗口框架  
□ 4. 配置PyInstaller打包环境（待完成）

### 中期行动（进行中，第2-4周）:
1. **用户管理模块开发**（用户档案列表、新建/编辑表单、CRUD操作）
2. **营养计算模块开发**（BMR/TDEE计算器界面、营养素分配计算）
3. **体重跟踪模块开发**（体重记录表格、趋势图表）
4. **仪表盘模块开发**（关键指标概览、数据可视化）
5. **数据可视化组件集成**（matplotlib图表、QPieSeries饼图等）
6. **测试套件扩展**（pytest-qt界面测试、集成测试）

### 长期行动（第5-6周）:
1. 多平台打包测试
2. 性能优化和调试
3. 文档更新和用户手册编写
4. 发布准备和部署

## 附录

### A. 参考资源
- [PyQt5官方文档](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [Matplotlib与PyQt5集成](https://matplotlib.org/stable/gallery/user_interfaces/embedding_in_qt_sgskip.html)
- [PyInstaller手册](https://pyinstaller.org/en/stable/)
- [Qt样式表参考](https://doc.qt.io/qt-5/stylesheet-reference.html)

### B. 开发环境配置
```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 2. 安装桌面版依赖
pip install -e .[desktop,dev]

# 3. 安装Qt Designer（可选）
# Windows: 安装PyQt5时会包含
# macOS: brew install pyqt5
# Linux: sudo apt-get install qttools5-dev-tools
```

### C. 项目文件清单（新增）
```
新增文件:
src/fatloss/desktop/                    # 桌面应用主目录
src/fatloss/desktop/main.py             # 应用入口点
src/fatloss/desktop/controllers/        # 控制器模块
src/fatloss/desktop/views/              # 视图模块
src/fatloss/desktop/models/             # Qt数据模型
src/fatloss/desktop/utils/              # 工具函数
src/fatloss/desktop/resources/          # 资源文件
src/fatloss/desktop/ui/                 # Qt Designer UI文件
pyinstaller_spec.py                     # PyInstaller配置
desktop_config.toml                     # 桌面应用配置

修改文件:
pyproject.toml                          # 添加桌面依赖
README.md                               # 更新文档
```

---
*文档版本: 1.1*
*创建日期: 2026-03-12*
*最后更新: 2026-03-12*
*作者: Fatloss Planner架构团队*
