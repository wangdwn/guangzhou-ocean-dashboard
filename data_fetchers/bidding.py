"""
招投标数据获取 - 中国政府采购网
政府采购/招投标演示模式
"""

import random
from datetime import datetime
from .base import BaseDataFetcher, SignalStatus


class BiddingDataFetcher(BaseDataFetcher):
    """招投标数据获取器 - 资金流"""
    
    def __init__(self, demo_mode=True):
        super().__init__(demo_mode=demo_mode)
        self.source_name = "中国政府采购网"
        # 中国政府采购网 http://www.ccgp.gov.cn/
        self.api_base = "http://www.ccgp.gov.cn/"
    
    def fetch(self, family_code=None, region="广州"):
        """
        获取招投标数据
        
        Args:
            region: 地区
        """
        cache_key = f"bidding_{region}_{family_code}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        if not self.demo_mode:
            result = self._fetch_real_data(region)
        else:
            result = self._generate_demo_bidding(family_code)
        
        self._set_cache(cache_key, result)
        return result
    
    def _fetch_real_data(self, region):
        """
        获取真实招投标数据
        注：中国政府采购网有公开API，需申请接入
        """
        try:
            # 实际对接代码（需申请API权限）
            # url = f"{self.api_base}/api/bidding?region={region}"
            # response = requests.get(url, timeout=30)
            
            # 当前返回演示数据
            return self._generate_demo_bidding()
            
        except Exception as e:
            print(f"招投标API调用失败: {e}")
            return self._generate_demo_bidding()
    
    def _generate_demo_bidding(self, family_code=None):
        """生成演示招投标数据"""
        
        # 基于产业代码调整金额
        base_amount = 5000  # 万元
        if family_code:
            code_hash = hash(family_code) % 10
            base_amount = 3000 + code_hash * 800
        
        amount = self._generate_demo_value(base_amount, 0.3)
        count = int(self._generate_demo_value(15, 0.4))
        
        signal = SignalStatus.GREEN if amount > base_amount * 1.1 else SignalStatus.YELLOW if amount > base_amount * 0.9 else SignalStatus.RED
        
        return {
            'status': 'demo',
            'value': round(amount, 1),
            'trend': round(random.uniform(-20, 30), 1),
            'unit': '万元',
            'source': '中国政府采购网 (演示模式)',
            'update': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'signal': signal,
            'data': {
                'project_count': count,
                'total_amount': amount,
                'avg_amount': round(amount / max(count, 1), 1),
            },
            'note': '实际需对接中国政府采购网或省采购平台API'
        }
