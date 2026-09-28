from build_state import *
d, sub = build()
d = d[d.year <= 2022].copy()  # 2023-2024 handled by coordinator
d['count'] = d['count'].astype('Int64')
# validation: sum of states vs All India per year/head
s = d[d.state_ut != 'All India'].groupby(['year', 'crime_head'])['count'].sum()
a = d[d.state_ut == 'All India'].groupby(['year', 'crime_head'])['count'].sum()
j = pd.concat([s.rename('states'), a.rename('allindia')], axis=1)
j['diff'] = j.states - j.allindia
bad = j[j['diff'].abs() > 0]
print('heads with state-sum != All India:', len(bad), 'of', len(j)); print(bad.to_string()[:3000])
tot = j.reset_index(); tot = tot[tot.crime_head.map(std_key) == 'total']
print(tot.to_string())
print(d.groupby('year').agg(rows=('count','size'), states=('state_ut','nunique'), heads=('crime_head','nunique')))
yrs = '%d_%d' % (d.year.min(), d.year.max())
out = os.path.join(OUT, 'ncrb_state_crime_heads_%s.csv' % yrs)
os.makedirs(OUT, exist_ok=True)
d.sort_values(['year', 'state_ut', 'crime_head'], key=lambda c: c.map(lambda x: '~' if x == 'All India' else x) if c.name=='state_ut' else c).to_csv(out, index=False)
print('wrote', out, len(d))
j.to_csv('val_state.csv')
