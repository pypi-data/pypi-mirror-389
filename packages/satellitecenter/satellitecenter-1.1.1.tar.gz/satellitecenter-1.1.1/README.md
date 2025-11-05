# SatelliteCenter - 卫星中心自动化建模工具

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## 项目介绍

SatelliteCenter 是一个用于处理遥感数据的光谱与实测数据匹配和建模的自动化工具。

- **光谱数据处理**：支持卫星遥感和 UAV 多光谱数据处理
- **数据匹配**：自动匹配光谱数据与实测数据
- **模型建立**：基于匹配的数据进行统计建模
- **质量评估**：对模型结果进行质量评估和验证
- **报告生成**：自动生成执行日志和处理报告

## 系统要求

### 环境要求

- Python 3.12+
- pip 或 uv 包管理工具

### 安装

#### 方式 1: 使用 uv（推荐）

```bash
# 克隆仓库
git clone <repository-url>
cd SatelliteCenter

# 创建虚拟环境
uv venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 安装依赖
uv pip install -e ".[dev]"
```

#### 方式 2: 使用 pip

```bash
python -m pip install -e ".[dev]"
```

### 使用示例

#### 1. 命令行传参

```bash
python interface.py \
  --spectrum /path/to/spectrum.csv \
  --measure /path/to/measure.csv \
  --save_dir /path/to/output/
```

#### 2. JSON 格式输入

```bash
echo '{"spectrum":"/path/to/spectrum.csv","measure":["/path/to/measure.csv"],"save_dir":"/path/to/output/"}' | python interface.py
```

#### 3. 配置文件输入

```bash
echo "/path/to/config.json" | python interface.py
```

配置文件格式（`config.json`）

```json
{
  "spectrum": "/path/to/spectrum.csv",
  "measure": ["/path/to/measure.csv"],
  "save_dir": "/path/to/output/"
}
```

## 数据格式

### 光谱数据文件 (spectrum.csv)

| 列号 | 列名 | 说明 |
|----|------|------|
| 0 | 日期 | 采集日期（YYYY-MM-DD 格式） |
| 1 | 纬度 | 采样点纬度坐标 |
| 2 | 经度 | 采样点经度坐标 |
| 3-453 | 波长 | 450 个波段光谱反射率值 |
| 454+ | 指标 | 水质指标如 Chl-a、TSS 等 |

### 实测数据文件 (measure.csv)

| 列号 | 列名 | 说明 |
|----|------|------|
| 0 | 日期 | 采集日期（YYYY-MM-DD 格式） |
| 1 | 纬度 | 采样点纬度坐标 |
| 2 | 经度 | 采样点经度坐标 |
| 3+ | 指标 | 实测的水质指标值 |

## 处理流程

### 处理步骤

1. **步骤 1 数据读取**
   - 读取光谱和实测数据文件
   - 数据格式验证和清洗

2. **步骤 2 数据匹配**
   - 基于时空位置进行数据配对
   - 执行空间和时间容差检查

### 容差设置

- **空间容差**：0.01 至 1.1 km 范围
- 修改 `match_data()` 函数的 `spatial_tolerance` 参数

### 输出结果

处理完成后生成 DataFrame 包含以下内容：

```python
spectrum_wavelengths,  # 光谱波长，列 3-453
spectrum_indices,      # 光谱指标，列 455+
measure_data          # 实测数据，列 3+
```

## 日志和输出

### 执行日志文件

执行日志文件保存在 `save_dir` 指定目录下：

```
execution_YYYYMMDD_HHMMSS.log
```

例如：`execution_20251105_143045.log`

### 日志功能

- 记录完整的执行过程
- 输出数据处理的统计信息
- 记录错误和警告信息
- 保存模型验证结果

### 日志级别

- `DEBUG`：详细的调试信息
- `INFO`：一般信息
- `WARNING`：警告信息
- `ERROR`：错误信息

## 项目结构

```
src/satellitecenter/
   __init__.py                      # 包初始化
   main.py                          # 主程序入口
  config/
      __init__.py
      indicator_mapping.py         # 指标映射配置
   utils/
       __init__.py
       encryption.py                # 数据加密工具
       config_loader.py             # 配置文件加载器
       indicator_standardizer.py    # 指标标准化工具

tests/
   __init__.py
   conftest.py                      # pytest 配置
   test_format_band_name.py         # 波段名称测试
   test_indicator_standardizer.py   # 指标标准化测试
```

## 开发指南

### 安装开发依赖

```bash
# 安装所有开发工具
uv pip install -e ".[dev]"
```

### 代码检查

```bash
# 代码格式化
uv run black src/ tests/

# 代码检查
uv run ruff check src/ tests/ --fix

# 类型检查
uv run mypy src/
```

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 生成覆盖率报告
uv run pytest --cov=src --cov-report=html

# 运行特定测试
uv run pytest tests/test_format_band_name.py -v
```

### 提交检查清单

- [ ] 通过 `black` 代码格式化
- [ ] 通过 `ruff` 代码检查
- [ ] 通过 `mypy` 类型检查
- [ ] 测试覆盖率不低于 60%
- [ ] 更新相关文档

## 配置说明

### 指标映射配置 (indicator_mapping.py)

用于统一不同数据源的指标名称：

```python
from satellitecenter.config.indicator_mapping import INDICATOR_MAPPING

print(INDICATOR_MAPPING["Turb"])
# 输出: ['turbidity', '浊度', 'turb']
```

## 常见问题

### CSV 文件格式错误

**问题**：无法读取 CSV 文件
**解决**：确保文件使用 UTF-8 编码

### 数据匹配失败

**问题**：光谱数据和实测数据无法匹配
**解决**：调整 `spatial_tolerance` 参数

### 输出文件位置

**问题**：不知道输出文件在哪里
**解决**：检查 `save_dir` 指定的输出目录

## 依赖说明

### 核心依赖

- `pandas>=2.3.3`：数据处理和 CSV 操作
- `numpy>=2.3.4`：数值计算
- `autowaterqualitymodeler>=4.5.1`：水质建模工具

### 开发依赖

- `pytest`：单元测试框架
- `pytest-cov`：测试覆盖率统计
- `black`：代码格式化
- `ruff`：代码检查
- `mypy`：类型检查
- `isort`：导入排序
- `bandit`：安全检查
- `pip-audit`：依赖安全审计

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- **作者**：Your Name
- **邮箱**：your.email@example.com
- **Issue Tracker**：[GitHub Issues](https://github.com/yourusername/SatelliteCenter/issues)

## 贡献指南

欢迎提交 Pull Request 和 Issue！

1. Fork 本仓库
2. 创建分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

**最后更新**：2025-11-05
