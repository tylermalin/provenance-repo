#!/usr/bin/env python3
"""Refresh the embedded TLE snapshot in index.html.

Orbital elements lose accuracy over weeks. Run this monthly, or the satellite
positions will drift from truth. CelesTrak sends no CORS header, which is why
the elements are embedded at build time rather than fetched in the browser.

    python3 tools/refresh-tle.py
"""
import json, re, sys, urllib.request
from pathlib import Path

GROUPS = {
    'weather':  'Polar weather · sounding and imaging',
    'resource': 'Earth resources · land, vegetation, fire',
    'goes':     'Geostationary · continuous hemispheric imaging',
    'science':  'Science · atmosphere, ocean, cryosphere',
}
KEEP = re.compile(r'NOAA|METOP|SUOMI|GOES|SENTINEL|LANDSAT|TERRA(?!SAR)|AQUA|AURA|ICESAT'
                  r'|CLOUDSAT|CALIPSO|SMAP|GRACE|JASON|SWOT|PACE|OCO|GCOM|HIMAWARI'
                  r'|FENGYUN|METEOSAT|SARAL|CRYOSAT|SAOCOM|PROBA|GOSAT|TROPICS|CYGNSS', re.I)
DROP = re.compile(r'DEB|R/B|TERRASAR|SKYTERRA|EWS-G|\bAIS\b', re.I)
PER_GROUP = 18

def fetch(group):
    url = f'https://celestrak.org/NORAD/elements/gp.php?GROUP={group}&FORMAT=tle'
    return urllib.request.urlopen(url, timeout=30).read().decode()

def main():
    out, seen = [], set()
    for group, desc in GROUPS.items():
        lines = [l.rstrip() for l in fetch(group).splitlines() if l.strip()]
        n = 0
        for i in range(0, len(lines) - 2, 3):
            name, l1, l2 = lines[i].strip(), lines[i+1], lines[i+2]
            if not l1.startswith('1 ') or not l2.startswith('2 '):
                continue
            if name in seen or DROP.search(name) or not KEEP.search(name):
                continue
            seen.add(name); n += 1
            out.append([name, l1, l2, desc])
            if n >= PER_GROUP:
                break
        print(f'{group:10} +{n}')

    if len(out) < 10:
        sys.exit(f'only {len(out)} satellites resolved; refusing to write')

    blob = json.dumps(out, separators=(',', ':'))
    root = Path(__file__).resolve().parent.parent
    html = (root / 'index.html').read_text()
    new, count = re.subn(r'const TLE=\[.*?\];', f'const TLE={blob};', html, flags=re.S)
    if count != 1:
        sys.exit(f'expected one TLE block in index.html, found {count}')
    (root / 'index.html').write_text(new)
    (root / 'tools' / 'tle.json').write_text(blob)
    print(f'\nwrote {len(out)} satellites into index.html')

if __name__ == '__main__':
    main()
