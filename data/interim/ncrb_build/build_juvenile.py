"""Build tidy NCRB juvenile (children in conflict with law) data for crimes against women.

Sources (NCRB Crime in India, chapter 5A):
  5A.2  IPC crimes - juveniles in conflict with law (State/UT-wise; crime heads are columns)
  5A.3  SLL crimes - juveniles in conflict with law (State/UT-wise)
  5A.4  Juveniles apprehended (crime head, age group & gender-wise; All India)
        from 2020 split into 5A.4A (IPC/BNS) and 5A.4B (SLL)
Only crime heads that are crimes against women (plus overall IPC/SLL totals for context) are kept.

Outputs (data/interim/):
  ncrb_juvenile_caw_2014_2024.csv
  ncrb_juvenile_validation.csv
"""
import json, re, sys
from pathlib import Path
import pandas as pd
import pdfplumber

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ncrb_cells import RAW, OUT, clean, xlsx_cells, pdf_cells, pdf_headers, to_num
from common import std_state

YEARS = range(2014, 2025)
# CII 2014-2015 used chapter 10 for juveniles: 10.2 IPC cases (State/UT-wise), 10.3 SLL cases, 10.4 age & sex
OLD_TABLE = {'10.2': '5A.2', '10.3': '5A.3', '10.4': '5A.4'}


def juv_std(label):
    n = (label or '').lower()
    if re.search(r'custodial|gang rape|^other rape|> other rape', n):
        return None  # sub-types of rape (2014-2015 tables); the rape total is kept
    rules = [
        (r'^(total cognizable ipc|total cognizable bns|total cognizable ipc/bns)', 'KEEP'),
        (r'^total cognizable sll', 'KEEP'),
        (r'^grand total', 'KEEP'),
        (r'murder with rape', 'murder_rape'),
        (r'attempt to commit rape', 'attempt_rape'),
        (r'^(offences affecting the human body > )?rape\b|> rape\b|^rape \(', 'rape'),
        (r'assault on women with intent to outrage', 'assault'),
        (r'sexual harassment', 'sexual_harassment'),
        (r'intent to disrobe', 'disrobe'),
        (r'voyeurism', 'voyeurism'),
        (r'stalking', 'stalking'),
        (r'insult to (the )?modesty', 'insult'),
        (r'dowry deaths', 'dowry'),
        (r'cruelty by husband', 'cruelty'),
        (r'compel her for marriage', 'kidnap_marriage'),
        (r'kidnapping (and|&) abduction of women', 'kidnap'),
        (r'human trafficking', 'trafficking'),
        (r'immoral traffic', 'itpa'),
        (r'dowry prohibition', 'dowry_act'),
        (r'domestic violence', 'dv_act'),
        (r'indecent representation', 'KEEP'),
        (r'protection of children from sexual', 'KEEP'),
        (r'crime against women\s*[–-]\s*related acts', 'KEEP'),
        (r'sexual intercourse by employing deceitful', 'KEEP'),
        (r'disclosure of identity of victim', 'KEEP'),
        (r'attempt to acid attack', 'attempt_acid_attack'),
        (r'acid attack', 'acid_attack'),
    ]
    for rx, k in rules:
        if re.search(rx, n):
            return '' if k == 'KEEP' else k
    # some 2014-2015 PDF headings are letter-spaced ('Human T r a ff i c k i n g')
    ns = re.sub(r'\s+', '', n)
    for rx, k in [(r'humantrafficking', 'trafficking'), (r'^totalcognizable(ipc|sll)', 'KEEP'),
                  (r'disclosureofidentity', 'KEEP')]:
        if re.search(rx, ns):
            return '' if k == 'KEEP' else k
    return None  # not a crime-against-women head: dropped


def head_label(h):
    """Drop the group heading ('Offences affecting the Human Body > ...')."""
    h = h.split(' > ')[-1] if ' > ' in h else h
    # fragments of a spanning group heading picked up by the 2014-2015 PDF heading extractor
    h = re.sub(r'^(& 326 |B IPC\) |Immoral (?=Immoral)|Children (?=The Protection))', '', h)
    return clean(despace(h))


def despace(h):
    """Re-join letter-spaced words printed in some 2014-2015 PDFs ('Human T r a ff i c k i n g')."""
    toks, out, run = h.split(' '), [], []
    for t in toks + ['']:
        if t and len(t) <= 2:
            run.append(t)
            continue
        out.extend([''.join(run)] if len(run) >= 3 else run)
        run = []
        if t:
            out.append(t)
    return ' '.join(out)


# ------------------------------------------------------------------ sources
def manifest():
    return json.loads((RAW / 'manifest.json').read_text(encoding='utf8'))


def title_of(p):
    if p.suffix == '.xlsx':
        try:
            x = pd.read_excel(p, header=None, nrows=2, dtype=object)
        except Exception:
            return None, None
        return clean(x.iat[0, 0]), clean(x.iat[1, 0])
    with pdfplumber.open(p) as pdf:
        L = (pdf.pages[0].extract_text() or '').split('\n')
    return clean(L[0]), clean(L[1])


def pick_sources():
    """(year, table, part) -> path, url. part: 'IPC', 'SLL' or 'IPC+SLL' (5A.4 only)."""
    src = {}
    for m in manifest():
        t = m.get('table')
        if m['year'] in (2014, 2015) and t in OLD_TABLE:
            p = RAW / m['local'].replace(chr(92), '/')
            part = {'10.2': 'IPC', '10.3': 'SLL', '10.4': 'IPC+SLL'}[t]
            src[(m['year'], t, part)] = (p, m['url'], m.get('pages'))
            continue
        if t not in ('5A.2', '5A.3', '5A.4') or m['year'] not in YEARS:
            continue
        p = RAW / m['local'].replace(chr(92), '/')
        t0, t1 = title_of(p)
        if not t0 or not re.match(r'^TABLE\s*' + re.escape(t) + r'[AB]?$', t0.replace(' (i)', '')):
            continue  # city-wise 5B tables or unreadable files
        if t1 is None or not re.search(str(m['year']), t1):
            continue
        part = 'IPC' if t == '5A.2' else 'SLL' if t == '5A.3' else \
            ('SLL' if 'SLL Crimes' in t1 else 'IPC' if re.search(r'IPC(/BNS)? Crimes', t1) else 'IPC+SLL')
        key = (m['year'], t, part)
        if key not in src or (p.suffix == '.xlsx' and src[key][0].suffix != '.xlsx'):
            src[key] = (p, m['url'], m.get('pages'))
    return src


# ------------------------------------------------------------------ 5A.2 / 5A.3 (State/UT-wise, heads in columns)
def statewise(year, table, p):
    if p.suffix == '.xlsx':
        d = xlsx_cells(p)
    else:
        d = pdf_cells(p)
        h = pdf_headers(p)
        d['header'] = [h.get((s, c)) for s, c in zip(d.seg, d.colno)]
    d['crime_head'] = d.header.map(head_label)
    d['crime_head_std'] = d.header.map(juv_std)
    d = d[d.crime_head_std.notna()].copy()
    kinds = d.label.map(std_state)
    d['kind'] = [k[0] for k in kinds]
    d['state_ut'] = [k[1] for k in kinds]
    unk = d[d.kind.isna()].label.unique()
    if len(unk):
        raise ValueError(f'{year} {table} unknown rows {unk}')
    d = d[d.kind.isin(['state', 'allindia'])]
    d['count'] = d.value.map(to_num)
    # a column repeated on two page blocks must agree
    g = d.groupby(['label', 'crime_head']).agg(n=('count', 'nunique'))
    if (g.n > 1).any():
        raise ValueError(f'{year} {table} conflicting duplicates')
    d = d.drop_duplicates(['label', 'crime_head'])
    # D&N Haveli + Daman & Diu (listed separately before 2020): sum into the merged UT
    d = d.groupby(['state_ut', 'crime_head', 'crime_head_std'], as_index=False).agg(
        count=('count', lambda s: s.sum(min_count=1)), n=('label', 'nunique'))
    d['note'] = d.n.map(lambda n: 'sum of D&N Haveli and Daman & Diu' if n > 1 else '')
    d['measure'] = 'cases_against_juveniles'
    d['unit'] = 'cases'
    return d.drop(columns='n')


# ------------------------------------------------------------------ 5A.4 (All India, heads in rows)
AGE = [(r'below 12', 'age_below_12'), (r'12 years (& above and below|to) 16', 'age_12_16'),
       (r'16 years (& above and below|to) 18', 'age_16_18'), (r'(^|> )total >|overall', 'total')]


def age_measure(h):
    h = h.lower()
    if 'cases reported' in h:
        return 'cases_against_juveniles'
    age = next((k for rx, k in AGE if re.search(rx, h)), None)
    sx = re.search(r'(boys \+ girls|boys|girls|trans(gender)?|total)\s*$', h)
    if age is None or sx is None:
        raise ValueError(f'unmapped 5A.4 header {h!r}')
    sx = sx.group(1)
    sfx = {'boys': '_boys', 'girls': '_girls', 'trans': '_transgender', 'transgender': '_transgender',
           'total': '', 'boys + girls': ''}[sx]
    base = 'juveniles_apprehended' if age == 'total' else 'juveniles_' + age
    return base + sfx


def age_table(year, p):
    if p.suffix == '.xlsx':
        d = xlsx_cells(p)
    else:
        d = pdf_cells(p)
    d['label'] = d.label.str.replace(r'^(IPC|SLL) - Cases\s+', '', regex=True)
    d['crime_head_std'] = d.label.map(juv_std)
    d = d[d.crime_head_std.notna()].copy()
    if p.suffix == '.xlsx':
        d['measure'] = d.header.map(age_measure)
    elif year <= 2016:  # printed layout (2014-2016): 3-5 below 12, 6-8 12-16, 9-11 16-18, 12-14 total (Boys, Girls, Total)
        m16 = {}
        for i, age in enumerate(['juveniles_age_below_12', 'juveniles_age_12_16', 'juveniles_age_16_18', 'juveniles_apprehended']):
            for j, sx in enumerate(['_boys', '_girls', '']):
                m16[3 + 3 * i + j] = age + sx
        d['measure'] = d.colno.map(m16)
    else:  # volume pages 2022/2024 use the 2021+ layout (columns 3-19), identical to the 2023 XLSX
        ref = xlsx_cells(RAW / '2023' / 'TABLE5A4B.xlsx')
        cmap = {c: age_measure(h) for c, h in ref.drop_duplicates('colno')[['colno', 'header']].values}
        hd = pdf_headers(p)
        for (s_, c), txt in hd.items():  # sanity check on the printed headings of the PDF pages
            if c in (3,) and 'cases' not in (txt or '').lower():
                raise ValueError(f'{p.name}: column 3 is not cases reported: {txt}')
        d['measure'] = d.colno.map(cmap)
    if d.measure.isna().any():
        raise ValueError(f'{year} {p.name}: unmapped columns {sorted(d[d.measure.isna()].colno.unique())}')
    d['count'] = d.value.map(to_num)
    # same head can be printed with different capitalisation on different pages
    d['k'] = d.label.str.lower().str.replace(r'[^a-z0-9]', '', regex=True)
    first = d.sort_values(['seg', 'row']).drop_duplicates('k').set_index('k').label
    d['crime_head'] = d.k.map(first).map(clean)
    g = d.groupby(['crime_head', 'measure'])['count'].nunique()
    if (g > 1).any():
        raise ValueError(f'{year} {p.name}: conflicting {g[g > 1]}')
    d = d.drop_duplicates(['crime_head', 'measure'])
    d['state_ut'] = 'All India'
    d['unit'] = d.measure.map(lambda m: 'cases' if m.startswith('cases') else 'persons')
    d['note'] = ''
    return d[['state_ut', 'crime_head', 'crime_head_std', 'measure', 'count', 'unit', 'note']]


# ------------------------------------------------------------------ validation
VAL = []


def check(year, table, name, measure, exp, act, detail='', tol=0):
    ok = exp is not None and act is not None and not pd.isna(exp) and not pd.isna(act) and abs(exp - act) <= tol
    VAL.append({'topic': 'juvenile', 'year': year, 'table': table, 'check': name, 'measure': measure,
                'expected': exp, 'actual': act,
                'diff': None if (exp is None or act is None or pd.isna(exp) or pd.isna(act)) else round(act - exp, 2),
                'result': 'pass' if ok else 'FAIL', 'detail': detail})


def main():
    src = pick_sources()
    frames = []
    for (y, t, part), (p, url, pages) in sorted(src.items()):
        d = statewise(y, t, p) if OLD_TABLE.get(t, t) in ('5A.2', '5A.3') else age_table(y, p)
        # 2016-2019: one 5A.4 table holds IPC and SLL heads; from 2020 it is split into 5A.4A / 5A.4B
        d['year'], d['table'] = y, t + ('' if t != '5A.4' or y <= 2019 else {'IPC': 'A', 'SLL': 'B'}[part])
        d['source'] = f'NCRB CII {y} Table {t} {part} ({p.name}{", pages " + pages if pages else ""})'
        frames.append(d)
        print(y, t, part, p.name, len(d))
    df = pd.concat(frames, ignore_index=True)
    # validation ------------------------------------------------------
    sw = df[df.table.isin(['5A.2', '5A.3', '10.2', '10.3'])]
    for (y, t, h), g in sw.groupby(['year', 'table', 'crime_head']):
        ai = g[g.state_ut == 'All India']['count']
        check(y, t, 'states_sum_to_all_india', 'cases_against_juveniles', ai.iloc[0] if len(ai) else None,
              g[g.state_ut != 'All India']['count'].sum(), h)
    ag = df[df.table.str.startswith('5A.4') | (df.table == '10.4')]
    for (y, t, h), g in ag.groupby(['year', 'table', 'crime_head']):
        v = dict(zip(g.measure, g['count']))
        for base in ['juveniles_age_below_12', 'juveniles_age_12_16', 'juveniles_age_16_18', 'juveniles_apprehended']:
            parts = [v[base + s] for s in ('_boys', '_girls', '_transgender') if base + s in v]
            if base in v and parts:
                check(y, t, 'boys_girls_trans_sum_to_total', base, v[base], sum(parts), h)
        if 'juveniles_apprehended' in v:
            check(y, t, 'age_groups_sum_to_total', 'juveniles_apprehended', v['juveniles_apprehended'],
                  sum(v.get(k, 0) for k in ['juveniles_age_below_12', 'juveniles_age_12_16', 'juveniles_age_16_18']), h)
    # State-wise All-India cases (5A.2/5A.3) against 'cases reported against juveniles' in 5A.4
    sa = sw[(sw.state_ut == 'All India') & (sw.crime_head_std != '')]
    sb = ag[(ag.measure == 'cases_against_juveniles') & (ag.crime_head_std != '')]
    a = {(y, k): c for y, k, c in zip(sa.year, sa.crime_head_std, sa['count'])}
    b = {(y, k): c for y, k, c in zip(sb.year, sb.crime_head_std, sb['count'])}
    for k in sorted(set(a) & set(b)):
        check(k[0], '5A.2/5A.3 vs 5A.4', 'statewise_all_india_equals_5A4_cases', 'cases_against_juveniles', b[k], a[k], k[1])
    v = pd.DataFrame(VAL)
    v.to_csv(OUT / 'ncrb_juvenile_validation.csv', index=False, float_format='%.10g')
    print(v.groupby(['check', 'result']).size().to_string())
    print(v[v.result == 'FAIL'].to_string()[:4000])
    cols = ['year', 'state_ut', 'crime_head', 'crime_head_std', 'measure', 'count', 'unit', 'table', 'source', 'note']
    df = df[cols].sort_values(['year', 'table', 'state_ut', 'crime_head', 'measure'])
    df.to_csv(OUT / 'ncrb_juvenile_caw_2014_2024.csv', index=False, float_format='%.10g')
    print(len(df))


if __name__ == '__main__':
    main()
