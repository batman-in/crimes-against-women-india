"""CII 2014-2015 disposal tables for crimes against women (All India, crime head-wise only):
  5.5 police disposal of cases, 5.6 court disposal of cases,
  5.7 police disposal of persons arrested, 5.8 court disposal of persons.
Used by build_disposal.py."""
import json, re
import pandas as pd
from ncrb_cells import RAW, pdf_cells, pdf_headers, to_num

OLD_KIND = {'5.5': 'police', '5.6': 'court', '5.7': 'persons', '5.8': 'persons'}
OLD_POLICE = [(r'pending investigation from previous', 'cases_pending_investigation_start'), (r'reported during', 'cases_reported'),
              (r'withdrawn', 'cases_withdrawn_investigation'), (r'transferred', 'cases_transferred'),
              (r'total cases for investigation', 'cases_for_investigation'), (r'not investigated', 'cases_not_investigated_157_1_b'),
              (r'final report false', 'cases_fr_false'), (r'mistake of fact', 'cases_fr_mistake_fact_law_civil'),
              (r'non cognizable', 'cases_fr_non_cognizable'), (r'not laid but final report as true', 'cases_fr_true_insufficient_evidence'),
              (r'charge- ?sheets were submitted', 'cases_chargesheeted'), (r'disposed of', 'cases_disposed_police'),
              (r'pending investigation at the end', 'cases_pending_investigation'), (r'charge-sheeting rate', 'chargesheeting_rate'),
              (r'pendency percentage', 'pendency_pct_investigation')]
OLD_COURT = {3: 'cases_pending_trial_start', 4: 'cases_sent_for_trial', 5: 'cases_withdrawn_prosecution', 6: 'cases_plea_bargaining',
             7: 'cases_for_trial', 8: 'cases_compounded_or_withdrawn', 9: 'cases_trials_completed', 10: 'cases_convicted',
             11: 'cases_acquitted_or_discharged', 12: 'cases_pending', 13: 'conviction_rate', 14: 'pendency_pct'}
OLD_COURT_KW = {3: 'previous', 4: 'sent', 5: 'withdrawn', 6: 'plea', 7: 'total', 8: 'compounded', 9: 'completed', 10: 'convicted',
                11: 'acquitted', 12: 'end of the year', 13: 'rate', 14: 'percentage'}
_P57 = ['pending_investigation_start_custody', 'pending_investigation_start_bail', 'pending_investigation_start', 'arrested',
        'released_before_trial', 'chargesheeted', 'pending_investigation_custody', 'pending_investigation_bail']
_P58 = ['pending_trial_start_custody', 'pending_trial_start_bail', 'total_under_trial', 'compounded', 'withdrawn',
        'trials_completed', 'convicted', 'acquitted', 'discharged', 'pending_trial_custody', 'pending_trial_bail']
OLD_PERSONS = {'5.7': {3 + 2 * i + j: m + sx for i, m in enumerate(_P57) for j, sx in enumerate(['_male', '_female'])},
               '5.8': {3 + 2 * i + j: m + sx for i, m in enumerate(_P58) for j, sx in enumerate(['_male', '_female'])}}
# printed heading keywords that must appear for the persons columns (checked on the first column of each pair)
OLD_PERSONS_KW = {'5.7': {3: 'custody', 5: 'bail', 7: 'total', 9: 'arrested', 11: 'police or magistrate', 13: 'charge',
                          15: 'investigation', 17: 'end'},
                  '5.8': {3: 'custody', 5: 'bail', 7: 'total', 9: 'compounded', 11: 'were', 13: 'completed', 21: 'end', 23: 'of the'}}


def old_tables(norm_label, attach_rows):
    man = json.loads((RAW / 'manifest.json').read_text(encoding='utf8'))
    frames, canon = [], {}
    # 5.5 first: its (page-1) labels are the canonical names for each serial number in that year
    man = sorted([m for m in man if m.get('table') in OLD_KIND and m['year'] in (2014, 2015)],
                 key=lambda m: (m['year'], m['table']))
    for m in man:
        t = m.get('table')
        y, kind = m['year'], OLD_KIND[t]
        p = RAW / m['local'].replace(chr(92), '/')
        d = pdf_cells(p)
        hd = pdf_headers(p)
        heads = {c: (txt or '').lower() for (sg, c), txt in hd.items()}
        if kind == 'police':
            cmap = {}
            for c, h in heads.items():
                k = next((k for rx, k in OLD_POLICE if re.search(rx, h)), None)
                if k is None:
                    raise ValueError(f'{y} {t} col {c}: {h}')
                cmap[c] = k
        else:
            kws = OLD_COURT_KW if kind == 'court' else OLD_PERSONS_KW[t]
            for c, kw in kws.items():
                txt = heads.get(c, '') + ' ' + (heads.get(c + 1, '') if kind == 'persons' else '')
                if kw not in txt:
                    raise ValueError(f'{y} {t} col {c} heading check: {heads.get(c)!r} lacks {kw!r}')
            cmap = OLD_COURT if kind == 'court' else OLD_PERSONS[t]
        d['measure'] = d.colno.map(cmap)
        if d.measure.isna().any():
            raise ValueError(f'{y} {t}: unmapped {sorted(d[d.measure.isna()].colno.unique())}')
        d['label'] = d.label.str.replace(r'^CRIME HEAD:\s*', '', regex=True)
        d['nl'] = d.label.apply(norm_label)
        # serial numbers are identical on every page and across Tables 5.5-5.8; labels are not
        d['key'] = [('sl' + str(sl)) if sl and str(sl) != 'nan' else nl for sl, nl in zip(d.sl, d.nl)]
        if t == '5.5':
            first = d.sort_values('seg').drop_duplicates('key')
            canon[y] = dict(zip(first.key, first.label))
        d['label'] = [canon.get(y, {}).get(k, l) if k.startswith('sl') else l for k, l in zip(d.key, d.label)]
        d['value'] = d.value.apply(to_num)
        g = d.groupby(['key', 'measure']).value.nunique()
        if (g > 1).any():
            raise ValueError(f'{y} {t}: conflicting cells')
        d = d.drop_duplicates(['key', 'measure'])
        lab = d.drop_duplicates('key').set_index('key')[['sl', 'label']]
        d = attach_rows(y, t, d, lab)
        d['note'] = ''
        if kind == 'persons':
            base = sorted(set(re.sub(r'_(male|female)$', '', x) for x in d.measure))
            add = []
            for (k, h, hs), gg in d.groupby(['key', 'crime_head', 'crime_head_std']):
                v = dict(zip(gg.measure, gg.value))
                for b in base:
                    if b + '_male' in v and b + '_female' in v and b not in v:
                        add.append({'key': k, 'crime_head': h, 'crime_head_std': hs, 'measure': b,
                                    'value': v[b + '_male'] + v[b + '_female'],
                                    'note': 'total = male + female (NCRB prints sexes only)'})
                pair = ('pending_trial_custody', 'pending_trial_bail') if t == '5.8' else \
                    ('pending_investigation_custody', 'pending_investigation_bail')
                pt = [v.get(b + sx) for b in pair for sx in ('_male', '_female')]
                if None not in pt:
                    add.append({'key': k, 'crime_head': h, 'crime_head_std': hs,
                                'measure': 'pending_trial' if t == '5.8' else 'pending_investigation', 'value': sum(pt),
                                'note': 'custody + bail at year end, male + female (NCRB prints these separately)'})
            d = pd.concat([d, pd.DataFrame(add)], ignore_index=True)
            d['state_ut'] = 'All India'
        d['year'], d['table'], d['kind'] = y, t, kind
        d['source'] = f'NCRB CII {y} Table {t} ({p.name})'
        d['note'] = d['note'].fillna('')
        frames.append(d[['year', 'table', 'kind', 'state_ut', 'crime_head', 'crime_head_std', 'measure', 'value', 'source', 'note', 'key']])
        print(y, t, len(d))
    return pd.concat(frames, ignore_index=True)
