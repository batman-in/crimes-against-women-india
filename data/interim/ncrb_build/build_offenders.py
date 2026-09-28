"""Offenders' relation to rape victims, State/UT-wise, 2011-2024."""
from common import *


def rel_std(label):
    l = label.lower()
    if 'percentage' in l:
        return None
    if l.startswith('total rape cases'):
        return 'total_cases'
    if 'unknown' in l or 'not identified' in l or 'not known' in l:
        return 'unknown'
    if '(total)' in l or l.endswith('known to the victims') or l == 'known to victim (total)':
        return 'known_total'
    if 'close family members (other' in l:
        return 'close_family_other'
    if 'grand father' in l or 'grandfather' in l:
        return 'grandfather_father_brother_son'
    if 'parents / close family' in l or 'parents/close family' in l:
        return 'parents_close_family'
    if l.endswith('family members'):
        return 'family'
    if 'family friends' in l:
        return 'family_friends_neighbours_employer_other_known'
    if 'online' in l:
        return 'friends_online_friends_livein_partners_separated_husband'
    if 'relatives' in l:
        return 'relatives'
    if 'neighbour' in l:
        return 'neighbours'
    if 'employer' in l:
        return 'employer_coworkers'
    if 'live in partner' in l:
        return 'livein_partner_separated_ex_husband'
    if 'promise to marry' in l:
        return 'known_person_on_promise_to_marry'
    if 'other known' in l:
        return 'other_known_persons'
    return ''


def pdf_lines(rel, fixes=()):
    with pdfplumber.open(os.path.join(RAW, rel)) as p:
        txt = '\n'.join(pg.extract_text() for pg in p.pages)
    for a, b in fixes:
        assert a in txt, (rel, a)
        txt = txt.replace(a, b)
    out = []
    for line in txt.split('\n'):
        m = re.match(r'^(?:\d+\s+)?([A-Za-z&().\- ]+?)\s+((?:-?\d+(?:\.\d+)?\s*)+)$', line.strip())
        if m:
            out.append((m.group(1).strip(), m.group(2).split()))
        if re.match(r'^TOTAL \(ALL', line.strip()):
            break
    return out


LAB_1113 = ['Known to victims (total)', 'Parents / close family members', 'Relatives', 'Neighbours',
            'Other known persons']
LAB_14 = ['Total rape cases', 'Known to victims (total)', 'Grand father/ father/ brother/ son etc.',
          'Close family members (other than grand father/father/brother/son)', 'Relatives (other than family)',
          'Neighbours', 'Employer/ co-workers', 'Other known persons', 'Percentage share of known cases']


def from_pdf_1114():
    recs = []
    srcs = {2011: '2011/Table-5.4_2011.pdf', 2012: '2012/Table-5.4.pdf', 2013: '2013/Table-5.4_2013.pdf'}
    for y, rel in srcs.items():
        for name, nums in pdf_lines(rel):
            if len(nums) != 5:
                continue
            for lab, v in zip(LAB_1113, nums):
                recs.append((y, name, lab, v, 'NCRB CII %d Table 5.4 (%s)' % (y, os.path.basename(rel))))
    fixes = [('Arunachal\n2 83 21 6 0 0 3 2 10\nPradesh 25.3', '2 Arunachal Pradesh 83 21 6 0 0 3 2 10 25.3'),
             ('TOTAL (ALL\n37413 32187 674 966 2217 8344 618 19368\nINDIA) 86.0',
              'TOTAL (ALL INDIA) 37413 32187 674 966 2217 8344 618 19368 86.0')]
    for name, nums in pdf_lines('2014/Table-5.4_2014.pdf', fixes):
        if len(nums) != 9:
            continue
        for lab, v in zip(LAB_14, nums):
            recs.append((2014, name, lab, v, 'NCRB CII 2014 Table 5.4 (Table-5.4_2014.pdf)'))
    return pd.DataFrame(recs, columns=['year', 'state_raw', 'relation', 'value', 'source'])


def clean_lab(c):
    c = re.sub(r'\s*-?\s*\(?Col\.?\s*\(?\d+[A-Z]?\)?\)?\s*', ' ', c).strip()
    c = re.sub(r'^Cases (in )?[Ww]hich Offenders were known to (the )?Victims? - ', 'Known to victim - ', c)
    c = c.replace('Known to victim - Cases Offender known to Victim (Total)', 'Known to victim (total)')
    c = c.replace('Known to victim - No. of Cases in Which Offenders were known to the Victims (Total)', 'Known to victim (total)')
    c = c.replace('Known to victim - Number of Cases in which Offenders were known to the Victims (Total)', 'Known to victim (total)')
    return re.sub(r'\s+', ' ', c).strip(' -')


def from_csv():
    srcs = {2015: 'Table_5.4-2015.csv', 2016: 'Table_3A.4_2016.csv', 2019: 'NCRB_CII-2019_Table_3A.4.csv',
            2020: 'NCRB_CII-2020_Table.No-3A.4.csv'}
    recs = []
    for y, f in srcs.items():
        d = pd.read_csv(os.path.join(DGI, f), dtype=str)
        stc = [c for c in d.columns if re.match(r'State', c)][0]
        for c in d.columns:
            if re.match(r'(S\. ?No|Si\. No|Sl\. No|Category|State)', c):
                continue
            for _, r in d.iterrows():
                recs.append((y, str(r[stc]).strip(), clean_lab(c), r[c],
                             'NCRB CII %d Table %s via data.gov.in (%s)' % (y, '5.4' if y == 2015 else '3A.4', f)))
    return pd.DataFrame(recs, columns=['year', 'state_raw', 'relation', 'value', 'source'])


def from_xlsx():
    srcs = {2017: '2017/Table-3A.4_1.xlsx', 2018: '2018/Table-3A.4_0.xlsx', 2021: '2021/1679652892TABLE3A4.xlsx',
            2022: '2022/1701935296TABLE3A4.xlsx', 2023: '2023/TABLE3A4.xlsx', 2024: '2024/TABLE3A41.xlsx'}
    parts = []
    for y, rel in srcs.items():
        d = parse_simple_xlsx(os.path.join(RAW, rel))
        d['relation'] = d['head'].apply(lambda h: clean_lab(' - '.join(h)))
        d['year'] = y
        d['source'] = 'NCRB CII %d Table 3A.4 (%s)' % (y, os.path.basename(rel))
        parts.append(d[['year', 'state_raw', 'relation', 'value', 'source']])
    return pd.concat(parts)


def build():
    d = pd.concat([from_pdf_1114(), from_csv(), from_xlsx()], ignore_index=True)
    d['relation'] = d['relation'].str.replace('Cases which Offenders were known to Victim', 'Known to victim', regex=False)
    d['relation'] = d['relation'].str.replace(r'^Known to victim - Cases Offender known to Victim \(Total\)$', 'Known to victim (total)', regex=True)
    d['relation_std'] = d['relation'].apply(rel_std)
    d = d[d.relation_std.notna()]
    d['count'] = d['value'].apply(to_num)
    ks = d.state_raw.apply(std_state)
    d['kind'] = [k for k, _ in ks]; d['state_ut'] = [n for _, n in ks]
    print('unknown states:', d[d.kind.isna()].state_raw.unique())
    d = d[d.kind.isin(['state', 'allindia'])]
    d = d.groupby(['year', 'state_ut', 'relation', 'relation_std', 'source'], as_index=False, sort=False)['count'].sum(min_count=1)
    return d[['year', 'state_ut', 'relation', 'relation_std', 'count', 'source']]


if __name__ == '__main__':
    d = build()
    print(d.groupby('year').size())
    print(d[d.state_ut == 'All India'].pivot_table(index='relation_std', columns='year', values='count', aggfunc='sum').to_string())
    # validate sum of states vs All India
    s = d[d.state_ut != 'All India'].groupby(['year', 'relation_std'])['count'].sum()
    a = d[d.state_ut == 'All India'].groupby(['year', 'relation_std'])['count'].sum()
    j = pd.concat([s.rename('states'), a.rename('allindia')], axis=1); j['diff'] = j.states - j.allindia
    print(j[j['diff'].abs() > 0])
    d.to_pickle('off.pkl')
