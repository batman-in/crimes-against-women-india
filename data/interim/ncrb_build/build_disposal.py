"""Build tidy NCRB disposal files for crimes against women.

Sources (NCRB Crime in India, chapter 3A, 'Contents/Tables' page):
  3A.5  Police disposal of CAW cases (crime head-wise, All India)
  3A.6  Police disposal of CAW cases (State/UT-wise)
  3A.7  Court disposal of CAW cases (crime head-wise, All India)
  3A.8  Court disposal of CAW cases (State/UT-wise)
  3A.9  Disposal of persons arrested for CAW (crime head-wise, All India)
  3A.10 Disposal of persons arrested for CAW (State/UT-wise)
2016-2024; XLSX used where published, otherwise the PDF.
Plus Kaggle rajanand/crime-in-india 43_Arrests_under_crime_against_women.csv (2001-2010, persons).

Outputs (data/interim/):
  ncrb_disposal_persons_2001_2024.csv
  ncrb_disposal_police_cases_2014_2024.csv
  ncrb_disposal_court_cases_2014_2024.csv
  ncrb_disposal_validation.csv
"""
import csv, json, re, sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ncrb_cells import RAW, OUT, PROJ, clean, xlsx_cells, pdf_cells, to_num
from common import std_state

YEARS = range(2016, 2025)
TABLES = ['3A.5', '3A.6', '3A.7', '3A.8', '3A.9', '3A.10']
KIND = {'3A.5': 'police', '3A.6': 'police', '3A.7': 'court', '3A.8': 'court', '3A.9': 'persons', '3A.10': 'persons'}
STATEWISE = {'3A.6', '3A.8', '3A.10'}

# ------------------------------------------------------------------ measure keys from header text (xlsx)
# 2017-2024 layout (identical column numbers every year); each entry: measure, keyword that must occur in
# the printed heading (checked for every XLSX)
MAP_2017 = {
    'police': {3: ('cases_pending_investigation_start', 'pending invest'), 4: ('cases_reported', 'reported'),
               5: ('cases_reopened', 'reopened'), 6: ('cases_for_investigation', 'total cases for invest'),
               7: ('cases_not_investigated_157_1_b', 'not invest'), 8: ('cases_transferred', 'transferred'),
               9: ('cases_withdrawn_investigation', 'drawn'), 10: ('cases_fr_non_cognizable', 'non cognizable'),
               11: ('cases_fr_false', 'false'), 12: ('cases_fr_mistake_fact_law_civil', 'mistake'),
               13: ('cases_fr_true_insufficient_evidence', 'true but insufficient'),
               14: ('cases_abated_investigation', 'abated'), 15: ('cases_final_report_total', 'final report > total'),
               16: ('cases_chargesheeted_prev_year', 'pr'), 17: ('cases_chargesheeted_current_year', 'during'),
               18: ('cases_chargesheeted', '16+'), 19: ('cases_disposed_police', 'disposed off by police'),
               20: ('cases_quashed_investigation', 'quashed'), 21: ('cases_stayed_investigation', 'stayed'),
               22: ('cases_pending_investigation', 'end of the year'), 23: ('chargesheeting_rate', 'rate'),
               24: ('pendency_pct_investigation', 'pendency')},
    'court': {3: ('cases_pending_trial_start', 'previous year'), 4: ('cases_sent_for_trial', 'sent for trial'),
              5: ('cases_for_trial', 'total cases for trial'), 6: ('cases_abated_court', 'abated'),
              7: ('cases_withdrawn_prosecution', 'drawn'), 8: ('cases_compounded', 'compoun'),
              9: ('cases_plea_bargaining', 'plea'), 10: ('cases_quashed', 'quashed'),
              11: ('cases_disposed_without_trial', 'without trial'), 12: ('cases_stayed_record_room', 'record room'),
              13: ('cases_convicted_prev_year', 'previous year'), 14: ('cases_convicted_current_year', 'during the year'),
              15: ('cases_convicted', 'convicted (col'), 16: ('cases_discharged', 'discharged'),
              17: ('cases_acquitted', 'acquitted'), 18: ('cases_trials_completed', 'trials were completed'),
              19: ('cases_disposed_courts', 'disposed off by courts'), 20: ('cases_pending', 'pending trial at end'),
              21: ('conviction_rate', 'conviction rate'), 22: ('pendency_pct', 'pendency')},
}
PERSON_GROUP = [(r'arrested', 'arrested'), (r'charge-? ?sheeted', 'chargesheeted'), (r'convicted', 'convicted'),
                (r'discharged', 'discharged'), (r'acquitted', 'acquitted')]
SEX = {'male': '_male', 'female': '_female', 'transgender': '_transgender', 'total': ''}


def measure_from_header(kind, h):
    h = h.lower().replace('\n', ' ')
    if kind == 'persons':
        g, _, s = h.partition(' > ')
        grp = next(k for rx, k in PERSON_GROUP if re.search(rx, g))
        return grp + SEX[s.strip()]
    raise ValueError('police/court tables are mapped by column number')


def measure_from_colno(kind, colno, header):
    m, kw = MAP_2017[kind][colno]
    if header is not None and kw not in header.lower():
        raise ValueError(f'heading check failed {kind} col {colno}: {header!r} lacks {kw!r}')
    return m


# explicit column maps for 2016 (PDF only, older layout; verified against printed headings/formulas)
MAP_2016 = {
    'police': {3: 'cases_pending_investigation_start', 4: 'cases_reported', 5: 'cases_for_investigation',
               6: 'cases_withdrawn_investigation', 7: 'cases_not_investigated_157_1_b', 8: 'cases_transferred',
               9: 'cases_fr_true_insufficient_evidence', 10: 'cases_fr_false', 11: 'cases_fr_mistake_fact_law_civil',
               12: 'cases_fr_non_cognizable', 13: 'cases_final_report_total', 14: 'cases_chargesheeted',
               15: 'cases_disposed_police', 16: 'cases_pending_investigation', 17: 'chargesheeting_rate',
               18: 'pendency_pct_investigation'},
    'court': {3: 'cases_pending_trial_start', 4: 'cases_sent_for_trial', 5: 'cases_for_trial',
              6: 'cases_withdrawn_prosecution', 7: 'cases_plea_bargaining', 8: 'cases_compounded',
              9: 'cases_trials_completed', 10: 'cases_convicted', 11: 'cases_acquitted_or_discharged',
              12: 'cases_disposed_courts', 13: 'cases_pending', 14: 'conviction_rate', 15: 'pendency_pct'},
    'persons': {3: 'arrested_male', 4: 'arrested_female', 5: 'arrested', 6: 'chargesheeted_male',
                7: 'chargesheeted_female', 8: 'chargesheeted', 9: 'convicted_male', 10: 'convicted_female',
                11: 'convicted', 12: 'acquitted_male', 13: 'acquitted_female', 14: 'acquitted',
                15: 'discharged_male', 16: 'discharged_female', 17: 'discharged'},
}
# PDF-only tables in 2019/2020 use the same column numbering as this XLSX (checked: identical column
# numbers and printed formulas, e.g. 'Conviction Rate (Col.15/Col.18)')
PDF_REF = {(2019, '3A.5'): (2018, '3A.5'), (2019, '3A.6'): (2018, '3A.5'), (2019, '3A.7'): (2018, '3A.7'),
           (2019, '3A.8'): (2018, '3A.7'), (2019, '3A.10'): (2019, '3A.9'),
           (2020, '3A.6'): (2020, '3A.5'), (2020, '3A.8'): (2020, '3A.7'), (2020, '3A.10'): (2020, '3A.9')}

UNIT = lambda m: 'percent' if m.endswith(('_rate', '_pct', '_pct_investigation')) else None


# ------------------------------------------------------------------ crime head std keys
def std_head(chain, sl):
    """chain: list of labels from top-level to this row."""
    n = ' - '.join(chain).lower()
    top, last = chain[0].lower(), chain[-1].lower()
    depth = len(chain)
    if re.match(r'^total crimes? against women', n):
        return 'total'
    if re.match(r'^total (bns/ipc|ipc/bns|ipc) crimes', n):
        return 'total_ipc'
    if re.match(r'^total sll', n):
        return 'total_sll'
    if depth == 1:
        for rx, k in [(r'^murder with rape', 'murder_rape'), (r'^dowry deaths', 'dowry'), (r'^abetment', 'abetment_suicide'),
                      (r'^acid attack(?! &)', 'acid_attack'), (r'^attempt to acid', 'attempt_acid_attack'),
                      (r'^cruelty by husband', 'cruelty'), (r'^kidnapp?ing (and|&) abduction of women$', 'kidnap'),
                      (r'^human trafficking', 'trafficking'), (r'^rape$', 'rape'), (r'^attempt to commit rape', 'attempt_rape'),
                      (r'^assault on women with intent to outrage', 'assault'), (r'^sexual harassment', 'sexual_harassment'),
                      (r'^assault or use of criminal force with intent to disrobe', 'disrobe'), (r'^voyeurism', 'voyeurism'),
                      (r'^stalking', 'stalking'), (r'^insult to the modesty', 'insult'), (r'^dowry prohibition', 'dowry_act'),
                      (r'^immoral traffic', 'itpa'), (r'domestic violence', 'dv_act'), (r'^cyber crimes', 'cyber'),
                      (r'^protection of children from sexual', 'pocso_girls'),
                      (r'^selling of (minor )?girls', 'selling_minor_girls'), (r'^buying of (minor )?girls', 'buying_minor_girls'),
                      (r'^procuration of minor girls', 'procuration_minor_girls'),
                      (r'^kidnapping and abduction of women to compel', 'kidnap_marriage'),
                      (r'^importation of girls', 'import')]:
            if re.search(rx, top):
                return k
        return ''
    # sub-heads
    if last == 'girls':
        for rx, k in [(r'^rape$', 'rape_minor'), (r'^attempt to commit rape', 'attempt_rape_minor'),
                      (r'^assault on women with intent', 'assault_minor'), (r'^insult', 'insult_minor')]:
            if re.search(rx, chain[-2].lower()):
                return k
        return ''
    if depth == 2 and top.startswith('assault on women with intent to outrage'):  # 2016 sub-heads of 354
        for rx, k in [(r'^sexual harassment', 'sexual_harassment'), (r'disrobe', 'disrobe'), (r'^voyeurism', 'voyeurism'),
                      (r'^stalking', 'stalking')]:
            if re.search(rx, last):
                return k
    if top.startswith('protection of children'):
        for rx, k in [(r'4 ?& ?6', 'pocso_penetrative'), (r'8 ?& ?10', 'pocso_sexual_assault'), (r'section 12', 'pocso_harassment'),
                      (r'14 ?& ?15', 'pocso_pornography')]:
            if re.search(rx, last):
                return k
    if top.startswith('kidnapp'):
        if re.search(r'compel her for marriage$', last):
            return 'kidnap_marriage'
        if re.search(r'importation', last):
            return 'import'
        if re.search(r'procuration', last):
            return 'procuration_minor_girls'
    return ''


# ------------------------------------------------------------------ sources
def sources():
    man = json.loads((RAW / 'manifest.json').read_text(encoding='utf8'))
    src = {}
    for m in man:
        t = m.get('table')
        if t not in TABLES or m['year'] not in YEARS:
            continue
        p = RAW / m['local'].replace(chr(92), '/')
        key = (m['year'], t)
        # prefer xlsx whose title row names the right table
        if p.suffix == '.xlsx':
            try:
                t0 = clean(pd.read_excel(p, header=None, nrows=1).iat[0, 0]) or ''
            except Exception:
                continue
            if re.sub(r'\s', '', t0).upper() != 'TABLE' + t:
                print('skip mislabelled xlsx', p.name, t0)
                continue
            src[key] = (p, m['url'])
        elif key not in src:
            src[key] = (p, m['url'])
    return src


def norm_label(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower().replace('kidnaping', 'kidnapping'))


def extract(year, table, path):
    kind = KIND[table]
    if path.suffix == '.xlsx':
        d = xlsx_cells(path)
        if kind == 'persons':
            d['measure'] = d.header.apply(lambda h: measure_from_header(kind, h))
        else:
            d['measure'] = [measure_from_colno(kind, c, h) for c, h in zip(d.colno, d.header)]
    else:
        d = pdf_cells(path)
        if year == 2016:
            cmap = MAP_2016[kind]
        elif kind != 'persons':
            cmap = {c: v[0] for c, v in MAP_2017[kind].items()}
        else:
            ry, rt = PDF_REF[(year, table)]
            ref = xlsx_cells(SRC[(ry, rt)][0])
            ref['measure'] = ref.header.apply(lambda h: measure_from_header(kind, h))
            cmap = dict(ref.drop_duplicates('colno')[['colno', 'measure']].values)
        d['measure'] = d.colno.map(cmap)
        if d.measure.isna().any():
            raise ValueError(f'{year} {table}: unmapped colnos {sorted(d[d.measure.isna()].colno.unique())}')
    # one label per row key: label (serial number only to split repeated labels such as Women/Girls)
    d['nl'] = d.label.apply(norm_label)
    dup = d.drop_duplicates(['seg', 'sl', 'nl']).groupby(['seg', 'nl']).size()
    rep = set(i[1] for i, v in dup.items() if v > 1)
    d['key'] = d.apply(lambda r: r.nl + ('#' + str(r.sl) if r.nl in rep else ''), axis=1)
    # same key on two different rows of one page (e.g. 2017 labels the UT subtotal 'TOTAL STATE(S)')
    occ = d.drop_duplicates(['seg', 'row'])[['seg', 'row', 'key']].copy()
    occ['occ'] = occ.groupby(['seg', 'key']).cumcount()
    d = d.merge(occ[['seg', 'row', 'occ']], on=['seg', 'row'])
    d['key'] = d.key + d.occ.map(lambda o: '~%d' % o if o else '')
    d['value'] = d.value.apply(to_num)
    # check no key/measure has conflicting values
    g = d.groupby(['key', 'measure']).value.nunique()
    if (g > 1).any():
        raise ValueError(f'{year} {table}: conflicting cells {g[g > 1].head()}')
    d = d.drop_duplicates(['key', 'measure'])
    lab = d.drop_duplicates('key').set_index('key')[['sl', 'label']]
    return d, lab


def attach_rows(year, table, d, lab):
    if table in STATEWISE:
        kinds = lab.label.apply(std_state)
        lab['kind'] = [k[0] for k in kinds]
        lab['state_ut'] = [k[1] for k in kinds]
        bad = lab[lab.kind.isna()]
        if len(bad):
            raise ValueError(f'{year} {table}: unknown rows {bad.label.tolist()}')
        d = d.join(lab[['kind', 'state_ut']], on='key')
        d = d[d.kind.isin(['state', 'allindia'])]
        d['crime_head'] = 'Total Crime against Women'
        d['crime_head_std'] = 'total'
    else:
        sl2label = {}
        for k, r in lab.iterrows():
            if r.sl and str(r.sl) != 'nan':
                sl2label.setdefault(str(r.sl), r.label)
        chains = {}
        for k, r in lab.iterrows():
            sl = str(r.sl) if r.sl and str(r.sl) != 'nan' else None
            chain = [r.label]
            while sl and '.' in sl:
                sl = sl.rsplit('.', 1)[0]
                chain.insert(0, sl2label.get(sl, sl))
            chains[k] = chain
        d['crime_head'] = d.key.map(lambda k: ' - '.join(re.sub(r'\s*\*+$', '', x) for x in chains[k]))
        d['crime_head_std'] = d.key.map(lambda k: std_head(chains[k], lab.at[k, 'sl']))
        d['state_ut'] = 'All India'
    return d


def merge_dnh(df):
    """Pre-2020 tables list D&N Haveli and Daman & Diu separately: sum counts into the merged UT and
    recompute rates with NCRB's own formulas."""
    key = 'Dadra & Nagar Haveli and Daman & Diu'
    out = []
    for (y, t), g in df.groupby(['year', 'table']):
        m = g[g.state_ut == key]
        if m.key.nunique() <= 1:
            out.append(g); continue
        rest = g[g.state_ut != key]
        s = m[~m.measure.map(lambda x: bool(UNIT(x)))].groupby('measure', as_index=False).value.sum(min_count=1)
        v = dict(zip(s.measure, s.value))
        rates = {}
        if 'cases_chargesheeted' in v:
            den = v.get('cases_chargesheeted', 0) + v.get('cases_fr_true_insufficient_evidence', 0) if y == 2016 else v.get('cases_disposed_police')
            if y == 2016:  # 2016 formula: Col.14/(Col.14+Col.9)
                den = v['cases_chargesheeted'] + v['cases_fr_true_insufficient_evidence']
            else:  # Col.18/Col.19
                den = v['cases_disposed_police']
            rates['chargesheeting_rate'] = 100 * v['cases_chargesheeted'] / den if den else None
            rates['pendency_pct_investigation'] = 100 * v['cases_pending_investigation'] / v['cases_for_investigation'] if v.get('cases_for_investigation') else None
        if 'cases_convicted' in v:
            rates['conviction_rate'] = 100 * v['cases_convicted'] / v['cases_trials_completed'] if v.get('cases_trials_completed') else None
            rates['pendency_pct'] = 100 * v['cases_pending'] / v['cases_for_trial'] if v.get('cases_for_trial') else None
        rows = [{'measure': k, 'value': val} for k, val in v.items()] + \
               [{'measure': k, 'value': None if val is None else round(val, 1)} for k, val in rates.items()]
        mm = pd.DataFrame(rows)
        base = m.iloc[0]
        for c in ['year', 'table', 'state_ut', 'crime_head', 'crime_head_std', 'source', 'kind']:
            mm[c] = base[c]
        mm['note'] = 'sum of D&N Haveli and Daman & Diu' + ('; rate recomputed' if rates else '')
        out.append(pd.concat([rest, mm], ignore_index=True))
    return pd.concat(out, ignore_index=True)


# ------------------------------------------------------------------ validation
VAL = []


def check(topic, year, table, check_name, measure, expected, actual, tol=0, detail=''):
    ok = expected is not None and actual is not None and abs(expected - actual) <= tol
    VAL.append({'topic': topic, 'year': year, 'table': table, 'check': check_name, 'measure': measure,
                'expected': expected, 'actual': actual, 'diff': None if not ok and (expected is None or actual is None) else round(actual - expected, 2),
                'result': 'pass' if ok else 'FAIL', 'detail': detail})


def validate_statewise(df, topic):
    for (y, t, m), g in df[(df.crime_head_std == 'total') & df.table.isin(STATEWISE)].groupby(['year', 'table', 'measure']):
        if UNIT(m):
            continue
        ai = g[g.state_ut == 'All India'].value
        st = g[g.state_ut != 'All India'].value.sum()
        check(topic, y, t, 'states_sum_to_all_india', m, ai.iloc[0] if len(ai) else None, st)


def validate_heads_vs_state(df, topic, tables):
    ch, sw = tables
    for y in YEARS:
        a = df[(df.year == y) & (df.table == ch) & (df.crime_head_std == 'total')].set_index('measure').value
        b = df[(df.year == y) & (df.table == sw) & (df.state_ut == 'All India')].set_index('measure').value
        for m in sorted(set(a.index) & set(b.index)):
            check(topic, y, f'{ch} vs {sw}', 'crimehead_total_equals_statewise_all_india', m, b[m], a[m], tol=0.05 if UNIT(m) else 0)
        # IPC + SLL = total
        ipc = df[(df.year == y) & (df.table == ch) & (df.crime_head_std == 'total_ipc')].set_index('measure').value
        sll = df[(df.year == y) & (df.table == ch) & (df.crime_head_std == 'total_sll')].set_index('measure').value
        for m in sorted(set(ipc.index) & set(sll.index) & set(a.index)):
            if not UNIT(m):
                check(topic, y, ch, 'ipc_plus_sll_equals_total', m, a[m], ipc[m] + sll[m])


def validate_internal(df, topic):
    for (y, t, s, h), g in df.groupby(['year', 'table', 'state_ut', 'crime_head']):
        v = dict(zip(g.measure, g.value))
        lab = f'{s} | {h}'
        def c(name, m, exp, act, tol=0):
            if exp is not None and act is not None and not pd.isna(exp) and not pd.isna(act):
                check(topic, y, t, name, m, exp, act, tol, lab)
        if topic == 'persons' and t == '5.8':
            if v.get('trials_completed') is not None:
                c('convicted_acquitted_discharged_eq_trials_completed', 'trials_completed', v['trials_completed'],
                  sum(v.get(k) or 0 for k in ['convicted', 'acquitted', 'discharged']))
                c('under_trial_minus_disposed_eq_pending', 'pending_trial', v.get('pending_trial'),
                  v['total_under_trial'] - sum(v.get(k) or 0 for k in ['compounded', 'withdrawn', 'trials_completed']))
        elif topic == 'persons' and t == '5.7':
            ks = ['pending_investigation_start', 'arrested', 'released_before_trial', 'chargesheeted']
            if all(v.get(k) is not None for k in ks):
                c('start_plus_arrested_minus_disposed_eq_pending', 'pending_investigation', v.get('pending_investigation'),
                  v['pending_investigation_start'] + v['arrested'] - v['released_before_trial'] - v['chargesheeted'])
            else:
                c('columns_present', 'pending_investigation_start', 1, None)
        elif topic == 'persons':
            for base in ['arrested', 'chargesheeted', 'convicted', 'discharged', 'acquitted']:
                parts = [v.get(base + sx) for sx in ('_male', '_female', '_transgender') if base + sx in v]
                if base in v and parts and None not in parts:
                    c('male_female_tg_sum_to_total', base, v[base], sum(parts))
        elif topic == 'court':
            if 'cases_discharged' in v:
                c('convicted_acquitted_discharged_eq_trials_completed', 'cases_trials_completed', v.get('cases_trials_completed'),
                  (v.get('cases_convicted') or 0) + (v.get('cases_acquitted') or 0) + (v.get('cases_discharged') or 0))
            elif 'cases_acquitted_or_discharged' in v:
                c('convicted_acquitted_discharged_eq_trials_completed', 'cases_trials_completed', v.get('cases_trials_completed'),
                  (v.get('cases_convicted') or 0) + (v.get('cases_acquitted_or_discharged') or 0))
            if t == '5.6' and v.get('cases_for_trial') is not None:
                c('for_trial_minus_disposed_eq_pending', 'cases_pending', v.get('cases_pending'),
                  v['cases_for_trial'] - v['cases_compounded_or_withdrawn'] - v['cases_trials_completed'])
            if 'cases_disposed_courts' in v and 'cases_for_trial' in v:
                c('for_trial_minus_disposed_eq_pending', 'cases_pending', v.get('cases_pending'), v['cases_for_trial'] - v['cases_disposed_courts']
                  - (v.get('cases_withdrawn_prosecution', 0) if y == 2016 else 0) * 0)
            if v.get('cases_trials_completed') and v.get('cases_convicted') is not None:
                c('conviction_rate_recomputed', 'conviction_rate', v.get('conviction_rate'),
                  round(100 * v['cases_convicted'] / v['cases_trials_completed'], 1), tol=0.11)
        elif topic == 'police':
            if 'cases_disposed_police' in v and t == '5.5':
                c('fr_plus_cs_eq_disposed', 'cases_disposed_police', v['cases_disposed_police'],
                  sum(v.get(k) or 0 for k in ['cases_fr_false', 'cases_fr_mistake_fact_law_civil', 'cases_fr_non_cognizable',
                                              'cases_chargesheeted', 'cases_fr_true_insufficient_evidence']))
            if 'cases_disposed_police' in v and y >= 2017:
                c('fr_plus_cs_plus_transfer_eq_disposed', 'cases_disposed_police', v['cases_disposed_police'],
                  sum(v.get(k) or 0 for k in ['cases_not_investigated_157_1_b', 'cases_transferred', 'cases_final_report_total', 'cases_chargesheeted']))


# ------------------------------------------------------------------ Kaggle 2001-2010 persons
KAGGLE_MEASURES = {
    'Persons_Arrested': 'arrested', 'Persons_Chargesheeted': 'chargesheeted', 'Persons_Convicted': 'convicted',
    'Persons_Acquitted': 'acquitted', 'Persons_Trial_Completed': 'trials_completed',
    'Persons_Released_or_Freed_by_Police_or_Magistrate_before_Trial_for_want_of_evidence_or_any_other_reason': 'released_before_trial',
    'Persons_against_whom_cases_Compounded_or_Withdrawn': 'compounded_or_withdrawn',
    'Persons_in_Custody_or_on_Bail_during_Investigation_at_Year_beginning': 'pending_investigation_start',
    'Persons_in_Custody_or_on_Bail_during_Investigation_at_Year_end': 'pending_investigation',
    'Persons_under_Trial_at_Year_beginning': 'pending_trial_start',
    'Total_Persons_under_Trial': 'total_under_trial',
    'Persons_in_Custody_or_on_Bail_during_Trial_at_Year_End': 'pending_trial',
}
KAGGLE_HEADS = {'Rape': 'rape', 'Kidnapping & Abduction - Women & Girls': 'kidnap', 'Dowry Deaths': 'dowry',
                'Molestation': 'assault', 'Sexual harassment': 'insult', 'Cruelty by Husband and Relatives': 'cruelty',
                'Importation of Girls': 'import', 'Immoral Traffic (Prevention) Act': 'itpa', 'Dowry Prohibition Act': 'dowry_act',
                'Indecent Representation of Women (Prohibition) Act': '', 'Sati Prevention Act': '',
                'Total Crime Against Women': 'total'}


def kaggle():
    p = PROJ / 'data' / 'raw' / 'rajanand_crime-in-india' / '43_Arrests_under_crime_against_women.csv'
    rows = [r for r in csv.reader(open(p, encoding='utf-8-sig')) if r]
    hdr = rows[0]
    # Sub_Group_Name values containing a comma are unquoted in the source: re-join them
    fixed = [r if len(r) == 16 else r[:3] + [r[3] + ',' + r[4]] + r[5:] for r in rows[1:]]
    k = pd.DataFrame(fixed, columns=hdr)
    recs = []
    for _, r in k.iterrows():
        kind, st = std_state(r.Area_Name)
        for col, m in KAGGLE_MEASURES.items():
            recs.append({'year': int(r.Year), 'state_ut': st, 'raw_state': r.Area_Name, 'crime_head': r.Group_Name,
                         'crime_head_std': KAGGLE_HEADS[r.Group_Name], 'measure': m, 'value': to_num(r[col]),
                         'table': 'Kaggle 43', 'source': 'Kaggle rajanand/crime-in-india 43_Arrests_under_crime_against_women.csv (NCRB CII)'})
    d = pd.DataFrame(recs)
    # D&N Haveli + Daman & Diu -> merged UT (counts only)
    n_before = d.groupby(['year', 'state_ut', 'crime_head', 'measure']).raw_state.nunique()
    d = d.groupby(['year', 'state_ut', 'crime_head', 'crime_head_std', 'measure', 'table', 'source'], as_index=False) \
        .agg(value=('value', lambda s: s.sum(min_count=1)), raw_state=('raw_state', lambda s: ' + '.join(sorted(set(s)))))
    d['note'] = d.raw_state.map(lambda s: 'sum of D&N Haveli and Daman & Diu' if '+' in s else '')
    # validation: heads sum to total? (Total group excludes nothing but is missing for some state-years)
    for (y, s, m), g in d.groupby(['year', 'state_ut', 'measure']):
        tot = g[g.crime_head_std == 'total'].value
        parts = g[g.crime_head_std != 'total'].value.sum()
        if len(tot):
            check('persons', y, 'Kaggle 43', 'crime_heads_sum_to_total', m, tot.iloc[0], parts, detail=s)
    for (y, s, h), g in d.groupby(['year', 'state_ut', 'crime_head']):
        v = dict(zip(g.measure, g.value))
        check('persons', y, 'Kaggle 43', 'convicted_plus_acquitted_eq_trials_completed', 'trials_completed',
              v['trials_completed'], v['convicted'] + v['acquitted'], detail=f'{s} | {h}')
        check('persons', y, 'Kaggle 43', 'under_trial_start_plus_chargesheeted_eq_total_under_trial', 'total_under_trial',
              v['total_under_trial'], v['pending_trial_start'] + v['chargesheeted'], detail=f'{s} | {h}')
        check('persons', y, 'Kaggle 43', 'total_under_trial_minus_disposed_eq_pending_trial', 'pending_trial',
              v['pending_trial'], v['total_under_trial'] - v['trials_completed'] - v['compounded_or_withdrawn'], detail=f'{s} | {h}')
    return d.drop(columns=['raw_state'])


# ------------------------------------------------------------------ main
SRC = {}


def main():
    SRC.update(sources())
    frames = []
    for y in YEARS:
        for t in TABLES:
            if (y, t) not in SRC:
                print('MISSING', y, t); continue
            p, url = SRC[(y, t)]
            d, lab = extract(y, t, p)
            d = attach_rows(y, t, d, lab)
            d['year'], d['table'] = y, t
            d['source'] = f'NCRB CII {y} Table {t} ({p.name})'
            d['kind'] = KIND[t]
            d['note'] = ''
            frames.append(d[['year', 'table', 'kind', 'state_ut', 'crime_head', 'crime_head_std', 'measure', 'value', 'source', 'note', 'key']])
            print(y, t, p.suffix, len(d))
    df = pd.concat(frames, ignore_index=True)
    df = merge_dnh(df)
    from disposal_2014_2015 import old_tables
    df = pd.concat([old_tables(norm_label, attach_rows), df], ignore_index=True)
    for topic in ['persons', 'police', 'court']:
        sub = df[df.kind == topic]
        validate_statewise(sub, topic)
        tabs = {'persons': ('3A.9', '3A.10'), 'police': ('3A.5', '3A.6'), 'court': ('3A.7', '3A.8')}[topic]
        validate_heads_vs_state(sub, topic, tabs)
        validate_internal(sub, topic)
    kg = kaggle()

    def finish(d, unit_default):
        d = d.copy()
        # drop the crime-head table's 'total' row where the State/UT table gives the same All-India figure
        d['unit'] = d.measure.map(lambda m: UNIT(m) or unit_default)
        d = d.rename(columns={'value': 'count'})
        d['table'] = d['table'].astype(str)
        cols = ['year', 'state_ut', 'crime_head', 'crime_head_std', 'measure', 'count', 'unit', 'table', 'source', 'note']
        return d[cols].sort_values(['year', 'table', 'state_ut', 'crime_head', 'measure']).reset_index(drop=True)

    def dedupe_total(d, ch, sw):
        # All-India total appears in both the crime-head and state-wise table; keep the state-wise one
        drop = (d.table == ch) & (d.crime_head_std == 'total')
        have = set(zip(d[d.table == sw].year, d[d.table == sw].measure))
        drop &= pd.Series([(y, m) in have for y, m in zip(d.year, d.measure)], index=d.index)
        return d[~drop]

    per = dedupe_total(df[df.kind == 'persons'], '3A.9', '3A.10')
    per = pd.concat([kg, per], ignore_index=True)
    per = finish(per, 'persons')
    pol = finish(dedupe_total(df[df.kind == 'police'], '3A.5', '3A.6'), 'cases')
    cou = finish(dedupe_total(df[df.kind == 'court'], '3A.7', '3A.8'), 'cases')
    for d in (per, pol, cou):
        d['count'] = d['count'].round(2)
        d.loc[d.unit != 'percent', 'count'] = d.loc[d.unit != 'percent', 'count'].round(0)
    per.to_csv(OUT / 'ncrb_disposal_persons_2001_2024.csv', index=False, float_format='%.10g')
    pol.to_csv(OUT / 'ncrb_disposal_police_cases_2014_2024.csv', index=False, float_format='%.10g')
    cou.to_csv(OUT / 'ncrb_disposal_court_cases_2014_2024.csv', index=False, float_format='%.10g')
    v = pd.DataFrame(VAL)
    v.to_csv(OUT / 'ncrb_disposal_validation.csv', index=False, float_format='%.10g')
    print(v.groupby(['topic', 'check', 'result']).size().to_string())
    print('FAILS:\n', v[v.result == 'FAIL'].head(40).to_string())


if __name__ == '__main__':
    main()
