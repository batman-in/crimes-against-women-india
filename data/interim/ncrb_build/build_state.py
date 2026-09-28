"""Build tidy state/UT x crime-head file (NCRB CII Table 3A.2 and 2015 equivalent)."""
from common import *

URLS = {}  # year -> source url, filled from manifest
import json
man = json.load(open(os.path.join(RAW, 'manifest.json')))
def url_of(local):
    for m in man:
        if m['local'].replace('\\', '/') == local:
            return m['url']
    return None

SRC = {
    2016: ('pdf', '2016/1683013216Table3A2.pdf'),
    2017: ('xlsx', '2017/Table-3A.2_1.xlsx'),
    2018: ('xlsx', '2018/Table-3A.2_0.xlsx'),
    2019: ('pdf', '2019/Table-3A.2_2.pdf'),
    2020: ('xlsx', '2020/TABLE-3A.2.xlsx'),
    2021: ('xlsx', '2021/1679652792TABLE3A2.xlsx'),
    2022: ('xlsx', '2022/1701935197TABLE3A2.xlsx'),
    2023: ('xlsx', '2023/TABLE3A2.xlsx'),
    2024: ('xlsx', '2024/TABLE3A22.xlsx'),
}


def head_name(h):
    h = [x for x in h]
    # drop redundant parent when child repeats it with (Total)
    out = []
    for x in h:
        x = re.sub(r'\s*\*+\s*', ' ', x).strip()
        x = re.sub(r'\s*@\s*$', '', x).strip()
        x = re.sub(r'\(Total \)', '(Total)', x)
        out.append(x)
    return ' - '.join(out)


def std_key(name):
    n = name.lower()
    parts = n.split(' - ')
    last, top = parts[-1], parts[0]
    if re.match(r'^total crimes? against women \((ipc ?\+ ?sll|ipc/bns \+ sll crimes)\)$', n) or n == 'total crimes against women':
        return 'total'
    if top.startswith('rape') and ('(total' in last or n == 'rape'):
        return 'rape'
    if top.startswith('attempt to commit rape') and (n == top or '(total' in last):
        return 'attempt_rape'
    if top.startswith('kidnapping') and ('of women (total' in last or last.endswith('_total') or n == 'kidnapping & abduction of women'):
        return 'kidnap'
    if top.startswith('dowry deaths'):
        return 'dowry'
    if top.startswith('assault on women with intent to outrage') and 'sec 74 bns' not in top and (
            '(total' in last or n == top or last.endswith('_total')):
        return 'assault'
    if last in ('sexual harassment',) or re.match(r'sexual harr?assment \(sec\. 354 a', last) or last.startswith('sexual harassment (total'):
        return 'sexual_harassment'
    if last.startswith('stalking'):
        return 'stalking'
    if last.startswith('voyeurism'):
        return 'voyeurism'
    if top.startswith('insult to') and ('(total' in last or n == top or last.endswith('_total')):
        return 'insult'
    if top.startswith('cruelty by husband'):
        return 'cruelty'
    if top.startswith('abetment'):
        return 'abetment_suicide'
    if top.startswith('acid attack') and 'attempt' not in top and '&' not in top:
        return 'acid_attack'
    if top.startswith('dowry prohibition'):
        return 'dowry_act'
    if 'domestic violence' in top or 'domestic offences' in top:
        return 'dv_act'
    if top.startswith('immoral traffic') and ('(total' in last or n == top):
        return 'itpa'
    if top.startswith('protection of children from sexual') and '(total' in last:
        return 'pocso_girls'
    return ''


def from_3a2(year, kind, rel):
    f = os.path.join(RAW, rel)
    if kind == 'xlsx':
        pick = ('Total', 'I') if year == 2024 else ('I', '1')
        d = parse_xlsx(f, measure_pick=pick)
    else:
        d = parse_pdf(f)
    d['crime_head'] = d['head'].apply(head_name)
    if year == 2024:
        # 2024: columns are IPC / BNS / Total cases; 'Total' = IPC + BNS cases registered
        pass
    d['count'] = d['value'].apply(to_num)
    d['year'] = year
    d['source'] = 'NCRB CII %d Table 3A.2 (%s)' % (year, os.path.basename(rel))
    return d[['year', 'state_raw', 'crime_head', 'count', 'source']]


WOMEN_2015_DROP = {'Murder', 'Attempt to commit Murder', 'Culpable Homicide not amounting to Murder',
                   'Attempt to commit Culpable Homicide', 'Grievous Hurt', 'Hurt', 'Dacoity_Total',
                   'Dacoity with Murder', 'Other Dacoity', 'Robbery', 'Arson', 'UnNatural Offences',
                   'Other IPC Crimes', 'Other SLL Crimes against Women', 'Total Crimes in which Women was Victim'}


def district_file_rows(rel):
    """Parse NCRB district-wise CAW xlsx (flat header, 2014-2016 style). Returns state, district, head, count,
    with state 'Total District(s)' rows flagged."""
    raw = pd.read_excel(os.path.join(RAW, rel), header=None, dtype=object)
    hdr = [clean(v) for v in raw.iloc[1]]
    recs = []
    state = None
    for r in range(2, raw.shape[0]):
        c0 = clean(raw.iat[r, 0]); c1 = clean(raw.iat[r, 1])
        if c0 and c0.startswith('State:'):
            state = c0.split(':', 1)[1].strip(); continue
        if c1 is None:
            continue
        for c in range(3, len(hdr)):
            if hdr[c] is None:
                continue
            recs.append((state, c1, hdr[c], to_num(raw.iat[r, c])))
    return pd.DataFrame(recs, columns=['state_raw', 'district', 'crime_head', 'count'])


DIST15_OVERLAP = {'Rape', 'Attempt to commit Rape', 'Kidnapping & Abduction_Total', 'Dowry Deaths',
                  'Assault on Women with intent to outrage her Modesty_Total', 'Insult to the Modesty of Women_Total',
                  'Cruelty by Husband or his Relatives', 'Importation of Girls from Foreign Country',
                  'Abetment of Suicides of Women', 'Dowry Prohibition Act, 1961',
                  'Indecent Representation of Women (P) Act, 1986', 'Commission of Sati Prevention Act, 1987',
                  'Protection of Women from Domestic Violence Act, 2005', 'Immoral Traffic Prevention Act',
                  'Total Crimes against Women'}
DIST15_RENAME = {'Assault on women with intent to Disrobe': 'Assault on Women with intent to outrage her Modesty - Assault on women with intent to Disrobe',
                 'Sexual Harassment': 'Assault on Women with intent to outrage her Modesty - Sexual Harassment',
                 'Voyeurism': 'Assault on Women with intent to outrage her Modesty - Voyeurism',
                 'Stalking': 'Assault on Women with intent to outrage her Modesty - Stalking',
                 'Others': 'Assault on Women with intent to outrage her Modesty - Others'}


def from_2015():
    # (a) state-level CR by crime head: NCRB 2015 additional table (state/UT, 2010-2015), sheet 2015
    rel = '2015/6-Data-Analysis-on-Crime-against-Women-Crimeheads-under-Various-Heads-during-2010-2015(StateUT).xlsx'
    v = pd.read_excel(os.path.join(RAW, rel), sheet_name='2015', header=None, dtype=object)
    h1 = [clean(x) for x in v.iloc[1]]; h2 = [clean(x) for x in v.iloc[2]]
    cur = None; heads = []
    for x in h1:
        if x: cur = x
        heads.append(cur)
    stcols = [c for c, x in enumerate(h1) if x == 'State/UT']
    recs = []
    for c in range(v.shape[1]):
        if h2[c] != 'CR':
            continue
        sc = max(s for s in stcols if s < c)
        for r in range(3, v.shape[0]):
            st = clean(v.iat[r, sc])
            if st:
                recs.append((st, heads[c], to_num(v.iat[r, c])))
    a = pd.DataFrame(recs, columns=['state_raw', 'crime_head', 'count'])
    a['year'] = 2015
    a['source'] = 'NCRB CII 2015 additional table: Crime against women crime heads, State/UT-wise 2010-2015 (sheet 2015, CR)'
    # (b) sub-heads only in the district-wise table: use state "Total District(s)" rows
    rel2 = '2015/5-District-wise-Crimes-committed-against-Women_2015.xlsx'
    d = district_file_rows(rel2)
    d = d[d.district.str.match(r'Total District', case=False)]
    d = d[~d.crime_head.isin(WOMEN_2015_DROP | DIST15_OVERLAP)]
    d['crime_head'] = d['crime_head'].replace(DIST15_RENAME)
    d['year'] = 2015
    d['source'] = 'NCRB CII 2015 additional table: District-wise crimes committed against women 2015 (state "Total District(s)" rows)'
    return pd.concat([a, d[['year', 'state_raw', 'crime_head', 'count', 'source']]], ignore_index=True)


def build():
    parts = [from_2015()]
    for y, (k, rel) in SRC.items():
        parts.append(from_3a2(y, k, rel))
    d = pd.concat(parts, ignore_index=True)
    kinds = d.state_raw.apply(std_state)
    d['kind'] = [k for k, _ in kinds]
    d['state_ut'] = [n for _, n in kinds]
    unk = d[d.kind.isna()].state_raw.unique()
    if len(unk):
        print('UNKNOWN STATES', unk)
    sub = d[d.kind == 'subtotal']
    d = d[d.kind.isin(['state', 'allindia'])]
    # 2015 (district file) has no All-India row: aggregate state totals
    ai = d[(d.year == 2015) & d.source.str.contains('District-wise')].groupby(['year', 'crime_head'], as_index=False, sort=False)['count'].sum(min_count=1)
    ai['state_ut'] = 'All India'; ai['kind'] = 'allindia'
    ai['source'] = 'Sum of state/UT "Total District(s)" rows, NCRB CII 2015 district-wise CAW table'
    ai['state_raw'] = 'All India'
    d = pd.concat([d, ai], ignore_index=True)
    # merge pre-2020 D&N Haveli + Daman & Diu into the merged UT (sum of NCRB figures)
    d = d.groupby(['year', 'state_ut', 'crime_head', 'source'], as_index=False, sort=False)['count'].sum(min_count=1)
    d['crime_head_std'] = d['crime_head'].apply(std_key)
    d = d[['year', 'state_ut', 'crime_head', 'crime_head_std', 'count', 'source']]
    return d, sub


if __name__ == '__main__':
    d, sub = build()
    # check std mapping uniqueness
    chk = d[(d.crime_head_std != '') & (d.state_ut == 'All India')].groupby(['year', 'crime_head_std']).crime_head.nunique()
    print('dup std mapping:\n', chk[chk > 1])
    for y in sorted(d.year.unique()):
        m = d[(d.year == y) & (d.state_ut == 'All India') & (d.crime_head_std != '')]
        print(y, dict(zip(m.crime_head_std, m['count'])))
    d.to_pickle('state.pkl'); sub.to_pickle('state_sub.pkl')
