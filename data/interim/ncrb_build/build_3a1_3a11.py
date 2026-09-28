"""Table 3A.1 (state totals, 3-year) and 3A.11 (rape section-wise incl. custodial), editions 2017-2022."""
from common import *

A1 = {2017: '2017/Table-3A.1_1.xlsx', 2018: '2018/Table-3A.1_0.xlsx', 2019: '2019/TABLE-3A.1.xlsx',
      2020: '2020/1680767998TABLE3A1.xlsx', 2021: '2021/1679652741TABLE3A1.xlsx', 2022: '2022/1701935121TABLE3A1.xlsx'}
A11 = {2017: '2017/Table-3A.11_1.xlsx', 2018: '2018/Table-3A.11_0.xlsx', 2019: '2019/TABLE-3A.11.xlsx',
       2020: '2020/1680767960TABLE3A11.xlsx', 2021: '2021/1679653232TABLE3A11.xlsx', 2022: '2022/1701935624TABLE3A11.xlsx'}


def metric_of(h):
    l = h.lower()
    if re.fullmatch(r'\d{4}(\.0)?', l):
        return 'cases', int(float(l))
    if 'percentage' in l:
        return 'pct_share_all_india', None
    if 'population' in l:
        return 'midyear_female_population_lakh', None
    if 'rate of total crime' in l:
        return 'crime_rate_per_lakh_women', None
    if 'chargesheet' in l:
        return 'chargesheeting_rate_pct', None
    return None, None


def build_3a1():
    recs = []
    for ed, rel in A1.items():
        raw = pd.read_excel(os.path.join(RAW, rel), header=None, dtype=object)
        hr = [i for i in range(8) if clean(raw.iat[i, 1]) == 'State/UT'][0]
        hdr = [clean(x) for x in raw.iloc[hr]]
        for r in range(hr + 2, raw.shape[0]):
            st = clean(raw.iat[r, 1])
            if not st:
                continue
            for c in range(2, len(hdr)):
                if not hdr[c]:
                    continue
                m, y = metric_of(hdr[c])
                if m is None:
                    continue
                recs.append((y if y else ed, st, m, to_num(raw.iat[r, c]), ed,
                             'NCRB CII %d Table 3A.1 (%s)' % (ed, os.path.basename(rel))))
    d = pd.DataFrame(recs, columns=['year', 'state_raw', 'metric', 'value', 'cii_edition', 'source'])
    ks = d.state_raw.apply(std_state); d['kind'] = [k for k, _ in ks]; d['state_ut'] = [n for _, n in ks]
    print('3A.1 unknown:', d[d.kind.isna()].state_raw.unique())
    d = d[d.kind.isin(['state', 'allindia'])]
    # merged UT: only sum additive metric (cases); drop non-additive metrics for pre-merger separate UTs
    pre = d.state_raw.str.lower().str.replace(' ', '').isin(['d&nhaveli', 'daman&diu'])
    d = d[~(pre & (d.metric != 'cases'))]
    d = d.groupby(['year', 'state_ut', 'metric', 'cii_edition', 'source'], as_index=False, sort=False)['value'].sum(min_count=1)
    return d[['year', 'state_ut', 'metric', 'value', 'cii_edition', 'source']]


CUST = [(r'376\(2\) ?\(a\)|by police', 'police_personnel'), (r'376\(2\) ?\(b\)|public servant', 'public_servant'),
        (r'376\(2\) ?\(c\)|armed forces', 'armed_forces'), (r'376\(2\) ?\(d\)|jail', 'jail_remand_home_place_of_custody'),
        (r'376\(2\) ?\(e\)|hospital', 'hospital'), (r'rape in custody \(total\)', 'custodial_total')]


def build_3a11():
    parts = []
    for ed, rel in A11.items():
        d = parse_simple_xlsx(os.path.join(RAW, rel))
        d['crime_head'] = d['head'].apply(lambda h: re.sub(r'376 \(2\)', '376(2)', ' - '.join(h)).replace('Custo- dial', 'Custodial').replace('Sepa-rated', 'Separated'))
        d['year'] = ed
        d['source'] = 'NCRB CII %d Table 3A.11 (%s)' % (ed, os.path.basename(rel))
        parts.append(d)
    d = pd.concat(parts, ignore_index=True)
    d['count'] = d['value'].apply(to_num)
    ks = d.state_raw.apply(std_state); d['kind'] = [k for k, _ in ks]; d['state_ut'] = [n for _, n in ks]
    print('3A.11 unknown:', d[d.kind.isna()].state_raw.unique())
    d = d[d.kind.isin(['state', 'allindia'])]
    d = d.groupby(['year', 'state_ut', 'crime_head', 'source'], as_index=False, sort=False)['count'].sum(min_count=1)

    def ctype(h):
        l = h.lower()
        if not l.startswith('rape in custody'):
            return ''
        for pat, k in CUST:
            if re.search(pat, l):
                return k
        return ''
    d['custody_type'] = d.crime_head.apply(ctype)
    return d[['year', 'state_ut', 'crime_head', 'custody_type', 'count', 'source']]


if __name__ == '__main__':
    a1 = build_3a1(); a11 = build_3a11()
    a1.to_pickle('a1.pkl'); a11.to_pickle('a11.pkl')
    print(a1[(a1.state_ut == 'All India') & (a1.metric == 'cases')].pivot_table(index='year', columns='cii_edition', values='value'))
    print(a11[['crime_head', 'custody_type']].drop_duplicates().to_string()[:6000])
    print(a11[(a11.state_ut == 'All India') & (a11.custody_type != '')].pivot_table(index='custody_type', columns='year', values='count'))
