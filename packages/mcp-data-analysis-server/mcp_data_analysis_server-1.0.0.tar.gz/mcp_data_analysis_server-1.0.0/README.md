# Data Analysis MCP (Python)

一个基于 Model Context Protocol 的数据分析服务器，使用 Python 开发。

## 功能特性

- 📊 数据统计分析（均值、中位数、标准差等）
- 📈 数据可视化（生成图表）
- 🔍 数据探索（查看数据摘要、缺失值等）
- 📉 趋势分析
- 📋 支持 CSV、Excel、JSON 等格式

## 技术栈

- Python 3.8+
- pandas
- numpy
- matplotlib
- seaborn

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行

```bash
python main.py
```

## MCP 工具列表

### 1. load-data
加载数据文件
- 支持 CSV、Excel、JSON 格式

### 2. describe-data
获取数据摘要统计
- 行列数
- 数据类型
- 缺失值统计
- 基本统计量

### 3. analyze-column
分析特定列的数据
- 唯一值数量
- 频率分布
- 数值统计

### 4. correlation-analysis
相关性分析
- 计算变量间相关系数
- 生成相关性矩阵

### 5. generate-chart
生成数据可视化图表
- 柱状图
- 折线图
- 散点图
- 箱线图

## 开发

```bash
python main.py
```

## 许可证

MIT

