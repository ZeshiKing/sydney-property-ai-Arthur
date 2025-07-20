#!/usr/bin/env python3
"""
系统状态检查脚本
"""

def check_system_status():
    """检查系统各组件状态"""
    print("🏡 demoRA 系统状态检查")
    print("=" * 30)
    
    success_count = 0
    total_checks = 6
    
    # 检查Python模块
    modules_to_check = [
        ("streamlit", "Streamlit Web框架"),
        ("anthropic", "Claude AI客户端"),
        ("pandas", "数据处理"),
        ("dotenv", "环境变量管理")
    ]
    
    for module, description in modules_to_check:
        try:
            __import__(module)
            print(f"✅ {description}: OK")
            success_count += 1
        except ImportError:
            print(f"❌ {description}: 缺失 - 请运行 pip install {module}")
    
    # 检查数据文件
    try:
        import pandas as pd
        df = pd.read_csv('sydney_properties_working_final.csv')
        print(f"✅ 房源数据: OK ({len(df)}条记录)")
        success_count += 1
    except Exception as e:
        print(f"❌ 房源数据: {e}")
    
    # 检查API密钥配置
    import os
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        pass
        
    if os.getenv('ANTHROPIC_API_KEY') and 'paste_your' not in os.getenv('ANTHROPIC_API_KEY', ''):
        print("✅ API密钥: 已配置")
        success_count += 1
    else:
        print("⚠️  API密钥: 需要配置")
        print("   请设置环境变量或编辑.env文件")
    
    print(f"\n📊 系统状态: {success_count}/{total_checks} 检查通过")
    
    if success_count == total_checks:
        print("🎉 系统完全就绪！")
        return True
    else:
        print("⚠️  请解决上述问题后重试")
        return False

if __name__ == "__main__":
    check_system_status()