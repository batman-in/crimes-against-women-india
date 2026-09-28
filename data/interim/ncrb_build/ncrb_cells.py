"""Generic cell extractors for NCRB Crime in India tables (XLSX and text PDFs).

Both return one record per data cell:
    page/segment, sl, label, colno (NCRB printed column number), header (xlsx only), value
Column numbers ([1], [2], ... printed under the headings) are the stable key: [1] is the serial
number, [2] the State/UT or crime-head label, [3..] the data columns.
"""
import re
from pathlib import Path
import pandas as pd
import pdfplumber

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent.parent.parent
RAW = PROJ / 'data' / 'raw' / 'ncrb_cii_tables'
OUT = PROJ / 'data' / 'interim'


def clean(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = re.sub(r'\s+', ' ', str(v).replace('\n', ' ')).strip()
    return s or None


def colno_of(v):
    s = clean(v)
    if s is None:
        return None
    if isinstance(v, float) and v.is_integer():
        s = str(int(v))
    m = re.fullmatch(r'[\[(]?(\d+)[\])]?', s)
    return int(m.group(1)) if m else None


SKIP_LABEL = re.compile(r'^(●|•|\*|note|states:?$|union territor|uts:?$|ipc cases$|sll cases$|ipc crimes$|sll crimes$|'
                        r'as per data|source)', re.I)


def xlsx_cells(path):
    raw = pd.read_excel(path, header=None, dtype=object)
    nr, nc = raw.shape
    # rows holding the printed column numbers: a cell [1] followed by [2]
    num_rows = []
    for r in range(nr):
        starts = [0] if colno_of(raw.iat[r, 0]) == 1 and colno_of(raw.iat[r, 1]) == 2 else []
        if starts:
            num_rows.append((r, starts))
    recs = []
    SLRX = re.compile(r'^(SL|S\.? ?No\.?|Sl\.?|S\. ?No\.?)$', re.I)
    for k, (r, _) in enumerate(num_rows):
        # header block: nearest row above r holding 'SL'/'S. No' cells; those columns start the page blocks
        top = r - 1
        while top > 0 and not any(clean(raw.iat[top, c]) and SLRX.match(clean(raw.iat[top, c])) for c in range(nc)):
            top -= 1
        starts = [c for c in range(nc) if clean(raw.iat[top, c]) and SLRX.match(clean(raw.iat[top, c]))]
        end = num_rows[k + 1][0] if k + 1 < len(num_rows) else nr
        # next segment's header starts a few rows above its number row; stop data at the TABLE title row
        for rr in range(r + 1, end):
            if clean(raw.iat[rr, 0]) and re.match(r'^TABLE\s', clean(raw.iat[rr, 0]), re.I):
                end = rr
                break
        bounds = starts + [nc]
        for b, c0 in enumerate(starts):
            cols = range(c0 + 2, bounds[b + 1])
            heads, cur = {}, [None] * (r - top)
            for c in cols:
                vals = [clean(raw.iat[h, c]) for h in range(top, r)]
                for i, v in enumerate(vals):
                    if v is not None:
                        cur[i] = v
                        for j in range(i + 1, len(vals)):
                            cur[j] = vals[j]
                        break
                heads[c] = ' > '.join(x for x in cur if x)
            for rr in range(r + 1, end):
                sl, label = clean(raw.iat[rr, c0]), clean(raw.iat[rr, c0 + 1])
                if label is None or SKIP_LABEL.match(label) or (sl and SKIP_LABEL.match(sl)):
                    continue
                for c in cols:
                    cn = colno_of(raw.iat[r, c])
                    if cn is None:
                        continue
                    recs.append({'seg': k, 'row': rr, 'sl': sl, 'label': label, 'colno': cn, 'header': heads[c],
                                 'value': raw.iat[rr, c]})
    return pd.DataFrame(recs)


NUMTOK = re.compile(r'^-?\d[\d,]*(\.\d+)?$|^-$|^NA$|^N\.A\.?$')
SLTOK = re.compile(r'^\d{1,2}(\.\d+)*\.?$')  # 1-2 digit serials; excludes years such as 1986


def pdf_cells(path):
    recs = []
    with pdfplumber.open(path) as pdf:
        for pi, pg in enumerate(pdf.pages):
            lines = [l.strip() for l in (pg.extract_text() or '').split('\n')]
            ci = None
            for i, l in enumerate(lines):
                toks = [colno_of(t) for t in l.split()]
                if len(toks) >= 3 and None not in toks and all(x < y for x, y in zip(toks, toks[1:])) and                         (toks[:2] == [1, 2] or toks == list(range(toks[0], toks[0] + len(toks)))):
                    ci = i
                    cols = toks[2:] if toks[:2] == [1, 2] else toks
                    break
            if ci is None:
                continue
            n = len(cols)
            buf, prev_wrapped, rows = [], False, []
            for l in lines[ci + 1:]:
                if not l or SKIP_LABEL.match(l) or re.match(r'^TABLE\s', l, re.I):
                    buf, prev_wrapped = [], False
                    continue
                toks = l.split()
                if len(toks) >= n and all(NUMTOK.match(t) for t in toks[-n:]) and \
                        not (len(toks) > n and NUMTOK.match(toks[-n - 1]) and not SLTOK.match(toks[-n - 1]) and len(toks) == n + 1 and False):
                    lab = toks[:-n]
                    sl = None
                    if lab and SLTOK.match(lab[0]):
                        sl, lab = lab[0].rstrip('.'), lab[1:]
                    if buf:  # label started on the line(s) above the figures
                        b = ' '.join(buf).split()
                        if b and SLTOK.match(b[0]):
                            if sl is None:
                                sl = b[0].rstrip('.')
                            b = b[1:]
                        lab, wrapped = b + lab, True
                    else:
                        wrapped = False
                    rows.append({'sl': sl, 'label': ' '.join(lab), 'vals': toks[-n:]})
                    buf, prev_wrapped = [], wrapped
                else:
                    if rows and SLTOK.match(toks[0]) and rows[-1]['sl'] is None and                             not rows[-1]['label'].lower().startswith('total') and not buf:
                        # serial number printed on the line after the figures (e.g. 2019 3A.7 last page)
                        rows[-1]['sl'] = toks[0].rstrip('.')
                        if len(toks) > 1:
                            rows[-1]['label'] += ' ' + ' '.join(toks[1:])
                        prev_wrapped = False
                    elif prev_wrapped and rows and not SLTOK.match(toks[0]):
                        rows[-1]['label'] += ' ' + l
                        prev_wrapped = False
                    else:
                        buf.append(l)
            for ri, r in enumerate(rows):
                for cn, v in zip(cols, r['vals']):
                    recs.append({'seg': pi, 'row': ri, 'sl': r['sl'], 'label': clean(r['label']), 'colno': cn, 'header': None,
                                 'value': v})
    return pd.DataFrame(recs)


def to_num(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace(',', '').strip().rstrip('*+@#$ ').strip()
    if s in ('', '-', '--', 'NA', 'N.A.', 'N.A'):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def pdf_headers(path):
    """Header text per (page index, column number) for a text PDF, by assigning the heading words to
    the x-range of each printed column number."""
    out = {}
    with pdfplumber.open(path) as pdf:
        for pi, pg in enumerate(pdf.pages):
            words = pg.extract_words(keep_blank_chars=False, use_text_flow=False)
            lines = {}
            for w in words:
                lines.setdefault(round(w['top']), []).append(w)
            # the column-number line: all tokens are integers and include 1, 2
            numline = None
            for top in sorted(lines):
                ws = sorted(lines[top], key=lambda w: w['x0'])
                toks = [colno_of(w['text']) for w in ws]
                if len(toks) >= 3 and None not in toks and toks[:2] == [1, 2] and all(x < y for x, y in zip(toks, toks[1:])):
                    numline = (top, ws, toks)
                    break
            if numline is None:
                continue
            top, ws, toks = numline
            centers = [(w['x0'] + w['x1']) / 2 for w in ws]
            bounds = [(centers[i - 1] + centers[i]) / 2 if i > 0 else -1 for i in range(len(centers))] + [1e9]
            # heading words: below the two title lines, above the number line
            title_bottom = sorted(lines)[1] + 5 if len(lines) > 1 else 0
            for i, cn in enumerate(toks):
                if cn in (1, 2):
                    continue
                lo, hi = bounds[i], bounds[i + 1]
                hw = [w for w in words if title_bottom < w['top'] < top - 1 and lo <= (w['x0'] + w['x1']) / 2 < hi]
                hw.sort(key=lambda w: (round(w['top']), w['x0']))
                out[(pi, cn)] = clean(' '.join(w['text'] for w in hw))
    return out
