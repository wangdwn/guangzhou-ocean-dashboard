# 核算基准层 data/accounting/

依据 HY/T 0362-2023 双轨方案的低频权威层。

| 文件 | 维度 | 说明 |
|------|------|------|
| shipping_price_index.json | price_index | 自动采集 SCFI/CCFI（及可拿到的 BDI） |
| gdp_total.json | gdp_total | 已写入 2025 广东海洋 GDP（省数）；市数〔待核〕 |
| employment.json | employment | 〔待核〕占位 |
| sci_tech.json | sci_tech | 〔待核〕占位 |
| production_finance.json | production_finance | 〔待核〕占位 |

采集命令：

```bash
python3 scripts/collect_shipping_prices.py
python3 scripts/build_signals_bundle.py
```

纪律：失败写〔待核〕+ log；省数不作市数；不编造 KPI。
