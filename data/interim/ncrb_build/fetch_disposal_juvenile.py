"""Download NCRB Crime in India tables on disposal of crimes against women (3A.5-3A.10)
and juveniles in conflict with law (5A.1-5A.5) for 2016-2024, using the catalogue written by
fetch_ncrb_catalog.py. Files go to data/raw/ncrb_cii_tables/<year>/ (existing files are kept)
and are appended to manifest.json."""
import json, re, time
from pathlib import Path
import requests

HERE = Path(__file__).resolve().parent
RAW = HERE.parent.parent / 'raw' / 'ncrb_cii_tables'
UA = {'User-Agent': 'Mozilla/5.0 (research data download)'}

# table id -> title regex (state-level chapter 'A' tables; city 'B' tables are excluded by URL)
TARGETS = {
    '3A.5': r'Police Disposal of Crime Against Women Cases \(Crime Head',
    '3A.6': r'Police Disposal of Crime Against Women Cases \(States?/UT',
    '3A.7': r'Court Disposal of Crime Against Women Cases \(Crime Head',
    '3A.8': r'Court Disposal of Crime Against Women Cases \(States?/UT',
    '3A.9': r'Disposal of Persons Arrested for Crime Against Women \(Crime Head',
    '3A.10': r'Disposal of Persons Arrested for Crime Against Women \(States?/UT',
    '5A.1': r'Crime Committed by Juveniles \(State/UT',
    '5A.2': r'IPC(/BNS)? Crimes Committed by Juveniles \(States?/UT',
    '5A.3': r'SLL Crimes Committed by Juveniles \(States?/UT',
    '5A.4': r'Juveniles Apprehended.*\(Crime Head, Age Group',
    '5A.5': r'Disposal of Juveniles (Arrested|Apprehended) \(States?/UT',
}
# files that exist on the NCRB server but are not linked from the Contents/Tables page
EXTRA = [
    (2023, '5A.4', 'Juveniles Apprehended - IPC Crimes (Crime Head, Age Group & Gender-wise) - 2023 [unlisted; found by URL pattern]',
     'https://www.ncrb.gov.in/uploads/files/TABLE5A4A.xlsx'),
    (2023, '5A.4', 'Juveniles Apprehended - IPC Crimes (Crime Head, Age Group & Gender-wise) - 2023 [unlisted; found by URL pattern]',
     'https://www.ncrb.gov.in/uploads/files/TABLE5A4A.pdf'),
]
# CII 2014-2015 (older chapter numbering; All-India disposal tables for crimes against women)
TARGETS_OLD = {
    '5.5': r'Disposal of Crimes? Committed Against Women Cases by Police',
    '5.6': r'Disposal of Crimes? Committed Against Women Cases by Courts',
    '5.7': r'Disposal of Persons Arrested for Crimes Committed Against Women by Police',
    '5.8': r'Disposal of Persons Arrested for Committing Crimes Against Women by Courts',
    '10.2': r'Cases of Juveniles in Conflict with Law under Different Crime Heads of Indian',
    '10.3': r'Cases of Juveniles in Conflict with Law under Different Crime Heads of Special',
    '10.4': r'Juveniles Apprehended under IPC & SLL Crimes by Age Groups & Sex During',
}
CITY = re.compile(r'(3B|5B|City)', re.I)


def grouped(cat):
    """Attach size-only links ('[ 12 KB ]') to the preceding titled entry."""
    groups, cur = [], None
    for r in cat:
        if r['title'].startswith('[') or not r['title']:
            if cur is not None:
                cur['urls'].append(r['url'])
        else:
            cur = {'year': r['year'], 'title': r['title'], 'urls': [r['url']]}
            groups.append(cur)
    for g in groups:
        g['urls'] = list(dict.fromkeys(g['urls']))
    return groups


def main():
    cat = json.loads((RAW / 'table_content_catalog.json').read_text(encoding='utf8'))
    old = RAW / 'table_content_catalog_2011_2015.json'
    cat_old = json.loads(old.read_text(encoding='utf8')) if old.exists() else []
    man_p = RAW / 'manifest.json'
    man = json.loads(man_p.read_text(encoding='utf8'))
    have = {m['url'] for m in man}
    s = requests.Session(); s.headers.update(UA)
    groups = [(g, TARGETS) for g in grouped(cat)] +         [({'year': y, 'title': t, 'urls': [u], 'extra': tid}, TARGETS) for y, tid, t, u in EXTRA] +         [(g, TARGETS_OLD) for g in grouped(cat_old) if g['year'] in (2014, 2015)]
    for g, targets in groups:
        for tid, rx in targets.items():
            if g.get('extra', tid) != tid or not re.search(rx, g['title'], re.I) or 'City' in g['title']:
                continue
            for u in g['urls']:
                fn = u.split('/')[-1]
                if CITY.search(fn.replace('Crime', '')) and not tid.startswith('5A'):
                    continue
                d = RAW / str(g['year']); d.mkdir(exist_ok=True)
                f = d / fn
                if not f.exists():
                    r = s.get(u, timeout=120)
                    if r.status_code != 200:
                        print('MISSING', r.status_code, g['year'], tid, u); continue
                    f.write_bytes(r.content); time.sleep(0.3)
                    print('got', g['year'], tid, fn, len(r.content))
                for m in man:  # tag entries recorded by earlier downloads
                    if m['url'] == u and not m.get('table'):
                        m['table'] = tid
                if u not in have:
                    man.append({'year': g['year'], 'table': tid, 'title': g['title'], 'url': u,
                                'local': str(g['year']) + chr(92) + fn, 'bytes': f.stat().st_size})
                    have.add(u)
    man_p.write_text(json.dumps(man, indent=1, ensure_ascii=False), encoding='utf8')


if __name__ == '__main__':
    main()
