"""
广州海洋经济数据采集模块
模块化设计：演示模式 + 真实数据模式
"""

from .base import BaseDataFetcher, SignalStatus
from .env_data import EnvDataFetcher
from .port_data import PortDataFetcher
from .ais_data import AISDataFetcher
from .enterprise import EnterpriseDataFetcher
from .bidding import BiddingDataFetcher
from .policy import PolicyDataFetcher

__all__ = [
    'BaseDataFetcher',
    'SignalStatus',
    'EnvDataFetcher',
    'PortDataFetcher',
    'AISDataFetcher',
    'EnterpriseDataFetcher',
    'BiddingDataFetcher',
    'PolicyDataFetcher',
]

# 统一数据管理器
class OceanDataManager:
    """海洋数据管理器 - 整合所有数据源"""
    
    def __init__(self, demo_mode=True):
        self.demo_mode = demo_mode
        self.fetchers = {
            'env': EnvDataFetcher(demo_mode=demo_mode),
            'port': PortDataFetcher(demo_mode=demo_mode),
            'ais': AISDataFetcher(demo_mode=demo_mode),
            'enterprise': EnterpriseDataFetcher(demo_mode=demo_mode),
            'bidding': BiddingDataFetcher(demo_mode=demo_mode),
            'policy': PolicyDataFetcher(demo_mode=demo_mode),
        }
        self._cache = {}
    
    def get_signal(self, dimension, family_code=None):
        """
        获取指定维度的信号数据
        
        Args:
            dimension: 信号维度 ID (fund_flow, logistics_flow, etc.)
            family_code: 产业分类代码 (可选)
        
        Returns:
            dict: 信号数据
        """
        mapper = {
            'env_risk': 'env',
            'logistics_flow': 'port',
            'fund_flow': 'bidding',
            'market_entity': 'enterprise',
            'industry_chain': 'enterprise',
            'policy': 'policy',
        }
        
        fetcher_key = mapper.get(dimension, 'env')
        fetcher = self.fetchers.get(fetcher_key)
        
        if fetcher:
            return fetcher.get_signal_for_dimension(dimension, family_code)
        
        return {'status': 'error', 'message': f'Unknown dimension: {dimension}'}
    
    def get_all_signals_for_family(self, family_code, signal_list):
        """
        获取某一"科"的所有信号
        
        Args:
            family_code: 科的代码
            signal_list: 该科拥有的信号维度列表
        
        Returns:
            dict: {signal_id: signal_data}
        """
        results = {}
        for sig_id in signal_list:
            results[sig_id] = self.get_signal(sig_id, family_code)
        return results
