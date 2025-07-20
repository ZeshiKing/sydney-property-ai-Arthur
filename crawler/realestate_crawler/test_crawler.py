#!/usr/bin/env python3
"""
测试爬虫 - 生成模拟数据来演示系统功能
"""

import random
import time
from datetime import datetime
from save_utils import save_to_csv, clean_data, save_summary_report
from config import DATA_CONFIG
import os

def generate_mock_properties(count=50, source="test"):
    """生成模拟房产数据"""
    
    suburbs = [
        "Sydney", "Bondi", "Surry Hills", "Paddington", "Newtown",
        "Manly", "Chatswood", "Parramatta", "Liverpool", "Bankstown",
        "Hornsby", "Dee Why", "Cronulla", "Hurstville", "Strathfield"
    ]
    
    property_types = [
        "Apartment / Unit / Flat",
        "House",
        "Townhouse", 
        "Villa",
        "Studio"
    ]
    
    properties = []
    
    for i in range(count):
        suburb = random.choice(suburbs)
        property_type = random.choice(property_types)
        
        # 生成价格
        if random.random() < 0.1:  # 10%概率为Contact Agent
            price_original = "Contact Agent"
            price_numeric = None
        else:
            price_numeric = random.randint(400000, 2500000)
            price_original = f"${price_numeric:,}"
        
        # 生成房间数
        bedrooms = random.randint(1, 5) if property_type != "Studio" else 0
        bathrooms = random.randint(1, min(bedrooms + 1, 4))
        parking = random.randint(0, 3)
        
        # 生成地址
        street_num = random.randint(1, 999)
        streets = ["George St", "King St", "Queen St", "Market St", "Park Ave", "Ocean Rd"]
        street = random.choice(streets)
        address = f"{street_num} {street}, {suburb} NSW {random.randint(2000, 2999)}"
        
        property_data = {
            'price': price_original,
            'price_numeric': price_numeric,
            'address': address,
            'suburb': suburb,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'parking': parking,
            'property_type': property_type,
            'link': f"https://{source}.com.au/property/{i+1}",
            'source': source
        }
        
        properties.append(property_data)
    
    return properties

def test_realestate_crawler():
    """测试realestate.com.au爬虫"""
    print("🏠 生成 realestate.com.au 模拟数据...")
    properties = generate_mock_properties(30, "realestate.com.au")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"test_realestate_{timestamp}.csv"
    filepath = os.path.join(DATA_CONFIG['output_dir'], filename)
    
    save_to_csv(properties, filepath)
    print(f"✅ 保存了 {len(properties)} 条 realestate 数据到 {filepath}")
    
    return properties

def test_domain_crawler():
    """测试domain.com.au爬虫"""
    print("🏠 生成 domain.com.au 模拟数据...")
    properties = generate_mock_properties(25, "domain.com.au")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"test_domain_{timestamp}.csv"
    filepath = os.path.join(DATA_CONFIG['output_dir'], filename)
    
    save_to_csv(properties, filepath)
    print(f"✅ 保存了 {len(properties)} 条 domain 数据到 {filepath}")
    
    return properties

def test_full_workflow():
    """测试完整工作流程"""
    print("🚀 开始测试完整爬虫工作流程...\n")
    
    # 确保数据目录存在
    if not os.path.exists(DATA_CONFIG['output_dir']):
        os.makedirs(DATA_CONFIG['output_dir'])
    
    # 生成两个网站的数据
    realestate_properties = test_realestate_crawler()
    time.sleep(1)  # 模拟延迟
    domain_properties = test_domain_crawler()
    
    # 合并数据
    print("\n🔄 合并数据...")
    all_properties = realestate_properties + domain_properties
    
    # 数据清理
    print("🧹 清理数据...")
    import pandas as pd
    df = pd.DataFrame(all_properties)
    cleaned_df = clean_data(df)
    
    # 保存合并数据
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    combined_file = os.path.join(DATA_CONFIG['output_dir'], f"test_combined_{timestamp}.csv")
    cleaned_df.to_csv(combined_file, index=False, encoding=DATA_CONFIG['encoding'])
    
    # 生成摘要报告
    print("📊 生成摘要报告...")
    summary_file = os.path.join(DATA_CONFIG['output_dir'], f"test_summary_{timestamp}.txt")
    save_summary_report(cleaned_df, summary_file)
    
    print(f"\n✅ 测试完成！")
    print(f"📁 合并数据: {combined_file}")
    print(f"📋 摘要报告: {summary_file}")
    print(f"📈 总计: {len(cleaned_df)} 条有效记录")
    
    # 显示统计信息
    print(f"\n📊 数据统计:")
    print(f"   - realestate.com.au: {len(realestate_properties)} 条")
    print(f"   - domain.com.au: {len(domain_properties)} 条")
    print(f"   - 清理后总计: {len(cleaned_df)} 条")
    
    if 'price_numeric' in cleaned_df.columns:
        price_data = cleaned_df['price_numeric'].dropna()
        if not price_data.empty:
            print(f"   - 平均价格: ${price_data.mean():,.0f}")
            print(f"   - 中位价格: ${price_data.median():,.0f}")
    
    return cleaned_df

if __name__ == "__main__":
    # 运行测试
    test_full_workflow()