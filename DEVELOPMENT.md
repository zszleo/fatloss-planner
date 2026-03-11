# Fatloss Planner 开发文档

## 项目状态 (更新于2026-03-11)

### 🎉 所有核心阶段已完成

#### ✅ Phase 1: 核心计算引擎
- **BMR计算**: Mifflin-St Jeor公式实现，支持性别、年龄、体重、身高参数
- **TDEE计算**: 基础代谢 + 训练消耗（训练分钟数×10）
- **营养分配**: 5:3:2比例（碳水:蛋白质:脂肪），支持热量系数转换（4/4/9）
- **减脂时间预测**: 基于目标体重差和每周减重速度预测
- **数据模型**: Pydantic V2模型（UserProfile, WeightRecord, NutritionPlan, AppConfig）
- **单元测试**: 37个单元测试，覆盖率100%

#### ✅ Phase 2: 存储层与业务服务层
- **Repository抽象层**: BaseRepository、FilterableRepository、DateRangeRepository接口
- **SQLAlchemy ORM模型**: 完整的数据库表结构定义
- **映射器模块**: Pydantic与SQLAlchemy模型双向自动转换
- **具体Repository实现**: UserRepository、WeightRepository、NutritionRepository、AppConfigRepository
- **工作单元模式**: UnitOfWork上下文管理器，支持事务管理和自动回滚
- **Planner业务服务**: PlannerService整合计算引擎与存储层
- **集成测试**: 17个集成测试，数据库操作验证

#### ✅ Phase 3: CLI命令行接口
- **7个核心命令**: `calculate`, `plan`, `adjust`, `config`, `export`, `user`, `weight`
- **完整功能覆盖**: 热量计算、计划生成、营养调整、配置管理、数据导出、用户管理、体重记录
- **CLI测试**: 98个CLI测试，覆盖所有命令和参数组合
- **用户友好界面**: 详细的帮助信息、参数验证、友好的输出格式
- **数据库集成**: 所有命令与数据库无缝集成，支持事务管理

### 📊 质量指标
- **总测试数**: 273个测试全部通过
- **测试覆盖率**: 99.37% (远超80%质量要求)
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