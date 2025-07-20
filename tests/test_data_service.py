"""
数据服务测试
"""

import pytest
import pandas as pd
import tempfile
import os
from unittest.mock import patch, MagicMock

from backend.services.data_service import DataService
from backend.models.property import UserIntent

class TestDataService:
    """数据服务测试类"""
    
    def setup_method(self):
        """测试设置"""
        self.service = DataService()
    
    def test_load_property_data_success(self):
        """测试成功加载数据"""
        # 创建临时CSV文件
        test_data = {
            'address': ['123 Test St', '456 Demo Ave'],
            'suburb': ['Testville', 'Demoburg'],
            'price': ['$500,000', '$600,000'],
            'price_numeric': [500000, 600000],
            'bedrooms': [2, 3],
            'bathrooms': [1, 2],
            'parking': [1, 2],
            'property_type': ['Apartment', 'House'],
            'link': ['http://test1.com', 'http://test2.com']
        }
        
        df = pd.DataFrame(test_data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            temp_file = f.name
        
        try:
            # 模拟配置
            with patch('backend.services.data_service.settings') as mock_settings:
                mock_settings.PROPERTY_DATA_FILE = temp_file
                
                # 重置缓存
                self.service._df = None
                
                # 测试加载
                result_df = self.service.load_property_data()
                
                assert len(result_df) == 2
                assert 'address' in result_df.columns
                assert result_df['price_numeric'].notna().all()
        
        finally:
            os.unlink(temp_file)
    
    def test_load_property_data_file_not_found(self):
        """测试文件不存在的情况"""
        with patch('backend.services.data_service.settings') as mock_settings:
            mock_settings.PROPERTY_DATA_FILE = '/nonexistent/file.csv'
            
            # 重置缓存
            self.service._df = None
            
            with pytest.raises(FileNotFoundError):
                self.service.load_property_data()
    
    def test_filter_properties_with_intent(self):
        """测试基于意图的房源筛选"""
        # 创建测试数据
        test_data = pd.DataFrame({
            'address': ['123 Bondi St', '456 Chatswood Ave', '789 Bondi Rd'],
            'suburb': ['Bondi', 'Chatswood', 'Bondi'],
            'price': ['$500,000', '$800,000', '$600,000'],
            'price_numeric': [500000, 800000, 600000],
            'bedrooms': [2, 3, 2],
            'bathrooms': [1, 2, 1],
            'parking': [1, 2, 1],
            'property_type': ['Apartment', 'House', 'Apartment'],
            'link': ['http://test1.com', 'http://test2.com', 'http://test3.com']
        })
        
        # 模拟数据加载
        self.service._df = test_data
        
        # 创建测试意图
        intent = UserIntent(
            suburb="Bondi",
            bedrooms=2,
            budget=60  # 60万澳币
        )
        
        # 测试筛选
        result = self.service.filter_properties_flexible(intent)
        
        assert len(result) == 2  # 应该返回2个Bondi的2室房源
        assert all(prop.suburb == "Bondi" for prop in result)
        assert all(prop.bedrooms == 2 for prop in result)
    
    def test_get_property_stats(self):
        """测试获取房产统计信息"""
        # 创建测试数据
        test_data = pd.DataFrame({
            'suburb': ['Bondi', 'Chatswood', 'Bondi'],
            'price_numeric': [500000, 800000, 600000],
            'property_type': ['Apartment', 'House', 'Apartment']
        })
        
        self.service._df = test_data
        
        stats = self.service.get_property_stats()
        
        assert stats['total_properties'] == 3
        assert stats['unique_suburbs'] == 2
        assert stats['avg_price'] == 633333.33 or abs(stats['avg_price'] - 633333.33) < 0.01
        assert 'Apartment' in stats['property_types']
        assert stats['property_types']['Apartment'] == 2