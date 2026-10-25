#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI：采集航运价格指数 → data/accounting/shipping_price_index.json"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data_fetchers.shipping_price import run  # noqa: E402

if __name__ == "__main__":
    payload = run(write=True)
    print(json_dumps := __import__("json").dumps(
        {
            "status": payload["status"],
            "indices": [
                {"id": i["id"], "value": i["value"], "as_of": i.get("as_of")}
                for i in payload.get("indices") or []
            ],
        },
        ensure_ascii=False,
    ))
    sys.exit(0 if payload["status"] == "ok" else 1)
