# Python减脂计划器 (Fatloss Planner)

基于科学计算逻辑的减脂计划管理软件，帮助用户制定个性化的减脂营养计划。提供完整的命令行接口，支持热量计算、营养分配、减脂计划生成、进度跟踪和动态调整功能。

## 功能特性

### ✅ 核心计算引擎
- **热量计算**：基于Mifflin-St Jeor公式计算基础代谢率（BMR）
- **能量消耗**：计算每日总能量消耗（TDEE = BMR + 训练消耗）
- **营养分配**：按5:3:2比例分配碳水化合物、蛋白质、脂肪
- **目标预测**：根据当前体重和目标体重智能预测减脂时间
- **动态调整**：基于每周体重变化自动调整营养摄入（±30g碳水）

### ✅ 数据管理
- **用户档案**：管理用户基本信息、健康数据和目标设定
- **体重记录**：记录体重变化，跟踪减脂进度
- **营养计划**：生成每日/每周营养计划，支持自动调整
- **应用配置**：管理营养比例、调整策略等配置参数

### ✅ 命令行接口（CLI）
- **7个核心命令**：`calculate`、`plan`、`adjust`、`config`、`export`、`user`、`weight`
- **用户友好**：详细帮助信息、参数验证、友好的输出格式
- **数据导出**：支持JSON/CSV格式导出，便于数据分析和备份

### ✅ 数据持久化
- **SQLite数据库**：本地数据存储，无需外部依赖
- **Repository模式**：抽象数据访问层，支持事务管理
- **工作单元模式**：确保数据一致性和事务完整性

## 技术栈

- **Python 3.9+** - 核心编程语言
- **Pydantic V2** - 数据验证和序列化
- **SQLAlchemy 2.0+** - ORM和数据访问
- **Click 8.0+** - 命令行接口框架
- **pytest** - 测试框架，覆盖率92.05%
- **Alembic** - 数据库迁移管理

## 核心计算逻辑

本项目基于以下科学减脂逻辑实现：

1. **基础代谢率（BMR）计算**：采用Mifflin-St Jeor公式，根据性别、年龄、体重、身高计算
2. **每日总能量消耗（TDEE）计算**：TDEE = BMR + 训练消耗（训练分钟数 × 10）
3. **营养分配**：按5:3:2比例分配碳水化合物、蛋白质、脂肪
   - 碳水化合物：TDEE × 0.5 ÷ 4（每克碳水4千卡）
   - 蛋白质：TDEE × 0.3 ÷ 4（每克蛋白质4千卡）
   - 脂肪：TDEE × 0.2 ÷ 9（每克脂肪9千卡）
4. **减脂时间预测**：基于目标体重差和每周减重速度（体重的4%）预测所需时间
5. **动态调整策略**：每周根据体重变化调整碳水化合物摄入量（±30g单位）

完整业务逻辑和计算示例请参见[业务逻辑参考.md](业务逻辑参考.md)。

## 项目状态

### 🎉 里程碑完成情况

| 阶段 | 状态 | 完成日期 | 测试覆盖率 |
|------|------|----------|------------|
| Phase 1: 核心计算引擎 | ✅ 已完成 | 2026-03-09 | 100% |
| Phase 2: 存储层与业务服务层 | ✅ 已完成 | 2026-03-09 | 100% |
| Phase 3: CLI命令行接口 | ✅ 已完成 | 2026-03-11 | 99% |
| **总体项目** | **✅ 核心功能完成** | **2026-03-11** | **92.05%** |

### ✅ Phase 1: 核心计算引擎（已完成）
- **基础代谢计算**：基于Mifflin-St Jeor公式实现，支持性别、年龄、体重、身高参数
- **每日总能量消耗**：BMR + 训练消耗计算，支持自定义活动系数
- **营养分配**：5:3:2比例实现，碳水化合物调整机制（±30g单位）
- **减脂时间预测**：基于体重变化率的智能预测算法
- **数据模型**：完整的Pydantic V2模型（UserProfile, WeightRecord, NutritionPlan, AppConfig）
- **单元测试**：37个单元测试，覆盖率100%

### ✅ Phase 2: 存储层与业务服务层（已完成）
- **Repository抽象层**：BaseRepository、FilterableRepository、DateRangeRepository接口
- **SQLAlchemy ORM模型**：完整的数据库表结构定义，支持SQLite/PostgreSQL
- **映射器模块**：Pydantic与SQLAlchemy模型双向自动转换
- **具体Repository实现**：UserRepository、WeightRepository、NutritionRepository、AppConfigRepository
- **工作单元模式**：UnitOfWork上下文管理器，支持事务管理和自动回滚
- **Planner业务服务**：PlannerService整合计算引擎与存储层
- **集成测试**：17个集成测试，数据库操作验证

### ✅ Phase 3: CLI命令行接口（已完成）
- **7个核心命令**：`calculate`、`plan`、`adjust`、`config`、`export`、`user`、`weight`
- **用户友好界面**：详细的帮助信息、参数验证、彩色输出
- **完整功能覆盖**：
  - `calculate`: 计算BMR、TDEE和营养分配
  - `plan`: 生成每日/每周减脂营养计划
  - `adjust`: 基于体重变化的营养调整建议
  - `config`: 应用程序配置管理
  - `export`: 数据导出功能（JSON/CSV格式）
  - `user`: 用户档案管理（创建、列表、查看）
  - `weight`: 体重记录管理（记录、历史、进度）
- **CLI测试**：98个CLI测试，覆盖所有命令和参数组合

### 🧪 测试质量

- **总测试数**: 297个测试全部通过
- **测试覆盖率**: 92.05%（远超80%质量要求）
- **单元测试**: 100%覆盖率，核心计算逻辑完全验证
- **集成测试**: 数据库操作和业务服务层验证
- **CLI测试**: 命令执行、参数验证、错误处理

### 🔮 未来规划（可选扩展）

- **Phase 4: PyQt5桌面界面**：跨平台桌面图形界面，提供数据可视化和更佳用户体验
- **移动应用**：iOS/Android移动端应用
- **云同步**：多设备数据同步功能

详细开发计划请参见[实施计划.md](实施计划.md)。

## 架构设计

项目采用清晰的分层架构，遵循关注点分离原则：

### 架构图
```
┌─────────────────────────────────────────────┐
│           用户界面层 (User Interface)        │
│  • CLI命令行接口 (fatloss-planner) ✅ 已完成 │
│  • 桌面应用                                  │
└───────────────────┬─────────────────────────┘
                    │
┌───────────────────▼─────────────────────────┐
│          业务服务层 (Business Layer)         │
│  • PlannerService - 核心业务逻辑 ✅ 已完成   │
│  • 营养计划生成、调整、进度跟踪               │
└───────────────────┬─────────────────────────┘
                    │
┌───────────────────▼─────────────────────────┐
│          核心计算引擎 (Calculator)           │
│  • BMR计算、TDEE计算、营养分配 ✅ 已完成     │
│  • 减脂时间预测、碳水化合物调整               │
└───────────────────┬─────────────────────────┘
                    │
┌───────────────────▼─────────────────────────┐
│          数据访问层 (Repository)             │
│  • Repository抽象接口 ✅ 已完成               │
│  • SQLAlchemy实现 ✅ 已完成                   │
│  • 工作单元模式 (Unit of Work) ✅ 已完成       │
└───────────────────┬─────────────────────────┘
                    │
┌───────────────────▼─────────────────────────┐
│          持久化层 (Persistence)              │
│  • SQLite数据库 (默认) ✅ 已完成              │
│  • PostgreSQL支持 (配置)                      │
│  • Alembic迁移管理 ✅ 已完成                  │
└─────────────────────────────────────────────┘
```

### 设计模式应用
- **Repository模式**: 数据访问抽象，支持多种数据源
- **工作单元模式**: 事务管理，确保数据一致性
- **策略模式**: 营养调整策略可配置
- **依赖注入**: 通过构造函数注入数据库连接

### 技术选型
- **Pydantic V2**: 数据验证和序列化，支持严格的类型检查
- **SQLAlchemy 2.0**: 现代ORM，支持异步操作和类型提示
- **Click**: 功能丰富的CLI框架，支持命令分组和自动帮助生成
- **Alembic**: 数据库迁移管理，支持版本控制和自动迁移生成

详细架构设计和开发文档请参见[DEVELOPMENT.md](DEVELOPMENT.md)。

## 安装与快速开始

### 环境要求
- **Python 3.9+** (推荐Python 3.12)
- **pip** (Python包管理器)
- **虚拟环境** (推荐使用python3-venv)

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/fatloss-planner.git
cd fatloss-planner

# 2. 创建虚拟环境 (Linux/macOS)
python -m venv venv
source venv/bin/activate

# Windows用户使用:
# python -m venv venv
# venv\Scripts\activate

# 3. 安装依赖 (包含开发工具)
pip install -e ".[dev]"

# 4. 验证安装
fatloss-planner --version
fatloss-db --help
```

### 数据库初始化

```bash
# 1. 复制环境配置 (可选)
cp .env.example .env

# 2. 初始化数据库 (创建表和默认数据)
fatloss-db init

# 3. 检查数据库状态
fatloss-db status
```

### 快速入门示例

```bash
# 1. 创建一个新用户
fatloss-planner user create --name "张三" --gender male --birth-date "1990-01-01" --height 175 --weight 70

# 2. 计算营养需求
fatloss-planner calculate --weight 70 --height 175 --age 34 --gender male --exercise 60

# 3. 生成每日营养计划
fatloss-planner plan daily --user-id 1 --exercise-minutes 60

# 4. 记录体重变化
fatloss-planner weight record --user-id 1 --weight 69.5 --date "2026-03-11"

# 5. 查看减脂进度
fatloss-planner weight progress --user-id 1
```

## CLI命令详解

Fatloss Planner提供7个核心命令，涵盖减脂计划管理的全流程：

### 1. `calculate` - 热量与营养计算
计算基础代谢率（BMR）、每日总能量消耗（TDEE）和营养分配。

```bash
# 基本用法
fatloss-planner calculate --weight 70 --height 175 --age 30 --gender male --exercise 60

# 参数说明
--weight, -w      体重（千克，30-200kg） [必需]
--height, -h      身高（厘米，100-250cm） [必需]
--age, -a         年龄（岁，18-80岁） [必需]
--gender, -g      性别（male/female） [必需]
--exercise, -e    训练时间（分钟，0-300） [默认: 60]

# 输出示例
BMR（基础代谢率）: 1641.5 kcal/天
TDEE（每日总消耗）: 2241.5 kcal/天
营养分配（5:3:2比例）:
  • 碳水化合物: 280.2g (1120.8 kcal)
  • 蛋白质: 168.1g (672.4 kcal)
  • 脂肪: 49.8g (448.3 kcal)
```

### 2. `plan` - 减脂计划生成
生成每日或每周的营养计划。

```bash
# 子命令
fatloss-planner plan daily    # 生成每日计划
fatloss-planner plan weekly   # 生成每周计划

# 生成每日计划示例
fatloss-planner plan daily --user-id 1 --exercise-minutes 60

# 生成每周计划示例
fatloss-planner plan weekly --user-id 1 --exercise-minutes 60 --weeks 4
```

### 3. `adjust` - 营养计划调整
基于体重变化调整营养计划。

```bash
# 自动调整建议
fatloss-planner adjust --user-id 1

# 手动调整并应用
fatloss-planner adjust --user-id 1 --manual-adjustment -1 --apply

# 参数说明
--user-id, -u           用户ID [必需]
--manual-adjustment, -m  手动调整单位数（正数增加碳水，负数减少碳水）
--apply, -a             应用调整到今日营养计划
```

### 4. `config` - 应用配置管理
管理应用程序配置，如营养比例、调整策略等。

```bash
# 查看当前配置
fatloss-planner config show --user-id 1

# 更新配置
fatloss-planner config update --user-id 1 --carb-ratio 0.5 --protein-ratio 0.3 --fat-ratio 0.2
```

### 5. `export` - 数据导出
导出用户数据为JSON或CSV格式。

```bash
# 导出为JSON格式
fatloss-planner export --user-id 1 --format json --output ./my_data.json

# 导出为CSV格式（包含体重记录）
fatloss-planner export --user-id 1 --format csv --include-weight-records

# 参数说明
--user-id, -u              用户ID [必需]
--format, -f               导出格式（json/csv） [默认: json]
--output, -o               输出文件路径
--include-weight-records   包含体重记录
--include-nutrition-plans  包含营养计划
```

### 6. `user` - 用户管理
管理用户档案。

```bash
# 子命令
fatloss-planner user create   # 创建新用户
fatloss-planner user list     # 列出所有用户
fatloss-planner user show     # 显示用户详情

# 创建用户示例
fatloss-planner user create \
  --name "李四" \
  --gender female \
  --birth-date "1995-05-15" \
  --height 165 \
  --weight 60 \
  --target-weight 55
```

### 7. `weight` - 体重记录管理
记录和跟踪体重变化。

```bash
# 子命令
fatloss-planner weight record    # 记录体重
fatloss-planner weight history   # 查看历史记录
fatloss-planner weight progress  # 查看减脂进度

# 记录体重示例
fatloss-planner weight record --user-id 1 --weight 68.5 --date "2026-03-11"

# 查看进度示例
fatloss-planner weight progress --user-id 1 --period 30  # 最近30天进度
```

## 项目结构

```
fatloss-planner/
├── src/fatloss/
│   ├── calculator/          # 核心计算引擎
│   │   ├── bmr_calculator.py      # BMR计算
│   │   ├── tdee_calculator.py     # TDEE计算
│   │   ├── nutrition_calculator.py # 营养分配
│   │   └── time_predictor.py      # 减脂时间预测
│   ├── models/              # 数据模型 (Pydantic V2)
│   │   ├── user_profile.py        # 用户档案
│   │   ├── weight_record.py       # 体重记录
│   │   ├── nutrition_plan.py      # 营养计划
│   │   └── app_config.py          # 应用配置
│   ├── repository/          # 数据访问层
│   │   ├── abstract_repository.py  # Repository接口
│   │   ├── sqlalchemy_repository.py # SQLAlchemy实现
│   │   ├── user_repository.py     # 用户Repository
│   │   ├── weight_repository.py   # 体重Repository
│   │   ├── nutrition_repository.py # 营养计划Repository
│   │   ├── unit_of_work.py        # 工作单元模式
│   │   └── database.py            # 数据库配置
│   ├── planner/            # 业务服务层
│   │   └── planner_service.py    # Planner业务服务
│   ├── cli/                # 命令行接口 (Click)
│   │   ├── main.py              # CLI入口点
│   │   ├── commands/            # 所有命令实现
│   │   └── utils/               # CLI工具函数
│   └── api/                # API服务 (可选扩展)
├── tests/                  # 测试套件 (297个测试)
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   └── test_cli/          # CLI命令测试
├── scripts/               # 实用脚本
│   └── init_db.py         # 数据库初始化CLI
├── data/                  # 数据文件
│   └── fatloss.db         # SQLite数据库 (默认)
├── docs/                  # 文档
├── pyproject.toml         # 项目配置和依赖
└── README.md              # 项目说明
```

完整目录结构请参见[项目结构.txt](项目结构.txt)。

## 开发指南

### 运行测试
```bash
# 运行所有测试
pytest tests/

# 运行测试并生成覆盖率报告
pytest tests/ --cov=src/fatloss --cov-report=html

# 运行特定测试模块
pytest tests/unit/test_calculator/ -v
```

### 代码质量检查
```bash
# 代码格式化
black src/ tests/
isort src/ tests/

# 代码检查
pylint src/
mypy src/

# 类型检查
mypy src/fatloss
```

### 数据库管理
```bash
# 查看所有数据库命令
fatloss-db --help

# 常用命令
fatloss-db init          # 初始化数据库
fatloss-db status        # 查看数据库状态
fatloss-db seed          # 添加示例数据
fatloss-db reset         # 重置数据库
fatloss-db dump-schema   # 导出数据库Schema
```

### 开发工作流
1. **创建功能分支**: `git checkout -b feat/feature-name`
2. **编写测试**: 遵循TDD原则，先写测试
3. **实现功能**: 确保代码通过测试
4. **代码检查**: 运行black、isort、mypy、pylint
5. **提交更改**: `git commit -m "feat: 功能描述"`
6. **运行完整测试**: `pytest tests/ --cov=src/fatloss --cov-fail-under=80`

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请创建Issue或通过项目仓库联系。

