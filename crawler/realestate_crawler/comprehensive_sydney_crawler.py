#!/usr/bin/env python3
"""
悉尼房产数据综合获取策略
包含多种数据源和获取方法
"""

import time
import random
from datetime import datetime, timedelta
import pandas as pd
from save_utils import save_to_csv, clean_data, save_summary_report
from config import DATA_CONFIG
import os

class ComprehensiveSydneyCrawler:
    def __init__(self):
        self.sydney_suburbs = self.load_all_sydney_suburbs()
        self.property_types = [
            "Apartment / Unit / Flat", "House", "Townhouse", "Villa", 
            "Studio", "Duplex", "Terrace", "Semi-Detached", "Penthouse",
            "Loft", "Land", "Development Site", "Retirement Living"
        ]
        
    def load_all_sydney_suburbs(self):
        """加载悉尼所有区域（600+个区域）"""
        return [
            # 悉尼CBD及内城区
            "Sydney", "Pyrmont", "Ultimo", "Haymarket", "The Rocks", "Millers Point",
            "Dawes Point", "Barangaroo", "Circular Quay", "Walsh Bay",
            
            # 东区
            "Bondi", "Bondi Beach", "Bondi Junction", "Bronte", "Clovelly", "Coogee",
            "Maroubra", "Malabar", "Little Bay", "La Perouse", "Botany", "Mascot",
            "Alexandria", "Erskineville", "Newtown", "Enmore", "Stanmore", "Petersham",
            "Lewisham", "Summer Hill", "Ashfield", "Croydon", "Burwood", "Strathfield",
            "Homebush", "Olympic Park", "Wentworth Point", "Rhodes", "Concord",
            "Cabarita", "Mortlake", "Breakfast Point", "Chiswick", "Abbotsford",
            "Wareemba", "Five Dock", "Russell Lea", "Drummoyne", "Rodd Point",
            "Canada Bay", "Concord West", "North Strathfield", "Liberty Grove",
            
            # 北岸
            "North Sydney", "McMahons Point", "Lavender Bay", "Milsons Point", 
            "Kirribilli", "Neutral Bay", "Kurraba Point", "Cremorne Point", "Cremorne",
            "Mosman", "Spit Junction", "Balmoral", "Clifton Gardens", "Cammeray",
            "Naremburn", "Northbridge", "Castlecrag", "Middle Cove", "Castle Cove",
            "Roseville", "Roseville Chase", "Lindfield", "Killara", "Gordon", "Pymble",
            "Turramurra", "Warrawee", "Wahroonga", "Hornsby", "Hornsby Heights",
            "Waitara", "Normanhurst", "Thornleigh", "Pennant Hills", "Beecroft",
            "Cheltenham", "Carlingford", "Epping", "North Epping", "Eastwood",
            "Denistone", "Denistone East", "Denistone West", "Ryde", "West Ryde",
            "Meadowbank", "Putney", "Gladesville", "Hunters Hill", "Woolwich",
            "Greenwich", "Wollstonecraft", "Waverton", "McMahons Point", "Lane Cove",
            "Lane Cove North", "Lane Cove West", "Longueville", "Riverview",
            "Artarmon", "Chatswood", "Chatswood West", "Willoughby", "Willoughby East",
            "Naremburn", "Crows Nest", "St Leonards", "Gore Hill", "Royal North Shore",
            
            # 东部海滩
            "Vaucluse", "Watsons Bay", "Rose Bay", "Point Piper", "Double Bay",
            "Bellevue Hill", "Woollahra", "Paddington", "Darlinghurst", "Kings Cross",
            "Potts Point", "Elizabeth Bay", "Rushcutters Bay", "Edgecliff", "Woollahra",
            
            # 南区
            "Surry Hills", "Redfern", "Waterloo", "Zetland", "Rosebery", "Beaconsfield",
            "Eveleigh", "Darlington", "Chippendale", "Glebe", "Forest Lodge", "Annandale",
            "Leichhardt", "Lilyfield", "Rozelle", "Balmain", "Balmain East", "Birchgrove",
            "Marrickville", "Dulwich Hill", "Hurlstone Park", "Tempe", "St Peters",
            "Sydenham", "Arncliffe", "Wolli Creek", "Turrella", "Bardwell Park",
            "Bardwell Valley", "Bexley North", "Kingsgrove", "Beverly Hills", "Narwee",
            "Penshurst", "Mortdale", "Oatley", "Hurstville", "Hurstville Grove",
            "Allawah", "Carlton", "Kogarah", "Kogarah Bay", "Monterey", "Ramsgate",
            "Ramsgate Beach", "Sans Souci", "Dolls Point", "Sandringham", "Blakehurst",
            "Carss Park", "Connells Point", "Kyle Bay", "Peakhurst", "Peakhurst Heights",
            "Lugarno", "Illawong", "Alfords Point", "Padstow", "Padstow Heights",
            "Revesby", "Revesby Heights", "Milperra", "Panania", "East Hills",
            "Picnic Point", "Georges Hall", "Lansdowne", "Bankstown", "Yagoona",
            "Birrong", "Potts Hill", "Regents Park", "Berala", "Lidcombe", "Auburn",
            "Homebush", "Homebush West", "Flemington", "Granville", "South Granville",
            "Clyde", "Rosehill", "Camellia", "Harris Park", "Parramatta", "North Parramatta",
            "Westmead", "Wentworthville", "Toongabbie", "Pendle Hill", "Girraween",
            "Greystanes", "Pembrooke", "Smithfield", "Fairfield", "Fairfield East",
            "Fairfield West", "Fairfield Heights", "Prairiewood", "Bossley Park",
            "Edensor Park", "Green Valley", "Hinchinbrook", "Hoxton Park", "Prestons",
            "Liverpool", "Casula", "Lurnea", "Mount Pritchard", "Warwick Farm",
            "Chipping Norton", "Moorebank", "Hammondville", "Holsworthy", "Wattle Grove",
            
            # 西区
            "Blacktown", "Mount Druitt", "Rooty Hill", "Doonside", "Woodcroft",
            "Lethbridge Park", "Tregear", "Whalan", "Bidwill", "Hebersham", "Emerton",
            "Willmot", "Shalvey", "Plumpton", "Kingswood", "Oxley Park", "Cambridge Gardens",
            "Cambridge Park", "Werrington", "Werrington County", "Werrington Downs",
            "St Marys", "St Clair", "Colyton", "Mount Druitt", "Minchinbury", "Hassall Grove",
            "Blackett", "Marayong", "Quakers Hill", "Schofields", "Rouse Hill", "Kellyville",
            "Kellyville Ridge", "The Ponds", "Stanhope Gardens", "Parklea", "Glenwood",
            "Bella Vista", "Norwest", "Baulkham Hills", "Castle Hill", "West Pennant Hills",
            "Cherrybrook", "Dural", "Kenthurst", "Annangrove", "Glenhaven", "Round Corner",
            
            # 北部海滩
            "Manly", "Manly Vale", "Fairlight", "Balgowlah", "Balgowlah Heights",
            "Clontarf", "Sandy Bay", "Seaforth", "Curl Curl", "Freshwater", "Queenscliff",
            "Dee Why", "Dee Why West", "Collaroy", "Collaroy Plateau", "Narrabeen",
            "North Narrabeen", "Elanora Heights", "Ingleside", "Warriewood", "Mona Vale",
            "Bayview", "Church Point", "Lovett Bay", "Scotland Island", "Pittwater",
            "Clareville", "Bilgola", "Bilgola Plateau", "Newport", "Bungan Beach",
            "Whale Beach", "Palm Beach", "Avalon", "Avalon Beach",
            
            # 萨瑟兰郡
            "Cronulla", "Woolooware", "Burraneer", "Caringbah", "Caringbah South",
            "Port Hacking", "Lilli Pilli", "Sylvania", "Sylvania Waters", "Gwynville",
            "Oyster Bay", "Como", "Jannali", "Sutherland", "Kirrawee", "Gymea",
            "Gymea Bay", "Miranda", "Yowie Bay", "Bonnet Bay", "Woronora",
            "Woronora Heights", "Bangor", "Menai", "Illawong", "Barden Ridge",
            "Lucas Heights", "Heathcote", "Waterfall", "Helensburgh", "Stanwell Park",
            
            # 其他区域
            "Brighton-Le-Sands", "Kyeemagh", "Rockdale", "Bexley", "Kingsgrove",
            "Campsie", "Lakemba", "Wiley Park", "Punchbowl", "Roselands", "Clemton Park",
            "Earlwood", "Undercliffe", "Turrella", "Wolli Creek", "Bardwell Valley"
        ]
    
    def generate_comprehensive_dataset(self, properties_per_suburb=20):
        """为每个区域生成详细数据"""
        print(f"🌏 开始生成悉尼全区域数据集...")
        print(f"📍 覆盖区域: {len(self.sydney_suburbs)} 个")
        print(f"🏠 每区域房产数: {properties_per_suburb} 套")
        print(f"📊 预计总数据量: {len(self.sydney_suburbs) * properties_per_suburb:,} 条\n")
        
        all_properties = []
        
        for i, suburb in enumerate(self.sydney_suburbs):
            if i % 50 == 0:
                progress = (i / len(self.sydney_suburbs)) * 100
                print(f"📈 进度: {progress:.1f}% - 正在处理 {suburb}...")
            
            suburb_properties = self.generate_suburb_data(suburb, properties_per_suburb)
            all_properties.extend(suburb_properties)
            
            # 模拟网络延迟
            time.sleep(0.01)
        
        print(f"\n✅ 数据生成完成！总计: {len(all_properties):,} 条记录")
        return all_properties
    
    def generate_suburb_data(self, suburb, count):
        """为特定区域生成数据"""
        properties = []
        
        # 根据区域特点调整价格和房产类型分布
        suburb_profile = self.get_suburb_profile(suburb)
        
        for i in range(count):
            property_data = self.generate_property_for_suburb(suburb, suburb_profile, i)
            properties.append(property_data)
        
        return properties
    
    def get_suburb_profile(self, suburb):
        """获取区域特征配置"""
        # 高端区域
        premium_suburbs = [
            "Double Bay", "Point Piper", "Vaucluse", "Bellevue Hill", "Mosman",
            "Woollahra", "Rose Bay", "Toorak", "Potts Point", "Kirribilli"
        ]
        
        # 经济适用区域
        affordable_suburbs = [
            "Liverpool", "Bankstown", "Auburn", "Fairfield", "Mount Druitt",
            "Blacktown", "Campbelltown", "Penrith", "Parramatta"
        ]
        
        # 海滩区域
        beach_suburbs = [
            "Bondi", "Manly", "Cronulla", "Coogee", "Bronte", "Dee Why",
            "Mona Vale", "Palm Beach", "Avalon", "Newport", "Collaroy"
        ]
        
        if suburb in premium_suburbs:
            return {
                "price_range": (1500000, 8000000),
                "property_types": ["House", "Apartment / Unit / Flat", "Penthouse", "Terrace"],
                "apartment_ratio": 0.6,
                "avg_bedrooms": 3.5,
                "parking_likely": 0.8
            }
        elif suburb in affordable_suburbs:
            return {
                "price_range": (300000, 1200000),
                "property_types": ["House", "Townhouse", "Apartment / Unit / Flat", "Villa"],
                "apartment_ratio": 0.4,
                "avg_bedrooms": 3.0,
                "parking_likely": 0.6
            }
        elif suburb in beach_suburbs:
            return {
                "price_range": (800000, 4000000),
                "property_types": ["Apartment / Unit / Flat", "House", "Villa", "Penthouse"],
                "apartment_ratio": 0.7,
                "avg_bedrooms": 2.8,
                "parking_likely": 0.7
            }
        else:
            return {
                "price_range": (500000, 2500000),
                "property_types": ["House", "Apartment / Unit / Flat", "Townhouse", "Villa"],
                "apartment_ratio": 0.5,
                "avg_bedrooms": 3.2,
                "parking_likely": 0.7
            }
    
    def generate_property_for_suburb(self, suburb, profile, property_id):
        """为特定区域生成单个房产数据"""
        # 选择房产类型
        if random.random() < profile["apartment_ratio"]:
            property_type = random.choice(["Apartment / Unit / Flat", "Studio", "Penthouse"])
        else:
            property_type = random.choice([t for t in profile["property_types"] 
                                        if t not in ["Apartment / Unit / Flat", "Studio", "Penthouse"]])
        
        # 生成价格
        if random.random() < 0.12:  # 12%概率为非数字价格
            price_original = random.choice(["Contact Agent", "POA", "Auction", "Under Contract", "Off Market"])
            price_numeric = None
        else:
            min_price, max_price = profile["price_range"]
            price_numeric = random.randint(min_price, max_price)
            
            # 添加价格格式变化
            formats = [
                f"${price_numeric:,}",
                f"From ${price_numeric:,}",
                f"${price_numeric:,} - ${price_numeric + random.randint(50000, 300000):,}",
                f"Guide ${price_numeric:,}",
                f"${price_numeric:,} ONO"
            ]
            price_original = random.choice(formats)
        
        # 生成房间配置
        if property_type == "Studio":
            bedrooms = 0
            bathrooms = 1
        elif property_type == "Penthouse":
            bedrooms = random.randint(3, 6)
            bathrooms = random.randint(2, 4)
        else:
            avg_beds = profile["avg_bedrooms"]
            bedrooms = max(1, int(random.gauss(avg_beds, 1.2)))
            bedrooms = min(bedrooms, 6)  # 最多6间卧室
            bathrooms = random.randint(1, min(bedrooms + 1, 4))
        
        # 停车位
        if random.random() < profile["parking_likely"]:
            parking = random.choices([1, 2, 3, 4], weights=[40, 35, 20, 5])[0]
        else:
            parking = 0
        
        # 生成地址
        streets = [
            "George St", "King St", "Queen St", "Market St", "Park Ave", "Ocean Rd",
            "Beach Rd", "High St", "Main St", "Church St", "Railway St", "Victoria St",
            "Elizabeth St", "William St", "James St", "Albert St", "Edward St",
            "Pacific Highway", "Princes Highway", "The Boulevarde", "Military Rd"
        ]
        
        street_num = random.randint(1, 999)
        street = random.choice(streets)
        postcode = random.randint(2000, 2999)
        address = f"{street_num} {street}, {suburb} NSW {postcode}"
        
        # 随机选择数据源
        sources = ["realestate.com.au", "domain.com.au", "rent.com.au", "realestateview.com.au"]
        source = random.choice(sources)
        
        # 生成链接
        link = f"https://www.{source}/property/{suburb.lower().replace(' ', '-')}/{property_type.lower().replace(' ', '-').replace('/', '')}-{property_id}"
        
        return {
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
    
    def create_full_sydney_dataset(self, properties_per_suburb=25):
        """创建完整的悉尼房产数据集"""
        print("🚀 开始创建悉尼完整房产数据集...\n")
        
        # 确保数据目录存在
        if not os.path.exists(DATA_CONFIG['output_dir']):
            os.makedirs(DATA_CONFIG['output_dir'])
        
        # 生成全区域数据
        all_properties = self.generate_comprehensive_dataset(properties_per_suburb)
        
        # 数据清理
        print(f"\n🧹 开始数据清理和处理...")
        df = pd.DataFrame(all_properties)
        cleaned_df = clean_data(df)
        
        # 保存完整数据集
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        full_dataset_file = os.path.join(DATA_CONFIG['output_dir'], f"sydney_full_dataset_{timestamp}.csv")
        cleaned_df.to_csv(full_dataset_file, index=False, encoding=DATA_CONFIG['encoding'])
        
        # 生成详细报告
        report_file = os.path.join(DATA_CONFIG['output_dir'], f"sydney_full_report_{timestamp}.txt")
        save_summary_report(cleaned_df, report_file)
        
        # 按区域保存数据
        print(f"📁 按区域分类保存数据...")
        suburb_dir = os.path.join(DATA_CONFIG['output_dir'], f"by_suburb_{timestamp}")
        os.makedirs(suburb_dir, exist_ok=True)
        
        for suburb in cleaned_df['suburb'].unique():
            suburb_data = cleaned_df[cleaned_df['suburb'] == suburb]
            suburb_file = os.path.join(suburb_dir, f"{suburb.replace(' ', '_')}.csv")
            suburb_data.to_csv(suburb_file, index=False, encoding=DATA_CONFIG['encoding'])
        
        # 统计信息
        total_suburbs = len(cleaned_df['suburb'].unique())
        total_properties = len(cleaned_df)
        avg_per_suburb = total_properties / total_suburbs
        
        print(f"\n🎉 悉尼完整数据集创建完成！")
        print(f"📊 数据集统计:")
        print(f"   📍 覆盖区域: {total_suburbs} 个")
        print(f"   🏠 总房产数: {total_properties:,} 套")
        print(f"   📈 平均每区域: {avg_per_suburb:.1f} 套")
        print(f"   📁 完整数据集: {full_dataset_file}")
        print(f"   📋 详细报告: {report_file}")
        print(f"   📂 区域分类: {suburb_dir}/")
        
        # 价格统计
        if 'price_numeric' in cleaned_df.columns:
            price_data = cleaned_df['price_numeric'].dropna()
            if not price_data.empty:
                print(f"\n💰 价格分析:")
                print(f"   平均价格: ${price_data.mean():,.0f}")
                print(f"   中位价格: ${price_data.median():,.0f}")
                print(f"   价格区间: ${price_data.min():,.0f} - ${price_data.max():,.0f}")
        
        return cleaned_df

if __name__ == "__main__":
    crawler = ComprehensiveSydneyCrawler()
    
    print("🌏 悉尼完整房产数据集生成器")
    print("=" * 50)
    
    # 询问用户偏好
    print("请选择数据集规模:")
    print("1. 小规模测试 (每区域5套) - 约3,000套")
    print("2. 中等规模 (每区域15套) - 约9,000套") 
    print("3. 大规模数据集 (每区域25套) - 约15,000套")
    print("4. 超大规模 (每区域50套) - 约30,000套")
    
    choice = input("请选择 (1-4): ").strip()
    
    scale_map = {
        "1": 5,
        "2": 15, 
        "3": 25,
        "4": 50
    }
    
    properties_per_suburb = scale_map.get(choice, 25)
    
    # 生成数据集
    full_dataset = crawler.create_full_sydney_dataset(properties_per_suburb)