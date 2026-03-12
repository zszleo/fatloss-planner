# Fatloss Planner 开发文档

## 项目状态 (更新于2026-03-12)

### 🎉 核心阶段完成状态

#### ✅ Phase 1: 核心计算引擎（已完成）
- **BMR计算**: Mifflin-St Jeor公式实现，支持性别、年龄、体重、身高参数
- **TDEE计算**: 基础代谢 + 训练消耗（训练分钟数×10）
- **营养分配**: 5:3:2比例（碳水:蛋白质:脂肪），支持热量系数转换（4/4/9）
- **减脂时间预测**: 基于目标体重差和每周减重速度预测
- **数据模型**: Pydantic V2模型（UserProfile, WeightRecord, NutritionPlan, AppConfig）
- **单元测试**: 37个单元测试，覆盖率100%

#### ✅ Phase 2: 存储层与业务服务层（已完成）
- **Repository抽象层**: BaseRepository、FilterableRepository、DateRangeRepository接口
- **SQLAlchemy ORM模型**: 完整的数据库表结构定义
- **映射器模块**: Pydantic与SQLAlchemy模型双向自动转换
- **具体Repository实现**: UserRepository、WeightRepository、NutritionRepository、AppConfigRepository
- **工作单元模式**: UnitOfWork上下文管理器，支持事务管理和自动回滚
- **Planner业务服务**: PlannerService整合计算引擎与存储层
- **集成测试**: 17个集成测试，数据库操作验证

#### ✅ Phase 3: CLI命令行接口（已完成）
- **7个核心命令**: `calculate`, `plan`, `adjust`, `config`, `export`, `user`, `weight`
- **完整功能覆盖**: 热量计算、计划生成、营养调整、配置管理、数据导出、用户管理、体重记录
- **CLI测试**: 98个CLI测试，覆盖所有命令和参数组合
- **用户友好界面**: 详细的帮助信息、参数验证、友好的输出格式
- **数据库集成**: 所有命令与数据库无缝集成，支持事务管理

#### 🔄 Phase 4: PyQt5桌面界面（进行中）
- **阶段1完成**: 基础框架搭建（2026-03-12）
- **桌面模块**: 完整目录结构（controllers/, views/, models/, utils/等）
- **主窗口框架**: QMainWindow实现，包含菜单栏、状态栏、标签页
- **应用启动器**: QApplication配置和跨平台字体设置
- **控制器**: MainController封装PlannerService业务逻辑
- **错误处理**: 统一的ErrorHandler类
- **数据库兼容**: 与CLI共享SQLite数据库，支持数据迁移

### 📊 质量指标
- **总测试数**: 297个测试全部通过
- **核心模块覆盖率**: >95% (计算引擎、数据模型、存储层、业务服务层、CLI)
- **整体测试覆盖率**: 27.05% (因包含8780行未测试桌面UI代码)
- **代码质量**: 通过black、isort、pylint、mypy检查
- **架构验证**: 分层架构清晰，设计模式应用正确


## 环境设置

### 解决依赖问题方案 已解决 ✅

#### 方案1：安装python3-venv（推荐）
```bash
# Ubuntu/Debian系统
sudo apt update
sudo apt install python3.12-venv

# 重新创建虚拟环境
cd /git_repo/fatloss-planner
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -e ".[dev]"
```

### 验证环境
```bash
# 激活虚拟环境后运行
python -c "import pydantic; print(f'pydantic版本: {pydantic.__version__}')"
python -c "import sqlalchemy; print(f'sqlalchemy版本: {sqlalchemy.__version__}')"
python -c "import pytest; print(f'pytest版本: {pytest.__version__}')"
```

## 项目结构

```
fatloss-planner/
├── src/fatloss/
│   ├── calculator/          # 核心计算引擎
│   │   ├── bmr_calculator.py      # 基础代谢率
│   │   ├── tdee_calculator.py     # 每日总能量消耗
│   │   ├── nutrition_calculator.py # 营养分配
│   │   └── time_predictor.py      # 减脂时间预测
│   ├── models/             # 数据模型（Pydantic）
│   │   ├── user_profile.py
│   │   ├── weight_record.py
│   │   ├── nutrition_plan.py
│   │   └── app_config.py
│   ├── repository/         # 数据访问层
│   │   ├── abstract_repository.py  # Repository接口
│   │   ├── database.py            # 数据库配置
│   │   ├── models.py              # SQLAlchemy ORM模型
│   │   ├── mapper.py              # Pydantic ↔ SQLAlchemy转换
│   │   ├── sqlalchemy_repository.py # 通用实现
│   │   ├── user_repository.py     # 用户Repository
│   │   ├── weight_repository.py   # 体重Repository
│   │   ├── nutrition_repository.py # 营养计划Repository
│   │   ├── app_config_repository.py # 配置Repository
│   │   └── unit_of_work.py        # 工作单元模式
│   ├── planner/           # 业务逻辑层
│   │   ├── planner_service.py    # Planner业务服务
│   │   └── __init__.py
│   ├── cli/               # CLI接口（已完成）
│   │   ├── main.py              # CLI入口点
│   │   ├── commands/            # 所有命令实现
│   │   │   ├── calculate.py    # 热量计算命令
│   │   │   ├── plan.py         # 计划生成命令
│   │   │   ├── adjust.py       # 营养调整命令
│   │   │   ├── config.py       # 配置管理命令
│   │   │   ├── export.py       # 数据导出命令
│   │   │   ├── user.py         # 用户管理命令
│   │   │   └── weight.py       # 体重记录命令
│   │   └── utils/              # CLI工具函数
│   ├── desktop/           # PyQt5桌面界面（进行中）
│   │   ├── main.py            # 应用入口点
│   │   ├── controllers/       # 控制器模块
│   │   ├── views/            # 视图模块
│   │   ├── models/           # Qt数据模型
│   │   ├── utils/            # 工具函数
│   │   └── resources/        # 资源文件
│   ├── api/               # API服务（可选扩展）
│   └── utils/             # 工具函数（已完成）
│       └── validation.py      # 数据验证工具
├── tests/                 # 测试套件（297个测试）
│   ├── unit/              # 单元测试
│   │   ├── test_calculator/      # 计算引擎测试
│   │   ├── test_models/          # 数据模型测试
│   │   ├── test_repository/      # Repository测试
│   │   ├── test_cli/             # CLI命令测试（98个测试）
│   │   └── test_utils/           # 工具函数测试
│   ├── integration/       # 集成测试
│   │   ├── test_repository/     # Repository集成测试
│   │   └── test_database/       # 数据库集成测试
│   └── e2e/              # 端到端测试（部分实现）
├── docs/                  # 文档
├── scripts/              # 脚本（已完成）
│   └── init_db.py         # 数据库初始化CLI工具（fatloss-db）
├── data/                 # 数据文件
├── pyproject.toml        # 项目配置和依赖
├── 实施计划.md           # 项目计划和进度
├── 项目结构.txt          # 目录结构规划
├── 业务逻辑参考.md       # 业务逻辑说明
└── README.md             # 项目说明
```

## 运行测试

### 单元测试
```bash
# 运行所有单元测试
pytest tests/unit/

# 运行特定测试模块
pytest tests/unit/test_calculator/test_bmr_calculator.py

# 运行测试并生成覆盖率报告
pytest tests/unit/ --cov=fatloss.calculator --cov-report=html
```

### 集成测试
```bash
# 运行Repository集成测试
pytest tests/integration/test_repository/
```

## 数据库操作

### 数据库初始化脚本
项目提供了完整的数据库管理脚本 `scripts/init_db.py`，可以通过命令行管理数据库：

```bash
# 安装项目后（数据库管理脚本已注册为入口点）
fatloss-db --help

# 或者直接运行脚本
python scripts/init_db.py --help

# 常用命令
fatloss-db init          # 初始化数据库，创建所有表
fatloss-db status        # 显示数据库状态和表信息
fatloss-db seed          # 添加示例数据
fatloss-db dump-schema   # 导出数据库Schema为SQL文件
fatloss-db reset         # 重置数据库（删除所有表并重新创建）
fatloss-db drop          # 删除所有表（危险操作）
```

### 环境配置
数据库连接通过环境变量 `DATABASE_URL` 配置：
```bash
# 默认SQLite数据库（存储在data/fatloss.db）
DATABASE_URL=sqlite:///./data/fatloss.db

# PostgreSQL示例
DATABASE_URL=postgresql://user:password@localhost:5432/fatloss

# SQLite内存数据库（用于测试）
DATABASE_URL=sqlite:///:memory:
```

### 数据库迁移（Alembic）
项目集成了Alembic进行数据库迁移管理：

```bash
# 初始化Alembic（已包含在项目中）
alembic init alembic

# 生成迁移脚本（检测模型变化）
alembic revision --autogenerate -m "描述变更"

# 应用迁移
alembic upgrade head

# 降级迁移
alembic downgrade -1

# 查看迁移历史
alembic history

# 检查当前版本
alembic current
```

迁移配置已预设：
- `alembic.ini`：配置数据库连接（默认使用环境变量DATABASE_URL）
- `alembic/env.py`：自动导入项目模型和Base.metadata

### 手动初始化数据库（编程方式）
```python
from fatloss.repository import create_engine_from_url, init_database

# 创建SQLite数据库
engine = create_engine_from_url("sqlite:///./data/fatloss.db")
init_database(engine)
```

### 使用工作单元模式
```python
from fatloss.repository import unit_of_work

with unit_of_work() as uow:
    # 创建用户
    user = uow.users.create(user_profile)
    
    # 记录体重
    weight_record = uow.weights.create(weight_record)
    
    # 自动提交事务
```

### 使用Planner服务
```python
from fatloss.planner import PlannerService
from datetime import date

service = PlannerService()

# 创建用户
user = service.create_user_profile(
    name="张三",
    gender=Gender.MALE,
    birth_date=date(1990, 1, 1),
    height_cm=175.0,
    initial_weight_kg=70.0
)

# 生成营养计划
request = NutritionPlanRequest(
    user_id=user.id,
    plan_date=date.today(),
    exercise_minutes=60.0
)
plan = service.generate_daily_nutrition_plan(request)
```

## 代码质量

### 代码格式化
```bash
# 使用black格式化代码
black src/ tests/

# 使用isort整理导入
isort src/ tests/
```

### 代码检查
```bash
# 使用pylint检查代码
pylint src/

# 使用mypy进行类型检查
mypy src/
```

## 开发工作流

1. **创建功能分支**
   ```bash
   git checkout -b feat/new-feature
   ```

2. **实现功能并编写测试**
   - 遵循测试驱动开发（TDD）
   - 编写单元测试 → 实现功能 → 运行测试

3. **运行代码质量检查**
   ```bash
   black src/ tests/
   isort src/ tests/
   mypy src/
   pytest tests/
   ```

4. **提交代码**
   ```bash
   git add .
   git commit -m "feat: 添加新功能"
   ```

## 当前开发状态与下一步计划

### ✅ Phase 1-3 已完成验收
所有核心功能已实现并通过测试，CLI版本已具备生产就绪状态。

### 🔄 Phase 4: PyQt5桌面界面（进行中）
**当前进度**：阶段1（基础框架搭建）已完成（2026-03-12）

#### 已完成的工作：
1. ✅ **PyQt5环境配置和依赖安装**
2. ✅ **主窗口框架和基本布局**
3. ✅ **应用启动器和配置管理**
4. ✅ **基础控制器和错误处理**
5. ✅ **数据库兼容性设计**

#### 下一步开发任务（Phase 4阶段2）：
1. **用户管理模块开发**（预计10小时）
   - 用户档案列表界面（QTableView）
   - 新建/编辑用户表单
   - 用户详情查看面板
   
2. **营养计算模块开发**（预计8小时）
   - BMR/TDEE计算器界面
   - 营养素分配计算和展示
   - 训练时间调整滑块

3. **体重跟踪模块开发**（预计10小时）
   - 体重记录表格
   - 体重趋势图表（matplotlib集成）
   - 目标进度可视化

4. **仪表盘模块开发**（预计12小时）
   - 关键指标概览面板
   - 营养分配饼图展示
   - 进度报告和统计信息

### 📅 后续可选扩展计划
1. **Phase 5: API服务**（可选，预计3天）
   - FastAPI应用实现
   - RESTful API端点
   - OpenAPI文档生成

2. **Phase 6: Web界面**（可选，预计2天）
   - 响应式Web界面
   - 数据可视化图表
   - 移动设备支持

### 🎯 近期优先任务
1. 完成Phase 4阶段2的核心功能模块
2. 添加桌面UI测试（pytest-qt）
3. 优化用户体验和界面设计
4. 准备多平台打包配置（PyInstaller）

## 故障排除

### 常见问题

#### Q: 无法安装依赖
**A**: 系统Python环境受保护，需要安装python3-venv或使用--break-system-packages参数。

#### Q: 测试失败
**A**: 检查依赖是否正确安装，数据库连接是否正常。

#### Q: 导入错误
**A**: 确保src目录在Python路径中，或已安装包（pip install -e .）。

#### Q: 数据库表不存在
**A**: 运行数据库初始化：`python scripts/init_db.py`

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 遵循代码规范
4. 编写测试
5. 提交Pull Request

## 许可证

MIT License