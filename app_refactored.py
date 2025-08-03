"""
重构后的主应用文件
采用模块化架构，分离UI组件和业务逻辑
"""

import streamlit as st
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入配置和样式
from config.settings import settings
from frontend.styles.theme import APP_STYLES

# 导入UI组件
from frontend.components.header import render_header
from frontend.components.input_area import render_input_area
from frontend.components.analysis_panel import render_analysis_panel
from frontend.components.recommendations import render_recommendations
from frontend.components.sidebar import render_sidebar
from frontend.components.footer import render_footer

# 导入业务服务
from backend.services.data_service import data_service
from backend.utils.logger import app_logger

# 导入AI服务（待重构）
try:
    from recommend_claude import explain_recommendation_flexible
    from geo_analyzer import SydneyGeoAnalyzer
except ImportError as e:
    app_logger.error(f"Failed to import legacy modules: {e}")
    st.error("无法加载AI服务模块，请检查依赖")
    st.stop()

def extract_intent_with_ai(user_input: str, api_key: str) -> dict:
    """
    使用Claude大模型智能识别用户意图
    TODO: 重构为独立的AI服务模块
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
            model=settings.CLAUDE_MODEL,
            max_tokens=settings.MAX_TOKENS,
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
        app_logger.error(f"AI意图识别失败: {e}")
        return extract_intent_fallback(user_input)

def extract_intent_fallback(user_input: str) -> dict:
    """
    备用意图识别函数
    TODO: 重构为独立的NLP服务模块
    """
    import re
    
    intent = {
        "suburb": None,
        "bedrooms": None,
        "budget": None,
        "property_type": None,
        "special_requirements": []
    }
    
    # 区域识别
    location_patterns = [
        r'在(.+?)区', r'在(.+?)地区', r'在(.+?)买', r'在(.+?)找',
        r'(.+?)区域', r'(.+?)附近', r'想住(.+?)', r'考虑(.+?)',
        r'(.+?)地区', r'(.+?)那边', r'(.+?)周边'
    ]
    for pattern in location_patterns:
        match = re.search(pattern, user_input)
        if match:
            suburb = match.group(1).strip()
            suburb = re.sub(r'(的房子|房源|地方|那里|那边)$', '', suburb)
            intent["suburb"] = suburb
            break
    
    # 卧室数量识别
    bedroom_patterns = [
        r'(\d+)室', r'(\d+)房', r'(\d+)个卧室', r'(\d+)间卧室',
        r'(\d+)b\b', r'(\d+)bedroom', r'(\d+)bed'
    ]
    for pattern in bedroom_patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            intent["bedrooms"] = int(match.group(1))
            break
    
    # 预算识别
    budget_patterns = [
        r'预算(\d+)万', r'(\d+)万以内', r'(\d+)万澳币',
        r'最多(\d+)万', r'不超过(\d+)万', r'(\d+)万左右'
    ]
    for pattern in budget_patterns:
        match = re.search(pattern, user_input)
        if match:
            intent["budget"] = float(match.group(1))
            break
    
    return intent

def main():
    """主应用函数"""
    # 页面配置
    st.set_page_config(**settings.STREAMLIT_CONFIG)
    
    # 应用样式
    st.markdown(APP_STYLES, unsafe_allow_html=True)
    
    # 验证配置
    if not settings.validate():
        st.error("⚠️ 系统配置检查失败，请检查API密钥和数据文件")
        st.stop()
    
    # 获取API密钥
    api_key = settings.ANTHROPIC_API_KEY or st.secrets.get('ANTHROPIC_API_KEY')
    
    # 渲染页面头部
    render_header()
    
    # 主要内容区域
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 用户输入区域
        user_input = render_input_area()
        
        if user_input:
            # 处理用户输入
            try:
                # AI意图识别
                intent = extract_intent_with_ai(user_input, api_key)
                app_logger.info(f"User intent extracted: {intent}")
                
                # 地理分析
                geo_analyzer = SydneyGeoAnalyzer()
                geo_analysis = geo_analyzer.comprehensive_analysis(user_input, intent)
                
                # 在右侧显示分析结果
                with col2:
                    render_analysis_panel(intent, geo_analysis)
                
                # 推荐按钮和结果显示
                if st.button("🚀 获取AI推荐", type="primary", use_container_width=True):
                    if intent["suburb"] or intent["bedrooms"] or intent["budget"]:
                        with st.spinner("🤖 AI正在为您精选最佳房源..."):
                            try:
                                # 调用推荐服务
                                recommendations = explain_recommendation_flexible(
                                    user_input, 
                                    intent["suburb"], 
                                    intent["bedrooms"], 
                                    intent["budget"], 
                                    api_key,
                                    geo_analysis,
                                    {"size_analysis": geo_analyzer.analyze_size_preference(user_input, intent)}
                                )
                                
                                # 显示推荐结果
                                render_recommendations(recommendations)
                                app_logger.info(f"Generated {len(recommendations)} recommendations")
                                
                            except Exception as e:
                                app_logger.error(f"Recommendation generation failed: {e}")
                                st.error(f"❌ 推荐生成失败: {e}")
                    else:
                        st.warning("⚠️ 请描述您的房屋需求（区域、卧室数量、预算等任意条件）")
            
            except Exception as e:
                app_logger.error(f"Error processing user input: {e}")
                st.error(f"❌ 处理用户输入时发生错误: {e}")
    
    # 渲染侧边栏
    render_sidebar()
    
    # 渲染页面底部
    render_footer()

if __name__ == "__main__":
    main()