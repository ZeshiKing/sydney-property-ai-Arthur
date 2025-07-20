"""
应用主题和样式配置
"""

# 应用主色调配置
THEME_CONFIG = {
    "primary_color": "#4A90E2",
    "secondary_color": "#FFF8DC", 
    "accent_color": "#357ABD",
    "text_color": "#2C5F88",
    "light_bg": "#E6F3FF",
    "sidebar_bg": "#F0F8FF"
}

# CSS样式定义
APP_STYLES = """
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
    
    /* 状态指示器样式 */
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
</style>
"""