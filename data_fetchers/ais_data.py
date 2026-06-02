"""
AIS船舶数据获取 - Global Fishing Watch演示模式
真实数据源需API Key
"""

import numpy as np
from datetime import datetime
from .base import BaseDataFetcher, SignalStatus


class AISDataFetcher(BaseDataFetcher):
    """AIS数据获取器 - 物流/交通流"""
    
    def __init__(self, demo_mode=True):
        super().__init__(demo_mode=demo_mode)
        self.source_name = "GFW AIS"
        # Global Fishing Watch API (真实模式需API Key)
        self.api_key = None  # 实际部署时配置
    
    def fetch(self, family_code=None, region="nansha"):
        """
        获取AIS船舶密度数据
        
        Args:
            region: 区域 (nansha:南沙港, guangzhou:广州港全域)
        """
        cache_key = f"ais_{region}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        if not self.demo_mode and self.api_key:
            result = self._fetch_real_data(region)
        else:
            result = self._generate_demo_ais(region)
        
        self._set_cache(cache_key, result)
        return result
    
    def _fetch_real_data(self, region):
        """
        从Global Fishing Watch API获取真实AIS数据
        注：需要API Key，申请地址: https://globalfishingwatch.org/
        """
        try:
            # GFW API调用示例（需真实API Key）
            # url = f"https://gateway.api.globalfishingwatch.org/v3/vessels"
            # headers = {"Authorization": f"Bearer {self.api_key}"}
            # response = requests.get(url, headers=headers, timeout=30)
            
            # 当前返回演示数据（需接入真实API）
            return self._generate_demo_ais(region)
            
        except Exception as e:
            print(f"GFW API调用失败: {e}")
            return self._generate_demo_ais(region)
    
    def _generate_demo_ais(self, region):
        """生成演示AIS数据"""
        # 双峰模式：早高峰6-9点，晚高峰18-21点
        hourly_data = []
        for hour in range(24):
            base = 150
            morning = 40 * np.exp(-((hour - 7.5) ** 2) / 8)
            evening = 50 * np.exp(-((hour - 19.5) ** 2) / 8)
            noise = np.random.normal(0, 10)
            hourly_data.append(max(80, base + morning + evening + noise))
        
        current_hour = datetime.now().hour
        current_count = hourly_data[current_hour]
        
        signal = self._compute_signal(current_count)
        
        return {
            'status': 'demo',
            'value': int(current_count),
            'trend': 0,
            'unit': '艘',
            'source': 'GFW AIS (演示模式)',
            'update': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'signal': signal,
            'data': {
                'hourly': hourly_data,
                'peak': max(hourly_data),
                'avg': np.mean(hourly_data),
            },
            'note': '实际部署需申请Global Fishing Watch API Key'
        }
    
    def _compute_signal(self, vessel_count):
        """计算信号灯状态"""
        if vessel_count >= 180:
            return SignalStatus.GREEN
        elif vessel_count >= 120:
            return SignalStatus.YELLOW
        else:
            return SignalStatus.RED
