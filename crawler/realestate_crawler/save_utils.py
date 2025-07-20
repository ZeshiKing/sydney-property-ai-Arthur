import csv
import pandas as pd
import os
import logging
from datetime import datetime
from config import DATA_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_to_csv(properties, filename, append=False):
    """
    保存房产数据到CSV文件
    
    Args:
        properties: 房产数据列表
        filename: 文件名或文件路径
        append: 是否追加到现有文件
    """
    if not properties:
        logger.warning("No properties to save")
        return
    
    # 确保数据目录存在
    dirname = os.path.dirname(filename)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)
    
    # 定义CSV列顺序
    columns = [
        'price', 'price_numeric', 'address', 'suburb', 
        'bedrooms', 'bathrooms', 'parking', 'property_type', 
        'link', 'source'
    ]
    
    mode = 'a' if append and os.path.exists(filename) else 'w'
    write_header = not (append and os.path.exists(filename))
    
    try:
        with open(filename, mode, newline='', encoding=DATA_CONFIG['encoding']) as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            
            if write_header:
                writer.writeheader()
            
            for prop in properties:
                # 确保所有必要的字段都存在
                row = {}
                for col in columns:
                    row[col] = prop.get(col, '')
                writer.writerow(row)
        
        logger.info(f"Saved {len(properties)} properties to {filename}")
        
    except Exception as e:
        logger.error(f"Error saving to CSV: {e}")
        raise

def load_from_csv(filename):
    """
    从CSV文件加载房产数据
    
    Args:
        filename: 文件路径
        
    Returns:
        pandas.DataFrame: 房产数据
    """
    try:
        if not os.path.exists(filename):
            logger.warning(f"File {filename} does not exist")
            return pd.DataFrame()
        
        df = pd.read_csv(filename, encoding=DATA_CONFIG['encoding'])
        logger.info(f"Loaded {len(df)} properties from {filename}")
        return df
        
    except Exception as e:
        logger.error(f"Error loading from CSV: {e}")
        return pd.DataFrame()

def merge_csv_files(file_paths, output_file):
    """
    合并多个CSV文件
    
    Args:
        file_paths: CSV文件路径列表
        output_file: 输出文件路径
    """
    all_data = []
    
    for file_path in file_paths:
        df = load_from_csv(file_path)
        if not df.empty:
            all_data.append(df)
    
    if all_data:
        merged_df = pd.concat(all_data, ignore_index=True)
        
        # 去重（基于link字段）
        if 'link' in merged_df.columns:
            merged_df = merged_df.drop_duplicates(subset=['link'])
            logger.info(f"Removed duplicates, {len(merged_df)} unique properties remain")
        
        # 保存合并后的数据
        merged_df.to_csv(output_file, index=False, encoding=DATA_CONFIG['encoding'])
        logger.info(f"Merged data saved to {output_file}")
        
        return merged_df
    else:
        logger.warning("No data to merge")
        return pd.DataFrame()

def clean_data(df):
    """
    清理数据
    
    Args:
        df: pandas.DataFrame
        
    Returns:
        pandas.DataFrame: 清理后的数据
    """
    if df.empty:
        return df
    
    # 创建副本以避免修改原数据
    cleaned_df = df.copy()
    
    # 清理价格数据
    if 'price_numeric' in cleaned_df.columns:
        # 移除价格为0或负数的记录
        cleaned_df = cleaned_df[cleaned_df['price_numeric'] > 0]
        
        # 移除异常高或低的价格（可能是错误数据）
        price_q1 = cleaned_df['price_numeric'].quantile(0.01)
        price_q99 = cleaned_df['price_numeric'].quantile(0.99)
        cleaned_df = cleaned_df[
            (cleaned_df['price_numeric'] >= price_q1) & 
            (cleaned_df['price_numeric'] <= price_q99)
        ]
    
    # 清理房间数据
    for col in ['bedrooms', 'bathrooms', 'parking']:
        if col in cleaned_df.columns:
            # 移除负数
            cleaned_df[col] = cleaned_df[col].apply(lambda x: x if pd.isna(x) or x >= 0 else None)
            # 移除异常高的数值
            cleaned_df[col] = cleaned_df[col].apply(lambda x: x if pd.isna(x) or x <= 20 else None)
    
    # 清理地址和suburb
    for col in ['address', 'suburb']:
        if col in cleaned_df.columns:
            cleaned_df[col] = cleaned_df[col].str.strip()
            cleaned_df[col] = cleaned_df[col].replace('', None)
    
    # 移除没有地址的记录
    if 'address' in cleaned_df.columns:
        cleaned_df = cleaned_df.dropna(subset=['address'])
    
    logger.info(f"Data cleaned: {len(df)} -> {len(cleaned_df)} properties")
    return cleaned_df

def get_data_summary(df):
    """
    获取数据摘要统计
    
    Args:
        df: pandas.DataFrame
        
    Returns:
        dict: 统计信息
    """
    if df.empty:
        return {"total_properties": 0}
    
    summary = {
        "total_properties": len(df),
        "timestamp": datetime.now().isoformat()
    }
    
    # 价格统计
    if 'price_numeric' in df.columns:
        price_data = df['price_numeric'].dropna()
        if not price_data.empty:
            summary["price_stats"] = {
                "mean": price_data.mean(),
                "median": price_data.median(),
                "min": price_data.min(),
                "max": price_data.max(),
                "std": price_data.std()
            }
    
    # 按来源统计
    if 'source' in df.columns:
        summary["by_source"] = df['source'].value_counts().to_dict()
    
    # 按suburb统计
    if 'suburb' in df.columns:
        summary["top_suburbs"] = df['suburb'].value_counts().head(10).to_dict()
    
    # 按房产类型统计
    if 'property_type' in df.columns:
        summary["by_property_type"] = df['property_type'].value_counts().to_dict()
    
    return summary

def save_summary_report(df, output_file):
    """
    保存数据摘要报告
    
    Args:
        df: pandas.DataFrame
        output_file: 输出文件路径
    """
    summary = get_data_summary(df)
    
    with open(output_file, 'w', encoding=DATA_CONFIG['encoding']) as f:
        f.write(f"# 房产数据摘要报告\n")
        f.write(f"生成时间: {summary['timestamp']}\n\n")
        f.write(f"总房产数量: {summary['total_properties']}\n\n")
        
        if 'price_stats' in summary:
            f.write("## 价格统计\n")
            price_stats = summary['price_stats']
            f.write(f"- 平均价格: ${price_stats['mean']:,.2f}\n")
            f.write(f"- 中位价格: ${price_stats['median']:,.2f}\n")
            f.write(f"- 最低价格: ${price_stats['min']:,.2f}\n")
            f.write(f"- 最高价格: ${price_stats['max']:,.2f}\n")
            f.write(f"- 标准差: ${price_stats['std']:,.2f}\n\n")
        
        if 'by_source' in summary:
            f.write("## 按来源统计\n")
            for source, count in summary['by_source'].items():
                f.write(f"- {source}: {count}\n")
            f.write("\n")
        
        if 'top_suburbs' in summary:
            f.write("## 热门区域 (前10)\n")
            for suburb, count in summary['top_suburbs'].items():
                f.write(f"- {suburb}: {count}\n")
            f.write("\n")
        
        if 'by_property_type' in summary:
            f.write("## 按房产类型统计\n")
            for prop_type, count in summary['by_property_type'].items():
                f.write(f"- {prop_type}: {count}\n")
    
    logger.info(f"Summary report saved to {output_file}")

if __name__ == "__main__":
    # 测试功能
    test_properties = [
        {
            'price': '$500,000',
            'price_numeric': 500000,
            'address': '123 Test St, Sydney NSW 2000',
            'suburb': 'Sydney',
            'bedrooms': 2,
            'bathrooms': 1,
            'parking': 1,
            'property_type': 'Apartment',
            'link': 'https://example.com/1',
            'source': 'test'
        }
    ]
    
    # 测试保存功能
    test_file = os.path.join(DATA_CONFIG['output_dir'], 'test.csv')
    save_to_csv(test_properties, test_file)
    
    # 测试加载功能
    df = load_from_csv(test_file)
    print(f"Loaded {len(df)} properties")
    
    # 测试摘要功能
    summary = get_data_summary(df)
    print("Summary:", summary)