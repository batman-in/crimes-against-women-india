"""Parse NCRB 'Crime in India' Additional Tables (XLSX) for crimes against women.

Handles the wide layout of Table 3A.2 (heads -> sub-heads -> I/V/R columns) and the
district-wise crimes-against-women workbook. Writes tidy CSVs to data/interim/:

  ncrb_state_<years>.csv      year,state_ut,crime_head,crime_head_std,count
  ncrb_district_<years>.csv   year,state_ut,district,crime_head,crime_head_std,count

Usage:  python scripts/parse_ncrb_xlsx.py 2023 2024
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "ncrb_cii_tables"
INTERIM = ROOT / "data" / "interim"

# (pattern on "head | sub-head", key). First match wins, so specific patterns come first.
RULES = [
    (r"total crimes? against women \((ipc|bns)", "total"),
    (r"total (ipc|bns|ipc/bns|bns/ipc)\S* crimes against women", "total_ipc"),
    (r"total sll crimes", "total_sll"),
    (r"murder with rape", "murder_rape"),
    (r"dowry deaths", "dowry"),
    (r"abetment to suicide", "abetment_suicide"),
    (r"attempt to acid", "attempt_acid_attack"),
    (r"acid attack", "acid_attack"),
    (r"cruelty by husband", "cruelty"),
    (r"procuration of minor girls", "procuration_minor_girls"),
    (r"importation of girls", "import"),
    (r"compel her for marriage.*girls \(below 18", "kidnap_marriage_girls"),
    (r"kidnapping (&|and) abduction of women \((total|col)", "kidnap"),
    (r"human trafficking", "trafficking"),
    (r"selling of +(minor )?girls", "selling_minor_girls"),
    (r"buying of +(minor )?girls", "buying_minor_girls"),
    # 354 sub-heads, reported separately from 2024 (BNS 75-78)
    (r"^sexual harassment \(.*\((total|col)", "sexual_harassment"),
    (r"intent to disrobe.*\((total|col)", "disrobe"),
    (r"^voyeurism.*\((total|col)", "voyeurism"),
    (r"^stalking.*\((total|col)", "stalking"),
    (r"^attempt to commit rape.*\| attempt to commit rape \((total|col)", "attempt_rape"),
    (r"^attempt to commit rape.*girls \(below 18", "attempt_rape_minor"),
    (r"^rape \(.*\| rape \((total|col)", "rape"),
    (r"^rape \(.*girls \(below 18", "rape_minor"),
    (r"^assault on women.*\| assault on women.*modesty", "assault"),
    (r"^assault on women.*girls \(below 18", "assault_minor"),
    (r"insult (to )?the modesty.*\((total|col)", "insult"),
    (r"insult (to )?the modesty.*girls \(below 18", "insult_minor"),
    (r"dowry prohibition", "dowry_act"),
    (r"immoral traffic.*\((total|col)", "itpa"),
    (r"domestic violence act", "dv_act"),
    (r"cyber crimes.*\| cyber crimes", "cyber"),
    (r"protection of children.*\| (protection of children|pocso act \(total)", "pocso_girls"),
    (r"protection of children.*pocso act sec\.? ?4 & 6", "pocso_penetrative"),
    (r"protection of children.*pocso act sec\.? ?8 & 10", "pocso_sexual_assault"),
    (r"protection of children.*pocso act sec\.? ?12", "pocso_harassment"),
    (r"protection of children.*pocso act sec\.? ?14 & 15", "pocso_pornography"),
    (r"protection of children.*child rape", "pocso_penetrative"),
    (r"protection of children.*sexual assault of children", "pocso_sexual_assault"),
    (r"protection of children.*sexual harassment", "pocso_harassment"),
    (r"protection of children.*pornography", "pocso_pornography"),
    (r"indecent representation", "indecent_rep"),
]


def std_key(label):
    low = re.sub(r"\s+", " ", label.lower())
    for pat, key in RULES:
        if re.search(pat, low):
            return key
    return None


def clean(v):
    return "" if pd.isna(v) else re.sub(r"\s+", " ", str(v)).strip()


def columns_by_label(x, header_rows, ivr_row=None):  # noqa: C901
    """Label each data column 'head | sub | subsub', forward-filling merged header cells."""
    labels, parts = {}, ["", "", ""]
    for c in range(x.shape[1]):
        cells = [clean(x.iat[r, c]) for r in header_rows[:3]]
        h = cells[0]
        if h in ("SL", "S. No", "Sl. No.") or h.startswith("State/"):
            parts = ["", "", ""]
            continue
        for i, v in enumerate(cells):
            if v:  # a new cell at level i resets the levels below it
                parts[i] = v
                for j in range(i + 1, 3):
                    parts[j] = ""
        if ivr_row is not None and clean(x.iat[ivr_row, c]) not in ("I", "Total"):
            continue
        labels[c] = " | ".join(p for p in parts if p)
    return labels


def report_unmatched(labels, path):
    miss = sorted({l.split(" | ")[0] for l in labels.values() if not std_key(l)})
    if miss:
        print(f"  unmatched heads in {path.name}: {miss}")


def find_row(x, col, pred, start=0):
    for r in range(start, len(x)):
        if pred(clean(x.iat[r, col])):
            return r
    raise ValueError("row not found")


STATE_FIX = {"D&N Haveli and Daman & Diu": "Dadra & Nagar Haveli and Daman & Diu",
             "A&N Islands": "Andaman & Nicobar Islands", "A & N Islands": "Andaman & Nicobar Islands"}


def parse_state_table(path, year):
    x = pd.read_excel(path, header=None)
    hdr = find_row(x, 1, lambda v: v == "State/UT")
    ivr = find_row(x, 2, lambda v: v in ("I", "IPC"), hdr)
    labels = columns_by_label(x, list(range(hdr, ivr)), ivr)
    report_unmatched(labels, path)
    rows = []
    for r in range(ivr + 1, len(x)):
        name = clean(x.iat[r, 1])
        if not name or name.upper().startswith(("STATES", "UNION")) or name.upper() in ("TOTAL STATE(S)", "TOTAL UT(S)"):
            continue
        if name.upper() == "TOTAL ALL INDIA":
            name = "All India"
        name = STATE_FIX.get(name, name)
        for c, label in labels.items():
            key = std_key(label)
            v = pd.to_numeric(x.iat[r, c], errors="coerce")
            if key and pd.notna(v):
                rows.append((year, name, label, key, int(v)))
    df = pd.DataFrame(rows, columns=["year", "state_ut", "crime_head", "crime_head_std", "count"])
    return df.drop_duplicates(["year", "state_ut", "crime_head_std"])


def parse_district_table(path, year):
    x = pd.read_excel(path, header=None)
    hdr = find_row(x, 1, lambda v: v.startswith("State/"))
    num = find_row(x, 0, lambda v: v in ("1", "[1]"), hdr)  # the column-number row
    labels = columns_by_label(x, list(range(hdr, num)))
    report_unmatched(labels, path)
    rows, state = [], None
    for r in range(num + 1, len(x)):
        first, name = clean(x.iat[r, 0]), clean(x.iat[r, 1])
        m = re.match(r"(?:State|UT)\s*:\s*(.+)", first or name, re.I)
        if m:
            state = STATE_FIX.get(m.group(1).strip(), m.group(1).strip())
            continue
        if not name or not state or name.lower().startswith("total"):
            continue
        for c, label in labels.items():
            key = std_key(label)
            v = pd.to_numeric(x.iat[r, c], errors="coerce")
            if key and pd.notna(v):
                rows.append((year, state, name, label, key, int(v)))
    df = pd.DataFrame(rows, columns=["year", "state_ut", "district", "crime_head", "crime_head_std", "count"])
    return df.drop_duplicates(["year", "state_ut", "district", "crime_head_std"])


SUB_354 = ["sexual_harassment", "disrobe", "voyeurism", "stalking"]


def harmonise_354(df, keys):
    """From 2024 (BNS) NCRB reports 354A-D (BNS 75-78) beside, not inside, the 354 head.
    Fold them back into "assault" so it stays comparable with earlier years."""
    out = []
    for _, g in df.groupby(keys):
        g = g.copy()
        subs = g[g.crime_head_std.isin(SUB_354)]["count"].sum()
        mask = g.crime_head_std == "assault"
        if subs and mask.any() and int(g["year"].iloc[0]) >= 2024:
            g.loc[mask, "count"] += subs
            g.loc[mask, "crime_head"] = "Assault on women to outrage modesty, incl. 354A-D (BNS 74-78, summed)"
        out.append(g)
    return pd.concat(out) if out else df


RELATION_COLS = {2: "known_total", 3: "family", 4: "friends_online_friends_livein_partners_separated_husband",
                 5: "family_friends_neighbours_employer_other_known", 6: "unknown", 7: "total_cases"}


def parse_relation_table(path, year):
    """Table 3A.4: offenders' relation to rape victims (fixed 9-column layout, 2017 on)."""
    x = pd.read_excel(path, header=None)
    rows = []
    for r in range(len(x)):
        name = clean(x.iat[r, 1])
        if not name or name in ("State/UT", "[2]") or name.upper() in ("TOTAL STATE(S)", "TOTAL UT(S)"):
            continue
        if name.upper() == "TOTAL ALL INDIA":
            name = "All India"
        name = STATE_FIX.get(name, name)
        for c, key in RELATION_COLS.items():
            v = pd.to_numeric(x.iat[r, c], errors="coerce")
            if pd.notna(v):
                rows.append((year, name, clean(x.iat[3, c]) or clean(x.iat[2, c]), key, int(v)))
    return pd.DataFrame(rows, columns=["year", "state_ut", "relation", "relation_std", "count"])


def pick(folder, pattern):
    hits = sorted(p for p in folder.glob("*.xlsx") if re.search(pattern, p.name, re.I))
    return hits


def main(years):
    states, districts = [], []
    for y in years:
        folder = RAW / str(y)
        for p in pick(folder, r"TABLE3A2"):
            try:
                df = parse_state_table(p, y)
            except ValueError:
                continue
            print(f"{y} {p.name}: {len(df)} state rows, heads {sorted(df.crime_head_std.unique())}")
            states.append(df)
        for p in pick(folder, r"Districtwise"):
            df = parse_district_table(p, y)
            print(f"{y} {p.name}: {df.district.nunique()} districts, heads {sorted(df.crime_head_std.unique())}")
            districts.append(df)
    relations = []
    for y in years:
        for p in pick(RAW / str(y), r"TABLE3A4"):
            df = parse_relation_table(p, y)
            if len(df):
                print(f"{y} {p.name}: {df.state_ut.nunique()} areas, relation rows {len(df)}")
                relations.append(df)
    tag = "_".join(str(y) for y in years)
    if relations:
        rel = pd.concat(relations).drop_duplicates(["year", "state_ut", "relation_std"])
        rel.to_csv(INTERIM / f"ncrb_relation_{tag}.csv", index=False)
        for y, g in rel[rel.relation_std == "known_total"].groupby("year"):
            nat = g[g.state_ut == "All India"]["count"].sum()
            print(f"  relation {y}: All India known {nat:,}; states sum {g[g.state_ut != 'All India']['count'].sum():,}")
    if states:
        s = pd.concat(states).drop_duplicates(["year", "state_ut", "crime_head_std"])
        s = harmonise_354(s, ["year", "state_ut"])
        s.to_csv(INTERIM / f"ncrb_state_{tag}.csv", index=False)
        validate(s)
    if districts:
        dd = harmonise_354(pd.concat(districts), ["year", "state_ut", "district"])
        dd.to_csv(INTERIM / f"ncrb_district_{tag}.csv", index=False)


def validate(s):
    for y, g in s.groupby("year"):
        nat = g[(g.state_ut == "All India") & (g.crime_head_std == "total")]["count"].sum()
        st = g[(g.state_ut != "All India") & (g.crime_head_std == "total")]["count"].sum()
        print(f"  {y}: All India total {nat:,}; sum of states/UTs {st:,}; match={nat == st}")


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or [2023, 2024])
