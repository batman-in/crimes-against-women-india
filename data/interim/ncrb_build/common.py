import re, os
import pandas as pd
import pdfplumber

PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))  # project root
RAW = os.path.join(PROJ, 'data', 'raw', 'ncrb_cii_tables')
DGI = os.path.join(PROJ, 'data', 'raw', 'datagovin')
OUT = os.path.join(PROJ, 'data', 'interim')


def clean(s):
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    s = re.sub(r'\s+', ' ', str(s).replace('\n', ' ')).strip()
    return s or None


# ---------------------------------------------------------------- state names
STATE_MAP = {
    'a&n islands': 'Andaman & Nicobar Islands', 'a & n islands': 'Andaman & Nicobar Islands',
    'andaman & nicobar islands': 'Andaman & Nicobar Islands', 'a&n island': 'Andaman & Nicobar Islands',
    'd&n haveli': 'Dadra & Nagar Haveli and Daman & Diu', 'd & n haveli': 'Dadra & Nagar Haveli and Daman & Diu',
    'dadra & nagar haveli': 'Dadra & Nagar Haveli and Daman & Diu',
    'daman & diu': 'Dadra & Nagar Haveli and Daman & Diu',
    'd&n haveli and daman & diu': 'Dadra & Nagar Haveli and Daman & Diu',
    'd & n haveli and daman & diu': 'Dadra & Nagar Haveli and Daman & Diu',
    'dnh and dd':'Dadra & Nagar Haveli and Daman & Diu',
    'd&n haveli & daman & diu': 'Dadra & Nagar Haveli and Daman & Diu',
    'delhi ut': 'Delhi', 'delhi': 'Delhi', 'nct of delhi': 'Delhi',
    'orissa': 'Odisha', 'odisha': 'Odisha',
    'andrha pradesh': 'Andhra Pradesh', 'pondicherry': 'Puducherry', 'uttaranchal': 'Uttarakhand',
    'chhatisgarh': 'Chhattisgarh', 'jammu and kashmir': 'Jammu & Kashmir', 'jammu & kashmir': 'Jammu & Kashmir',
    'ladakh': 'Ladakh', 'telangana': 'Telangana',
}
CANON = ['Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 'Goa', 'Gujarat', 'Haryana',
         'Himachal Pradesh', 'Jharkhand', 'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
         'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana',
         'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal', 'Andaman & Nicobar Islands', 'Chandigarh',
         'Dadra & Nagar Haveli and Daman & Diu', 'Delhi', 'Jammu & Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry']
for c in CANON:
    STATE_MAP.setdefault(c.lower(), c)


def std_state(s):
    """Return (kind, name): kind in {'state','allindia','subtotal',None}"""
    if s is None:
        return None, None
    t = re.sub(r'\s+', ' ', str(s)).strip().strip('*@+#$ ').strip()
    tl = t.lower()
    if re.search(r'total', tl):
        if re.search(r'all[\s-]*india', tl):
            return 'allindia', 'All India'
        return 'subtotal', t
    if tl in STATE_MAP:
        return 'state', STATE_MAP[tl]
    return None, t


# ---------------------------------------------------------------- xlsx header parser
def parse_xlsx(f, measure_pick=('I', '1')):
    """Parse an NCRB CII 'CIIReport' xlsx with horizontally repeated page blocks.
    Returns long df: state_raw, head(tuple), measure, value (only picked measure columns)."""
    raw = pd.read_excel(f, header=None, dtype=object)
    mrow = None
    for i in range(0, 14):
        vals = [clean(v) for v in raw.iloc[i]]
        if sum(v in ('I', 'V', 'R', 'Total', 'IPC', 'BNS') for v in vals) >= 3:
            mrow = i
            break
    srow = [i for i in range(mrow) if any(clean(v) and re.match(r'State', clean(v)) for v in raw.iloc[i])][0]
    hdr_rows = list(range(srow, mrow))
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
    meas = [clean(v) for v in raw.iloc[mrow]]
    # state column per block: column whose header is State/UT
    state_cols = [c for c in range(raw.shape[1]) if heads[c] and re.match(r'State', heads[c][0])]
    recs = []
    for c in range(raw.shape[1]):
        if meas[c] not in measure_pick:
            continue
        sc = max(s for s in state_cols if s < c)
        for r in range(mrow + 1, raw.shape[0]):
            st = clean(raw.iat[r, sc])
            v = raw.iat[r, c]
            if st is None:
                continue
            recs.append((st, heads[c], meas[c], v))
    return pd.DataFrame(recs, columns=['state_raw', 'head', 'measure', 'value'])


def parse_simple_xlsx(f):
    """NCRB xlsx without I/V/R measure row (e.g. 3A.4, 3A.11): header rows between State/UT row
    and the column-number row."""
    raw = pd.read_excel(f, header=None, dtype=object)
    srow = [i for i in range(10) if any(clean(v) and re.match(r'State', clean(v)) for v in raw.iloc[i])][0]
    nrow = [i for i in range(srow + 1, 12) if clean(raw.iat[i, 1]) in ('2', '[2]')][0]
    hdr_rows = list(range(srow, nrow))
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
    colno = [clean(v) for v in raw.iloc[nrow]]
    state_cols = [c for c in range(raw.shape[1]) if heads[c] and re.match(r'State', heads[c][0])]
    recs = []
    for c in range(raw.shape[1]):
        if not heads[c] or re.match(r'(State|S\. ?No|SL)', heads[c][0], re.I):
            continue
        sc = max(s for s in state_cols if s < c)
        for r in range(nrow + 1, raw.shape[0]):
            st = clean(raw.iat[r, sc])
            if st is None:
                continue
            recs.append((st, heads[c], colno[c], raw.iat[r, c]))
    return pd.DataFrame(recs, columns=['state_raw', 'head', 'colno', 'value'])


# ---------------------------------------------------------------- pdf parser
NUM = r'-?\d[\d,]*(?:\.\d+)?'


def parse_pdf(f, pick=('I',), pages=None):
    """Generic NCRB CII PDF table parser (pdfplumber). Header cells from extract_tables,
    data rows from the first cell text. Returns state_raw, head, measure, colno, value."""
    recs = []
    with pdfplumber.open(f) as pdf:
        for pi, pg in enumerate(pdf.pages):
            if pages and pi + 1 not in pages:
                continue
            ts = pg.extract_tables()
            if not ts:
                continue
            t = ts[0]
            # measure row
            mi = next(i for i, r in enumerate(t) if sum((c or '').strip() in ('I', 'V', 'R') for c in r) >= 3)
            hdr = t[:mi]
            ncol = len(t[0])
            heads, cur = [], [None] * len(hdr)
            for c in range(ncol):
                vals = [clean(r[c]) if c < len(r) else None for r in hdr]
                for k, v in enumerate(vals):
                    if v is not None:
                        cur[k] = v
                        for kk in range(k + 1, len(vals)):
                            cur[kk] = vals[kk]
                        break
                heads.append(tuple(x for x in cur if x))
            meas = [clean(c) for c in t[mi]]
            colno = [clean(c) for c in t[mi + 1]] if mi + 1 < len(t) else [None] * ncol
            datacols = [c for c in range(ncol) if meas[c] in ('I', 'V', 'R')]
            lines = []
            for r in t[mi + 2:]:
                first = (r[0] or '').split(chr(10))
                rest = ' '.join(clean(c) for c in r[1:] if clean(c))
                if rest:
                    first[-1] = first[-1] + ' ' + rest
                lines.extend(first)
            for txt in lines:
                txt = clean(txt)
                if not txt or txt.upper().startswith(('STATES', 'UNION TERR', 'UTS')):
                    continue
                m = re.match(r'^(?:(\d+)\s+)?(.*?)\s+((?:' + NUM + r'\s*)+)$', txt)
                if not m:
                    continue
                name = m.group(2)
                nums = m.group(3).split()
                if len(nums) != len(datacols):
                    # try: name may end with digits? report
                    print('WARN col mismatch', os.path.basename(f), pi + 1, txt[:80], len(nums), len(datacols))
                    continue
                for c, v in zip(datacols, nums):
                    if meas[c] in pick:
                        recs.append((name, heads[c], meas[c], colno[c], pi + 1, v))
    return pd.DataFrame(recs, columns=['state_raw', 'head', 'measure', 'colno', 'page', 'value'])


def to_num(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).replace(',', '').strip().rstrip('*+@#$ ').strip()
    if s in ('', '-', '--', 'NA', 'N.A.'):
        return None
    try:
        return float(s)
    except ValueError:
        return None
