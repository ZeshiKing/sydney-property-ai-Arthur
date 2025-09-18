#!/usr/bin/env python3
"""
API测试脚本
测试智能推荐和普通搜索功能
"""

import asyncio
import json
import time
import httpx
from typing import Optional

BASE_URL = "http://localhost:3000"

async def test_health():
    """测试健康检查"""
    print("🔍 测试健康检查...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("✅ 健康检查通过")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False

async def test_openai_connection():
    """测试OpenAI连接"""
    print("🤖 测试OpenAI API连接...")
    
    # 简单的解析测试
    test_data = {
        "query": "Looking for a 2 bedroom apartment in Sydney, budget $800 per week"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/properties/recommend",
                json=test_data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✅ OpenAI API连接正常")
                    print(f"   解析结果包含: {len(result.get('properties', []))} 个房产")
                    return True
                else:
                    print(f"❌ API调用失败: {result.get('message', '未知错误')}")
                    return False
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   错误详情: {error_detail}")
                except:
                    print(f"   响应内容: {response.text[:200]}")
                return False
                
        except httpx.TimeoutException:
            print("❌ 请求超时 (30秒)")
            return False
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return False

async def test_recommendation():
    """测试智能推荐功能"""
    print("\n🎯 测试智能推荐功能...")
    
    test_queries = [
        {
            "name": "英文查询",
            "query": "Looking for a 2 bedroom apartment in Camperdown, budget $900 per week, must have parking"
        },
        {
            "name": "中英混合",
            "query": "我想在悉尼找一个2室1厅的公寓，预算每周$800-1000"
        }
    ]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for i, test in enumerate(test_queries, 1):
            print(f"\n  📝 测试 {i}: {test['name']}")
            print(f"     查询: {test['query']}")
            
            start_time = time.time()
            
            try:
                response = await client.post(
                    f"{BASE_URL}/api/v1/properties/recommend",
                    json={
                        "query": test['query'],
                        "max_results": 3
                    }
                )
                
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        properties = result.get('properties', [])
                        print(f"     ✅ 成功 ({duration:.2f}s)")
                        print(f"     📊 找到 {len(properties)} 个推荐房产")
                        
                        # 显示第一个结果
                        if properties:
                            prop = properties[0]
                            print(f"     🏠 示例: {prop.get('title', 'N/A')}")
                            print(f"         💰 {prop.get('price', 'N/A')}")
                            print(f"         📍 {prop.get('location', 'N/A')}")
                    else:
                        print(f"     ❌ 推荐失败: {result.get('message', '未知错误')}")
                else:
                    print(f"     ❌ HTTP错误: {response.status_code}")
                    
            except Exception as e:
                print(f"     ❌ 请求异常: {e}")

async def test_normal_search():
    """测试普通搜索功能"""
    print("\n🔍 测试普通搜索功能...")
    
    test_data = {
        "location": "Sydney",
        "min_price": 600,
        "max_price": 1000,
        "bedrooms": 2,
        "property_type": "apartment",
        "max_results": 5
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        print(f"  📝 搜索参数: {json.dumps(test_data, indent=4)}")
        
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/properties/search",
                json=test_data
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    properties = result.get('properties', [])
                    print(f"  ✅ 搜索成功 ({duration:.2f}s)")
                    print(f"  📊 找到 {len(properties)} 个房产")
                    
                    # 显示搜索结果摘要
                    if properties:
                        prices = [prop.get('price', '') for prop in properties]
                        print(f"  💰 价格范围: {', '.join(prices[:3])}...")
                else:
                    print(f"  ❌ 搜索失败: {result.get('message', '未知错误')}")
            else:
                print(f"  ❌ HTTP错误: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ 请求异常: {e}")

async def test_firecrawl():
    """测试Firecrawl功能"""
    print("\n🔥 测试Firecrawl连接...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{BASE_URL}/api/v1/properties/test")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✅ Firecrawl API连接正常")
                else:
                    print(f"❌ Firecrawl连接失败: {result.get('message', '未知错误')}")
            else:
                print(f"❌ 测试请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Firecrawl测试失败: {e}")

async def main():
    """主测试函数"""
    print("🧪 澳洲房产智能推荐系统 - API测试")
    print("=" * 50)
    
    # 基础连接测试
    if not await test_health():
        print("\n❌ 服务未启动，请先运行:")
        print("   python start.py")
        print("   或")
        print("   python -m app.main")
        return
    
    # 测试各个功能
    await test_firecrawl()
    
    print("\n" + "="*50)
    await test_openai_connection()
    
    print("\n" + "="*50)
    await test_recommendation()
    
    print("\n" + "="*50)
    await test_normal_search()
    
    print("\n" + "="*50)
    print("🎉 测试完成!")
    print("\n💡 使用建议:")
    print("   - 访问 http://localhost:3000/api/v1/docs 查看完整API文档")
    print("   - 打开 frontend/index.html 使用Web界面")
    print("   - 查看 logs/ 目录下的日志文件排查问题")

if __name__ == "__main__":
    asyncio.run(main())