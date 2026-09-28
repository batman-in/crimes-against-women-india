import re, pandas as pd, pypdf
from pathlib import Path
ROOT=str(Path(__file__).resolve().parents[2])  # project root
RAW=ROOT+"/data/raw/population"; OUT=ROOT+"/data/interim"
# ---------- district 2011 ----------
d=pd.read_csv(RAW+"/danofer_india-census/india-districts-census-2011.csv")
smap={'ANDAMAN AND NICOBAR ISLANDS':'Andaman & Nicobar Islands','JAMMU AND KASHMIR':'Jammu & Kashmir',
 'DADRA AND NAGAR HAVELI':'Dadra & Nagar Haveli','DAMAN AND DIU':'Daman & Diu','NCT OF DELHI':'Delhi',
 'ORISSA':'Odisha','PONDICHERRY':'Puducherry'}
TEL={'Adilabad','Nizamabad','Karimnagar','Medak','Hyderabad','Rangareddy','Mahbubnagar','Nalgonda','Warangal','Khammam'}
def st(r):
    s=smap.get(r['State name'], r['State name'].title())
    if s=='Jammu & Kashmir' and r['District name'] in ('Leh(Ladakh)','Kargil'): return 'Ladakh'
    if s=='Andhra Pradesh' and r['District name'] in TEL: return 'Telangana'
    return s
d['state_ut']=d.apply(st,axis=1)
d['state_ut_2011']=d['State name'].map(lambda s: smap.get(s,s.title()))
def tc(x):  # title case, keep census spelling
    return re.sub(r"\b([a-z])", lambda m:m.group(1).upper(), x.lower()) if x.isupper() or x.islower() else x
d=d.copy()
d['district']=d['District name'].str.replace(r'\s+',' ',regex=True).str.replace(' AND ',' and ').str.strip()
dist=d.rename(columns={'District code':'census_code','Female':'female_pop','Population':'total_pop'})[
 ['state_ut','district','census_code','female_pop','total_pop','state_ut_2011']]
dist.to_csv(OUT+"/female_pop_district_2011.csv",index=False)
# ---------- state 2011 ----------
SRC_C="Census 2011 PCA (district sums; danofer/india-census Kaggle)"
g=dist.groupby('state_ut')['female_pop'].sum()
rows=[(s,2011,int(v),SRC_C) for s,v in g.items()]
rows.append(('Andhra Pradesh (undivided, 2011)',2011,int(g['Andhra Pradesh']+g['Telangana']),SRC_C))
rows.append(('Jammu & Kashmir (incl. Ladakh, 2011 state)',2011,int(g['Jammu & Kashmir']+g['Ladakh']),SRC_C))
rows.append(('Dadra & Nagar Haveli and Daman & Diu',2011,int(g['Dadra & Nagar Haveli']+g['Daman & Diu']),SRC_C))
rows.append(('India',2011,int(dist.female_pop.sum()),SRC_C))
# ---------- projections Table 11 (1 July) ----------
r=pypdf.PdfReader(RAW+"/TG_population_projections_2011_2036.pdf")
pages={86:['India','Jammu & Kashmir','Himachal Pradesh'],87:['Punjab','Haryana','Delhi'],
 88:['Rajasthan','Uttar Pradesh','Bihar'],89:['Assam','West Bengal','Jharkhand'],
 90:['Odisha','Chhattisgarh','Madhya Pradesh'],91:['Gujarat','Maharashtra','Andhra Pradesh'],
 92:['Karnataka','Kerala','Tamil Nadu'],93:['Chandigarh','Uttarakhand','Sikkim'],
 94:['Arunachal Pradesh','Nagaland','Manipur'],95:['Mizoram','Tripura','Meghalaya'],
 96:['Daman & Diu','Dadra & Nagar Haveli','Goa'],97:['Lakshadweep','Puducherry','Andaman & Nicobar Islands'],
 98:['Telangana','Ladakh']}
SRC_P="MoHFW Technical Group Population Projections 2011-2036 (Jul 2020), Table 11, 1 July, rounded to '000"
proj=[]
for pg,names in pages.items():
    t=r.pages[pg-1].extract_text()
    assert 'Table - 11'.lower() in t.lower().replace('–','-') or 'TABLE - 11' in t, pg
    n=len(names)*3
    found=0
    for m in re.finditer(r'(?<!\d)(20[1-3]\d)((?:\s+[\d,]+){%d})(?=\s|$)'%n, t):
        yr=int(m.group(1)); vals=[int(v.replace(',','')) for v in m.group(2).split()]
        for i,nm in enumerate(names):
            p,ml,f=vals[3*i:3*i+3]
            assert abs(p-ml-f)<=2,(pg,yr,nm,p,ml,f)
            proj.append((nm,yr,f*1000,p*1000))
        found+=1
    assert found==26,(pg,found)
P=pd.DataFrame(proj,columns=['state_ut','year','female_pop','persons'])
P.to_csv(RAW+"/TG_table11_1july_parsed.csv",index=False)
# check state sum vs India
chk=P[P.state_ut!='India'].groupby('year').female_pop.sum()-P[P.state_ut=='India'].set_index('year').female_pop
print('state-sum minus India (proj, persons):',chk.abs().max())
Pk=P[(P.year>=2011)&(P.year<=2036)].copy()
for y,gp in Pk.groupby('year'):
    dd=gp.set_index('state_ut').female_pop
    Pk=pd.concat([Pk,pd.DataFrame([{'state_ut':'Dadra & Nagar Haveli and Daman & Diu','year':y,'female_pop':dd['Dadra & Nagar Haveli']+dd['Daman & Diu']}])])
Pk['source']=SRC_P
Pk=Pk[(Pk.year>=2012)&(Pk.year<=2036)]
S=pd.concat([pd.DataFrame(rows,columns=['state_ut','year','female_pop','source']),
             Pk[['state_ut','year','female_pop','source']]])
S['female_pop']=S.female_pop.astype('int64')
S.to_csv(OUT+"/female_pop_state.csv",index=False)
print(len(dist),len(S)); print(S[S.year==2011].to_string())
print('proj years',sorted(Pk.year.unique()))
print(set(S[S.year==2011].state_ut)^set(Pk.state_ut))
