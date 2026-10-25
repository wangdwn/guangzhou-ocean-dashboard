#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把可追溯的公开/库内数据打成 signals_bundle.json，供静态质量盘使用。

规则：
- 双轨：六流信号层（高频证据有/无）+ 核算基准层（HY/T 0362 低频权威）。
- 不编造景气红绿灯；产业科×六维格子 = 库内证据有/无（或海温实测）。
- 海温：NOAA coastwatch OISST v2.1 NRT，广州海域格点。
- 价格指数：data/accounting/shipping_price_index.json（SCFI/CCFI/BDI）。
- KPI：结构判断 JSON + 企业名录 meta；核算层无市数标〔待核〕。
失败时写 status=unavailable，前端保持灰灯并标明原因。
"""
from __future__ import annotations

import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "signals_bundle.json"

# 兄弟仓库默认路径（本机 / CI 可覆盖）
WORKSPACE = ROOT.parent
PATHS = {
    "structure": WORKSPACE / "wangdwn.github.io" / "data" / "structure_judgment.json",
    "structure_fallback": WORKSPACE / "marine-monitor" / "app" / "public" / "data" / "structure_judgment.json",
    "enterprises": WORKSPACE / "guangzhou-marine-enterprises" / "data" / "enterprises.json",
    "funding": WORKSPACE / "marine-monitor" / "app" / "public" / "data" / "funding.json",
    "policies": WORKSPACE / "marine-monitor" / "app" / "public" / "data" / "policies.json",
    "map": WORKSPACE / "marine-monitor" / "app" / "public" / "data" / "map.json",
    "notices": WORKSPACE / "geo-ocean-bidding" / "docs" / "data" / "notices.json",
    "tree": ROOT / "industry_tree.json",
    "shipping_prices": ROOT / "data" / "accounting" / "shipping_price_index.json",
    "accounting_gdp": ROOT / "data" / "accounting" / "gdp_total.json",
    "accounting_employment": ROOT / "data" / "accounting" / "employment.json",
    "accounting_sci": ROOT / "data" / "accounting" / "sci_tech.json",
    "accounting_finance": ROOT / "data" / "accounting" / "production_finance.json",
}

# 产业科 → 名录 sector 标签（只映射能对上口径的）
FAMILY_SECTORS = {
    "F07": ["海洋矿业"],
    "F08": ["海洋矿业"],
    "F09": ["海洋矿业"],
    "F10": ["海洋电力业"],
    "F11": ["海洋电力业"],
    "F14": ["海洋生物医药业"],
    "F15": ["海洋船舶工业"],
    "F16": ["海洋船舶工业"],
    "F17": ["海洋船舶工业"],
    "F18": ["海洋工程装备制造业"],
    "F19": ["海洋工程装备制造业"],
    "F22": ["海洋交通运输业"],
    "F23": ["海洋交通运输业"],
    "F24": ["海洋工程建筑业", "海洋工程装备制造业"],
    "F27": ["海洋旅游业"],
    "F28": ["海洋旅游业"],
}

# 产业科额外关键词（匹配专项资金 / 政策 / 招标标题）
FAMILY_KEYWORDS = {
    "F01": ["远洋", "金枪鱼", "捕捞"],
    "F02": ["鱿钓", "远洋渔"],
    "F03": ["对虾", "工厂化养殖", "海水养殖"],
    "F04": ["贝类", "牡蛎", "底播"],
    "F05": ["海洋牧场", "人工鱼礁"],
    "F06": ["水产加工", "冷冻", "调理"],
    "F07": ["油气", "海上油", "中海油"],
    "F08": ["深海采矿", "多金属", "结核"],
    "F09": ["海砂"],
    "F10": ["海上风电", "近海风电", "风电"],
    "F11": ["漂浮式", "深远海风电"],
    "F12": ["潮汐", "波浪能"],
    "F13": ["氢能", "制氢"],
    "F14": ["生物医药", "海洋药物", "蓝碳药"],
    "F15": ["集装箱船", "造船", "船舶建造"],
    "F16": ["LNG", "特种船", "邮轮建造"],
    "F17": ["修船", "船舶改装", "船舶修理"],
    "F18": ["钻井平台", "海工平台"],
    "F19": ["ROV", "AUV", "水下机器人"],
    "F20": ["传感器", "CTD", "ADCP"],
    "F21": ["海洋遥感", "卫星海洋"],
    "F22": ["集装箱码头", "港口", "码头运营", "广州港"],
    "F23": ["航运", "海运", "集装箱运输"],
    "F24": ["海上安装", "航道", "海洋工程"],
    "F25": ["船舶检验", "船级社"],
    "F26": ["风暴潮", "海啸", "海洋预警", "预报"],
    "F27": ["邮轮", "邮轮母港"],
    "F28": ["海岛旅游", "滨海旅游"],
    "F29": ["实验室", "海洋科学"],
    "F30": ["地质调查", "海洋地质"],
    "F31": ["产业基金", "海洋基金"],
    "F32": ["海洋保险", "船舶保险"],
    "F33": ["碳汇", "蓝碳", "碳排放"],
    "F34": ["大数据", "智慧海洋"],
    "F35": ["人工智能", "智能养殖", "智能航运"],
}


def load_json(path: Path):
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def fetch_sst():
    """NOAA OISST v2.1 NRT，广州附近格点。"""
    url = (
        "https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21NrtAgg.json?"
        "sst%5B(2026-10-03T12:00:00Z):1:(last)%5D%5B(0.0):1:(0.0)%5D"
        "%5B(22.5):1:(22.5)%5D%5B(113.5):1:(113.5)%5D"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "wangdw-ocean-dashboard/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        rows = data.get("table", {}).get("rows") or []
        series = []
        for r in rows:
            # time, zlev, lat, lon, sst
            if len(r) < 5 or r[4] is None:
                continue
            series.append(
                {
                    "time": str(r[0])[:10],
                    "sst": round(float(r[4]), 2),
                    "lat": float(r[2]),
                    "lon": float(r[3]),
                }
            )
        if not series:
            return {
                "status": "unavailable",
                "reason": "NOAA 返回空序列",
                "source": "coastwatch ncdcOisst21NrtAgg",
            }
        last = series[-1]
        temp = last["sst"]
        if 22 <= temp <= 29:
            signal = "green"
            label = "适宜区间"
        elif 20 <= temp < 22 or 29 < temp <= 31:
            signal = "yellow"
            label = "偏高/偏低"
        else:
            signal = "red"
            label = "超阈值"
        return {
            "status": "live",
            "value": temp,
            "unit": "°C",
            "signal": signal,
            "label": label,
            "as_of": last["time"],
            "point": {"lat": last["lat"], "lon": last["lon"]},
            "source": "NOAA coastwatch · ncdcOisst21NrtAgg（OISST v2.1 NRT）",
            "rule": "绿灯 22–29°C；黄灯 20–22 或 29–31；红灯其余",
            "note": "广州海域共用格点，非分产业指标",
            "series": series,
        }
    except Exception as e:
        return {
            "status": "unavailable",
            "reason": str(e),
            "source": "coastwatch ncdcOisst21NrtAgg",
        }


def text_blob(obj) -> str:
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, (int, float)):
        return str(obj)
    if isinstance(obj, list):
        return " ".join(text_blob(x) for x in obj)
    if isinstance(obj, dict):
        return " ".join(text_blob(v) for v in obj.values())
    return str(obj)


def match_keywords(text: str, keywords: list[str]) -> list[str]:
    hits = []
    for kw in keywords:
        if kw and kw in text:
            hits.append(kw)
    return hits


def all_families(tree: dict):
    out = []
    for p in tree.get("phyla") or []:
        for c in p.get("classes") or []:
            for o in c.get("orders") or []:
                for f in o.get("families") or []:
                    out.append(
                        {
                            **f,
                            "phylumName": p.get("name"),
                            "className": c.get("name"),
                            "orderName": o.get("name"),
                        }
                    )
    return out


def evidence_cell(state: str, **kwargs):
    cell = {"state": state, **kwargs}
    return cell


def main():
    tree = load_json(PATHS["tree"]) or {}
    structure = load_json(PATHS["structure"]) or load_json(PATHS["structure_fallback"]) or {}
    enterprises = load_json(PATHS["enterprises"]) or {}
    funding = load_json(PATHS["funding"]) or {}
    policies = load_json(PATHS["policies"]) or {}
    mmap = load_json(PATHS["map"]) or {}
    notices = load_json(PATHS["notices"]) or {}
    shipping = load_json(PATHS["shipping_prices"]) or {}
    accounting = {
        "gdp_total": load_json(PATHS["accounting_gdp"]),
        "employment": load_json(PATHS["accounting_employment"]),
        "sci_tech": load_json(PATHS["accounting_sci"]),
        "production_finance": load_json(PATHS["accounting_finance"]),
        "price_index": shipping,
    }

    ent_list = enterprises.get("enterprises") or []
    sector_counts = {}
    for e in ent_list:
        s = e.get("sector") or "未知"
        sector_counts[s] = sector_counts.get(s, 0) + 1

    funding_items = funding.get("items") or []
    policy_items = policies.get("items") or []
    notice_items = notices.get("notices") or []
    map_items = mmap.get("resources") or []

    sst = fetch_sst()

    # KPI 条：只用结构判断里已有实数
    kpis = []
    q = (structure.get("质量盘") or {}).get("metrics") or []
    for m in q:
        kpis.append(
            {
                "id": m.get("id"),
                "label": m.get("label"),
                "value": m.get("value"),
                "unit": m.get("unit") or "家",
                "source": m.get("source"),
                "pan": "质量",
            }
        )
    biz = structure.get("经营盘") or {}
    if biz.get("funding", {}).get("available"):
        kpis.append(
            {
                "id": "funding_count",
                "label": "专项资金条目",
                "value": biz["funding"].get("count"),
                "unit": "条",
                "source": biz["funding"].get("source"),
                "pan": "经营",
            }
        )
    if biz.get("notices", {}).get("available"):
        kpis.append(
            {
                "id": "notices_total",
                "label": "招投标公告",
                "value": biz["notices"].get("total"),
                "unit": "条",
                "source": biz["notices"].get("source"),
                "pan": "经营",
            }
        )
    home = structure.get("家底盘") or {}
    for m in home.get("metrics") or []:
        if m.get("id") == "ent_total":
            kpis.append(
                {
                    "id": "ent_total",
                    "label": m.get("label"),
                    "value": m.get("value"),
                    "unit": m.get("unit") or "家",
                    "source": m.get("source"),
                    "pan": "家底",
                }
            )

    families_out = {}
    for fam in all_families(tree):
        fid = fam.get("id") or fam.get("code")
        code = fam.get("code") or fid
        if not fid:
            continue
        kws = list(FAMILY_KEYWORDS.get(fid, []))
        # also add family name pieces
        name = fam.get("name") or ""
        for part in re.split(r"[/、·\s]+", name):
            if len(part) >= 2 and part not in kws:
                kws.append(part)

        dims = {}
        signal_dims = set(fam.get("signals") or [])

        # fund_flow
        fund_hits = []
        for it in funding_items:
            blob = text_blob(it)
            hits = match_keywords(blob, kws)
            if hits:
                fund_hits.append(
                    {
                        "name": it.get("name"),
                        "status": it.get("status"),
                        "amountRange": it.get("amountRange"),
                        "matched": hits[:4],
                        "basisDoc": it.get("basisDoc"),
                    }
                )
        if "fund_flow" in signal_dims or fund_hits:
            dims["fund_flow"] = evidence_cell(
                "evidence" if fund_hits else "none",
                count=len(fund_hits),
                samples=fund_hits[:3],
                source="marine-monitor/funding.json",
            )

        # policy
        pol_hits = []
        for it in policy_items:
            blob = text_blob(it)
            hits = match_keywords(blob, kws)
            if hits:
                pol_hits.append(
                    {
                        "title": it.get("title"),
                        "issueDate": it.get("issueDate"),
                        "issueOrg": it.get("issueOrg"),
                        "matched": hits[:4],
                    }
                )
        if "policy" in signal_dims or pol_hits:
            dims["policy"] = evidence_cell(
                "evidence" if pol_hits else "none",
                count=len(pol_hits),
                samples=pol_hits[:3],
                source="marine-monitor/policies.json",
            )

        # industry_chain / logistics via notices + map
        notice_hits = []
        for it in notice_items:
            blob = text_blob(it)
            hits = match_keywords(blob, kws)
            if hits:
                notice_hits.append(
                    {
                        "title": it.get("title"),
                        "publish_date": it.get("publish_date"),
                        "source_url": it.get("source_url"),
                        "matched": hits[:4],
                    }
                )
        map_hits = []
        for it in map_items:
            blob = text_blob(it)
            hits = match_keywords(blob, kws)
            if hits:
                map_hits.append(
                    {
                        "resourceName": it.get("resourceName"),
                        "resourceType": it.get("resourceType"),
                        "region": it.get("region"),
                        "matched": hits[:4],
                    }
                )

        if "industry_chain" in signal_dims or notice_hits:
            dims["industry_chain"] = evidence_cell(
                "evidence" if notice_hits else "none",
                count=len(notice_hits),
                samples=notice_hits[:3],
                source="geo-ocean-bidding/notices.json",
            )
        if "logistics_flow" in signal_dims or map_hits or notice_hits:
            # logistics: map resources + port-ish notices
            log_count = len(map_hits) + len(notice_hits)
            dims["logistics_flow"] = evidence_cell(
                "evidence" if log_count else "none",
                count=log_count,
                samples=(map_hits[:2] + notice_hits[:1])[:3],
                source="marine-monitor/map.json + notices.json",
            )

        # 核算维 price_index：挂在物流旁证（有公开指数则 live，否则 pending）
        if "price_index" in signal_dims:
            idx_list = (shipping or {}).get("indices") or []
            if (shipping or {}).get("status") == "ok" and idx_list:
                scfi = next((x for x in idx_list if x.get("id") == "SCFI"), None)
                dims["price_index"] = evidence_cell(
                    "live",
                    signal="green",
                    value=(scfi or idx_list[0]).get("value"),
                    unit="点",
                    label="SCFI" if scfi else idx_list[0].get("id"),
                    as_of=(scfi or idx_list[0]).get("as_of"),
                    indices=[{k: x.get(k) for k in ("id", "value", "as_of", "unit")} for x in idx_list],
                    source="data/accounting/shipping_price_index.json",
                    note="全球航运旁证，不替代广州港吞吐",
                )
            else:
                dims["price_index"] = evidence_cell(
                    "unavailable",
                    reason=(shipping or {}).get("note") or "〔待核〕价格指数未采集到",
                    source="data/accounting/shipping_price_index.json",
                )

        # market_entity from sector counts
        sectors = FAMILY_SECTORS.get(fid) or []
        ent_n = sum(sector_counts.get(s, 0) for s in sectors)
        if "market_entity" in signal_dims or sectors:
            dims["market_entity"] = evidence_cell(
                "evidence" if ent_n else "none",
                count=ent_n,
                sectors=sectors,
                source="guangzhou-marine-enterprises/enterprises.json#sector",
                note="按广海汇名录 sector 字段汇总；「待打标」未计入分产业",
            )

        # env_risk: regional SST shared
        if "env_risk" in signal_dims:
            if sst.get("status") == "live":
                dims["env_risk"] = evidence_cell(
                    "live",
                    signal=sst.get("signal"),
                    value=sst.get("value"),
                    unit=sst.get("unit"),
                    as_of=sst.get("as_of"),
                    source=sst.get("source"),
                    note=sst.get("note"),
                )
            else:
                dims["env_risk"] = evidence_cell(
                    "unavailable",
                    reason=sst.get("reason"),
                    source=sst.get("source"),
                )

        # ensure all six dims present for families that declare them; gray for undeclared
        for d in [
            "fund_flow",
            "logistics_flow",
            "market_entity",
            "industry_chain",
            "env_risk",
            "policy",
        ]:
            if d not in dims:
                if d in signal_dims:
                    dims[d] = evidence_cell("none", count=0, note="库内暂无匹配证据")
                else:
                    dims[d] = evidence_cell("na", note="该科未挂此维")

        families_out[fid] = {
            "id": fid,
            "code": code,
            "name": fam.get("name"),
            "declared_signals": list(signal_dims),
            "dims": dims,
        }

    # 汇总统计（真计数，非随机）
    evidence_cells = 0
    none_cells = 0
    live_cells = 0
    for fam in families_out.values():
        for d, cell in fam["dims"].items():
            if cell["state"] == "evidence":
                evidence_cells += 1
            elif cell["state"] == "none":
                none_cells += 1
            elif cell["state"] == "live":
                live_cells += 1

    # 核算层摘要（供前端灰灯/KPI；无市数保持 pending）
    accounting_summary = []
    for dim_id, payload in accounting.items():
        if not payload:
            accounting_summary.append({
                "id": dim_id,
                "status": "pending",
                "label": dim_id,
                "pending_tag": "〔待核〕",
            })
            continue
        if dim_id == "price_index":
            idxs = payload.get("indices") or []
            accounting_summary.append({
                "id": dim_id,
                "name": "航运价格指数",
                "status": payload.get("status") or ("ok" if idxs else "pending"),
                "indices": [
                    {"id": x.get("id"), "value": x.get("value"), "as_of": x.get("as_of"), "unit": x.get("unit")}
                    for x in idxs
                ],
                "source": "data/accounting/shipping_price_index.json",
            })
            continue
        items = payload.get("items") or []
        ok_items = [it for it in items if it.get("status") == "ok"]
        pending_items = [it for it in items if it.get("status") != "ok"]
        first_ok = ok_items[0] if ok_items else None
        accounting_summary.append({
            "id": dim_id,
            "name": (payload.get("dimension_id") or dim_id),
            "hyt0362": payload.get("hyt0362"),
            "status": "ok" if ok_items and not pending_items else ("partial" if ok_items else "pending"),
            "value": (first_ok or {}).get("value"),
            "unit": (first_ok or {}).get("unit"),
            "label": (first_ok or {}).get("label"),
            "geo": (first_ok or {}).get("geo"),
            "pending_tag": None if (ok_items and not pending_items) else "〔待核〕",
            "ok_count": len(ok_items),
            "pending_count": len(pending_items),
            "source": "data/accounting/",
        })

    # 把 SCFI 作为旁证 KPI（标明全球指数）
    if (shipping or {}).get("status") == "ok":
        for x in shipping.get("indices") or []:
            if x.get("id") == "SCFI":
                kpis.append({
                    "id": "scfi",
                    "label": f"SCFI（{x.get('as_of') or '最新'}）",
                    "value": x.get("value"),
                    "unit": "点",
                    "source": x.get("source_url"),
                    "pan": "核算·价格",
                })
                break

    bundle = {
        "schema": "signals_bundle/1.1",
        "version_note": "dual-track HY/T 0362-2023 + six-flow",
        "generated_at": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H:%M:%S%z"),
        "methodology": (
            "双轨：①信号流层——产业科×六维格子表示库内可追溯证据有/无（非景气灯）；"
            "资金←专项资金库；政策←政策库；产业链←招投标；物流←资源点+公告；"
            "主体←企业名录 sector；环境←NOAA 海温。"
            "②核算基准层——HY/T 0362 五维（总量/就业/价格/科技/生产经营）；"
            "价格指数自动采集；总量仅录已公开省报；市数〔待核〕不编造；省数不作市数。"
        ),
        "kpis": kpis,
        "env_sst": sst,
        "accounting": accounting_summary,
        "shipping_prices": shipping or None,
        "sector_counts": sector_counts,
        "sources": {
            "structure_judgment": (
                str(PATHS["structure"]) if PATHS["structure"].exists()
                else (str(PATHS["structure_fallback"]) if PATHS["structure_fallback"].exists() else None)
            ),
            "enterprises_meta_count": (enterprises.get("meta") or {}).get("count"),
            "funding_updated": funding.get("updated"),
            "funding_count": funding.get("count") or len(funding_items),
            "policies_total": policies.get("total") or len(policy_items),
            "notices_updated": notices.get("updated_at"),
            "notices_count": len(notice_items),
            "map_count": mmap.get("count") or len(map_items),
            "shipping_prices": "data/accounting/shipping_price_index.json",
            "industry_tree_version": tree.get("version"),
        },
        "stats": {
            "family_count": len(families_out),
            "evidence_cells": evidence_cells,
            "none_cells": none_cells,
            "live_cells": live_cells,
        },
        "families": families_out,
        "still_demo_or_unavailable": [
            {
                "item": "广州港集装箱/货物吞吐量实时同比",
                "need": "广州市港务局或统计局可机读接口 / 定期公报手工入库",
            },
            {
                "item": "AIS 船舶密度热力",
                "need": "Global Fishing Watch 或 MarineTraffic API Key + 采集任务",
            },
            {
                "item": "赤潮/风暴潮等灾害预警分色",
                "need": "自然资源部/南海预报中心公开预警接口或人工摘录",
            },
            {
                "item": "分产业科「景气」综合分",
                "need": "上期快照 + 口径加权规则；当前仅证据有无，不做综合分",
            },
            {
                "item": "产业树代表企业名单",
                "need": "仍为结构样例；主体流已改用名录 sector 实数",
            },
            {
                "item": "广州市海洋生产总值（核算层）",
                "need": "市统计调查／公报；已录 2025 广东省数仅作背景",
            },
            {
                "item": "涉海就业人数／劳动报酬",
                "need": "统计年鉴或调查回填",
            },
        ],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)
    print(f"wrote {OUT} families={len(families_out)} evidence={evidence_cells} sst={sst.get('status')}")


if __name__ == "__main__":
    main()
