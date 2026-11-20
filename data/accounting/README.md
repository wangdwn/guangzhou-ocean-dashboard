# 核算基准层 data/accounting/

依据 HY/T 0362-2023 双轨方案的低频权威层。  
**补采时点**：2026-10-25（Asia/Shanghai）公开网；省数不作市数；采不到保留〔待核〕。

| 文件 | 维度 | 实测状态 |
|------|------|----------|
| shipping_price_index.json | price_index | **已测** SCFI/CCFI/BDI（均 as_of 2026-10-23） |
| gdp_total.json | gdp_total | **已测** 市 2024=4979亿、2025=5231亿；当季仍〔待核〕；含省背景 |
| employment.json | employment | **部分** 省渔民纯收入 27381.84元(2024)；市涉海就业／报酬仍〔待核〕 |
| sci_tech.json | sci_tech | **部分** 涉海科研机构／重点实验室／工程中心；R&D经费与海洋专利正式统计仍〔待核〕 |
| production_finance.json | production_finance | **部分** 港航快报／蓝碳签发／邮轮客流／活动单位与船舶产值；四上财务汇总仍〔待核〕 |

采集命令：

```bash
python3 scripts/collect_shipping_prices.py
python3 scripts/build_signals_bundle.py
```

纪律：失败写〔待核〕+ log；省数不作市数；不编造 KPI。详见 `docs/公开补采纪要` 或 marine-weekly 同名纪要。
