# Sydney Property AI - API 文档

## 概述

悉尼房产AI推荐系统的API接口文档。本系统提供基于自然语言的智能房产推荐服务。

## 架构概览

```
Frontend (Streamlit UI)
    ↓
Backend Services
    ├── Intent Processor (AI)
    ├── Data Service
    ├── Recommendation Service
    └── Geo Analyzer
    ↓
Data Layer (CSV + Models)
```

## 核心服务

### 1. IntentProcessor - 用户意图处理器

**位置**: `ai/processors/intent_processor.py`

#### 类: `IntentProcessor`

##### 方法: `extract_intent(user_input: str) -> UserIntent`

**功能**: 从自然语言输入中提取用户意图

**参数**:
- `user_input` (str): 用户输入的自然语言文本

**返回**: `UserIntent` 对象，包含以下属性：
- `suburb` (str|None): 区域名称
- `bedrooms` (int|None): 卧室数量
- `budget` (float|None): 预算（万澳币）
- `size_preference` (str|None): 房屋大小偏好
- `location_preference` (str|None): 位置偏好
- `special_requirements` (List[str]): 特殊要求列表
- `inferred_needs` (List[str]): AI推测的隐含需求

**示例**:
```python
from ai.processors.intent_processor import intent_processor

intent = intent_processor.extract_intent("我要在Bondi找个2室的房子，预算100万")
print(intent.suburb)     # "Bondi"
print(intent.bedrooms)   # 2
print(intent.budget)     # 100.0
```

### 2. DataService - 数据服务

**位置**: `backend/services/data_service.py`

#### 类: `DataService`

##### 方法: `load_property_data() -> pd.DataFrame`

**功能**: 加载房产数据

**返回**: pandas DataFrame，包含所有房产数据

##### 方法: `filter_properties_flexible(intent: UserIntent, geo_analysis: dict = None) -> List[Property]`

**功能**: 基于用户意图灵活筛选房产

**参数**:
- `intent` (UserIntent): 用户意图对象
- `geo_analysis` (dict, 可选): 地理分析结果

**返回**: `Property` 对象列表

**筛选策略**:
1. 完全匹配所有条件
2. 放宽预算限制（+50%）
3. 仅匹配区域+卧室
4. 仅匹配区域
5. 仅匹配卧室
6. 仅匹配预算
7. 基于地理分析扩展搜索
8. 返回默认结果

##### 方法: `get_property_stats() -> dict`

**功能**: 获取房产数据统计信息

**返回**: 包含以下统计信息的字典：
- `total_properties`: 总房源数量
- `avg_price`: 平均价格
- `unique_suburbs`: 区域数量
- `property_types`: 房产类型分布

### 3. RecommendationService - 推荐服务

**位置**: `backend/services/recommendation_service.py`

#### 类: `RecommendationService`

##### 方法: `generate_recommendations(user_input: str, intent: UserIntent, geo_analysis: dict = None, intent_analysis: dict = None) -> List[str]`

**功能**: 生成个性化房产推荐

**参数**:
- `user_input` (str): 用户原始输入
- `intent` (UserIntent): 解析后的用户意图
- `geo_analysis` (dict, 可选): 地理分析结果
- `intent_analysis` (dict, 可选): 意图分析结果

**返回**: 推荐文本列表（3-5条）

**异常**:
- `ValueError`: API密钥未设置或无法解析用户偏好
- `RuntimeError`: 未找到匹配房源或API调用失败

## 数据模型

### UserIntent

```python
@dataclass
class UserIntent:
    suburb: Optional[str] = None
    bedrooms: Optional[int] = None
    budget: Optional[float] = None  # 万澳币
    property_type: Optional[str] = None
    size_preference: Optional[str] = None
    location_preference: Optional[str] = None
    distance_from_city: Optional[str] = None
    special_requirements: List[str] = None
    inferred_needs: List[str] = None
    priority_analysis: str = ""
```

### Property

```python
@dataclass
class Property:
    address: str
    suburb: str
    price: str
    price_numeric: Optional[float]
    bedrooms: int
    bathrooms: int
    parking: int
    property_type: str
    link: str
```

## 配置管理

### Settings

**位置**: `config/settings.py`

#### 核心配置项:

- `ANTHROPIC_API_KEY`: Claude AI API密钥
- `CLAUDE_MODEL`: AI模型版本 (claude-3-5-sonnet-20241022)
- `PROPERTY_DATA_FILE`: 房产数据文件路径
- `DEFAULT_RESULT_LIMIT`: 默认结果数量限制 (10)
- `BUDGET_RELAXATION_FACTOR`: 预算放宽系数 (1.5)

## 使用示例

### 完整推荐流程

```python
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from ai.processors.intent_processor import intent_processor
from backend.services.recommendation_service import recommendation_service

# 1. 提取用户意图
user_input = "我要在Bondi找个2室的房子，预算100万，要安静的环境"
intent = intent_processor.extract_intent(user_input)

# 2. 生成推荐
recommendations = recommendation_service.generate_recommendations(
    user_input=user_input,
    intent=intent
)

# 3. 显示结果
for i, rec in enumerate(recommendations, 1):
    print(f"{i}. {rec}")
```

### 数据查询示例

```python
from backend.services.data_service import data_service

# 获取统计信息
stats = data_service.get_property_stats()
print(f"总房源数量: {stats['total_properties']}")
print(f"平均价格: ${stats['avg_price']:,.0f}")

# 获取所有区域
suburbs = data_service.get_suburbs()
print(f"可选区域: {suburbs[:10]}")  # 显示前10个

# 筛选房源
from backend.models.property import UserIntent
intent = UserIntent(suburb="Bondi", bedrooms=2, budget=100)
properties = data_service.filter_properties_flexible(intent)
print(f"找到 {len(properties)} 套匹配房源")
```

## 错误处理

### 常见错误及解决方案

1. **API密钥未设置**
   ```
   ValueError: 请设置环境变量 ANTHROPIC_API_KEY
   ```
   解决：设置环境变量 `export ANTHROPIC_API_KEY=your_key`

2. **数据文件未找到**
   ```
   FileNotFoundError: 未找到房产数据文件
   ```
   解决：确保 `sydney_properties_working_final.csv` 文件存在

3. **无法解析用户偏好**
   ```
   ValueError: 无法解析用户偏好，请提供更多详细信息
   ```
   解决：提供更明确的搜索条件（区域、卧室、预算等）

## 日志记录

系统使用统一的日志记录，日志文件位于 `logs/` 目录：

- `app.log`: 应用程序日志
- `api.log`: API调用日志  
- `data.log`: 数据处理日志

日志级别可通过环境变量 `LOG_LEVEL` 设置（DEBUG, INFO, WARNING, ERROR）。

## 性能优化

### 缓存策略

- 数据服务自动缓存加载的DataFrame
- 重复查询时直接使用缓存，提高响应速度

### 筛选优化

- 多层次筛选策略，优先使用精确匹配
- 智能放宽条件，确保返回有意义的结果
- 结果数量控制，避免过载

## 扩展性

### 添加新的筛选条件

1. 在 `UserIntent` 模型中添加新字段
2. 在 `IntentProcessor` 中添加对应的提取逻辑
3. 在 `DataService.filter_properties_flexible()` 中添加筛选逻辑

### 集成新的AI模型

1. 继承或修改 `IntentProcessor` 类
2. 实现新的 `_extract_with_ai()` 方法
3. 更新配置中的模型设置

### 添加新的数据源

1. 扩展 `Property` 模型以支持新字段
2. 在 `DataService` 中添加新的加载方法
3. 更新筛选和推荐逻辑以处理新数据