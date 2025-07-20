"""
侧边栏组件
"""

import streamlit as st
import pandas as pd
from pathlib import Path

def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        render_usage_guide()
        st.markdown("---")
        render_system_status()

def render_usage_guide():
    """渲染使用指南"""
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

def render_system_status():
    """渲染系统状态"""
    st.markdown("### ⚙️ 系统状态")
    
    # API Key 状态
    api_key = st.secrets.get('ANTHROPIC_API_KEY') if hasattr(st, 'secrets') else None
    if not api_key:
        import os
        api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if api_key and api_key != "your_api_key_here":
        st.markdown('<p class="status-success">✅ AI服务已连接</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="status-error">❌ 请配置API Key</p>', unsafe_allow_html=True)
        with st.expander("配置说明"):
            st.code("export ANTHROPIC_API_KEY=your_key")
    
    # 数据状态
    try:
        data_file = Path("sydney_properties_working_final.csv")
        if data_file.exists():
            df = pd.read_csv(data_file)
            st.markdown(f'<p class="status-success">✅ 房源数据已载入 ({len(df):,}条)</p>', 
                       unsafe_allow_html=True)
        else:
            st.markdown('<p class="status-error">❌ 房源数据未找到</p>', unsafe_allow_html=True)
    except Exception as e:
        st.markdown('<p class="status-error">❌ 数据加载失败</p>', unsafe_allow_html=True)