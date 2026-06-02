"""
数据采集定时任务
用法: python scheduler.py
   或: nohup python scheduler.py &
"""

import schedule
import time
import json
import os
from datetime import datetime
from data_fetcher import OceanDataFetcher

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

def fetch_all_data():
    """定时任务：采集所有数据源"""
    print(f"[{datetime.now()}] 开始数据采集...")
    
    fetcher = OceanDataFetcher()
    results = {}
    
    # 1. NOAA海温
    try:
        sst = fetcher.fetch_noaa_sst(days=30)
        results['sst'] = {
            'status': sst['status'],
            'current': sst.get('current'),
            'trend': sst.get('trend'),
            'timestamp': datetime.now().isoformat()
        }
        print(f"  ✓ Sea Surface Temp: {sst.get('current', 'N/A')}°C")
    except Exception as e:
        print(f"  ✗ Sea Surface Temp: {e}")
        results['sst'] = {'status': 'error', 'message': str(e)}
    
    # 2. 港口数据  
    try:
        port = fetcher.fetch_guangzhou_port()
        results['port'] = {
            'status': port['status'],
            'container': port.get('current_container'),
            'yoy': port.get('yoy_growth'),
            'timestamp': datetime.now().isoformat()
        }
        print(f"  ✓ Port Data: {port.get('current_container', 'N/A')}万TEU")
    except Exception as e:
        print(f"  ✗ Port Data: {e}")
        results['port'] = {'status': 'error', 'message': str(e)}
    
    # 3. AIS密度
    try:
        ais = fetcher.fetch_ais_density()
        results['ais'] = {
            'status': ais['status'],
            'current': ais.get('current'),
            'avg': ais.get('avg'),
            'timestamp': datetime.now().isoformat()
        }
        print(f"  ✓ AIS Density: {ais.get('current', 'N/A')} vessels")
    except Exception as e:
        print(f"  ✗ AIS Density: {e}")
        results['ais'] = {'status': 'error', 'message': str(e)}
    
    # 保存
    latest_file = os.path.join(DATA_DIR, 'latest.json')
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"  ✓ 数据已保存")
    print(f"[{datetime.now()}] 采集完成\n{'='*50}")

def main():
    print("="*60)
    print("广州海洋经济数据采集调度器")
    print(f"启动: {datetime.now()}")
    print("="*60)
    
    fetch_all_data()
    schedule.every(30).minutes.do(fetch_all_data)
    
    print("\n调度器已启动，Ctrl+C 停止")
    print("周期: 每30分钟\n")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()
