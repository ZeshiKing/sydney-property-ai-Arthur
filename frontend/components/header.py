"""
页面头部组件
"""

import streamlit as st

def render_header():
    """渲染页面头部"""
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