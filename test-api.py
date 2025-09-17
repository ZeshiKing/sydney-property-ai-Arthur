#!/usr/bin/env python3
"""
澳洲租房聚合系统 - API测试脚本
快速测试所有API端点功能
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any
from datetime import datetime


class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []

    async def test_endpoint(self, name: str, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """测试单个API端点"""
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.request(method, f"{self.base_url}{url}", **kwargs)

                duration = time.time() - start_time
                success = response.status_code < 400

                result = {
                    "name": name,
                    "method": method,
                    "url": url,
                    "status_code": response.status_code,
                    "success": success,
                    "duration": round(duration * 1000, 2),  # 转换为毫秒
                    "response_size": len(response.content),
                }

                # 尝试解析JSON响应
                try:
                    result["response"] = response.json()
                except:
                    result["response"] = response.text[:200] + "..." if len(response.text) > 200 else response.text

                return result

        except Exception as e:
            duration = time.time() - start_time
            return {
                "name": name,
                "method": method,
                "url": url,
                "status_code": 0,
                "success": False,
                "duration": round(duration * 1000, 2),
                "error": str(e),
                "response": None
            }

    def print_header(self):
        """打印测试头部信息"""
        print("🧪 澳洲租房聚合系统 - API功能测试")
        print("=" * 50)
        print(f"📍 测试目标: {self.base_url}")
        print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    def print_test_result(self, result: Dict[str, Any]):
        """打印单个测试结果"""
        status_icon = "✅" if result["success"] else "❌"
        duration_str = f"{result['duration']}ms"

        print(f"{status_icon} {result['name']}")
        print(f"   {result['method']} {result['url']}")
        print(f"   状态码: {result['status_code']} | 耗时: {duration_str}")

        if not result["success"] and "error" in result:
            print(f"   错误: {result['error']}")
        elif result.get("response"):
            if isinstance(result["response"], dict):
                # 显示关键信息
                if "message" in result["response"]:
                    print(f"   响应: {result['response']['message']}")
                elif "success" in result["response"]:
                    print(f"   成功: {result['response']['success']}")
            else:
                print(f"   响应: {str(result['response'])[:100]}...")
        print()

    def print_summary(self):
        """打印测试总结"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests

        avg_duration = sum(r["duration"] for r in self.test_results) / total_tests if total_tests > 0 else 0

        print("📊 测试总结")
        print("=" * 30)
        print(f"✅ 通过: {passed_tests}/{total_tests}")
        print(f"❌ 失败: {failed_tests}/{total_tests}")
        print(f"⚡ 平均响应时间: {avg_duration:.1f}ms")
        print()

        if failed_tests > 0:
            print("❌ 失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['name']} - {result.get('error', 'HTTP ' + str(result['status_code']))}")
            print()

        # 性能分析
        slow_tests = [r for r in self.test_results if r["duration"] > 2000]
        if slow_tests:
            print("⚠️  较慢的接口 (>2秒):")
            for result in slow_tests:
                print(f"   • {result['name']} - {result['duration']}ms")
            print()

    async def run_all_tests(self):
        """运行所有API测试"""
        self.print_header()

        # 测试用例列表
        test_cases = [
            {
                "name": "根端点测试",
                "method": "GET",
                "url": "/",
            },
            {
                "name": "简单健康检查",
                "method": "GET",
                "url": "/health",
            },
            {
                "name": "详细健康检查",
                "method": "GET",
                "url": "/api/v1/health/",
            },
            {
                "name": "支持区域查询",
                "method": "GET",
                "url": "/api/v1/properties/locations",
            },
            {
                "name": "Firecrawl连接测试",
                "method": "GET",
                "url": "/api/v1/properties/test",
            },
            {
                "name": "房产搜索 - 基本测试",
                "method": "POST",
                "url": "/api/v1/properties/search",
                "json": {
                    "location": "Sydney",
                    "max_results": 3
                }
            },
            {
                "name": "房产搜索 - 完整参数",
                "method": "POST",
                "url": "/api/v1/properties/search",
                "json": {
                    "location": "Melbourne",
                    "min_price": 400,
                    "max_price": 800,
                    "bedrooms": 2,
                    "bathrooms": 1,
                    "property_type": "Apartment",
                    "max_results": 5
                }
            },
            {
                "name": "房产搜索 - 参数验证测试",
                "method": "POST",
                "url": "/api/v1/properties/search",
                "json": {
                    "location": "Brisbane",
                    "min_price": 1000,
                    "max_price": 500,  # 故意设置错误的价格范围
                }
            },
        ]

        # 依次执行测试
        for i, test_case in enumerate(test_cases, 1):
            print(f"[{i}/{len(test_cases)}] 正在测试: {test_case['name']}...")

            result = await self.test_endpoint(**test_case)
            self.test_results.append(result)
            self.print_test_result(result)

            # 短暂延迟，避免过于频繁的请求
            await asyncio.sleep(0.5)

        # 打印总结
        self.print_summary()

        # 额外的集成测试
        await self.run_integration_tests()

    async def run_integration_tests(self):
        """运行集成测试"""
        print("🔗 集成测试")
        print("=" * 20)

        # 检查CSV导出功能
        print("📄 检查CSV导出功能...")
        try:
            # 执行一次搜索
            search_result = await self.test_endpoint(
                "CSV导出测试",
                "POST",
                "/api/v1/properties/search",
                json={"location": "Perth", "max_results": 2}
            )

            if search_result["success"]:
                print("✅ 搜索请求成功，CSV文件应该已生成")

                # 检查文件系统中的CSV文件
                import os
                csv_dir = "csv_exports"
                if os.path.exists(csv_dir):
                    csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
                    print(f"📁 找到 {len(csv_files)} 个CSV文件")
                    if csv_files:
                        latest_file = max(csv_files, key=lambda x: os.path.getctime(os.path.join(csv_dir, x)))
                        print(f"📄 最新文件: {latest_file}")
                else:
                    print("⚠️  CSV导出目录不存在")
            else:
                print("❌ 搜索请求失败，无法测试CSV导出")

        except Exception as e:
            print(f"❌ CSV导出测试失败: {e}")

        print()

        # API文档可访问性测试
        print("📚 API文档可访问性测试...")
        docs_result = await self.test_endpoint(
            "Swagger文档",
            "GET",
            "/docs"
        )

        if docs_result["success"]:
            print("✅ Swagger UI 可访问")
        else:
            print("❌ Swagger UI 不可访问")

        redoc_result = await self.test_endpoint(
            "ReDoc文档",
            "GET",
            "/redoc"
        )

        if redoc_result["success"]:
            print("✅ ReDoc 可访问")
        else:
            print("❌ ReDoc 不可访问")

        print()


def main():
    """主函数"""
    import sys

    # 支持自定义API地址
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    tester = APITester(api_url)

    try:
        asyncio.run(tester.run_all_tests())
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()