#!/bin/bash

# 悉尼房产智能推荐系统启动脚本

echo "🏡 demoRA - 悉尼房产智能推荐系统"
echo "================================="

# 检查.env文件是否存在且配置正确
if [ -f ".env" ]; then
    if grep -q "paste_your_copied_key_here" .env; then
        echo "⚠️  请先设置您的API密钥:"
        echo "   1. 编辑 .env 文件"
        echo "   2. 将 'paste_your_copied_key_here' 替换为您的Claude API密钥"
        echo "   3. 重新运行此脚本"
        echo ""
        echo "或者使用环境变量:"
        echo "   export ANTHROPIC_API_KEY='your_api_key_here'"
        echo "   ./start.sh"
        exit 1
    fi
    echo "✅ 发现 .env 配置文件"
    source .env
else
    echo "⚠️  未找到 .env 文件，请确保设置了环境变量 ANTHROPIC_API_KEY"
fi

# 检查API密钥是否设置
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ 未设置 ANTHROPIC_API_KEY"
    echo "请运行: export ANTHROPIC_API_KEY='your_api_key_here'"
    exit 1
fi

echo "✅ API密钥已配置"

# 检查依赖
echo "📦 检查依赖..."
pip install -r requirements.txt --quiet

# 启动应用
echo "🚀 启动应用..."
echo "📱 本地访问: http://localhost:8502"
echo "🌐 局域网访问: http://$(ipconfig getifaddr en0):8502"
echo ""
echo "按 Ctrl+C 停止应用"

streamlit run app.py --server.port=8502 --server.address=0.0.0.0