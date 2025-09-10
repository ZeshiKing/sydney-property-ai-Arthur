# 数据结构文档

## 📊 澳洲租房聚合系统数据格式说明

### 🏠 完整数据结构概览

本系统从Domain.com.au抓取的房产数据采用标准化的JSON格式，确保数据的一致性和可用性。

## 🔍 搜索查询结构 (searchQuery)

```typescript
interface SearchQuery {
  location: {
    suburb: string;        // 街区名称，如 "Camperdown"
    state: string;         // 州名，如 "NSW"  
    postcode: string;      // 邮编，如 "2050"
  };
  listingType: "rent" | "buy";           // 租赁或购买
  propertyType: "apartment" | "house" | "townhouse" | "unit";
  bedrooms?: {
    min?: number;          // 最少卧室数
    max?: number;          // 最多卧室数
  };
  bathrooms?: {
    min?: number;          // 最少浴室数
    max?: number;          // 最多浴室数
  };
  priceRange?: {
    min?: number;          // 最低价格
    max?: number;          // 最高价格
  };
  searchUrl: string;       // 构建的Domain.com.au搜索URL
}
```

## 📋 搜索结果结构 (searchResults)

### 总体信息
```typescript
interface SearchResults {
  totalProperties: number;              // 找到的房产总数
  priceRange: {
    min: number;                        // 最低价格
    max: number;                        // 最高价格  
    unit: "per week" | "per month";     // 价格周期
    currency: "AUD";                    // 货币单位
  };
  bedroomDistribution: string[];        // 卧室数量分布，如["2", "3"]
  properties: Property[];               // 房产列表
}
```

### 🏡 单个房产数据结构 (Property)

```typescript
interface Property {
  id: string;                          // 房产唯一标识符
  
  // 价格信息
  price: {
    amount: number;                     // 价格数额，如 940
    period: "per week" | "per month";   // 计费周期
    currency: "AUD";                    // 货币
    displayText: string;                // 显示文本，如 "$940 per week"
  };
  
  // 房产基本信息
  bedrooms: number;                     // 卧室数量
  bathrooms: number;                    // 浴室数量  
  parkingSpaces: number;                // 停车位数量
  propertyType: string;                 // 房产类型
  listingType: string;                  // 列表类型
  
  // 地址信息
  address: {
    streetNumber?: string;              // 门牌号
    streetName: string;                 // 街道名
    suburb: string;                     // 街区
    state: string;                      // 州
    postcode: string;                   // 邮编
    fullAddress: string;                // 完整地址
  };
  
  // 房产特色
  features: {
    furnished?: boolean | null;         // 是否带家具
    petFriendly?: boolean | null;       // 是否允许宠物
    parking: boolean;                   // 是否有停车位
    balcony?: boolean | null;           // 是否有阳台
    airConditioning?: boolean | null;   // 是否有空调
  };
  
  // 媒体资源
  images: string[];                     // 房产图片URL数组
  
  // 中介信息
  agency: {
    name: string;                       // 中介公司名称
    logo?: string;                      // 中介公司Logo URL
  };
  
  // 元数据
  extractedAt: string;                  // 数据抓取时间 (ISO 8601)
  source: string;                       // 数据来源，如 "domain.com.au"
}
```

## 📈 元数据结构 (metadata)

```typescript
interface Metadata {
  searchTimestamp: string;              // 搜索时间戳
  processingTime: number;               // 处理时间（毫秒）
  dataSource: string;                   // 数据源
  extractionMethod: string;             // 抓取方法
  totalCharacters: number;              // 原始数据字符数
  apiVersion: string;                   // API版本
  cacheStatus: "hit" | "miss";          // 缓存状态
  
  // 位置相关数据
  locationData?: {
    coordinates: {
      latitude: number;                 // 纬度
      longitude: number;                // 经度
    };
    nearbySuburbs: string[];            // 附近街区
    publicTransport: string[];          // 公共交通信息
    schools: string[];                  // 附近学校
    shopping: string[];                 // 购物中心
  };
}
```

## 🔢 实际数据样本

### 价格范围示例：
- **最低**: $875/周 (2卧1卫，Wilson Street)
- **最高**: $2000/周 (高端公寓)  
- **平均**: $1100-1300/周 (2-3卧公寓)

### 常见房产类型：
- **Apartment**: 公寓 (最常见)
- **Unit**: 单元房
- **House**: 独栋房屋
- **Townhouse**: 联排别墅

### 地址格式示例：
```
51/46 Dunblane Street, Camperdown NSW 2050
[单元号]/[门牌号] [街道名], [街区] [州] [邮编]
```

## 🔧 API响应格式

### 成功响应 (200 OK)
```json
{
  "success": true,
  "data": {
    // 完整的SearchResults结构
  },
  "message": "搜索完成",
  "timestamp": "2025-09-10T10:45:00Z"
}
```

### 错误响应 (400/500)
```json
{
  "success": false,
  "error": {
    "code": "SEARCH_FAILED",
    "message": "搜索失败：API配额不足",
    "details": "Firecrawl API返回402错误"
  },
  "timestamp": "2025-09-10T10:45:00Z"
}
```

## 📊 数据质量指标

### 当前系统表现：
- **提取准确率**: >95% (价格、卧室、地址)
- **数据完整性**: ~85% (部分特色信息可能缺失)
- **处理速度**: 3-5秒/搜索
- **平均房产数量**: 15-25个/搜索

### 数据来源可靠性：
- ✅ **价格**: 高度准确
- ✅ **卧室/浴室数**: 高度准确  
- ✅ **地址**: 高度准确
- ⚠️ **房产特色**: 中等准确 (依赖原始描述)
- ⚠️ **中介信息**: 中等准确 (部分缺失)

## 🚀 使用示例

### API调用示例：
```bash
curl -X POST http://localhost:3000/api/properties/search \
  -H "Content-Type: application/json" \
  -d '{
    "listingType": "rent",
    "location": {
      "suburb": "Camperdown",
      "state": "NSW",
      "postcode": "2050"
    },
    "propertyType": "apartment",
    "bedrooms": {"min": 2}
  }'
```

### 前端使用示例 (JavaScript):
```javascript
const response = await fetch('/api/properties/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    listingType: 'rent',
    location: { suburb: 'Camperdown', state: 'NSW', postcode: '2050' },
    bedrooms: { min: 2 }
  })
});

const data = await response.json();
console.log(`找到${data.data.totalProperties}套房产`);
```

---

**💡 提示**: 这个数据结构设计支持未来扩展更多房产网站（如realestate.com.au），保持了良好的可扩展性和标准化格式。