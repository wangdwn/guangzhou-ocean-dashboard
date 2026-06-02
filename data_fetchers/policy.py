"""
政策数据获取 - 国家/省/市政策文件
政策数据采集演示模式
"""

import random
from datetime import datetime
from .base import BaseDataFetcher, SignalStatus


class PolicyDataFetcher(BaseDataFetcher):
    """政策数据获取器 - 政策流"""
    
    def __init__(self, demo_mode=True):
        super().__init__(demo_mode=demo_mode)
        self.source_name = "国家发改委/省市政府"
    
    def fetch(self, family_code=None, level="all"):
        """
        获取政策数据
        
        Args:
            level: all/国家级/省级/市级
        """
        cache_key = f"policy_{level}_{family_code}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        result = self._generate_demo_policy(family_code)
        self._set_cache(cache_key, result)
        return result
    
    def _generate_demo_policy(self, family_code=None):
        """生成演示政策数据"""
        
        # 基于产业代码生成不同数量的政策支持
        base_policies = 8
        if family_code:
            # 某些产业有更多政策支持
            if 'BIO' in family_code or 'ENERGY' in family_code:
                base_policies = 12
            elif 'SHIP' in family_code or 'OIL' in family_code:
                base_policies = 10
            elif 'TOURISM' in family_code:
                base_policies = 6
        
        national = int(base_policies * 0.3)
        provincial = int(base_policies * 0.4)
        municipal = int(base_policies * 0.3)
        
        total = national + provincial + municipal
        funding = random.choice([1000, 2000, 5000, 100, 500])  # 万元
        
        signal = SignalStatus.GREEN if total >= 8 else SignalStatus.YELLOW if total >= 4 else SignalStatus.RED
        
        return {
            'status': 'demo',
            'value': total,
            'trend': round(random.uniform(-10, 50), 1),  # 政策数量环比变化
            'unit': '项',
            'source': '政府信息公开 (演示模式)',
            'update': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'signal': signal,
            'data': {
                'national': national,
                'provincial': provincial,
                'municipal': municipal,
                'funding': funding,
                'recent': [
                    '《广州市海洋经济发展规划2025》',
                    '《广东省海洋牧场建设实施方案》',
                    '《海洋装备产业三年行动计划》',
                ]
            },
            'note': '实际需对接国务院/省市政府信息公开API'
        }
