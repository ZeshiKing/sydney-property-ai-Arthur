"""
页面底部组件
"""

import streamlit as st

def render_footer():
    """渲染页面底部"""
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #5A7A92; padding: 2rem 0;">
        <p><strong>demoRA</strong> - 让找房变得简单智能</p>
        <p><em>Powered by Claude AI • Made with ❤️ in Australia</em></p>
    </div>
    """, unsafe_allow_html=True)