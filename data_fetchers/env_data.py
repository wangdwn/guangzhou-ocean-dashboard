"""
环境数据获取 - NOAA ERDDAP海温等
真实数据源接入
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .base import BaseDataFetcher, SignalStatus


class EnvDataFetcher(BaseDataFetcher):
    """环境数据获取器 - 海洋环境/风险流"""
    
    def __init__(self, demo_mode=True):
        super().__init__(demo_mode=demo_mode)
        self.source_name = "NOAA ERDDAP"
        self.base_url = "https://www.ncei.noaa.gov/erddap/griddap/ncdcOisst2Agg.json"
    
    def fetch(self, family_code=None, lat=22.5, lon=113.5, days=30):
        """
        获取海表温度数据
        
        Args:
            lat: 纬度 (广州海域 ~22.5)
            lon: 经度 (广州海域 ~113.5)
            days: 返回多少天的历史数据
        """
        cache_key = f"sst_{lat}_{lon}_{days}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        if not self.demo_mode:
            # 真实模式 - 调用NOAA ERDDAP API
            result = self._fetch_real_data(lat, lon, days)
        else:
            # 演示模式
            result = self._generate_demo_sst(days)
        
        self._set_cache(cache_key, result)
        return result
    
    def _fetch_real_data(self, lat, lon, days):
        """从NOAA ERDDAP获取真实数据"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # ERDDAP查询URL构建
            url = f"{self.base_url}?sst%5B({start_date.strftime('%Y-%m-%d')}T12:00:00Z):1:({end_date.strftime('%Y-%m-%d')}T12:00:00Z)%5D%5B(0.0):1:(0.0)%5D%5B({lat}):1:({lat})%5D%5B({lon}):1:({lon})%5D"
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'table' in data and 'rows' in data['table']:
                    rows = data['table']['rows']
                    
                    if rows and len(rows) > 0:
                        df = pd.DataFrame(rows, columns=['time', 'zlev', 'lat', 'lon', 'sst'])
                        df['time'] = pd.to_datetime(df['time'])
                        df['sst'] = pd.to_numeric(df['sst'], errors='coerce')
                        df = df.dropna(subset=['sst'])
                        
                        if len(df) > 0:
                            current_temp = float(df['sst'].iloc[-1])
                            trend = float(df['sst'].iloc[-7:].mean() - df['sst'].iloc[:7].mean()) if len(df) >= 14 else 0
                            
                            # 信号灯判定
                            signal = self._compute_signal(current_temp)
                            
                            return {
                                'status': 'success',
                                'value': round(current_temp, 1),
                                'trend': round(trend, 2),
                                'unit': '°C',
                                'source': 'NOAA ERDDAP - NCEI OISST v2',
                                'update': datetime.now().strftime('%Y-%m-%d %H:%M'),
                                'signal': signal,
                                'data': df,
                            }
            
            # API调用失败，降级到演示模式
            print(f"NOAA API返回状态码: {response.status_code}，降级到演示模式")
            return self._generate_demo_sst(days)
            
        except Exception as e:
            print(f"NOAA API调用失败: {e}，降级到演示模式")
            return self._generate_demo_sst(days)
    
    def _generate_demo_sst(self, days):
        """生成演示用海温数据"""
        dates = [datetime.now() - timedelta(days=i) for i in range(days, 0, -1)]
        base_temp = 26.5
        temps = []
        
        for d in dates:
            day_of_year = d.timetuple().tm_yday
            seasonal = 2 * np.sin(2 * np.pi * day_of_year / 365)
            noise = np.random.normal(0, 0.5)
            temps.append(base_temp + seasonal + noise)
        
        df = pd.DataFrame({'time': dates, 'sst': temps})
        current_temp = temps[-1]
        trend = temps[-7] - temps[-14] if len(temps) >= 14 else 0
        
        signal = self._compute_signal(current_temp)
        
        return {
            'status': 'demo',
            'value': round(current_temp, 1),
            'trend': round(trend, 2),
            'unit': '°C',
            'source': 'NOAA ERDDAP (演示模式)',
            'update': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'signal': signal,
            'data': df,
            'note': '实际部署时连接NOAA ERDDAP获取真实数据'
        }
    
    def _compute_signal(self, temp):
        """计算信号灯状态"""
        if 22 <= temp <= 29:
            return SignalStatus.GREEN
        elif 20 <= temp < 22 or 29 < temp <= 31:
            return SignalStatus.YELLOW
        else:
            return SignalStatus.RED
