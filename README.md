# demoRA - 悉尼房产智能推荐系统

🏡 **全澳洲最好用的AI找房软件**

## 项目简介

基于Claude AI的智能房产推荐系统，支持自然语言理解，为用户提供个性化的悉尼房源推荐。

### 核心功能

- 🤖 **智能语言理解**：支持"大一点的房子"、"离市区远"等口语化表达
- 🗺️ **地理智能分析**：内置悉尼各区域特征数据
- 🎯 **个性化推荐**：基于用户需求的智能匹配算法
- 📊 **17,938条真实房源数据**

### 在线体验

🚀 **部署到Streamlit Cloud**: [点击访问]()

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 设置API密钥
export ANTHROPIC_API_KEY=your_api_key_here

# 运行应用
streamlit run app.py
```

### 使用示例

- "我要个大一点的房子在Bondi，预算100万"
- "离市区远的地方，安静环境，2室"

- "海边的公寓，80万以内"

### 技术架构

- **前端**: Streamlit
- **AI引擎**: Claude-3.5-Sonnet
- **数据处理**: Pandas
- **部署**: Streamlit Cloud

---
### ⚠️免责声明

本项目仅用于技术学习和交流目的，爬虫脚本仅用于演示如何从公开网页中提取结构化信息。
请勿将该代码用于未经授权的商业用途，也请尊重目标网站的 robots.txt 协议与使用条款。

若您是站点所有者并对此内容有任何异议，请联系我们及时下架或调整。
**Made by Arthur and Ryan in whitemirror** | Powered by Claude AI
