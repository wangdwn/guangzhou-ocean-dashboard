"""
数据采集基类 - 所有fetcher的父类
支持演示模式和真实数据模式
"""

from datetime import datetime, timedelta
from enum import Enum
import random
import json


class SignalStatus(Enum):
    """信号状态枚举"""
    GREEN = "green"      # 良好/活跃
    YELLOW = "yellow"    # 一般/平稳
    RED = "red"          # 异常/下滑
    OFF = "off"          # 无数据


class BaseDataFetcher:
    """数据采集基类"""
    
    def __init__(self, demo_mode=True, cache_ttl=3600):
        """
        Args:
            demo_mode: True=使用演示数据, False=使用真实API
            cache_ttl: 缓存时间(秒)
        """
        self.demo_mode = demo_mode
        self.cache_ttl = cache_ttl
        self._cache = {}
        self._cache_time = {}
        self.source_name = "Base"
    
    def _get_cached(self, key):
        """获取缓存数据"""
        if key in self._cache:
            cached_time = self._cache_time.get(key)
            if cached_time and (datetime.now() - cached_time).seconds < self.cache_ttl:
                return self._cache[key]
        return None
    
    def _set_cache(self, key, data):
        """设置缓存"""
        self._cache[key] = data
        self._cache_time[key] = datetime.now()
    
    def fetch(self, **kwargs):
        """
        主数据获取方法 - 子类必须实现
        
        Returns:
            dict: 统一格式的数据
                {
                    'status': 'success'|'demo'|'error',
                    'value': float,  # 当前值
                    'trend': float,  # 趋势(周/月)
                    'unit': str,     # 单位
                    'source': str,   # 数据来源
                    'update': str,   # 更新时间
                    'signal': SignalStatus,  # 信号灯状态
                    'data': any,     # 详细数据(可选)
                }
        """
        raise NotImplementedError("子类必须实现fetch方法")
    
    def get_signal_for_dimension(self, dimension_id, family_code=None):
        """
        为特定信号维度获取信号
        
        Args:
            dimension_id: 信号维度ID
            family_code: 产业分类代码
        
        Returns:
            dict: 信号数据
        """
        data = self.fetch(family_code=family_code)
        
        # 转换为统一的信号格式
        signal_color = data.get('signal', SignalStatus.OFF).value
        signal_label = self._get_signal_label(signal_color, dimension_id)
        
        return {
            'status': data.get('status', 'error'),
            'dimension': dimension_id,
            'family_code': family_code,
            'color': signal_color,
            'label': signal_label,
            'value': data.get('value'),
            'trend': data.get('trend'),
            'unit': data.get('unit', ''),
            'source': data.get('source', self.source_name),
            'update': data.get('update', datetime.now().strftime('%Y-%m-%d %H:%M')),
            'raw_data': data.get('data'),
        }
    
    def _get_signal_label(self, color, dimension_id):
        """根据信号灯颜色生成标签"""
        mapper = {
            'fund_flow': {'green': '融资活跃', 'yellow': '融资平稳', 'red': '融资收紧', 'off': '数据缺失'},
            'logistics_flow': {'green': '物流畅通', 'yellow': '物流正常', 'red': '物流受阻', 'off': '数据缺失'},
            'market_entity': {'green': '主体活跃', 'yellow': '主体平稳', 'red': '主体萎缩', 'off': '数据缺失'},
            'industry_chain': {'green': '产业链强', 'yellow': '产业链稳', 'red': '产业链弱', 'off': '数据缺失'},
            'env_risk': {'green': '环境安全', 'yellow': '环境一般', 'red': '环境风险', 'off': '数据缺失'},
            'policy': {'green': '政策利好', 'yellow': '政策中性', 'red': '政策收紧', 'off': '数据缺失'},
        }
        return mapper.get(dimension_id, {}).get(color, '未知')
    
    def _generate_demo_value(self, base, variance=0.2, trend=0):
        """生成演示数据 - 基于种子保证可重复性"""
        if family_code := random.random():
            random.seed(hash(str(family_code)) % 10000)
        
        value = base * (1 + random.uniform(-variance, variance))
        if trend:
            value += trend
        
        return round(value, 2)
