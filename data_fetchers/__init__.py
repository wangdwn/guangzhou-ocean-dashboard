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

    def get_overview_signals(self):
        """顶层 5 路信号灯（整合方案）：海温 / 港口吞吐 / AIS密度 / 海洋灾害 / 企业风险指数"""
        def _conv(res, label, default_unit=''):
            if not res or res.get('status') == 'error':
                return {'color': 'off', 'label': label, 'value': '-', 'unit': default_unit}
            sig = res.get('signal')
            color = sig.value if hasattr(sig, 'value') else str(sig)
            val = res.get('value', res.get('current_container', '-'))
            unit = res.get('unit', default_unit)
            return {'color': color, 'label': label, 'value': val, 'unit': unit, 'source': res.get('source', '')}

        out = {}
        try:
            out['sea_temp'] = _conv(self.fetchers['env'].fetch(days=7), '海表温度', '°C')
        except Exception:
            out['sea_temp'] = {'color': 'off', 'label': '海表温度', 'value': '-', 'unit': '°C'}
        try:
            out['port_throughput'] = _conv(self.fetchers['port'].fetch(), '港口吞吐')
        except Exception:
            out['port_throughput'] = {'color': 'off', 'label': '港口吞吐', 'value': '-'}
        try:
            out['ais_density'] = _conv(self.fetchers['ais'].fetch(), 'AIS船舶密度')
        except Exception:
            out['ais_density'] = {'color': 'off', 'label': 'AIS船舶密度', 'value': '-'}
        try:
            out['enterprise_risk'] = _conv(self.fetchers['enterprise'].fetch(metric='legal_case'), '企业风险指数')
        except Exception:
            out['enterprise_risk'] = {'color': 'off', 'label': '企业风险指数', 'value': '-'}
        try:
            out['marine_disaster'] = self.fetchers['env'].get_disaster_signal()
        except Exception:
            out['marine_disaster'] = {'color': 'off', 'label': '海洋灾害', 'value': '-'}
        return out
