"""
智能分析面板组件
"""

import streamlit as st
from typing import Dict, Any, Optional

def render_analysis_panel(intent: Dict[str, Any], geo_analysis: Optional[Dict] = None):
    """
    渲染智能分析面板
    
    Args:
        intent: 用户意图分析结果
        geo_analysis: 地理分析结果
    """
    st.markdown("### 🔍 智能解析")
    
    # 基础需求识别
    st.markdown("**🎯 基础需求识别：**")
    
    if intent.get("suburb"):
        st.info(f"🏘️ 区域：{intent['suburb']}")
    
    if intent.get("bedrooms"):
        st.info(f"🛏️ 卧室：{intent['bedrooms']}室")
    
    if intent.get("budget"):
        st.info(f"💰 预算：{intent['budget']}万澳币")
    
    # AI深度分析结果
    if intent.get("size_preference"):
        st.info(f"📐 房屋大小偏好：{intent['size_preference']}")
    
    if intent.get("location_preference"):
        st.info(f"📍 位置偏好：{intent['location_preference']}")
    
    if intent.get("distance_from_city"):
        st.info(f"🚗 距离市中心：{intent['distance_from_city']}")
    
    if intent.get("special_requirements"):
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
    if geo_analysis and geo_analysis.get("location_analysis", {}).get("recommended_areas"):
        st.markdown("**🗺️ 推荐区域：**")
        areas = geo_analysis["location_analysis"]["recommended_areas"][:5]
        st.write(f"🎯 {', '.join(areas)}")
    
    # 显示搜索策略
    if geo_analysis and geo_analysis.get("comprehensive_recommendations", {}).get("search_strategy"):
        st.markdown("**🔍 搜索策略：**")
        st.write(geo_analysis["comprehensive_recommendations"]["search_strategy"])