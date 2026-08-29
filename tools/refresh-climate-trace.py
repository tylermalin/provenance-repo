#!/usr/bin/env python3
"""Refresh the Climate TRACE facility snapshot in data/climate-trace.json.

Climate TRACE asks API users to keep volume low and states the v7 API is beta
and not guaranteed for production. So the data is pulled once here and shipped
static rather than called from every visitor's browser.

    python3 tools/refresh-climate-trace.py
"""
import json, time, urllib.request, sys
from pathlib import Path
import re

def write_block(name, blob):
    """Replace `const NAME=...;` in index.html. The data is embedded rather than
    shipped as a sidecar file so the page stays a single self-contained document."""
    root = Path(__file__).resolve().parent.parent
    html = (root / "index.html").read_text()
    new, n = re.subn(rf"const {name}=.*?;\n", f"const {name}={blob};\n", html, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"expected one `const {name}=` block in index.html, found {n}")
    (root / "index.html").write_text(new)

SECTORS = ["power", "manufacturing", "fossil-fuel-operations", "transportation",
           "waste", "mineral-extraction", "agriculture", "buildings"]
YEAR, GAS, PER_SECTOR = 2025, "co2e_100yr", 150

def main():
    out = []
    for s in SECTORS:
        url = (f"https://api.climatetrace.org/v7/sources?year={YEAR}&gas={GAS}"
               f"&sectors={s}&limit={PER_SECTOR}")
        try:
            d = json.load(urllib.request.urlopen(url, timeout=90))
        except Exception as e:
            print(f"{s:26} FAILED {e}", file=sys.stderr); time.sleep(3); continue
        recs = d.get("sources") if isinstance(d, dict) else d
        n = 0
        for r in recs or []:
            c = r.get("centroid") or {}
            lat, lon, q = c.get("latitude"), c.get("longitude"), r.get("emissionsQuantity")
            if lat is None or lon is None or not q:
                continue
            out.append([r.get("name") or "unnamed", round(lat, 3), round(lon, 3),
                        r.get("sector"), r.get("assetType") or "", float(f"{q:.4g}"),
                        r.get("country") or "", r.get("sourceType") or ""])
            n += 1
        print(f"{s:26} +{n}")
        time.sleep(2.5)                      # deliberate: their beta, their bandwidth

    if len(out) < 100:
        sys.exit(f"only {len(out)} facilities resolved; refusing to write")
    out.sort(key=lambda x: -x[5])
    write_block("CT", json.dumps(out, separators=(",", ":")))
    print(f"\nwrote {len(out)} facilities into index.html")

if __name__ == "__main__":
    main()
