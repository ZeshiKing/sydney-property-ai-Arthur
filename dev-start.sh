#!/bin/bash

# 澳洲租房聚合系统 - 本地开发启动脚本
# 支持多种启动模式，适合本地开发使用

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示logo
echo -e "${BLUE}"
echo "🏠 澳洲租房聚合系统 - 本地开发环境"
echo "========================================="
echo -e "${NC}"

# 检查Python版本
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 未安装，请先安装 Python 3.9+${NC}"
        exit 1
    fi

    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo -e "${GREEN}✅ Python版本: $python_version${NC}"
}

# 检查虚拟环境
setup_venv() {
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}🔧 创建虚拟环境...${NC}"
        python3 -m venv venv
    fi

    echo -e "${GREEN}🚀 激活虚拟环境...${NC}"
    source venv/bin/activate

    echo -e "${YELLOW}📦 安装/更新依赖...${NC}"
    pip install -r requirements.txt
}

# 检查环境变量文件
check_env() {
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠️  .env 文件不存在，从模板复制...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}📝 请编辑 .env 文件设置你的配置（特别是 FIRECRAWL_API_KEY）${NC}"
    else
        echo -e "${GREEN}✅ .env 文件存在${NC}"
    fi
}

# 检查数据库连接
check_services() {
    echo -e "${BLUE}🔍 检查外部服务状态...${NC}"

    # 检查PostgreSQL
    if nc -z localhost 5432 2>/dev/null; then
        echo -e "${GREEN}✅ PostgreSQL (端口 5432) 可用${NC}"
        PG_AVAILABLE=true
    else
        echo -e "${YELLOW}⚠️  PostgreSQL 未运行，将使用内存模式${NC}"
        PG_AVAILABLE=false
    fi

    # 检查Redis
    if nc -z localhost 6379 2>/dev/null; then
        echo -e "${GREEN}✅ Redis (端口 6379) 可用${NC}"
        REDIS_AVAILABLE=true
    else
        echo -e "${YELLOW}⚠️  Redis 未运行，将跳过缓存功能${NC}"
        REDIS_AVAILABLE=false
    fi
}

# 显示启动选项
show_menu() {
    echo -e "${BLUE}"
    echo "请选择启动模式："
    echo "=================="
    echo -e "${NC}"
    echo "1. 🚀 仅启动API服务 (默认 - 适合纯开发)"
    echo "2. 🐳 启动Docker完整环境 (PostgreSQL + Redis + API)"
    echo "3. 🗄️  仅启动数据库服务 (PostgreSQL + Redis)"
    echo "4. 🧪 运行API测试"
    echo "5. 📊 查看服务状态"
    echo "6. 🔧 重置环境"
    echo "0. ❌ 退出"
    echo ""
}

# 仅启动API服务
start_api_only() {
    echo -e "${GREEN}🚀 启动FastAPI开发服务器...${NC}"
    echo -e "${BLUE}📋 服务信息:${NC}"
    echo "   • API地址: http://localhost:8000"
    echo "   • API文档: http://localhost:8000/docs"
    echo "   • 健康检查: http://localhost:8000/health"
    echo ""
    echo -e "${YELLOW}💡 提示: 按 Ctrl+C 停止服务${NC}"
    echo ""

    # 激活虚拟环境并启动
    source venv/bin/activate
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

# 启动Docker完整环境
start_docker_full() {
    echo -e "${GREEN}🐳 启动Docker完整环境...${NC}"

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安装，请先安装 Docker${NC}"
        return 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose 未安装，请先安装 Docker Compose${NC}"
        return 1
    fi

    echo -e "${YELLOW}📋 启动服务: PostgreSQL + Redis + API...${NC}"
    docker-compose up -d

    echo -e "${GREEN}✅ Docker环境启动完成！${NC}"
    echo -e "${BLUE}📋 服务信息:${NC}"
    echo "   • API地址: http://localhost:8000"
    echo "   • API文档: http://localhost:8000/docs"
    echo "   • PostgreSQL: localhost:5432"
    echo "   • Redis: localhost:6379"
    echo ""
    echo "🔍 查看日志: docker-compose logs -f"
    echo "🛑 停止服务: docker-compose down"
}

# 仅启动数据库服务
start_db_only() {
    echo -e "${GREEN}🗄️  启动数据库服务...${NC}"

    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose 未安装${NC}"
        return 1
    fi

    docker-compose up -d postgres redis
    echo -e "${GREEN}✅ 数据库服务启动完成！${NC}"
    echo "   • PostgreSQL: localhost:5432"
    echo "   • Redis: localhost:6379"
}

# 运行API测试
run_tests() {
    echo -e "${GREEN}🧪 运行API测试...${NC}"

    # 激活虚拟环境
    source venv/bin/activate

    # 检查服务是否运行
    if curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✅ API服务正在运行${NC}"
    else
        echo -e "${RED}❌ API服务未运行，请先启动服务${NC}"
        return 1
    fi

    echo -e "${BLUE}📋 运行测试套件...${NC}"

    # 健康检查测试
    echo "1. 健康检查测试..."
    curl -s http://localhost:8000/health | jq .

    # 详细健康检查
    echo -e "\n2. 详细健康检查..."
    curl -s http://localhost:8000/api/v1/health/ | jq .

    # 房产搜索测试
    echo -e "\n3. 房产搜索测试..."
    curl -s -X POST "http://localhost:8000/api/v1/properties/search" \
         -H "Content-Type: application/json" \
         -d '{"location": "Sydney", "max_results": 3}' | jq .

    # 支持区域测试
    echo -e "\n4. 支持区域测试..."
    curl -s http://localhost:8000/api/v1/properties/locations | jq .

    echo -e "\n${GREEN}✅ 测试完成！${NC}"
}

# 查看服务状态
show_status() {
    echo -e "${BLUE}📊 服务状态检查...${NC}"

    # 检查API服务
    if curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✅ API服务 (端口 8000): 运行中${NC}"
    else
        echo -e "${RED}❌ API服务 (端口 8000): 未运行${NC}"
    fi

    # 检查PostgreSQL
    if nc -z localhost 5432 2>/dev/null; then
        echo -e "${GREEN}✅ PostgreSQL (端口 5432): 运行中${NC}"
    else
        echo -e "${RED}❌ PostgreSQL (端口 5432): 未运行${NC}"
    fi

    # 检查Redis
    if nc -z localhost 6379 2>/dev/null; then
        echo -e "${GREEN}✅ Redis (端口 6379): 运行中${NC}"
    else
        echo -e "${RED}❌ Redis (端口 6379): 未运行${NC}"
    fi

    # 检查Docker服务
    if command -v docker &> /dev/null; then
        echo -e "${BLUE}\n🐳 Docker容器状态:${NC}"
        docker-compose ps 2>/dev/null || echo "Docker Compose 未运行"
    fi

    # 检查CSV导出
    if [ -d "csv_exports" ]; then
        csv_count=$(ls csv_exports/*.csv 2>/dev/null | wc -l)
        echo -e "${BLUE}\n📄 CSV导出文件: ${csv_count} 个${NC}"
    fi
}

# 重置环境
reset_env() {
    echo -e "${YELLOW}🔧 重置开发环境...${NC}"

    # 停止所有服务
    echo "停止Docker服务..."
    docker-compose down 2>/dev/null || true

    # 重新创建虚拟环境
    echo "重置虚拟环境..."
    rm -rf venv
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

    # 清理日志
    echo "清理日志..."
    rm -rf logs/*

    echo -e "${GREEN}✅ 环境重置完成！${NC}"
}

# 主函数
main() {
    # 基础检查
    check_python
    setup_venv
    check_env
    check_services

    # 如果有参数，直接执行对应操作
    case $1 in
        "api"|"1")
            start_api_only
            ;;
        "docker"|"2")
            start_docker_full
            ;;
        "db"|"3")
            start_db_only
            ;;
        "test"|"4")
            run_tests
            ;;
        "status"|"5")
            show_status
            ;;
        "reset"|"6")
            reset_env
            ;;
        *)
            # 交互式菜单
            while true; do
                show_menu
                read -p "请选择 (1-6, 0退出): " choice

                case $choice in
                    1)
                        start_api_only
                        break
                        ;;
                    2)
                        start_docker_full
                        break
                        ;;
                    3)
                        start_db_only
                        break
                        ;;
                    4)
                        run_tests
                        ;;
                    5)
                        show_status
                        ;;
                    6)
                        reset_env
                        ;;
                    0)
                        echo -e "${GREEN}👋 再见！${NC}"
                        exit 0
                        ;;
                    *)
                        echo -e "${RED}❌ 无效选择，请重试${NC}"
                        ;;
                esac

                if [ "$choice" != "4" ] && [ "$choice" != "5" ] && [ "$choice" != "6" ]; then
                    break
                fi

                echo ""
                read -p "按回车键继续..."
                clear
            done
            ;;
    esac
}

# 执行主函数
main "$@"