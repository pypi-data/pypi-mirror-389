# MiniShare SDK

pip install minishare --upgrade

## 简介

MiniShare 是一个轻量级的金融数据API封装库，提供简洁易用的接口来获取股票、基金等金融数据。

## 安装

```bash
pip install minishare
```

## 快速开始

```python
import minishare as ms

# 设置API token
ms.set_token('your_token_here')

# 获取API客户端
pro = ms.pro_api()

# 获取日线数据
df = pro.daily(ts_code='000001.SZ', start_date='20230101', end_date='20231231')
print(df.head())

# 获取通用行情数据
df = ms.pro_bar(ts_code='000001.SZ', start_date='20230101', end_date='20231231')
print(df.head())
```

## 主要功能

- 支持多种金融数据API
- 简化的数据获取接口
- 自动错误处理和重试
- 缓存机制优化性能
- 设备ID管理防止滥用

## API参考

### 主要函数

- `set_token(token)`: 设置API token
- `pro_api(token=None)`: 获取Pro API客户端
- `pro_bar()`: 通用行情数据接口

### 数据接口

通过 `pro_api()` 获取的客户端支持以下主要接口：

- `daily()`: 日线行情
- `weekly()`: 周线行情
- `monthly()`: 月线行情
- `stk_mins()`: 分钟数据

## 许可证

MIT License
