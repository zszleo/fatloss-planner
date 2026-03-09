# Fatloss Planner 开发文档

## 项目状态

### 已完成阶段
- **Phase 1**: 核心计算引擎 ✅
  - BMR计算（Mifflin-St Jeor公式）
  - TDEE计算（基础代谢 + 训练消耗）
  - 营养分配（5:3:2比例，碳水化合物调整）
  - 减脂时间预测
  - 数据模型（Pydantic）：UserProfile, WeightRecord, NutritionPlan, AppConfig
  - 单元测试框架

- **Phase 2**: 存储层与业务服务层 ✅
  - Repository抽象层（BaseRepository接口）
  - SQLAlchemy ORM模型
  - 映射器模块（Pydantic ↔ SQLAlchemy转换）
  - 具体Repository实现（User, Weight, Nutrition, Config）
  - 工作单元模式（UnitOfWork, DatabaseContext）
  - Planner业务服务（整合计算引擎与存储）
  - 集成测试模板

### 技术债务状态（更新于2026-03-09）

#### 已解决的技术债务 ✅

1. **依赖安装问题**：已通过创建虚拟环境解决 ✅
   - 虚拟环境 (`venv/`) 已创建并激活（验证：`venv/bin/activate` 文件存在）
   - 所有核心依赖 (`pydantic`, `sqlalchemy`, `click`) 和开发依赖 (`pytest`, `alembic`, `black`, `isort`, `mypy`) 已成功安装
   - 验证：`python -c "import pydantic; print(pydantic.__version__)"` 返回 2.12.5
   - 验证：`pytest --version` 返回 9.0.2，`mypy --version` 返回 1.19.1

2. **虚拟环境**：已解决 ✅
   - `python3-venv` 已安装，`venv/` 目录完整存在（包含完整的Python环境）
   - 虚拟环境可以正常激活并使用，所有Python包在虚拟环境中隔离安装
   - 验证：`venv/bin/python` 可执行文件存在，虚拟环境结构完整

3. **测试执行**：已解决 ✅
   - 单元测试全部通过（37个测试，覆盖率100%）
   - 集成测试可正常运行（使用SQLite内存数据库），Repository集成测试全部通过
   - 验证：`pytest tests/unit/` 和 `pytest tests/integration/` 执行成功，无失败测试
   - 测试环境已完全配置，支持TDD工作流程

4. **数据库初始化**：已完成 ✅
   - 数据库初始化脚本 `scripts/init_db.py` 已实现并提供完整CLI（支持init、status、seed、dump-schema、reset、drop命令）
   - Alembic迁移配置已设置（版本：3e91eaef9bd7），支持自动迁移生成和应用
   - 数据库Schema已生成并存储在 `data/schema.sql`，示例数据可正常添加
   - 验证：`alembic current` 显示迁移版本，`fatloss-db status` 显示5个表已创建，`data/fatloss.db` 文件存在（90KB）
   - 数据库管理已集成到项目入口点：`fatloss-db`

5. **Pydantic V2迁移完成** ✅
   - 已将Pydantic V1风格的验证器（`@validator`）迁移到V2的 `@field_validator`
   - 已将 `class Config` 迁移到 `ConfigDict`
   - 已更新所有4个Pydantic模型文件（`user_profile.py`, `weight_record.py`, `nutrition_plan.py`, `app_config.py`）
   - 已修复：10处V1风格代码（`@validator`装饰器8处，`class Config` 2处）全部迁移完成
   - 验证：所有单元测试和集成测试通过，功能正常

6. **数据库路径不一致已解决** ✅
   - 已更新默认数据库URL：`DEFAULT_DATABASE_URL = "sqlite:///./data/fatloss.db"`（`src/fatloss/repository/database.py:16`）
   - 实际数据库文件位置与配置一致：`./data/fatloss.db`
   - `fatloss-db status` 命令现在可以正确检查数据库文件
   - 解决方案：更新 `DEFAULT_DATABASE_URL`，确保默认值与实际文件位置一致
   - 验证：`fatloss-db status` 命令正常显示6个表和数据库大小（90KB）

7. **开发工具完整性已解决** ✅
   - `mypy` 类型检查工具已安装（版本1.19.1），配置完整，可用
   - 已运行 `git init` ，完整开发工作流已配置
   - 所有开发工具（black, isort, pylint, mypy, pytest）已可用且配置正确

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
│   ├── cli/               # CLI接口（待实现）
│   ├── api/               # API服务（待实现）
│   └── utils/             # 工具函数（待实现）
├── tests/                 # 测试套件
│   ├── unit/              # 单元测试
│   │   └── test_calculator/
│   │       ├── test_bmr_calculator.py
│   │       ├── test_tdee_calculator.py
│   │       ├── test_nutrition_calculator.py
│   │       └── test_time_predictor.py
│   ├── integration/       # 集成测试
│   │   └── test_repository/
│   │       ├── test_user_repository.py
│   │       └── test_weight_repository.py
│   └── e2e/              # 端到端测试（待实现）
├── docs/                  # 文档
├── scripts/              # 脚本（待实现）
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
pytest tests/unit/ --cov=src.fatloss.calculator --cov-report=html
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
from src.fatloss.repository import create_engine_from_url, init_database

# 创建SQLite数据库
engine = create_engine_from_url("sqlite:///./data/fatloss.db")
init_database(engine)
```

### 使用工作单元模式
```python
from src.fatloss.repository import unit_of_work

with unit_of_work() as uow:
    # 创建用户
    user = uow.users.create(user_profile)
    
    # 记录体重
    weight_record = uow.weights.create(weight_record)
    
    # 自动提交事务
```

### 使用Planner服务
```python
from src.fatloss.planner import PlannerService
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

## 下一步开发任务

### Phase 2收尾 - 技术债务清理
1. ✅ 解决依赖安装问题 - **已完成**
2. ✅ 运行完整测试套件验证实现 - **已完成**（单元测试覆盖率100%）
3. ✅ 创建数据库初始化脚本 - **已完成**（提供完整CLI工具）
4. ✅ 迁移Pydantic V1到V2 - **已完成**（已迁移4个模型文件中的10处V1代码）
5. ✅ 统一数据库路径配置 - **已完成**（更新DEFAULT_DATABASE_URL为sqlite:///./data/fatloss.db）
6. ✅ 验证完整开发工具链 - **已完成**（mypy可用，git仓库已初始化）

### Phase 3: CLI接口（预计3天）
- 实现CLI命令结构
- 添加用户管理命令
- 添加体重记录命令
- 添加营养计划生成命令
- 添加进度查看命令

### Phase 4: API服务（预计3天）
- 实现FastAPI应用
- 创建RESTful API端点
- 添加API文档
- 实现认证和授权

### Phase 5: Web界面（预计2天）
- 创建简单的Web界面
- 实现数据可视化
- 添加响应式设计

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