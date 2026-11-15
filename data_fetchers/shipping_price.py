#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""航运价格指数采集（SCFI / CCFI / BDI）。

规则：只写公开可核数值；抓取失败则 status=unavailable + 错误，禁止编造。
优先：上海航运交易所转载页 / 东方财富等公开快讯；BDI 尝试公开行情页。
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UA = (
    "Mozilla/5.0 (compatible; GuangzhouOceanMonitor/3.0; "
    "+https://wangdwn.github.io/guangzhou-ocean-dashboard/)"
)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "accounting"
OUT_FILE = OUT_DIR / "shipping_price_index.json"
LOG_FILE = OUT_DIR / "shipping_price_index.log"

# 候选公开源（按顺序尝试；官方上航所优先，旧快讯兜底）
SCFI_CCFI_SOURCES = [
    {
        "name": "sse_scfi_table",
        "url": "https://www.sse.net.cn/index/singleIndex?indexType=scfi",
        "kind": "sse_table",
        "index_type": "scfi",
    },
    {
        "name": "sse_ccfi_table",
        "url": "https://www.sse.net.cn/index/singleIndex?indexType=ccfi",
        "kind": "sse_table",
        "index_type": "ccfi",
    },
    {
        "name": "eastmoney_20261023",
        "url": "https://wap.eastmoney.com/a/202610233906214289.html",
        "kind": "html_pair",
    },
    {
        "name": "ths_20261023",
        "url": "https://goodsfu.10jqka.com.cn/20261023/c681019853.shtml",
        "kind": "html_pair",
    },
]

BDI_SOURCES = [
    {
        "name": "balticdryindex_json",
        "url": "https://www.balticdryindex.com/v1/latest",
        "kind": "balticdryindex_json",
    },
    {
        "name": "investing_bdi",
        "url": "https://www.investing.com/indices/baltic-dry",
        "kind": "investing",
    },
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")


def _fetch(url: str, timeout: int = 25) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        charset = "utf-8"
        ctype = resp.headers.get_content_charset()
        if ctype:
            charset = ctype
        return raw.decode(charset, errors="replace")


def _parse_pair_from_html(html: str) -> dict[str, Any] | None:
    """从中文快讯中解析 SCFI / CCFI 综合指数。"""
    scfi = None
    ccfi = None
    scfi_chg = None
    ccfi_chg = None
    as_of = None

    m_date = re.search(r"截至\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", html)
    if m_date:
        # 缺少年份时用当前年（采集日所在年）
        year = datetime.now().year
        as_of = f"{year}-{int(m_date.group(1)):02d}-{int(m_date.group(2)):02d}"

    m_scfi = re.search(
        r"SCFI[^0-9]{0,40}?(\d{3,5}(?:\.\d+)?)\s*点",
        html,
        re.I,
    )
    if m_scfi:
        scfi = float(m_scfi.group(1))

    m_scfi_chg = re.search(
        r"SCFI[^。]{0,80}?(?:上涨|上涨了|涨)(\d+(?:\.\d+)?)\s*点|(?:与上期相比上涨)(\d+(?:\.\d+)?)\s*点",
        html,
    )
    if m_scfi_chg:
        scfi_chg = float(m_scfi_chg.group(1) or m_scfi_chg.group(2))

    m_ccfi = re.search(
        r"CCFI[^0-9]{0,40}?(\d{3,5}(?:\.\d+)?)\s*点",
        html,
        re.I,
    )
    if m_ccfi:
        ccfi = float(m_ccfi.group(1))

    m_ccfi_chg = re.search(
        r"CCFI[^。]{0,100}?(?:跌|下跌|跌幅)[^0-9]{0,6}(\d+(?:\.\d+)?)\s*%",
        html,
    )
    if m_ccfi_chg:
        ccfi_chg = -float(m_ccfi_chg.group(1))  # percent

    if scfi is None and ccfi is None:
        return None
    return {
        "scfi": scfi,
        "ccfi": ccfi,
        "scfi_change_points": scfi_chg,
        "ccfi_change_pct": ccfi_chg,
        "as_of": as_of,
    }


def _parse_sse_table(html: str, index_type: str = "scfi") -> dict[str, Any] | None:
    """解析上航所 SCFI/CCFI 页面表格中的综合指数（上期/本期/涨跌）。

    表格结构：综合指数 Comprehensive Index | 上期值 | 本期值 | 涨跌
    """
    m = re.search(
        r"综合指数[\s\S]{0,200}?(\d+\.\d+)\s*</td>\s*<td[^>]*>\s*(\d+\.\d+)\s*</td>\s*<td[^>]*>\s*([-\d.]+)",
        html,
    )
    if not m:
        return None
    prev, cur, chg = float(m.group(1)), float(m.group(2)), float(m.group(3))
    # 提取"本期<br>YYYY-MM-DD"作为数据日期
    as_of = None
    m_date = re.search(r"本期[\s\S]{0,20}?(20\d{2}-\d{2}-\d{2})", html)
    if m_date:
        as_of = m_date.group(1)
    if index_type == "ccfi":
        # CCFI 涨跌为百分比
        return {"scfi": None, "ccfi": cur, "scfi_change_points": None, "ccfi_change_pct": chg, "as_of": as_of}
    # SCFI 涨跌为点数
    return {"scfi": cur, "ccfi": None, "scfi_change_points": chg, "ccfi_change_pct": None, "as_of": as_of}


def collect_scfi_ccfi() -> dict[str, Any]:
    errors: list[str] = []
    scfi = ccfi = None
    scfi_chg = ccfi_chg = None
    as_of = None
    used_sources: list[str] = []

    # 1. 优先官方上海航交所（SCFI 与 CCFI 分别从各自页面采，均为最新周度数据）
    for src in SCFI_CCFI_SOURCES:
        if src["kind"] != "sse_table":
            continue
        try:
            html = _fetch(src["url"])
            parsed = _parse_sse_table(html, src.get("index_type", "scfi"))
            if not parsed:
                errors.append(f"{src['name']}: parse_empty")
                continue
            used_sources.append(src["name"])
            if parsed.get("scfi") is not None:
                scfi = parsed["scfi"]
                scfi_chg = parsed.get("scfi_change_points")
            if parsed.get("ccfi") is not None:
                ccfi = parsed["ccfi"]
                ccfi_chg = parsed.get("ccfi_change_pct")
            if parsed.get("as_of"):
                as_of = parsed["as_of"]
        except Exception as e:  # noqa: BLE001
            errors.append(f"{src['name']}: {type(e).__name__}: {e}")

    # 2. 官方源未取到任一指数时，fallback 中文快讯（历史转载，可能滞后）
    if scfi is None and ccfi is None:
        for src in SCFI_CCFI_SOURCES:
            if src["kind"] != "html_pair":
                continue
            try:
                html = _fetch(src["url"])
                parsed = _parse_pair_from_html(html)
                if not parsed or (parsed.get("scfi") is None and parsed.get("ccfi") is None):
                    errors.append(f"{src['name']}: parse_empty")
                    continue
                used_sources.append(src["name"])
                scfi = parsed.get("scfi")
                ccfi = parsed.get("ccfi")
                scfi_chg = parsed.get("scfi_change_points")
                ccfi_chg = parsed.get("ccfi_change_pct")
                as_of = parsed.get("as_of")
                break
            except Exception as e:  # noqa: BLE001
                errors.append(f"{src['name']}: {type(e).__name__}: {e}")

    if scfi is None and ccfi is None:
        return {
            "status": "unavailable",
            "fetched_at": _now_iso(),
            "errors": errors,
            "scfi": None,
            "ccfi": None,
            "note": "〔待核〕公开源抓取失败，未写入假数",
        }

    return {
        "status": "ok",
        "source_name": "+".join(used_sources),
        "source_url": "https://www.sse.net.cn/index/singleIndex",
        "fetched_at": _now_iso(),
        "scfi": scfi,
        "ccfi": ccfi,
        "scfi_change_points": scfi_chg,
        "ccfi_change_pct": ccfi_chg,
        "as_of": as_of,
    }


def collect_bdi() -> dict[str, Any]:
    errors: list[str] = []
    for src in BDI_SOURCES:
        try:
            html = _fetch(src["url"])
            # balticdryindex.com 免费 JSON：{"index":"BDI","value":...,"change":...,"pct":...,"date":...}
            if src["kind"] == "balticdryindex_json":
                j = json.loads(html)
                if j.get("value") is None:
                    errors.append(f"{src['name']}: json_no_value")
                    continue
                return {
                    "status": "ok",
                    "source_name": src["name"],
                    "source_url": src["url"],
                    "fetched_at": _now_iso(),
                    "bdi": float(j["value"]),
                    "as_of": j.get("date"),
                    "change_points": j.get("change"),
                    "source_display": j.get("source", "Baltic Exchange"),
                }
            # investing: data-test="instrument-price-last"
            m = re.search(
                r'data-test="instrument-price-last"[^>]*>\s*([0-9,]+\.?\d*)',
                html,
            )
            if not m:
                m = re.search(r'"last"\s*:\s*"?([0-9,]+\.?\d*)"?', html)
            if not m:
                errors.append(f"{src['name']}: parse_empty")
                continue
            val = float(m.group(1).replace(",", ""))
            return {
                "status": "ok",
                "source_name": src["name"],
                "source_url": src["url"],
                "fetched_at": _now_iso(),
                "bdi": val,
            }
        except Exception as e:  # noqa: BLE001
            errors.append(f"{src['name']}: {type(e).__name__}: {e}")
    return {
        "status": "unavailable",
        "fetched_at": _now_iso(),
        "errors": errors,
        "bdi": None,
        "note": "〔待核〕BDI 公开源抓取失败",
    }


def run(write: bool = True) -> dict[str, Any]:
    scfi_ccfi = collect_scfi_ccfi()
    bdi = collect_bdi()
    indices = []
    if scfi_ccfi.get("scfi") is not None:
        indices.append(
            {
                "id": "SCFI",
                "name": "上海出口集装箱运价指数（综合）",
                "value": scfi_ccfi["scfi"],
                "unit": "点",
                "change_points": scfi_ccfi.get("scfi_change_points"),
                "as_of": scfi_ccfi.get("as_of"),
                "source_url": scfi_ccfi.get("source_url"),
                "hyt0362": "H（海运价）",
            }
        )
    if scfi_ccfi.get("ccfi") is not None:
        indices.append(
            {
                "id": "CCFI",
                "name": "中国出口集装箱运价综合指数",
                "value": scfi_ccfi["ccfi"],
                "unit": "点",
                "change_pct": scfi_ccfi.get("ccfi_change_pct"),
                "as_of": scfi_ccfi.get("as_of"),
                "source_url": scfi_ccfi.get("source_url"),
                "hyt0362": "H（海运价）",
            }
        )
    if bdi.get("bdi") is not None:
        indices.append(
            {
                "id": "BDI",
                "name": "波罗的海干散货指数",
                "value": bdi["bdi"],
                "unit": "点",
                "as_of": bdi.get("as_of"),
                "change_points": bdi.get("change_points"),
                "source_url": bdi.get("source_url"),
                "source_name": bdi.get("source_display"),
                "hyt0362": "H（海运价）",
            }
        )

    overall = "ok" if indices else "unavailable"
    payload = {
        "schema": "shipping_price_index/1.0",
        "dimension_id": "price_index",
        "generated_at": _now_iso(),
        "status": overall,
        "indices": indices,
        "raw": {"scfi_ccfi": scfi_ccfi, "bdi": bdi},
        "note": "旁证全球航运景气，不替代广州港吞吐 KPI；省/全球指数不作市数。",
    }
    if write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        with OUT_FILE.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
        with LOG_FILE.open("a", encoding="utf-8") as log:
            log.write(f"{payload['generated_at']} status={overall} n={len(indices)}\n")
            if scfi_ccfi.get("errors"):
                log.write("  scfi_errors: " + "; ".join(scfi_ccfi["errors"]) + "\n")
            if bdi.get("errors"):
                log.write("  bdi_errors: " + "; ".join(bdi["errors"]) + "\n")
        print(f"wrote {OUT_FILE} status={overall} indices={len(indices)}")
    return payload


if __name__ == "__main__":
    run(write=True)
