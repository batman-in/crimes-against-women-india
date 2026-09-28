"""List every file on NCRB's 'Crime in India' Additional Tables page and Contents/Tables page
for each year (English locale) and save the catalogues as JSON next to the raw tables.
Usage: python fetch_ncrb_catalog.py [year ...]"""
import json, re, sys, html
from pathlib import Path
import requests

HERE = Path(__file__).resolve().parent
RAW = HERE.parent.parent / 'raw' / 'ncrb_cii_tables'
BASE = 'https://www.ncrb.gov.in'
UA = {'User-Agent': 'Mozilla/5.0 (research data download)'}


def session():
    s = requests.Session(); s.headers.update(UA)
    p = s.get(f'{BASE}/crime-in-india-additional-table.html?year=2024&category=', timeout=60).text
    tok = re.search(r'name="csrf-token" content="([^"]+)"', p).group(1)
    r = s.post(f'{BASE}/api/language/set', data={'lang': 'en', 'slug': 'crime-in-india-additional-table', '_csrf': tok},
               headers={'X-Requested-With': 'XMLHttpRequest'}, timeout=60)
    assert r.json().get('success') in (1, '1'), r.text
    return s


def catalog(s, year):
    p = s.get(f'{BASE}/crime-in-india-additional-table.html?year={year}&category=', timeout=60).text
    out, section = [], None
    for m in re.finditer(r'<h2 class="c-genriccontent__subhead">(.*?)</h2>|<a target="_blank" class="link" href="([^"]+)">(.*?)</a>', p, re.S):
        if m.group(1):
            section = html.unescape(m.group(1).strip())
        else:
            out.append({'year': year, 'section': section, 'title': html.unescape(re.sub(r'\s+', ' ', m.group(3)).strip()),
                        'url': m.group(2)})
    return out


def table_content(s, year):
    """Contents/Tables page: every published CII table (PDF, sometimes XLSX) for a year."""
    p = s.get(f'{BASE}/crime-in-india-table-content?year={year}', timeout=90).text
    out = []
    for u, t in re.findall(r'href="([^"]+)"[^>]*>(.*?)</a>', p, re.S):
        if '/uploads/' not in u:
            continue
        t = re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', '', t))).strip()
        if u.startswith('/'):
            u = BASE + u
        out.append({'year': year, 'title': t, 'url': u})
    return out


if __name__ == '__main__':
    years = [int(y) for y in sys.argv[1:]] or list(range(2016, 2025))
    s = session()
    allrows = []
    for y in years:
        rows = catalog(s, y); allrows += rows
        print(y, len(rows))
    (RAW / 'additional_tables_catalog.json').write_text(json.dumps(allrows, indent=1, ensure_ascii=False), encoding='utf8')
    tc = []
    for y in years:
        rows = table_content(s, y); tc += rows
        print('contents', y, len(rows))
    (RAW / 'table_content_catalog.json').write_text(json.dumps(tc, indent=1, ensure_ascii=False), encoding='utf8')
    # (additional tables written above)
    (RAW / 'additional_tables_catalog.json').write_text(json.dumps(allrows, indent=1, ensure_ascii=False), encoding='utf8')
