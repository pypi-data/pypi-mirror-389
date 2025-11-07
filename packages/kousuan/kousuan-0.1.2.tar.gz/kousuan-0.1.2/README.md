# Kousuan Skill

一个提供口算计算技巧的Python包，帮助提高心算能力和数学计算技巧。

## 功能特性

- 基础四则运算
- 快速加法技巧
- 快速乘法技巧
- 数字分解
- 百分比计算
- 乘法表生成
- 心算技巧集合

## 安装

```bash
pip install kousuan
```

## 使用方法

### 命令行工具

```bash
# 加法
kousuan calc "15+17"
```

### Python API

```python
from kousuan.core import resolve

results = resolve('13*17')

```

## 心算技巧

本包包含多种心算技巧，包括：

- **乘以11的技巧**：两位数乘以11时，将两个数字相加，结果放在中间
- **乘以5的技巧**：乘以10再除以2
- **乘以9的技巧**：乘以10再减去原数
- **以5结尾的数字平方**：将前一位数字乘以(前一位数字+1)，后面加上25
- **百分比计算**：计算10%时，将小数点左移一位

## 开发

### 安装开发依赖

```bash
pip install -e .[dev]
```

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black kousuan/
flake8 kousuan/
```

## 许可证

MIT License

## 作者

liandong