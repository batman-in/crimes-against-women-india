"""Rebuild all NCRB 2015-2022 interim outputs (years 2023-2024 intentionally excluded)."""
import os, pandas as pd, subprocess, sys
from common import OUT
for script in ['write_state.py', 'build_district.py', 'build_offenders.py', 'build_3a1_3a11.py']:
    r = subprocess.run([sys.executable, script], capture_output=True, text=True, encoding='utf8')
    if r.returncode: print(r.stderr); raise SystemExit(script)
# district
d = pd.read_pickle('dist_raw.pkl'); d = d[(d.district != '__STATE_TOTAL__') & (d.year <= 2022)].copy()
d['count'] = d['count'].astype('Int64')
d[['year','state_ut','district','crime_head','crime_head_std','count','source']].to_csv(os.path.join(OUT, 'ncrb_district_crime_heads_2015_2022.csv'), index=False)
# relation
o = pd.read_pickle('off.pkl'); o = o[o.year <= 2022].copy(); o['count'] = o['count'].astype('Int64')
o.to_csv(os.path.join(OUT, 'ncrb_rape_offender_relation_2011_2022.csv'), index=False)
# 3A.1
a1 = pd.read_pickle('a1.pkl'); a1 = a1[(a1.year <= 2022) & (a1.cii_edition <= 2022)]
a1.to_csv(os.path.join(OUT, 'ncrb_state_totals_3A1_2015_2022.csv'), index=False)
# 3A.11 + custodial
a11 = pd.read_pickle('a11.pkl'); a11 = a11[a11.year <= 2022].copy(); a11['count'] = a11['count'].astype('Int64')
a11.to_csv(os.path.join(OUT, 'ncrb_rape_sectionwise_3A11_2017_2022.csv'), index=False)
st = pd.read_csv(os.path.join(OUT, 'ncrb_state_crime_heads_2015_2022.csv'))
m = {'Custodial Rape': 'custodial_total', 'Custodial_Gang Rape': 'custodial_gang_rape',
     'Custodial_Other Rape': 'custodial_other_rape', 'Rape - Custodial Rape (Sec. 376C IPC)': 'custodial_total_sec376C'}
e = st[st.crime_head.isin(m)].copy(); e['custody_type'] = e.crime_head.map(m)
cu = pd.concat([e[['year','state_ut','crime_head','custody_type','count','source']], a11[a11.custody_type != '']], ignore_index=True)
cu['count'] = cu['count'].astype('Int64')
cu.to_csv(os.path.join(OUT, 'ncrb_custodial_rape_2015_2022.csv'), index=False)
for f in sorted(os.listdir(OUT)):
    if f.startswith('ncrb_') and f.endswith('.csv'):
        x = pd.read_csv(os.path.join(OUT, f)); print(f, len(x), x.year.min(), x.year.max())
