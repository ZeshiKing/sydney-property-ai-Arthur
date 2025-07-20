import schedule
import time
import logging
from datetime import datetime
from realestate_spider import RealEstateSpider
from domain_spider import DomainSpider
from save_utils import save_to_csv
from config import DATA_CONFIG
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CrawlerScheduler:
    def __init__(self):
        self.realestate_spider = RealEstateSpider()
        self.domain_spider = DomainSpider()
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """确保数据目录存在"""
        if not os.path.exists(DATA_CONFIG['output_dir']):
            os.makedirs(DATA_CONFIG['output_dir'])
            logger.info(f"Created data directory: {DATA_CONFIG['output_dir']}")
    
    def run_realestate_scraper(self):
        """运行realestate.com.au爬虫"""
        logger.info("Starting scheduled realestate.com.au scraping...")
        try:
            properties = self.realestate_spider.run()
            if properties:
                filename = f"realestate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                filepath = os.path.join(DATA_CONFIG['output_dir'], filename)
                save_to_csv(properties, filepath)
                logger.info(f"Realestate.com.au scraping completed. Saved {len(properties)} properties to {filepath}")
            else:
                logger.warning("No properties found from realestate.com.au")
        except Exception as e:
            logger.error(f"Error in realestate.com.au scraping: {e}")
    
    def run_domain_scraper(self):
        """运行domain.com.au爬虫"""
        logger.info("Starting scheduled domain.com.au scraping...")
        try:
            properties = self.domain_spider.run()
            if properties:
                filename = f"domain_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                filepath = os.path.join(DATA_CONFIG['output_dir'], filename)
                save_to_csv(properties, filepath)
                logger.info(f"Domain.com.au scraping completed. Saved {len(properties)} properties to {filepath}")
            else:
                logger.warning("No properties found from domain.com.au")
        except Exception as e:
            logger.error(f"Error in domain.com.au scraping: {e}")
    
    def run_both_scrapers(self):
        """运行两个爬虫"""
        logger.info("Starting scheduled scraping for both sites...")
        
        # 运行realestate.com.au爬虫
        self.run_realestate_scraper()
        
        # 等待一段时间再运行domain.com.au爬虫
        time.sleep(60)  # 等待1分钟
        
        # 运行domain.com.au爬虫
        self.run_domain_scraper()
        
        logger.info("Scheduled scraping for both sites completed.")
    
    def setup_schedule(self):
        """设置定时任务"""
        # 每天早上9点运行
        schedule.every().day.at("09:00").do(self.run_both_scrapers)
        
        # 每天下午6点运行
        schedule.every().day.at("18:00").do(self.run_both_scrapers)
        
        # 每周一早上8点运行
        schedule.every().monday.at("08:00").do(self.run_both_scrapers)
        
        # 可以根据需要添加更多定时任务
        # schedule.every(4).hours.do(self.run_both_scrapers)  # 每4小时运行一次
        # schedule.every().hour.do(self.run_realestate_scraper)  # 每小时运行realestate爬虫
        
        logger.info("Scheduled tasks set up:")
        logger.info("- Daily at 09:00 and 18:00")
        logger.info("- Weekly on Monday at 08:00")
    
    def run_scheduler(self):
        """运行调度器"""
        self.setup_schedule()
        logger.info("Scheduler started. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user.")
    
    def run_once(self):
        """立即运行一次爬虫（用于测试）"""
        logger.info("Running scrapers once for testing...")
        self.run_both_scrapers()

# 命令行工具函数
def run_manual_scraping():
    """手动运行爬虫"""
    scheduler = CrawlerScheduler()
    
    print("\n选择要运行的爬虫:")
    print("1. 仅运行 realestate.com.au")
    print("2. 仅运行 domain.com.au")
    print("3. 运行两个爬虫")
    print("4. 启动定时任务")
    
    choice = input("请输入选择 (1-4): ").strip()
    
    if choice == "1":
        scheduler.run_realestate_scraper()
    elif choice == "2":
        scheduler.run_domain_scraper()
    elif choice == "3":
        scheduler.run_both_scrapers()
    elif choice == "4":
        scheduler.run_scheduler()
    else:
        print("无效选择")

if __name__ == "__main__":
    run_manual_scraping()