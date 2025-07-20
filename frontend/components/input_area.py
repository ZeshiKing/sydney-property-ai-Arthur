"""
用户输入区域组件
"""

import streamlit as st
from typing import Optional

def render_input_area() -> Optional[str]:
    """
    渲染用户输入区域
    
    Returns:
        用户输入的文本
    """
    st.markdown("### 💬 告诉我们您的理想房屋")
    
    # 处理示例输入
    default_value = ""
    if "example_input" in st.session_state:
        default_value = st.session_state["example_input"]
        del st.session_state["example_input"]
    
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
    render_example_buttons()
    
    return user_input.strip() if user_input else None

def render_example_buttons():
    """渲染示例按钮"""
    st.markdown("**💡 快速示例：**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🏖️ 海边公寓"):
            st.session_state["example_input"] = "我要个1b的海边房子在Bondi，80w预算"
            st.rerun()
    
    with col2:
        if st.button("🏡 郊外大房"):
            st.session_state["example_input"] = "想要个离市区远一点的大房子，安静的环境，预算120万"
            st.rerun()
    
    with col3:
        if st.button("🎓 学区房"):
            st.session_state["example_input"] = "2b的房子，Hornsby附近，120万以内，学区要好"
            st.rerun()