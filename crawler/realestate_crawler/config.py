import random
import time

# 代理池配置
PROXY_POOL = [
    # 可以添加免费代理或付费代理
    # 格式: {'http': 'http://proxy_ip:port', 'https': 'https://proxy_ip:port'}
    # 示例（需要替换为实际可用的代理）:
    # {'http': 'http://123.456.789.10:8080', 'https': 'https://123.456.789.10:8080'},
]

# User-Agent池
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0',
]

# 请求配置
REQUEST_CONFIG = {
    'timeout': 10,
    'max_retries': 3,
    'retry_delay': 1,
    'rate_limit': 2,  # 每次请求间隔秒数
}

# 数据保存配置
DATA_CONFIG = {
    'output_dir': 'data',
    'realestate_file': 'realestate_data.csv',
    'domain_file': 'domain_data.csv',
    'encoding': 'utf-8',
}

# 搜索配置
SEARCH_CONFIG = {
    'realestate': {
        'base_url': 'https://www.realestate.com.au',
        'search_url': 'https://www.realestate.com.au/buy/in-sydney,+nsw/list-1',
        'max_pages': 50,
        'items_per_page': 20,
    },
    'domain': {
        'base_url': 'https://www.domain.com.au',
        'search_url': 'https://www.domain.com.au/sale/sydney-nsw/',
        'max_pages': 50,
        'items_per_page': 20,
    }
}

def get_random_user_agent():
    """获取随机User-Agent"""
    return random.choice(USER_AGENTS)

def get_random_proxy():
    """获取随机代理"""
    if PROXY_POOL:
        return random.choice(PROXY_POOL)
    return None

def get_request_headers():
    """获取请求头"""
    return {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

def apply_rate_limit():
    """应用速率限制"""
    time.sleep(REQUEST_CONFIG['rate_limit'])