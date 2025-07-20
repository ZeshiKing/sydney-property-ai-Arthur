# 安装依赖：
# pip install streamlit anthropic

import streamlit as st
import os
import re
from recommend_claude import explain_recommendation_flexible

# 页面配置
st.set_page_config(
    page_title="demoRA - 智能找房助手",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式 - 淡蓝色+米黄色专业配色
st.markdown("""
<style>
    /* 主背景色 - 米黄色 */
    .main {
        background-color: #FFF8DC;
    }
    
    /* 侧边栏背景 - 淡蓝色 */
    .css-1d391kg {
        background-color: #E6F3FF;
    }
    
    /* 标题样式 */
    .title-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0;
        border-bottom: 3px solid #4A90E2;
        margin-bottom: 2rem;
    }
    
    .main-title {
        color: #2C5F88;
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
    }
    
    .brand-logo {
        color: #4A90E2;
        font-size: 1.8rem;
        font-weight: bold;
        text-align: right;
    }
    
    .subtitle {
        color: #5A7A92;
        font-size: 1.1rem;
        margin-top: 0.5rem;
        font-style: italic;
    }
    
    /* 输入框样式 */
    .natural-input {
        background-color: #FFFFFF;
        border: 2px solid #4A90E2;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(74, 144, 226, 0.1);
    }
    
    /* 推荐卡片样式 */
    .recommendation-card {
        background-color: #FFFFFF;
        border-left: 4px solid #4A90E2;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(74, 144, 226, 0.15);
    }
    
    /* 按钮样式 */
    .stButton > button {
        background-color: #4A90E2;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #357ABD;
        box-shadow: 0 4px 8px rgba(74, 144, 226, 0.3);
    }
    
    /* 侧边栏样式 */
    .sidebar-content {
        background-color: #F0F8FF;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 获取 API Key
api_key = os.getenv('ANTHROPIC_API_KEY') or st.secrets.get('ANTHROPIC_API_KEY')

# 头部品牌区域
st.markdown("""
<div class="title-container">
    <div>
        <h1 class="main-title">🏡 智能找房助手</h1>
        <p class="subtitle">用自然语言描述您的需求，AI为您智能匹配最佳房源</p>
    </div>
    <div class="brand-logo">
        demoRA<br>
        <small style="font-size: 0.6em; color: #5A7A92;">全澳洲最好用的AI找房软件</small>
    </div>
</div>
""", unsafe_allow_html=True)

# 智能意图识别函数 - 使用Claude大模型理解多样化表达
def extract_intent_with_ai(user_input: str, api_key: str) -> dict:
    """
    使用Claude大模型智能识别用户意图，支持多样化表达方式
    """
    if not api_key:
        return extract_intent_fallback(user_input)
    
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        prompt = f"""
你是一个专业的房产需求分析师，请深度分析以下用户的房屋需求描述，提取并推理关键信息。

用户输入："{user_input}"

请分析以下维度：

1. **基础需求**：
   - 卧室：2室、2b、两个卧室、2bedroom、1b1b、2室1厅、双卧等
   - 区域：在Bondi、Bondi地区、邦迪、靠近Bondi、Bondi附近等
   - 预算：100万、100w、一百万、100万澳币、不超过100万、预算100万以内等

2. **口语化表达识别**：
   - 大小：大一点的、宽敞的、小巧的、紧凑的 → 推测面积需求
   - 位置：离市区远的、偏远的、郊外的、市中心的、繁华的
   - 环境：安静的、热闹的、便民的、偏僻的

3. **地理位置关系**：
   - 距离概念：离市区远、靠近海边、远离喧嚣、市中心附近
   - 交通便利：地铁沿线、公交方便、交通便利
   - 周边设施：学校附近、商圈周边、医院附近

4. **隐含需求推测**：
   - "大一点的" → 可能需要更多卧室或更大面积
   - "离市区远" → 可能预算有限，愿意牺牲便利换取性价比
   - "安静" → 可能需要住宅区而非商业区
   - "便民" → 可能需要生活设施齐全的区域

请以JSON格式返回分析结果：
{{
    "suburb": "具体区域名称或null",
    "bedrooms": 卧室数量(数字)或null,
    "budget": 预算万澳币(数字)或null,
    "size_preference": "大、中、小 或 null",
    "location_preference": "市中心、郊外、海边、安静区域 等或null",
    "distance_from_city": "近、中、远 或 null",
    "special_requirements": ["明确的特殊要求"],
    "inferred_needs": ["推测的隐含需求"],
    "priority_analysis": "用户最重视的因素分析"
}}

只返回JSON，不要其他文字。
"""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        import json
        result = json.loads(response.content[0].text.strip())
        
        # 确保返回格式正确
        return {
            "suburb": result.get("suburb"),
            "bedrooms": result.get("bedrooms"),
            "budget": result.get("budget"),
            "property_type": None,
            "size_preference": result.get("size_preference"),
            "location_preference": result.get("location_preference"),
            "distance_from_city": result.get("distance_from_city"),
            "special_requirements": result.get("special_requirements", []),
            "inferred_needs": result.get("inferred_needs", []),
            "priority_analysis": result.get("priority_analysis", "")
        }
        
    except Exception as e:
        print(f"AI意图识别失败，使用备用方案: {e}")
        return extract_intent_fallback(user_input)

# 备用意图识别函数（增强版正则表达式）
def extract_intent_fallback(user_input: str) -> dict:
    """
    备用意图识别 - 增强版正则表达式，支持更多表达方式
    """
    intent = {
        "suburb": None,
        "bedrooms": None,
        "budget": None,
        "property_type": None,
        "special_requirements": []
    }
    
    # 增强区域识别
    location_patterns = [
        r'在(.+?)区', r'在(.+?)地区', r'在(.+?)买', r'在(.+?)找', r'在(.+?)租',
        r'(.+?)区域', r'(.+?)附近', r'想住(.+?)', r'考虑(.+?)', r'靠近(.+?)',
        r'(.+?)地区', r'(.+?)那边', r'(.+?)周边'
    ]
    for pattern in location_patterns:
        match = re.search(pattern, user_input)
        if match:
            suburb = match.group(1).strip()
            # 清理常见后缀
            suburb = re.sub(r'(的房子|房源|地方|那里|那边)$', '', suburb)
            intent["suburb"] = suburb
            break
    
    # 增强卧室数量识别 - 支持多种表达方式
    bedroom_patterns = [
        r'(\d+)室', r'(\d+)房', r'(\d+)个卧室', r'(\d+)间卧室',
        r'(\d+)b\b', r'(\d+)bedroom', r'(\d+)bed',
        r'(\d+)室(\d+)厅', r'(\d+)b(\d+)b',  # 2室1厅, 1b1b格式
        r'(一|二|三|四|五)室', r'(一|二|三|四|五)个卧室',
        r'(\d+)\s*卧室', r'双卧', r'单卧'
    ]
    
    # 数字映射
    chinese_numbers = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '单': 1, '双': 2}
    
    for pattern in bedroom_patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            bedroom_str = match.group(1)
            if bedroom_str in chinese_numbers:
                intent["bedrooms"] = chinese_numbers[bedroom_str]
            elif bedroom_str.isdigit():
                intent["bedrooms"] = int(bedroom_str)
            break
    
    # 增强预算识别
    budget_patterns = [
        r'预算(\d+)万', r'(\d+)万以内', r'(\d+)万澳币', r'(\d+)w\b',
        r'最多(\d+)万', r'不超过(\d+)万', r'(\d+)万左右', r'(\d+)万预算',
        r'(\d+)万到(\d+)万', r'(\d+)-(\d+)万', r'(\d+)万以下',
        r'(一|二|三|四|五|六|七|八|九|十)百万', r'(\d+)百万'
    ]
    
    for pattern in budget_patterns:
        match = re.search(pattern, user_input)
        if match:
            if len(match.groups()) >= 2 and match.group(2):  # 范围预算，取上限
                intent["budget"] = float(match.group(2))
            else:
                budget_str = match.group(1)
                # 处理中文数字
                if budget_str in ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']:
                    budget_map = {'一': 100, '二': 200, '三': 300, '四': 400, '五': 500, 
                                '六': 600, '七': 700, '八': 800, '九': 900, '十': 1000}
                    intent["budget"] = budget_map.get(budget_str, 100)
                elif budget_str.isdigit():
                    intent["budget"] = float(budget_str)
            break
    
    # 增强特殊要求识别
    special_keywords = {
        "安静": "环境安静", "静": "环境安静", "安静环境": "环境安静",
        "交通": "交通便利", "地铁": "交通便利", "公交": "交通便利", "交通方便": "交通便利",
        "学校": "靠近学校", "学区": "靠近学校", "教育": "靠近学校", "好学校": "靠近学校",
        "海边": "海景房", "海景": "海景房", "海滩": "海景房", "海": "海景房",
        "新房": "新建房屋", "新": "新建房屋", "新建": "新建房屋", "新装修": "新建房屋",
        "停车": "停车位", "车位": "停车位", "停车场": "停车位", "garage": "停车位",
        "花园": "带花园", "院子": "带花园", "outdoor": "带花园", "户外": "带花园",
        "阳台": "带阳台", "balcony": "带阳台", "露台": "带阳台"
    }
    
    for keyword, description in special_keywords.items():
        if keyword in user_input.lower():
            if description not in intent["special_requirements"]:
                intent["special_requirements"].append(description)
    
    return intent

# 主要内容区域
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 💬 告诉我们您的理想房屋")
    
    # 处理示例输入
    if "example_input" in st.session_state:
        default_value = st.session_state["example_input"]
        del st.session_state["example_input"]
    else:
        default_value = ""
    
    # 自然语言输入框
    user_input = st.text_area(
        "描述您的需求",
        placeholder="支持口语化表达：我要个大一点的房子 / 离市区远的地方 / 安静的环境 / 海边的房子 / 便民的地方 / 100w以内的郊外房...",
        height=120,
        key="user_input",
        label_visibility="hidden",
        value=default_value
    )
    
    # 快速示例按钮
    st.markdown("**💡 快速示例：**")
    example_col1, example_col2, example_col3 = st.columns(3)
    
    with example_col1:
        if st.button("🏖️ 海边公寓"):
            st.session_state["example_input"] = "我要个1b的海边房子在Bondi，80w预算"
            st.rerun()
    
    with example_col2:
        if st.button("🏡 郊外大房"):
            st.session_state["example_input"] = "想要个离市区远一点的大房子，安静的环境，预算120万"
            st.rerun()
    
    with example_col3:
        if st.button("🎓 学区房"):
            st.session_state["example_input"] = "2b的房子，Hornsby附近，120万以内，学区要好"
            st.rerun()

with col2:
    st.markdown("### 🔍 智能解析")
    
    if user_input:
        intent = extract_intent_with_ai(user_input, api_key)
        
        # 地理分析
        from geo_analyzer import SydneyGeoAnalyzer
        geo_analyzer = SydneyGeoAnalyzer()
        geo_analysis = geo_analyzer.comprehensive_analysis(user_input, intent)
        
        st.markdown("**🎯 基础需求识别：**")
        
        if intent["suburb"]:
            st.info(f"🏘️ 区域：{intent['suburb']}")
        
        if intent["bedrooms"]:
            st.info(f"🛏️ 卧室：{intent['bedrooms']}室")
        
        if intent["budget"]:
            st.info(f"💰 预算：{intent['budget']}万澳币")
        
        # 显示新的分析结果
        if intent.get("size_preference"):
            st.info(f"📐 房屋大小偏好：{intent['size_preference']}")
        
        if intent.get("location_preference"):
            st.info(f"📍 位置偏好：{intent['location_preference']}")
        
        if intent.get("distance_from_city"):
            st.info(f"🚗 距离市中心：{intent['distance_from_city']}")
        
        if intent["special_requirements"]:
            st.info(f"✨ 明确要求：{', '.join(intent['special_requirements'])}")
        
        # 显示推测的隐含需求
        if intent.get("inferred_needs"):
            st.markdown("**🧠 AI推测的隐含需求：**")
            for need in intent["inferred_needs"]:
                st.success(f"💡 {need}")
        
        # 显示优先级分析
        if intent.get("priority_analysis"):
            st.markdown("**📊 需求优先级分析：**")
            st.write(intent["priority_analysis"])
        
        # 显示地理位置分析
        if geo_analysis["location_analysis"]["recommended_areas"]:
            st.markdown("**🗺️ 推荐区域：**")
            areas = geo_analysis["location_analysis"]["recommended_areas"][:5]
            st.write(f"🎯 {', '.join(areas)}")
        
        # 显示搜索策略
        if geo_analysis["comprehensive_recommendations"]["search_strategy"]:
            st.markdown("**🔍 搜索策略：**")
            st.write(geo_analysis["comprehensive_recommendations"]["search_strategy"])
        
        # 智能推荐按钮
        if st.button("🚀 获取AI推荐", type="primary", use_container_width=True):
            if intent["suburb"] or intent["bedrooms"] or intent["budget"]:  # 只要有任一条件即可
                # 显示加载状态
                with st.spinner("🤖 AI正在为您精选最佳房源..."):
                    try:
                        # 调用增强的推荐函数
                        recommendations = explain_recommendation_flexible(
                            user_input, 
                            intent["suburb"], 
                            intent["bedrooms"], 
                            intent["budget"], 
                            api_key,
                            geo_analysis,
                            {"size_analysis": geo_analyzer.analyze_size_preference(user_input, intent)}
                        )
                        
                        # 在主区域显示推荐结果
                        with col1:
                            st.markdown("---")
                            st.markdown("### 🎯 AI精选推荐")
                            
                            for i, rec in enumerate(recommendations, 1):
                                st.markdown(f"""
                                <div class="recommendation-card">
                                    <h4>🏠 推荐 {i}</h4>
                                    <p>{rec}</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # 添加反馈区域
                            st.markdown("---")
                            st.markdown("### 📝 这些推荐如何？")
                            feedback_col1, feedback_col2 = st.columns(2)
                            
                            with feedback_col1:
                                if st.button("👍 很满意"):
                                    st.success("感谢您的反馈！")
                            
                            with feedback_col2:
                                if st.button("🔄 重新推荐"):
                                    st.info("请尝试调整您的需求描述")
                                    
                    except ValueError as e:
                        st.error(f"❌ 配置错误: {e}")
                        if "无法解析用户偏好" in str(e):
                            st.info("💡 请确保输入完整的偏好信息")
                        else:
                            st.info("💡 请确保已设置环境变量 ANTHROPIC_API_KEY")
                        
                    except RuntimeError as e:
                        st.error(f"❌ API 调用失败: {e}")
                        
                    except FileNotFoundError as e:
                        st.error(f"❌ 数据文件错误: {e}")
                        st.info("💡 请确保 sydney_properties_working_final.csv 文件存在")
                        
                    except Exception as e:
                        st.error(f"❌ 未知错误: {e}")
            else:
                st.warning("⚠️ 请描述您的房屋需求（区域、卧室数量、预算等任意条件）")

# 侧边栏功能
with st.sidebar:
    st.markdown("### 🎯 使用指南")
    st.markdown("""
    <div class="sidebar-content">
        <h4>📝 如何使用</h4>
        <ol>
            <li>用自然语言描述您的理想房屋</li>
            <li>查看AI智能解析的需求</li>
            <li>点击获取AI推荐</li>
            <li>浏览精选房源推荐</li>
        </ol>
        
        <h4>💡 多样化表达</h4>
        <ul>
            <li><strong>区域：</strong>Bondi、在Chatswood买、Hornsby那边、靠近Parramatta、离市区远的</li>
            <li><strong>卧室：</strong>2室、2b、2bedroom、双卧、2室1厅、1b1b</li>
            <li><strong>预算：</strong>100万、100w、一百万澳币、不超过150万</li>
            <li><strong>大小：</strong>大一点的、宽敞的、小巧的、紧凑的</li>
            <li><strong>距离：</strong>离市区远、郊外、市中心、靠近海边</li>
            <li><strong>环境：</strong>安静、热闹、便民、偏僻、远离喧嚣</li>
        </ul>
        
        <h4>🌟 智能识别示例</h4>
        <ul>
            <li>"我要个大一点的房子" → AI推测需要更多卧室</li>
            <li>"离市区远的地方" → AI推荐外环区域</li>
            <li>"安静的环境" → AI筛选住宅区</li>
            <li>"便民的地方" → AI重点推荐交通便利区域</li>
            <li>"海边的房子" → AI推荐海滨区域</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### ⚙️ 系统状态")
    
    # API Key 状态
    if api_key and api_key != "your_api_key_here":
        st.success("✅ AI服务已连接")
    else:
        st.error("❌ 请配置API Key")
        with st.expander("配置说明"):
            st.code("export ANTHROPIC_API_KEY=your_key")
    
    # 数据状态
    try:
        import pandas as pd
        df = pd.read_csv('sydney_properties_working_final.csv')
        st.success(f"✅ 房源数据已载入 ({len(df):,}条)")
    except:
        st.error("❌ 房源数据未找到")

# 页面底部
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #5A7A92; padding: 2rem 0;">
    <p><strong>demoRA</strong> - 让找房变得简单智能</p>
    <p><em>Powered by Claude AI • Made with ❤️ in Australia</em></p>
</div>
""", unsafe_allow_html=True)