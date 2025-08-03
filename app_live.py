# Enhanced app with Live Property Recommendations
# pip install streamlit anthropic aiohttp beautifulsoup4

import streamlit as st
import os
import re
import asyncio
import sys
from datetime import datetime

# Add backend path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import live recommendation engine
from backend.services.live_recommendation_engine import LiveRecommendationEngine

# Try to load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Page configuration
st.set_page_config(
    page_title="demoRA Live - 智能找房助手",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styles with live data indicators
st.markdown("""
<style>
    /* Main background - cream */
    .main {
        background-color: #FFF8DC;
    }
    
    /* Sidebar background - light blue */
    .css-1d391kg {
        background-color: #E6F3FF;
    }
    
    /* Title styles */
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
    
    /* Live data indicator */
    .live-indicator {
        background: linear-gradient(90deg, #4CAF50, #45a049);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: bold;
        display: inline-block;
        margin: 0.5rem 0;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    /* Input styles */
    .natural-input {
        background-color: #FFFFFF;
        border: 2px solid #4A90E2;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(74, 144, 226, 0.1);
    }
    
    /* Recommendation card styles */
    .recommendation-card {
        background-color: #FFFFFF;
        border-left: 4px solid #4A90E2;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(74, 144, 226, 0.15);
    }
    
    .live-recommendation-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 8px;
        box-shadow: 0 3px 10px rgba(40, 167, 69, 0.2);
    }
    
    /* Button styles */
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
    
    /* Sidebar styles */
    .sidebar-content {
        background-color: #F0F8FF;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    /* Performance metrics */
    .metrics-container {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize live recommendation engine
@st.cache_resource
def initialize_live_engine():
    """Initialize the live recommendation engine with caching."""
    api_key = os.getenv('ANTHROPIC_API_KEY') or st.secrets.get('ANTHROPIC_API_KEY')
    return LiveRecommendationEngine(
        api_key=api_key,
        cache_ttl_minutes=30,
        enable_fallback_to_static=True
    )

# Get API Key
api_key = os.getenv('ANTHROPIC_API_KEY') or st.secrets.get('ANTHROPIC_API_KEY')

# Header brand area
st.markdown("""
<div class="title-container">
    <div>
        <h1 class="main-title">🏡 智能找房助手</h1>
        <p class="subtitle">使用实时数据和AI为您智能匹配最佳房源</p>
        <div class="live-indicator">🔴 实时数据 LIVE</div>
    </div>
    <div class="brand-logo">
        demoRA Live<br>
        <small style="font-size: 0.6em; color: #5A7A92;">全澳洲最先进的AI实时找房系统</small>
    </div>
</div>
""", unsafe_allow_html=True)

# Enhanced intent extraction with AI (keeping the existing function)
def extract_intent_with_ai(user_input: str, api_key: str) -> dict:
    """Use Claude AI to understand diverse expressions (keeping original logic)"""
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
        print(f"AI intent extraction failed, using fallback: {e}")
        return extract_intent_fallback(user_input)

# Fallback intent extraction (keeping original logic)
def extract_intent_fallback(user_input: str) -> dict:
    """Enhanced fallback intent recognition with regex patterns"""
    intent = {
        "suburb": None,
        "bedrooms": None,
        "budget": None,
        "property_type": None,
        "special_requirements": []
    }
    
    # Enhanced area recognition
    location_patterns = [
        r'在(.+?)区', r'在(.+?)地区', r'在(.+?)买', r'在(.+?)找', r'在(.+?)租',
        r'(.+?)区域', r'(.+?)附近', r'想住(.+?)', r'考虑(.+?)', r'靠近(.+?)',
        r'(.+?)地区', r'(.+?)那边', r'(.+?)周边'
    ]
    for pattern in location_patterns:
        match = re.search(pattern, user_input)
        if match:
            suburb = match.group(1).strip()
            suburb = re.sub(r'(的房子|房源|地方|那里|那边)$', '', suburb)
            intent["suburb"] = suburb
            break
    
    # Enhanced bedroom number recognition
    bedroom_patterns = [
        r'(\d+)室', r'(\d+)房', r'(\d+)个卧室', r'(\d+)间卧室',
        r'(\d+)b\b', r'(\d+)bedroom', r'(\d+)bed',
        r'(\d+)室(\d+)厅', r'(\d+)b(\d+)b',
        r'(一|二|三|四|五)室', r'(一|二|三|四|五)个卧室',
        r'(\d+)\s*卧室', r'双卧', r'单卧'
    ]
    
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
    
    # Enhanced budget recognition
    budget_patterns = [
        r'预算(\d+)万', r'(\d+)万以内', r'(\d+)万澳币', r'(\d+)w\b',
        r'最多(\d+)万', r'不超过(\d+)万', r'(\d+)万左右', r'(\d+)万预算',
        r'(\d+)万到(\d+)万', r'(\d+)-(\d+)万', r'(\d+)万以下',
        r'(一|二|三|四|五|六|七|八|九|十)百万', r'(\d+)百万'
    ]
    
    for pattern in budget_patterns:
        match = re.search(pattern, user_input)
        if match:
            if len(match.groups()) >= 2 and match.group(2):
                intent["budget"] = float(match.group(2))
            else:
                budget_str = match.group(1)
                if budget_str in ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']:
                    budget_map = {'一': 100, '二': 200, '三': 300, '四': 400, '五': 500, 
                                '六': 600, '七': 700, '八': 800, '九': 900, '十': 1000}
                    intent["budget"] = budget_map.get(budget_str, 100)
                elif budget_str.isdigit():
                    intent["budget"] = float(budget_str)
            break
    
    # Special requirements recognition
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

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 💬 告诉我们您的理想房屋")
    
    # Handle example inputs
    if "example_input" in st.session_state:
        default_value = st.session_state["example_input"]
        del st.session_state["example_input"]
    else:
        default_value = ""
    
    # Natural language input
    user_input = st.text_area(
        "描述您的需求",
        placeholder="支持口语化表达：我要个大一点的房子 / 离市区远的地方 / 安静的环境 / 海边的房子 / 便民的地方 / 100w以内的郊外房...",
        height=120,
        key="user_input",
        label_visibility="hidden",
        value=default_value
    )
    
    # Quick example buttons
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
        
        # Geographic analysis
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
        
        # Show new analysis results
        if intent.get("size_preference"):
            st.info(f"📐 房屋大小偏好：{intent['size_preference']}")
        
        if intent.get("location_preference"):
            st.info(f"📍 位置偏好：{intent['location_preference']}")
        
        if intent.get("distance_from_city"):
            st.info(f"🚗 距离市中心：{intent['distance_from_city']}")
        
        if intent["special_requirements"]:
            st.info(f"✨ 明确要求：{', '.join(intent['special_requirements'])}")
        
        # Show inferred needs
        if intent.get("inferred_needs"):
            st.markdown("**🧠 AI推测的隐含需求：**")
            for need in intent["inferred_needs"]:
                st.success(f"💡 {need}")
        
        # Show priority analysis
        if intent.get("priority_analysis"):
            st.markdown("**📊 需求优先级分析：**")
            st.write(intent["priority_analysis"])
        
        # Show geographical analysis
        if geo_analysis["location_analysis"]["recommended_areas"]:
            st.markdown("**🗺️ 推荐区域：**")
            areas = geo_analysis["location_analysis"]["recommended_areas"][:5]
            st.write(f"🎯 {', '.join(areas)}")
        
        # Show search strategy
        if geo_analysis["comprehensive_recommendations"]["search_strategy"]:
            st.markdown("**🔍 搜索策略：**")
            st.write(geo_analysis["comprehensive_recommendations"]["search_strategy"])
        
        # Live recommendation button
        if st.button("🚀 获取实时AI推荐", type="primary", use_container_width=True):
            if intent["suburb"] or intent["bedrooms"] or intent["budget"]:
                # Show loading state
                with st.spinner("🔴 正在获取实时房源数据并进行AI分析..."):
                    try:
                        # Initialize live engine
                        live_engine = initialize_live_engine()
                        
                        # Get live recommendations
                        async def get_recommendations():
                            return await live_engine.get_live_recommendations(
                                user_input=user_input,
                                user_intent=intent,
                                geo_analysis=geo_analysis,
                                max_recommendations=5,
                                include_alternatives=True
                            )
                        
                        # Run async function
                        result = asyncio.run(get_recommendations())
                        
                        # Display results in main area
                        with col1:
                            st.markdown("---")
                            
                            # Show data source indicator
                            if result['metadata']['data_source'] == 'live':
                                st.markdown("""
                                <div style="background: linear-gradient(90deg, #28a745, #20c997); color: white; padding: 0.5rem 1rem; border-radius: 10px; margin-bottom: 1rem; text-align: center;">
                                    🔴 实时数据 • 数据获取时间: """ + datetime.now().strftime("%H:%M:%S") + """
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.warning("⚠️ 实时数据获取失败，显示缓存数据作为备选")
                            
                            st.markdown("### 🎯 AI实时推荐")
                            
                            # Show recommendations
                            for i, rec in enumerate(result['recommendations'], 1):
                                st.markdown(f"""
                                <div class="live-recommendation-card">
                                    <h4>🏠 实时推荐 {i}</h4>
                                    <p>{rec}</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # Show analysis if available
                            if result.get('analysis'):
                                st.markdown("### 📊 市场分析")
                                st.info(result['analysis'])
                            
                            # Show suggestions
                            if result.get('suggestions'):
                                st.markdown("### 💡 搜索优化建议")
                                for suggestion in result['suggestions']:
                                    st.write(f"• {suggestion}")
                            
                            # Show performance metrics
                            metadata = result['metadata']
                            
                            st.markdown("### 📈 处理信息")
                            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                            
                            with metrics_col1:
                                st.markdown("""
                                <div class="metrics-container">
                                    <strong>数据获取</strong><br>
                                    搜索网站: """ + str(metadata.get('search_urls_generated', 0)) + """<br>
                                    处理时间: """ + str(metadata.get('processing_time_ms', 0)) + """ms
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with metrics_col2:
                                properties_data = result.get('properties_data', {})
                                st.markdown("""
                                <div class="metrics-container">
                                    <strong>房源数据</strong><br>
                                    发现房源: """ + str(properties_data.get('total_raw', 0)) + """<br>
                                    去重后: """ + str(properties_data.get('total_found', 0)) + """
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with metrics_col3:
                                fetch_data = metadata.get('fetch_results', {})
                                st.markdown("""
                                <div class="metrics-container">
                                    <strong>网站状态</strong><br>
                                    成功: """ + str(fetch_data.get('successful_fetches', 0)) + """<br>
                                    失败: """ + str(fetch_data.get('failed_fetches', 0)) + """
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # Feedback area
                            st.markdown("---")
                            st.markdown("### 📝 这些推荐如何？")
                            feedback_col1, feedback_col2 = st.columns(2)
                            
                            with feedback_col1:
                                if st.button("👍 很满意"):
                                    st.success("感谢您的反馈！实时推荐系统会持续改进")
                            
                            with feedback_col2:
                                if st.button("🔄 重新搜索"):
                                    st.info("请尝试调整您的需求描述或搜索条件")
                    
                    except Exception as e:
                        st.error(f"❌ 实时推荐系统错误: {e}")
                        st.info("💡 系统可能正在维护，请稍后重试或联系技术支持")
            else:
                st.warning("⚠️ 请描述您的房屋需求（区域、卧室数量、预算等任意条件）")

# Enhanced sidebar
with st.sidebar:
    st.markdown("### 🎯 实时系统指南")
    st.markdown("""
    <div class="sidebar-content">
        <h4>🔴 实时数据特性</h4>
        <ul>
            <li><strong>多源数据：</strong>同时搜索 Domain、RealEstate、Rent 等主流网站</li>
            <li><strong>智能去重：</strong>自动识别和合并重复房源</li>
            <li><strong>即时更新：</strong>显示最新价格和可用性</li>
            <li><strong>AI增强：</strong>基于实时数据的个性化分析</li>
        </ul>
        
        <h4>📝 使用步骤</h4>
        <ol>
            <li>用自然语言描述您的理想房屋</li>
            <li>查看AI智能解析和需求识别</li>
            <li>点击"获取实时AI推荐"</li>
            <li>浏览基于最新数据的推荐</li>
        </ol>
        
        <h4>💡 表达方式示例</h4>
        <ul>
            <li><strong>区域：</strong>Bondi、在Chatswood买、Hornsby那边、靠近Parramatta、离市区远的</li>
            <li><strong>卧室：</strong>2室、2b、2bedroom、双卧、2室1厅、1b1b</li>
            <li><strong>预算：</strong>100万、100w、一百万澳币、不超过150万</li>
            <li><strong>大小：</strong>大一点的、宽敞的、小巧的、紧凑的</li>
            <li><strong>距离：</strong>离市区远、郊外、市中心、靠近海边</li>
            <li><strong>环境：</strong>安静、热闹、便民、偏僻、远离喧嚣</li>
        </ul>
        
        <h4>🌟 AI智能识别</h4>
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
    
    # API Key status
    if api_key and api_key != "your_api_key_here":
        st.success("✅ AI服务已连接")
    else:
        st.error("❌ 请配置API Key")
        with st.expander("配置说明"):
            st.code("export ANTHROPIC_API_KEY=your_key")
    
    # Live data status
    try:
        live_engine = initialize_live_engine()
        st.success("✅ 实时数据系统已就绪")
        
        # Show engine metrics if available
        if hasattr(live_engine, 'metrics'):
            metrics = live_engine.get_performance_metrics()
            if metrics['total_requests'] > 0:
                st.info(f"📊 处理请求: {metrics['total_requests']} | 平均响应: {metrics['average_response_time']:.2f}s")
    except Exception as e:
        st.warning(f"⚠️ 实时数据系统: {str(e)}")
    
    # Static data fallback status
    try:
        import pandas as pd
        df = pd.read_csv('sydney_properties_working_final.csv')
        st.success(f"✅ 备用数据已载入 ({len(df):,}条)")
    except:
        st.error("❌ 备用数据未找到")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #5A7A92; padding: 2rem 0;">
    <p><strong>demoRA Live</strong> - 全澳洲最先进的AI实时找房系统</p>
    <p><em>Powered by Claude AI • Real-time Data • Made with ❤️ in Australia</em></p>
    <p style="font-size: 0.8em;">🔴 实时数据源: Domain.com.au • RealEstate.com.au • Rent.com.au</p>
</div>
""", unsafe_allow_html=True)