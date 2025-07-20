"""
推荐结果组件
"""

import streamlit as st
from typing import List

def render_recommendations(recommendations: List[str]):
    """
    渲染推荐结果
    
    Args:
        recommendations: 推荐文本列表
    """
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
    render_feedback_section()

def render_feedback_section():
    """渲染反馈区域"""
    st.markdown("---")
    st.markdown("### 📝 这些推荐如何？")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("👍 很满意"):
            st.success("感谢您的反馈！")
    
    with col2:
        if st.button("🔄 重新推荐"):
            st.info("请尝试调整您的需求描述")