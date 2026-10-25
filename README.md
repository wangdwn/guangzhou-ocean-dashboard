# 广州海洋经济信号灯仪表板（双轨 v3）

**广州海洋发展促进中心 | C 质量盘**

双轨融合 **HY/T 0362-2023《海洋经济运行监测指标体系》**：

- **信号流层（高频）**：六流 `signal_dimensions`（资金／物流／市场主体／产业链／环境风险／政策）
- **核算基准层（低频权威）**：`accounting_dimensions` 五维（总量／就业／航运价格／科技／生产经营）

依据文档：[`docs/HYT0362-dual-track-2026-10-21.md`](docs/HYT0362-dual-track-2026-10-21.md)

## 当前数据口径（静态 Pages）

- `index.html` 读取 `industry_tree.json`（**v3.0**）+ `data/signals_bundle.json`
- 六维格子 = 库内证据有／无（或海温实测），**不是**景气红绿灯
- 核算条：有公开数亮灯（如 SCFI／CCFI／省海洋 GDP）；市数〔待核〕灰灯，**禁止编造**；**省数不作市数**
- KPI：结构判断 JSON + 企业名录；SCFI 作为航运旁证 KPI

## 采集与重建

```bash
# 1) 航运价格指数（SCFI/CCFI，能拿到则 BDI）
python3 scripts/collect_shipping_prices.py
# → data/accounting/shipping_price_index.json

# 2) 重建证据包（需本机有兄弟仓库克隆：marine-monitor / enterprises / bidding 等）
python3 scripts/build_signals_bundle.py
# → data/signals_bundle.json
```

核算骨架（低频）：`data/accounting/{gdp_total,employment,sci_tech,production_finance}.json`

## 核心功能

### 信号灯（六流）
产业科 × 六维证据格；海温 NOAA OISST 全区共用。

### 核算基准层入口
总览页核算条 + 产业诊断页已挂维芯片；无数据灰灯〔待核〕。

### 多数据源
1. NOAA ERDDAP 海表温度（22.5°N, 113.5°E）
2. 上海航运交易所公开转载（SCFI／CCFI）+ Investing（BDI，能拿到才写）
3. 经营盘 funding／policies／map；招投标 notices；企业名录 sector
4. 广东海洋 GDP 年报公开报道（仅省景气背景）

---

## 快速启动

```bash
pip install -r requirements.txt
streamlit run app.py   # 可选；静态 Pages 以 index.html 为准
python3 scheduler.py   # 可选定时
```

Pages：https://wangdwn.github.io/guangzhou-ocean-dashboard/

## 文件结构

```
guangzhou-ocean-dashboard/
├── index.html              # 静态质量盘（双轨 UI）
├── industry_tree.json      # v3.0 双轨产业树
├── app.py / data_fetcher.py / scheduler.py
├── data_fetchers/          # 含 shipping_price.py
├── scripts/
│   ├── collect_shipping_prices.py
│   └── build_signals_bundle.py
├── data/
│   ├── signals_bundle.json
│   └── accounting/         # 核算基准层
├── docs/HYT0362-dual-track-2026-10-21.md
└── README.md
```

## 纪律

- 不编造 KPI／海洋 GDP 终值／就业人数
- 自动采集失败 → 〔待核〕+ log
- 省数／全球航运指数不作广州市数

**最后更新**: 2026-10-25（Asia/Shanghai）
