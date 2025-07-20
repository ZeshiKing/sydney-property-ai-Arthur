# 房产爬虫系统

这是一个用于爬取澳大利亚房产网站（realestate.com.au 和 domain.com.au）数据的 Python 爬虫系统。

## 功能特点

- 支持爬取 realestate.com.au 和 domain.com.au 两个网站
- 多种运行模式：单次运行、定时任务、交互式选择
- 智能反爬虫机制：随机User-Agent、代理池、请求间隔
- 数据清理和去重功能
- 自动生成摘要报告
- 支持数据合并和分析

## 项目结构

```
realestate_crawler/
├── config.py              # 配置文件（代理池、User-Agent等）
├── realestate_spider.py    # realestate.com.au 爬虫
├── domain_spider.py        # domain.com.au 爬虫
├── scheduler.py           # 定时任务模块
├── save_utils.py          # 数据保存和处理工具
├── run_all.py             # 主程序入口
├── requirements.txt       # 依赖包列表
└── README.md             # 说明文档
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 交互式模式（推荐）

```bash
python run_all.py
```

然后按照提示选择要执行的操作。

### 2. 命令行模式

```bash
# 运行所有爬虫
python run_all.py --mode all

# 只运行 realestate.com.au 爬虫
python run_all.py --mode realestate

# 只运行 domain.com.au 爬虫
python run_all.py --mode domain

# 启动定时任务
python run_all.py --mode schedule

# 设置最大页数和请求间隔
python run_all.py --mode all --pages 10 --delay 3
```

### 3. 单独运行爬虫

```bash
# 运行 realestate.com.au 爬虫
python realestate_spider.py

# 运行 domain.com.au 爬虫
python domain_spider.py

# 运行定时任务
python scheduler.py
```

## 配置说明

在 `config.py` 中可以配置：

- **代理池**：添加代理服务器以避免IP被封
- **User-Agent池**：随机切换浏览器标识
- **请求配置**：超时时间、重试次数、请求间隔
- **搜索配置**：最大页数、每页项目数、搜索URL

## 数据格式

爬取的数据包含以下字段：

- `price`: 原始价格字符串
- `price_numeric`: 数值型价格
- `address`: 完整地址
- `suburb`: 区域名称
- `bedrooms`: 卧室数量
- `bathrooms`: 浴室数量
- `parking`: 停车位数量
- `property_type`: 房产类型
- `link`: 原始链接
- `source`: 数据来源

## 定时任务

系统支持以下定时任务：

- 每天早上 9:00 运行
- 每天下午 6:00 运行
- 每周一早上 8:00 运行

可以在 `scheduler.py` 中修改定时设置。

## 数据处理

- **自动去重**：基于链接去除重复数据
- **数据清理**：移除异常价格和无效数据
- **数据合并**：支持合并多个CSV文件
- **摘要报告**：自动生成统计报告

## 注意事项

1. **遵守robots.txt**：请检查目标网站的robots.txt文件
2. **合理设置间隔**：避免过于频繁的请求
3. **代理配置**：如需要，请配置有效的代理服务器
4. **数据使用**：仅用于学习和研究目的

## 错误处理

- 自动重试机制
- 详细的日志记录
- 优雅的错误处理

## 数据存储

- 数据保存在 `data/` 目录下
- 支持CSV格式导出
- 自动按时间戳命名文件

## 许可证

本项目仅用于学习和研究目的，请遵守相关法律法规和网站使用条款。