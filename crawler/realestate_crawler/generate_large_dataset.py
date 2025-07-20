#!/usr/bin/env python3
"""
生成大规模测试数据集 - 模拟真实的房产数据爬取结果
"""

import random
import time
from datetime import datetime, timedelta
from save_utils import save_to_csv, clean_data, save_summary_report
from config import DATA_CONFIG
import os

def generate_large_mock_dataset():
    """生成大规模模拟数据集"""
    
    # 悉尼所有主要区域
    suburbs = [
        "Sydney", "Bondi", "Surry Hills", "Paddington", "Newtown", "Manly", "Chatswood", 
        "Parramatta", "Liverpool", "Bankstown", "Hornsby", "Dee Why", "Cronulla", 
        "Hurstville", "Strathfield", "Ashfield", "Burwood", "Eastwood", "Epping",
        "North Sydney", "Mosman", "Neutral Bay", "Crows Nest", "Lane Cove", "Ryde",
        "Macquarie Park", "West Ryde", "Pymble", "Gordon", "Killara", "Roseville",
        "Artarmon", "Willoughby", "Castle Cove", "Middle Cove", "Northbridge",
        "Cammeray", "Naremburn", "St Leonards", "Wollstonecraft", "McMahons Point",
        "Kirribilli", "Milsons Point", "Lavender Bay", "Waverton", "Greenwich",
        "Woolwich", "Hunters Hill", "Gladesville", "Tennyson Point", "Putney",
        "Concord", "Rhodes", "Homebush", "Lidcombe", "Auburn", "Granville",
        "Harris Park", "Westmead", "Wentworthville", "Toongabbie", "Seven Hills",
        "Blacktown", "Mount Druitt", "Rooty Hill", "Doonside", "Lalor Park",
        "Bondi Beach", "Bondi Junction", "Bellevue Hill", "Double Bay", "Point Piper",
        "Rose Bay", "Vaucluse", "Watsons Bay", "Dover Heights", "Bronte", "Clovelly",
        "Coogee", "Maroubra", "Malabar", "Little Bay", "La Perouse", "Botany",
        "Mascot", "Alexandria", "Erskineville", "St Peters", "Tempe", "Marrickville",
        "Dulwich Hill", "Summer Hill", "Ashbury", "Canterbury", "Campsie",
        "Belmore", "Lakemba", "Wiley Park", "Punchbowl", "Roselands", "Narwee",
        "Beverly Hills", "Kingsgrove", "Bexley", "Rockdale", "Kogarah", "Carlton",
        "Allawah", "Hurstville Grove", "Penshurst", "Mortdale", "Oatley", "Lugarno",
        "Peakhurst", "Forest Road", "Beverley Park", "Ramsgate", "Sans Souci",
        "Monterey", "Brighton-Le-Sands", "Kyeemagh", "Tempe", "Wolli Creek"
    ]
    
    property_types = [
        "Apartment / Unit / Flat",
        "House", 
        "Townhouse",
        "Villa",
        "Studio",
        "Duplex",
        "Terrace",
        "Semi-Detached"
    ]
    
    streets = [
        "George St", "King St", "Queen St", "Market St", "Park Ave", "Ocean Rd",
        "Beach Rd", "High St", "Main St", "Church St", "School St", "Railway St",
        "Victoria St", "Elizabeth St", "William St", "James St", "Charles St",
        "Albert St", "Edward St", "Frederick St", "Henry St", "John St", "Thomas St",
        "Pacific Highway", "Princes Highway", "Anzac Parade", "Oxford St", "Crown St",
        "Liverpool Rd", "Parramatta Rd", "Canterbury Rd", "King Georges Rd",
        "Forest Rd", "The Boulevarde", "Military Rd", "Spit Rd", "Warringah Rd",
        "Pittwater Rd", "Barrenjoey Rd", "Mona Vale Rd", "Condamine St", "Falcon St"
    ]
    
    all_properties = []
    
    # 为每个数据源生成大量数据
    sources = [
        ("realestate.com.au", 800),  # 800条数据
        ("domain.com.au", 600),      # 600条数据
        ("rent.com.au", 400),        # 额外数据源
        ("realestateview.com.au", 300)  # 额外数据源
    ]
    
    print("🏗️ 开始生成大规模数据集...")
    
    property_id = 1
    
    for source, count in sources:
        print(f"📊 生成 {source} 数据: {count} 条...")
        
        source_properties = []
        
        for i in range(count):
            suburb = random.choice(suburbs)
            property_type = random.choice(property_types)
            street = random.choice(streets)
            
            # 根据区域调整价格范围（模拟真实市场）
            expensive_suburbs = ["Bondi", "Mosman", "Double Bay", "Point Piper", "Vaucluse", "Bellevue Hill"]
            affordable_suburbs = ["Liverpool", "Bankstown", "Auburn", "Blacktown", "Mount Druitt"]
            
            if suburb in expensive_suburbs:
                price_range = (800000, 5000000)
            elif suburb in affordable_suburbs:
                price_range = (300000, 1200000)
            else:
                price_range = (400000, 2500000)
            
            # 生成价格（15%概率为Contact Agent）
            if random.random() < 0.15:
                price_original = random.choice(["Contact Agent", "POA", "Auction", "Under Contract"])
                price_numeric = None
            else:
                price_numeric = random.randint(price_range[0], price_range[1])
                # 添加一些价格格式变化
                if random.random() < 0.3:
                    price_original = f"${price_numeric:,}"
                elif random.random() < 0.2:
                    price_original = f"From ${price_numeric:,}"
                else:
                    price_original = f"${price_numeric:,}"
            
            # 根据房产类型生成房间数
            if property_type == "Studio":
                bedrooms = 0
                bathrooms = 1
            elif property_type in ["Apartment / Unit / Flat", "Duplex"]:
                bedrooms = random.randint(1, 4)
                bathrooms = random.randint(1, min(bedrooms + 1, 3))
            else:  # House, Townhouse, Villa, etc.
                bedrooms = random.randint(2, 6)
                bathrooms = random.randint(1, min(bedrooms, 4))
            
            parking = random.choices([0, 1, 2, 3, 4], weights=[15, 35, 30, 15, 5])[0]
            
            # 生成地址
            street_num = random.randint(1, 999)
            postcode = random.randint(2000, 2999)
            address = f"{street_num} {street}, {suburb} NSW {postcode}"
            
            # 生成链接
            link = f"https://www.{source}/property-{property_type.lower().replace(' ', '-').replace('/', '')}-{suburb.lower().replace(' ', '-')}-{property_id}"
            
            property_data = {
                'price': price_original,
                'price_numeric': price_numeric,
                'address': address,
                'suburb': suburb,
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'parking': parking,
                'property_type': property_type,
                'link': link,
                'source': source
            }
            
            source_properties.append(property_data)
            property_id += 1
        
        all_properties.extend(source_properties)
        
        # 保存每个数据源的单独文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"large_{source.replace('.', '_')}_{timestamp}.csv"
        filepath = os.path.join(DATA_CONFIG['output_dir'], filename)
        save_to_csv(source_properties, filepath)
        print(f"   ✅ 已保存到 {filename}")
        
        time.sleep(0.1)  # 避免时间戳冲突
    
    return all_properties

def process_large_dataset():
    """处理大规模数据集"""
    print("\n🚀 开始生成大规模房产数据集...\n")
    
    # 确保数据目录存在
    if not os.path.exists(DATA_CONFIG['output_dir']):
        os.makedirs(DATA_CONFIG['output_dir'])
    
    # 生成大规模数据
    all_properties = generate_large_mock_dataset()
    
    print(f"\n📈 原始数据统计:")
    print(f"   总计: {len(all_properties)} 条记录")
    
    # 按来源统计
    from collections import Counter
    source_counts = Counter([prop['source'] for prop in all_properties])
    for source, count in source_counts.items():
        print(f"   - {source}: {count} 条")
    
    # 数据清理
    print(f"\n🧹 开始数据清理...")
    import pandas as pd
    df = pd.DataFrame(all_properties)
    cleaned_df = clean_data(df)
    
    # 保存合并的大数据集
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    combined_file = os.path.join(DATA_CONFIG['output_dir'], f"large_combined_{timestamp}.csv")
    cleaned_df.to_csv(combined_file, index=False, encoding=DATA_CONFIG['encoding'])
    
    # 生成详细摘要报告
    summary_file = os.path.join(DATA_CONFIG['output_dir'], f"large_summary_{timestamp}.txt")
    save_summary_report(cleaned_df, summary_file)
    
    print(f"\n✅ 大规模数据集生成完成！")
    print(f"📁 合并数据: {combined_file}")
    print(f"📋 摘要报告: {summary_file}")
    print(f"📊 最终统计:")
    print(f"   - 原始数据: {len(all_properties)} 条")
    print(f"   - 清理后: {len(cleaned_df)} 条有效记录")
    print(f"   - 数据清理率: {(len(all_properties) - len(cleaned_df)) / len(all_properties) * 100:.1f}%")
    
    # 显示详细统计
    if 'price_numeric' in cleaned_df.columns:
        price_data = cleaned_df['price_numeric'].dropna()
        if not price_data.empty:
            print(f"\n💰 价格统计:")
            print(f"   - 有价格数据: {len(price_data)} 条 ({len(price_data)/len(cleaned_df)*100:.1f}%)")
            print(f"   - 平均价格: ${price_data.mean():,.0f}")
            print(f"   - 中位价格: ${price_data.median():,.0f}")
            print(f"   - 价格区间: ${price_data.min():,.0f} - ${price_data.max():,.0f}")
    
    # 按区域统计
    if 'suburb' in cleaned_df.columns:
        print(f"\n🏘️ 区域分布 (前10):")
        suburb_counts = cleaned_df['suburb'].value_counts().head(10)
        for suburb, count in suburb_counts.items():
            print(f"   - {suburb}: {count} 条")
    
    return cleaned_df

if __name__ == "__main__":
    # 生成大规模数据集
    large_dataset = process_large_dataset()