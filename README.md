# 🚢 广州海洋经济信号灯仪表板

**广州海洋发展促进中心 | 胜哥项目**

基于钱学森系统工程控制论思想的多信号交叉验证仪表板——像看楼房空置率，有人看开灯、有人看水表、有人看电表，叠在一起就八九不离十。

---

## 核心功能

### 🚦 信号灯系统
- **海洋环境** (绿/黄/红)：海温数据 → 自然条件基础
- **港口物流** (绿/黄/红)：吞吐量 → 实体经济晴雨表
- **航运交通** (绿/黄/红)：AIS密度 → 实时物流脉搏
- **综合判断** (绿/黄/红)：加权融合 → 最终信号

### 📊 多数据源
1. **NOAA ERDDAP** - 海表温度 (22.5°N, 113.5°E)
2. **广州港公开数据** - 集装箱/货物吞吐量
3. **AIS船舶密度** - Global Fishing Watch / MarineTraffic

---

## 快速启动

### 1. 安装依赖
```bash
cd /Users/macos13/WorkBuddy/海洋经济仪表板
pip install -r requirements.txt
```

### 2. 启动仪表板
```bash
streamlit run app.py
```
浏览器自动打开 http://localhost:8501

### 3. 启动定时采集 (后台)
```bash
python scheduler.py
# 或后台运行
nohup python scheduler.py > data_collection.log 2>&1 &
```

---

## 文件结构

```
海洋经济仪表板/
├── app.py              # Streamlit主程序 (仪表板)
├── data_fetcher.py     # 数据采集模块
├── scheduler.py        # 定时采集任务
├── requirements.txt    # Python依赖
├── data/              # 数据缓存目录
│   └── latest.json    # 最新采集数据
└── README.md          # 本文件
```

---

## 信号灯逻辑

### 单信号判定
| 指标 | 绿灯 | 黄灯 | 红灯 |
|------|------|------|------|
| 海温 | 22-29°C | 20-22°C或29-31°C | <20°C或>31°C |
| 港口同比 | ≥5% | 0%-5% | <0% |
| AIS密度 | ≥180艘 | 120-180艘 | <120艘 |

### 综合信号
- **🟢 绿 (景气)**：全部绿灯或多绿少黄
- **🟡 黄 (平稳)**：1个红灯 或 2个黄灯
- **🔴 红 (预警)**：2个及以上红灯

---

## 数据源配置

### NOAA ERDDAP (已接入)
- 数据集: NCEI OISST v2
- 坐标: 22.5°N, 113.5°E (广州海域)
- URL: https://www.ncei.noaa.gov/erddap/griddap/ncdcOisst2Agg

### 广州港数据 (演示模式)
- 来源: 广州市港务局/统计局
- 实际部署: 需接入官方API或爬虫

### AIS密度 (演示模式)
- 需配置: Global Fishing Watch API Key
- 或: MarineTraffic API Key
- 参考: https://globalfishingwatch.org/api/

---

## 部署建议

### 方式1: 本地开发
```bash
streamlit run app.py
```

### 方式2: 服务器部署
```bash
# 使用screen后台运行
screen -S ocean-dashboard
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### 方式3: 生产环境
- 配置nginx反向代理
- 配置HTTPS
- 使用systemd管理进程

---

## 待扩展数据源

- [ ] GFW API - 船舶AIS热力图
- [ ] 广州海事法院 - 案件数量
- [ ] 招投标平台 - 海洋工程项目
- [ ] 南海环境数据 - 叶绿素/盐度
- [ ] 海关数据 - 外贸进出口

---

## 技术栈

- **前端**: Streamlit + Plotly
- **后端**: Python 3.9+
- **数据源**: NOAA ERDDAP, 公开API
- **定时任务**: schedule库

---

## 许可证

内部使用 | 广州海洋发展促进中心

---

**最后更新**: 2025-06
