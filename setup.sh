#!/bin/bash

# 悉尼房产智能推荐系统环境设置脚本

echo "🏡 demoRA 环境设置向导"
echo "===================="

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

echo "✅ Python3: $(python3 --version)"

# 安装依赖
echo "📦 安装依赖包..."
pip3 install -r requirements.txt

# 检查API密钥配置
if [ -f ".env" ]; then
    if grep -q "paste_your_copied_key_here" .env; then
        echo ""
        echo "⚠️  需要配置API密钥:"
        echo "   1. 访问 https://console.anthropic.com"
        echo "   2. 获取您的Claude API密钥"
        echo "   3. 编辑 .env 文件，替换 'paste_your_copied_key_here'"
        echo ""
        echo "或者直接设置环境变量:"
        echo "   export ANTHROPIC_API_KEY='sk-ant-api03-your-key-here'"
    else
        echo "✅ API密钥配置文件已存在"
    fi
else
    echo "📝 创建 .env 配置文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件设置您的API密钥"
fi

echo ""
echo "🎯 设置完成! 使用以下命令启动应用:"
echo "   ./start.sh"
echo ""
echo "或手动启动:"
echo "   streamlit run app.py --server.port=8502"