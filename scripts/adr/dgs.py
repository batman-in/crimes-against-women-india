import requests,sys,json,urllib.parse
seen={}
def q(query,n=100):
    for off in range(0,n,50):
        u="https://www.data.gov.in/backend/dmspublic/v1/resources?query="+urllib.parse.quote(query)+f"&offset={off}&limit=50&format=json"
        r=requests.get(u,headers={'User-Agent':'Mozilla/5.0'},timeout=60).json()
        rows=r['data']['rows']
        for x in rows:
            t=x['title'][0]; seen[x['uuid'][0]]=dict(title=t,file=(x.get('datafile') or [''])[0],alias=x['node_alias'][0],src=x.get('source',[''])[0] if x.get('source') else '',cat=x.get('catalog_title',[''])[0])
        if len(rows)<50: break
for s in sys.argv[1:]: q(s,200)
json.dump(seen,open('dg_results.json','w'),indent=1)
for k,v in seen.items():
    t=v['title'].lower()
    if 'women' in t or 'rape' in t or 'custod' in t:
        print(v['title'],'|',v['file'])
