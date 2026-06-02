"""
企业数据获取 - 信用公示/注册/招聘
企业工商数据演示模式
"""

import random
from datetime import datetime
from .base import BaseDataFetcher, SignalStatus


class EnterpriseDataFetcher(BaseDataFetcher):
    """企业数据获取器 - 市场主体流/产业链流"""
    
    def __init__(self, demo_mode=True):
        super().__init__(demo_mode=demo_mode)
        self.source_name = "天眼查/企查查"
    
    def fetch(self, family_code=None, metric="new_enterprise"):
        """
        获取企业数据
        
        Args:
            metric: new_enterprise(新增注册)/recruitment(招聘)/legal_case(司法)
        """
        cache_key = f"enterprise_{family_code}_{metric}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        result = self._generate_demo_enterprise(family_code, metric)
        self._set_cache(cache_key, result)
        return result
    
    def _generate_demo_enterprise(self, family_code, metric):
        """生成演示企业数据"""
        
        # 基于产业代码生成不同规模的数据
        base_multiplier = 1.0
        if family_code:
            # 不同产业有不同基数
            code_hash = hash(family_code) % 5
            base_multiplier = 0.5 + code_hash * 0.3
        
        if metric == "new_enterprise":
            # 新增企业数
            base = 50 * base_multiplier
            value = self._generate_demo_value(base, 0.3)
            signal = SignalStatus.GREEN if value > base * 1.1 else SignalStatus.YELLOW if value > base * 0.9 else SignalStatus.RED
            
            return {
                'status': 'demo',
                'value': int(value),
                'trend': round(random.uniform(-10, 20), 1),
                'unit': '家',
                'source': '天眼查 (演示模式)',
                'update': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'signal': signal,
                'note': '实际需对接天眼查/企查查API'
            }
        
        elif metric == "recruitment":
            # 招聘人数
            base = 200 * base_multiplier
            value = self._generate_demo_value(base, 0.25)
            signal = SignalStatus.GREEN if value > base * 1.15 else SignalStatus.YELLOW if value > base * 0.85 else SignalStatus.RED
            
            return {
                'status': 'demo',
                'value': int(value),
                'trend': round(random.uniform(-15, 25), 1),
                'unit': '人',
                'source': '智联招聘 (演示模式)',
                'update': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'signal': signal,
                'note': '实际需对接招聘平台API'
            }
        
        elif metric == "legal_case":
            # 司法案件数（越少越好）
            base = 10 * base_multiplier
            value = max(0, self._generate_demo_value(base, 0.4))
            signal = SignalStatus.GREEN if value < 8 else SignalStatus.YELLOW if value < 15 else SignalStatus.RED
            
            return {
                'status': 'demo',
                'value': int(value),
                'trend': round(random.uniform(-20, 10), 1),
                'unit': '件',
                'source': '裁判文书网 (演示模式)',
                'update': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'signal': signal,
                'note': '实际需对接裁判文书网/企查查API'
            }
        
        else:
            return {
                'status': 'error',
                'message': f'Unknown metric: {metric}'
            }
