"""District-wise crimes against women (NCRB CII additional tables), 2015-2022."""
from common import *
from build_state import std_key, head_name, district_file_rows, WOMEN_2015_DROP

SRC = {
    2015: '2015/5-District-wise-Crimes-committed-against-Women_2015.xlsx',
    2016: '2016/District-wise-Crimes-committed-against-Women_2016.xlsx',
    2017: '2017/District-wise-Crime-against-Women - 2017.xlsx',
    2018: '2018/3-District-wise-Crime-against-Women - 2018.xlsx',
    2019: '2019/3-District-wise-Crime-against-Women - 2019.xlsx',
    2020: '2020/Districtwise-Crime-against-Women_2020.xlsx',
    2021: '2021/16730066503DistrictwiseCrimeagainstWomen2021.xlsx',
    2022: '2022/17016840143DistrictwiseCrimeagainstWomen2022.xlsx',
}


def parse_multi(rel):
    raw = pd.read_excel(os.path.join(RAW, rel), header=None, dtype=object)
    nrow = [i for i in range(1, 12) if clean(raw.iat[i, 1]) in ('2', '[2]')][0]
    hdr_rows = list(range(1, nrow))
    heads, cur = [], [None] * len(hdr_rows)
    for c in range(raw.shape[1]):
        vals = [clean(raw.iat[r, c]) for r in hdr_rows]
        for k, v in enumerate(vals):
            if v is not None:
                cur[k] = v
                for kk in range(k + 1, len(vals)):
                    cur[kk] = vals[kk]
                break
        heads.append(tuple(x for x in cur if x))
    recs, state, seen = [], None, []
    for r in range(nrow + 1, raw.shape[0]):
        c0 = clean(raw.iat[r, 0]); c1 = clean(raw.iat[r, 1])
        m = re.match(r'^(State|UT)\s*:\s*(.*)$', c0 or '', re.I)
        if m:
            state = m.group(2).strip().rstrip('#*').strip()
            if state in seen:
                # NCRB labelling slips: a state header repeated for the next block; verified by district names
                nxt = clean(raw.iat[r + 1, 1])
                fix = {('Uttar Pradesh', 'Almora'): 'Uttarakhand', ('Lakshadweep', 'Karaikal'): 'Puducherry'}
                state = fix.get((state, nxt), state + ' ??')
                print('   relabel', rel, r, '->', state)
            seen.append(state)
            continue
        if (c0 and c0.lower().startswith('total')) and c1 is None:
            c1 = 'Total'
        if c1 is None:
            continue
        if re.match(r'^total', c1, re.I):
            c1 = '__STATE_TOTAL__'
        for c in range(2, raw.shape[1]):
            if not heads[c]:
                continue
            recs.append((state, c1, head_name(heads[c]), to_num(raw.iat[r, c])))
    return pd.DataFrame(recs, columns=['state_raw', 'district', 'crime_head', 'count'])


def tidy_head(h):
    h = re.sub(r'\s*\(Col[^)]*\)', '', h)
    h = re.sub(r'\s*Col\.\s*\d+\s*=.*$', '', h).strip()
    parts = [p.strip() for p in h.split(' - ')]
    if len(parts) >= 2:
        base = re.sub(r'\s*\(Sec.*$', '', parts[0]).strip()
        if parts[-1] == base:
            parts[-1] = base + ' (Total)'
    return ' - '.join(parts)


def build():
    parts = []
    for y, rel in SRC.items():
        if y in (2015, 2016):
            d = district_file_rows(rel)
            d = d[~d.crime_head.isin(WOMEN_2015_DROP)]
            d.loc[d.district.str.match(r'^total', case=False), 'district'] = '__STATE_TOTAL__'
            d['state_raw'] = d['state_raw'].str.rstrip('#*').str.strip()
        else:
            d = parse_multi(rel)
        d['year'] = y
        d['source'] = 'NCRB CII %d additional table: district-wise crime against women (%s)' % (y, os.path.basename(rel))
        parts.append(d)
    d = pd.concat(parts, ignore_index=True)
    d['state_ut'] = [std_state(s)[1] for s in d.state_raw]
    d['crime_head'] = d.crime_head.apply(tidy_head)
    d['crime_head_std'] = d.crime_head.apply(std_key)
    return d


if __name__ == '__main__':
    d = build()
    print(d.groupby('year').agg(rows=('count', 'size'), states=('state_ut', 'nunique'), dists=('district', 'nunique'),
                                heads=('crime_head', 'nunique')))
    print(sorted(d.state_ut.unique()))
    print(d[d.district.str.contains('total', case=False)].district.value_counts().head(20))
    d.to_pickle('dist_raw.pkl')
