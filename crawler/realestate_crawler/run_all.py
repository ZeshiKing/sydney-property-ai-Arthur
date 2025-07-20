#!/usr/bin/env python3
"""
房产爬虫主程序
支持多种运行模式：单次运行、定时任务、交互式选择
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from realestate_spider import RealEstateSpider
from domain_spider import DomainSpider
from scheduler import CrawlerScheduler
from save_utils import save_to_csv, merge_csv_files, clean_data, save_summary_report
from config import DATA_CONFIG

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def ensure_data_directory():
    """确保数据目录存在"""
    if not os.path.exists(DATA_CONFIG['output_dir']):
        os.makedirs(DATA_CONFIG['output_dir'])
        logger.info(f"Created data directory: {DATA_CONFIG['output_dir']}")

def run_single_crawler(crawler_type):
    """运行单个爬虫"""
    ensure_data_directory()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if crawler_type == 'realestate':
        logger.info("Starting realestate.com.au crawler...")
        spider = RealEstateSpider()
        properties = spider.run()
        filename = f"realestate_{timestamp}.csv"
    elif crawler_type == 'domain':
        logger.info("Starting domain.com.au crawler...")
        spider = DomainSpider()
        properties = spider.run()
        filename = f"domain_{timestamp}.csv"
    else:
        logger.error(f"Unknown crawler type: {crawler_type}")
        return
    
    if properties:
        filepath = os.path.join(DATA_CONFIG['output_dir'], filename)
        save_to_csv(properties, filepath)
        logger.info(f"Saved {len(properties)} properties to {filepath}")
    else:
        logger.warning("No properties found")

def run_all_crawlers():
    """运行所有爬虫"""
    ensure_data_directory()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    all_properties = []
    
    # 运行realestate.com.au爬虫
    logger.info("Starting realestate.com.au crawler...")
    try:
        realestate_spider = RealEstateSpider()
        realestate_properties = realestate_spider.run()
        if realestate_properties:
            all_properties.extend(realestate_properties)
            # 保存单独的文件
            realestate_file = os.path.join(DATA_CONFIG['output_dir'], f"realestate_{timestamp}.csv")
            save_to_csv(realestate_properties, realestate_file)
            logger.info(f"Saved {len(realestate_properties)} realestate properties")
    except Exception as e:
        logger.error(f"Error running realestate crawler: {e}")
    
    # 运行domain.com.au爬虫
    logger.info("Starting domain.com.au crawler...")
    try:
        domain_spider = DomainSpider()
        domain_properties = domain_spider.run()
        if domain_properties:
            all_properties.extend(domain_properties)
            # 保存单独的文件
            domain_file = os.path.join(DATA_CONFIG['output_dir'], f"domain_{timestamp}.csv")
            save_to_csv(domain_properties, domain_file)
            logger.info(f"Saved {len(domain_properties)} domain properties")
    except Exception as e:
        logger.error(f"Error running domain crawler: {e}")
    
    # 保存合并的数据
    if all_properties:
        # 清理数据
        import pandas as pd
        df = pd.DataFrame(all_properties)
        cleaned_df = clean_data(df)
        
        # 保存清理后的数据
        combined_file = os.path.join(DATA_CONFIG['output_dir'], f"combined_{timestamp}.csv")
        cleaned_df.to_csv(combined_file, index=False, encoding=DATA_CONFIG['encoding'])
        
        # 生成摘要报告
        summary_file = os.path.join(DATA_CONFIG['output_dir'], f"summary_{timestamp}.txt")
        save_summary_report(cleaned_df, summary_file)
        
        logger.info(f"Total properties scraped: {len(all_properties)}")
        logger.info(f"Combined data saved to: {combined_file}")
        logger.info(f"Summary report saved to: {summary_file}")
    else:
        logger.warning("No properties found from any crawler")

def interactive_mode():
    """交互式模式"""
    print("\n=== 房产爬虫系统 ===")
    print("1. 运行 realestate.com.au 爬虫")
    print("2. 运行 domain.com.au 爬虫")
    print("3. 运行所有爬虫")
    print("4. 启动定时任务")
    print("5. 合并现有CSV文件")
    print("6. 生成数据摘要报告")
    print("0. 退出")
    
    while True:
        choice = input("\n请选择操作 (0-6): ").strip()
        
        if choice == '0':
            print("退出程序")
            break
        elif choice == '1':
            run_single_crawler('realestate')
        elif choice == '2':
            run_single_crawler('domain')
        elif choice == '3':
            run_all_crawlers()
        elif choice == '4':
            scheduler = CrawlerScheduler()
            scheduler.run_scheduler()
        elif choice == '5':
            merge_existing_files()
        elif choice == '6':
            generate_summary_report()
        else:
            print("无效选择，请重新输入")

def merge_existing_files():
    """合并现有的CSV文件"""
    data_dir = DATA_CONFIG['output_dir']
    if not os.path.exists(data_dir):
        print(f"数据目录 {data_dir} 不存在")
        return
    
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    if not csv_files:
        print("没有找到CSV文件")
        return
    
    print(f"找到 {len(csv_files)} 个CSV文件:")
    for i, file in enumerate(csv_files):
        print(f"{i+1}. {file}")
    
    print("输入要合并的文件编号（用逗号分隔），或输入 'all' 合并所有文件:")
    choice = input().strip()
    
    if choice.lower() == 'all':
        selected_files = csv_files
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            selected_files = [csv_files[i] for i in indices if 0 <= i < len(csv_files)]
        except:
            print("无效输入")
            return
    
    if not selected_files:
        print("没有选择有效的文件")
        return
    
    file_paths = [os.path.join(data_dir, f) for f in selected_files]
    output_file = os.path.join(data_dir, f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    
    merged_df = merge_csv_files(file_paths, output_file)
    if not merged_df.empty:
        print(f"成功合并 {len(merged_df)} 条记录到 {output_file}")

def generate_summary_report():
    """生成数据摘要报告"""
    data_dir = DATA_CONFIG['output_dir']
    if not os.path.exists(data_dir):
        print(f"数据目录 {data_dir} 不存在")
        return
    
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    if not csv_files:
        print("没有找到CSV文件")
        return
    
    print(f"找到 {len(csv_files)} 个CSV文件:")
    for i, file in enumerate(csv_files):
        print(f"{i+1}. {file}")
    
    choice = input("选择要分析的文件编号: ").strip()
    
    try:
        index = int(choice) - 1
        if 0 <= index < len(csv_files):
            selected_file = csv_files[index]
            file_path = os.path.join(data_dir, selected_file)
            
            from save_utils import load_from_csv
            df = load_from_csv(file_path)
            
            if not df.empty:
                summary_file = os.path.join(data_dir, f"summary_{selected_file.replace('.csv', '')}.txt")
                save_summary_report(df, summary_file)
                print(f"摘要报告已生成: {summary_file}")
            else:
                print("文件为空或加载失败")
        else:
            print("无效的文件编号")
    except:
        print("无效输入")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='房产爬虫系统')
    parser.add_argument('--mode', choices=['realestate', 'domain', 'all', 'schedule', 'interactive'], 
                       default='interactive', help='运行模式')
    parser.add_argument('--output', help='输出文件路径（可选）')
    parser.add_argument('--pages', type=int, help='最大页数（可选）')
    parser.add_argument('--delay', type=float, help='请求间隔时间（可选）')
    
    args = parser.parse_args()
    
    # 更新配置（如果提供了参数）
    if args.pages:
        from config import SEARCH_CONFIG
        SEARCH_CONFIG['realestate']['max_pages'] = args.pages
        SEARCH_CONFIG['domain']['max_pages'] = args.pages
    
    if args.delay:
        from config import REQUEST_CONFIG
        REQUEST_CONFIG['rate_limit'] = args.delay
    
    # 根据模式运行
    if args.mode == 'realestate':
        run_single_crawler('realestate')
    elif args.mode == 'domain':
        run_single_crawler('domain')
    elif args.mode == 'all':
        run_all_crawlers()
    elif args.mode == 'schedule':
        scheduler = CrawlerScheduler()
        scheduler.run_scheduler()
    elif args.mode == 'interactive':
        interactive_mode()

if __name__ == "__main__":
    main()