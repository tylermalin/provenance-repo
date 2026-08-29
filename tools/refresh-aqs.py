#!/usr/bin/env python3
"""Refresh the EPA AQS regulatory monitor snapshot in data/aqs-monitors.json.

Layer 14 of the AQS monitor sites service is the active PM2.5 NAAQS/AQI network.
EPA's ArcGIS endpoints send no CORS header, so this is pulled server side and
shipped static rather than fetched from the browser.

    python3 tools/refresh-aqs.py
"""
import json, sys, urllib.request
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

BASE = ("https://gispub.epa.gov/arcgis/rest/services/OAR_OAQPS/"
        "AQSmonitor_sites/MapServer/14/query")
FIELDS = ("Local_Site_Name,City,State,Latitude,Longitude,Sample_Duration,"
          "Sample_Collection_Frequency,Sample_Collection_Method,"
          "Last_Sample_Date,LatLon_Accuracy_meters")

def main():
    recs, off = [], 0
    while True:
        url = (f"{BASE}?where=1%3D1&outFields={FIELDS}&resultOffset={off}"
               f"&resultRecordCount=1000&f=json")
        d = json.load(urllib.request.urlopen(url, timeout=120))
        fs = d.get("features", [])
        if not fs:
            break
        recs += [f["attributes"] for f in fs]
        off += len(fs)
        if not d.get("exceededTransferLimit"):
            break
    if len(recs) < 100:
        sys.exit(f"only {len(recs)} monitors resolved; refusing to write")

    methods, freqs = [], []
    def idx(lst, v):
        if v not in lst: lst.append(v)
        return lst.index(v)

    sites = []
    for r in recs:
        la, lo = r.get("Latitude"), r.get("Longitude")
        if la is None or lo is None:
            continue
        sites.append([
            (r.get("Local_Site_Name") or r.get("City") or "AQS site").strip()[:44],
            round(la, 4), round(lo, 4),
            idx(methods, r.get("Sample_Collection_Method") or "?"),
            idx(freqs, r.get("Sample_Collection_Frequency") or "?"),
            r.get("LatLon_Accuracy_meters"),
            (r.get("Last_Sample_Date") or "")[:10],
        ])

    write_block("AQS", json.dumps({"methods": methods, "freqs": freqs, "sites": sites},
                                  separators=(",", ":")))
    print(f"wrote {len(sites)} monitors, {len(methods)} instrument models into index.html")

if __name__ == "__main__":
    main()
