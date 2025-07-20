"""
用户意图处理器测试
"""

import pytest
from ai.processors.intent_processor import IntentProcessor

class TestIntentProcessor:
    """意图处理器测试类"""
    
    def setup_method(self):
        """测试设置"""
        self.processor = IntentProcessor(api_key=None)  # 使用fallback模式测试
    
    def test_extract_suburb(self):
        """测试区域提取"""
        test_cases = [
            ("我想在Bondi买房", "Bondi"),
            ("找个Chatswood附近的房子", "Chatswood"),
            ("Hornsby那边有什么好房源", "Hornsby"),
            ("没有区域信息", None)
        ]
        
        for text, expected in test_cases:
            result = self.processor._extract_suburb(text)
            assert result == expected
    
    def test_extract_bedrooms(self):
        """测试卧室数量提取"""
        test_cases = [
            ("我要2室的房子", 2),
            ("3b的公寓", 3),
            ("双卧室", 2),
            ("1bedroom", 1),
            ("没有卧室信息", None)
        ]
        
        for text, expected in test_cases:
            result = self.processor._extract_bedrooms(text)
            assert result == expected
    
    def test_extract_budget(self):
        """测试预算提取"""
        test_cases = [
            ("预算100万", 100.0),
            ("80万以内", 80.0),
            ("不超过150万", 150.0),
            ("120w左右", 120.0),
            ("没有预算信息", None)
        ]
        
        for text, expected in test_cases:
            result = self.processor._extract_budget(text)
            assert result == expected
    
    def test_extract_special_requirements(self):
        """测试特殊要求提取"""
        text = "我要安静的环境，靠近学校，有停车位"
        result = self.processor._extract_special_requirements(text)
        
        expected = ["环境安静", "靠近学校", "停车位"]
        assert all(req in result for req in expected)
    
    def test_extract_intent_complete(self):
        """测试完整意图提取"""
        text = "我想在Bondi找个2室的房子，预算100万，要安静的环境"
        intent = self.processor.extract_intent(text)
        
        assert intent.suburb == "Bondi"
        assert intent.bedrooms == 2
        assert intent.budget == 100.0
        assert "环境安静" in intent.special_requirements
    
    def test_has_criteria(self):
        """测试意图验证"""
        intent = self.processor.extract_intent("我想在Bondi买房")
        assert intent.has_criteria() == True
        
        intent = self.processor.extract_intent("随便看看")
        assert intent.has_criteria() == False