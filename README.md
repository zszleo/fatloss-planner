# Python减脂计划器 (Fatloss Planner)

基于科学计算逻辑的减脂计划管理软件，帮助用户制定个性化的减脂营养计划。

## 功能特性

- **热量计算**：基于基础代谢和训练消耗计算每日总热量
- **营养分配**：按5:3:2比例分配碳水化合物、蛋白质、脂肪
- **目标预测**：根据当前体重和目标体重预测减脂时间
- **动态调整**：基于每周体重变化调整营养摄入
- **计划生成**：生成周度营养计划和食物分量建议

## 核心计算逻辑

本项目基于以下科学减脂逻辑实现：

```
1.1计算初始热量
基础代谢计算器结果：2100打卡 +训练消耗热量（训练时间分钟数*10） 600 = 2700

1.2分配每日三大营养素 532比例
 5碳水 2700*0.5/4（每克碳水热量）= 337.5g
 3蛋白质 2700*0.3/4（每克蛋白质热量）= 202.5g
 2脂肪 2700*0.2/9（每克脂肪热量）= 60g

1.3计算食物分量
借助软件设计食谱

2.1设立减脂目标与预测减脂时间
目标103kg-75kg=28kg，54斤，每月减脂重量：体重的4%，103*0.05=5.15kg

2.2减脂目标28kg
每月最高减脂5.15kg，每周1.28kg
大概要花费 5个半月

3.1如何调整热量
记录每天早上体重，取固定日的体重和上周固定日体重对比，以此为依据调整热量摄入：
上下调整一个单位30g的碳水
每周日做未来一周的减脂餐，根据下月摄入食物总量制作

第一周向下减少一个单位碳水 第一周摄每日入碳蛋脂：307.5/202.5/60
碳水 307.5 * 7 = 2152.5g
蛋白质 202.5 * 7 = 1417.5g
脂肪 60 * 7 = 420g
```

完整业务逻辑请参见[业务逻辑参考.md](业务逻辑参考.md)。

## 项目状态

### ✅ Phase 1: 核心计算引擎（已完成）
- **基础代谢计算**：Mifflin-St Jeor公式实现
- **每日总能量消耗**：BMR + 训练消耗计算
- **营养分配**：5:3:2比例，碳水化合物调整机制
- **减脂时间预测**：基于体重变化率的智能预测
- **数据模型**：完整的Pydantic模型（UserProfile, WeightRecord, NutritionPlan, AppConfig）
- **单元测试**：核心计算引擎的完整测试套件

### ✅ Phase 2: 存储层与业务服务层（代码完成）
- **Repository抽象层**：BaseRepository、FilterableRepository、DateRangeRepository接口
- **SQLAlchemy ORM模型**：完整的数据库表结构定义
- **映射器模块**：Pydantic与SQLAlchemy模型双向转换
- **具体Repository实现**：User、Weight、Nutrition、Config的完整数据访问层
- **工作单元模式**：UnitOfWork、DatabaseContext，支持事务管理
- **Planner业务服务**：整合计算引擎与存储层的完整业务逻辑
- **集成测试模板**：Repository和Planner的测试框架

### ✅ Phase 2技术债务状态（更新于2026-03-09）

#### 已解决的技术债务 ✅
- **依赖安装**：✅ 虚拟环境已创建，依赖已安装
- **测试执行**：✅ 单元测试通过率100%，集成测试正常
- **数据库初始化**：✅ 完整CLI工具和Alembic迁移已实现

#### 当前技术债务 🔧
- **Pydantic V2迁移**：⚠️ 代码中使用已弃用的V1 API，产生弃用警告
- **数据库路径不一致**：⚠️ 默认URL与实际文件位置不统一
- **开发工具完整性**：🔍 需要验证mypy和pre-commit配置

详细技术债务跟踪请参见[TECH_DEBT.md](TECH_DEBT.md)。

### 🔄 下一步开发计划

#### Phase 2收尾（技术债务清理）
- **Pydantic V2迁移**：更新数据模型使用最新API（2-4小时）
- **开发工具完善**：验证mypy、pre-commit等工具链完整性（1-2小时）
- **配置统一**：修复数据库路径不一致问题（1小时）

#### Phase 3: CLI命令行接口实现（预计3天）
- 实现CLI命令结构
- 添加用户管理命令
- 添加体重记录命令
- 添加营养计划生成命令
- 添加进度查看命令

#### Phase 4: API服务层实现（预计3天）
- 实现FastAPI应用
- 创建RESTful API端点
- 添加API文档
- 实现认证和授权

#### Phase 5: Web界面实现（预计2天）
- 创建简单的Web界面
- 实现数据可视化
- 添加响应式设计

详细实施计划请参见[实施计划.md](实施计划.md)。

## 架构设计

项目采用分层架构：

```
用户界面层 (CLI/Web/Desktop)
    ↓
API服务层 (可选)
    ↓
业务服务层 (Planner)           ✅ 已完成
    ↓
核心计算引擎 (Calculator)      ✅ 已完成
    ↓
数据访问层 (Repository)        ✅ 已完成
    ↓
持久化层 (SQLite/PostgreSQL)   ✅ 模型完成
```

详细开发文档请参见[DEVELOPMENT.md](DEVELOPMENT.md)。

## 快速开始

### 环境要求
- Python 3.9+
- pip 或 poetry
- **注意**：当前系统可能需要安装python3-venv包

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd fatloss-planner

# 1. 创建虚拟环境（确保已安装python3-venv）
# 如果需要安装python3-venv：
# sudo apt update && sudo apt install python3.12-venv  # Ubuntu/Debian
python -m venv venv

# 2. 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖（开发环境包含所有工具）
pip install -e ".[dev]"

# 4. 验证安装
python -c "import pydantic; print(f'Pydantic版本: {pydantic.__version__}')"
python -c "import sqlalchemy; print(f'SQLAlchemy版本: {sqlalchemy.__version__}')"
```

### 环境配置

1. **数据库配置**：复制环境变量文件并设置数据库路径：
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，设置 DATABASE_URL（默认使用SQLite数据库）
   ```

2. **初始化数据库**：
   ```bash
   fatloss-db init  # 或 python scripts/init_db.py init
   ```

3. **运行测试**：
   ```bash
   pytest tests/unit/  # 运行单元测试
   pytest tests/integration/  # 运行集成测试
   ```

详细配置请参考[DEVELOPMENT.md](DEVELOPMENT.md)。

### 使用示例

```bash
# 计算基础热量和营养分配
fatloss-planner calculate --weight 70 --height 175 --age 30 --activity-level moderate --exercise-minutes 60

# 制定减脂计划
fatloss-planner plan --current-weight 103 --target-weight 75

# 调整营养计划
fatloss-planner adjust --weight-change -0.5
```

## 项目结构

```
fatloss-planner/
├── src/
│   └── fatloss/
│       ├── calculator/     # 核心计算引擎
│       ├── models/         # 数据模型
│       ├── repository/     # 数据访问层
│       ├── planner/        # 业务服务层
│       ├── cli/           # 命令行界面
│       └── api/           # Web API (可选)
├── tests/                  # 测试代码
├── docs/                  # 文档
├── pyproject.toml         # 项目配置
└── README.md
```

完整目录结构请参见[项目结构.txt](项目结构.txt)。

## 开发指南

### 运行测试
```bash
pytest tests/ --cov=src/fatloss --cov-report=html
```

### 代码检查
```bash
# 代码格式化
black src/ tests/
isort src/ tests/

# 代码检查
pylint src/
mypy src/
```

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

