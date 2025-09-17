@echo off
chcp 65001 >nul
title 澳洲租房聚合系统 - 本地开发环境

:: 颜色定义（Windows）
:: 使用PowerShell来显示彩色输出，但简化版本使用echo

echo.
echo 🏠 澳洲租房聚合系统 - 本地开发环境
echo =========================================
echo.

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装，请先安装 Python 3.9+
    pause
    exit /b 1
)

echo ✅ Python 已安装
python --version

:: 检查虚拟环境
if not exist "venv" (
    echo 🔧 创建虚拟环境...
    python -m venv venv
)

echo 🚀 激活虚拟环境...
call venv\Scripts\activate

echo 📦 安装/更新依赖...
pip install -r requirements.txt

:: 检查环境变量文件
if not exist ".env" (
    echo ⚠️ .env 文件不存在，从模板复制...
    copy .env.example .env
    echo 📝 请编辑 .env 文件设置你的配置（特别是 FIRECRAWL_API_KEY）
) else (
    echo ✅ .env 文件存在
)

:: 检查服务状态
echo 🔍 检查外部服务状态...

:: 检查PostgreSQL（简化版本）
netstat -an | find ":5432" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  PostgreSQL 未运行，将使用内存模式
    set PG_AVAILABLE=false
) else (
    echo ✅ PostgreSQL (端口 5432) 可用
    set PG_AVAILABLE=true
)

:: 检查Redis（简化版本）
netstat -an | find ":6379" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Redis 未运行，将跳过缓存功能
    set REDIS_AVAILABLE=false
) else (
    echo ✅ Redis (端口 6379) 可用
    set REDIS_AVAILABLE=true
)

:: 显示菜单
:menu
echo.
echo 请选择启动模式：
echo ==================
echo.
echo 1. 🚀 仅启动API服务 (默认 - 适合纯开发)
echo 2. 🐳 启动Docker完整环境 (PostgreSQL + Redis + API)
echo 3. 🗄️  仅启动数据库服务 (PostgreSQL + Redis)
echo 4. 🧪 运行API测试
echo 5. 📊 查看服务状态
echo 6. 🔧 重置环境
echo 0. ❌ 退出
echo.

set /p choice="请选择 (1-6, 0退出): "

if "%choice%"=="1" goto start_api
if "%choice%"=="2" goto start_docker
if "%choice%"=="3" goto start_db
if "%choice%"=="4" goto run_tests
if "%choice%"=="5" goto show_status
if "%choice%"=="6" goto reset_env
if "%choice%"=="0" goto exit
goto invalid_choice

:start_api
echo 🚀 启动FastAPI开发服务器...
echo 📋 服务信息:
echo    • API地址: http://localhost:8000
echo    • API文档: http://localhost:8000/docs
echo    • 健康检查: http://localhost:8000/health
echo.
echo 💡 提示: 按 Ctrl+C 停止服务
echo.
call venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
goto end

:start_docker
echo 🐳 启动Docker完整环境...

:: 检查Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker 未安装，请先安装 Docker
    pause
    goto menu
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose 未安装，请先安装 Docker Compose
    pause
    goto menu
)

echo 📋 启动服务: PostgreSQL + Redis + API...
docker-compose up -d

echo ✅ Docker环境启动完成！
echo 📋 服务信息:
echo    • API地址: http://localhost:8000
echo    • API文档: http://localhost:8000/docs
echo    • PostgreSQL: localhost:5432
echo    • Redis: localhost:6379
echo.
echo 🔍 查看日志: docker-compose logs -f
echo 🛑 停止服务: docker-compose down
pause
goto menu

:start_db
echo 🗄️  启动数据库服务...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose 未安装
    pause
    goto menu
)

docker-compose up -d postgres redis
echo ✅ 数据库服务启动完成！
echo    • PostgreSQL: localhost:5432
echo    • Redis: localhost:6379
pause
goto menu

:run_tests
echo 🧪 运行API测试...
call venv\Scripts\activate

:: 检查服务是否运行（简化版本）
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ❌ API服务未运行，请先启动服务
    pause
    goto menu
)

echo ✅ API服务正在运行
echo 📋 运行测试套件...

echo 1. 健康检查测试...
curl -s http://localhost:8000/health

echo.
echo 2. 房产搜索测试...
curl -s -X POST "http://localhost:8000/api/v1/properties/search" -H "Content-Type: application/json" -d "{\"location\": \"Sydney\", \"max_results\": 3}"

echo.
echo ✅ 测试完成！
pause
goto menu

:show_status
echo 📊 服务状态检查...

:: 检查API服务
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ❌ API服务 (端口 8000): 未运行
) else (
    echo ✅ API服务 (端口 8000): 运行中
)

:: 检查PostgreSQL
netstat -an | find ":5432" >nul 2>&1
if errorlevel 1 (
    echo ❌ PostgreSQL (端口 5432): 未运行
) else (
    echo ✅ PostgreSQL (端口 5432): 运行中
)

:: 检查Redis
netstat -an | find ":6379" >nul 2>&1
if errorlevel 1 (
    echo ❌ Redis (端口 6379): 未运行
) else (
    echo ✅ Redis (端口 6379): 运行中
)

:: 检查Docker
docker ps >nul 2>&1
if not errorlevel 1 (
    echo.
    echo 🐳 Docker容器状态:
    docker-compose ps 2>nul || echo Docker Compose 未运行
)

:: 检查CSV导出
if exist "csv_exports\*.csv" (
    for /f %%i in ('dir /b csv_exports\*.csv 2^>nul ^| find /c /v ""') do echo 📄 CSV导出文件: %%i 个
) else (
    echo 📄 CSV导出文件: 0 个
)

pause
goto menu

:reset_env
echo 🔧 重置开发环境...

echo 停止Docker服务...
docker-compose down 2>nul

echo 重置虚拟环境...
if exist "venv" rmdir /s /q venv
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt

echo 清理日志...
if exist "logs" (
    del /q logs\* 2>nul
)

echo ✅ 环境重置完成！
pause
goto menu

:invalid_choice
echo ❌ 无效选择，请重试
pause
goto menu

:exit
echo 👋 再见！
pause
exit /b 0

:end