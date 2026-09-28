"""Build tidy CSVs on crimes against minor girls (under 18) in India from NCRB primary tables.

Inputs (data/raw/minor_girls/):
  ncrb_additional/  NCRB "Crime in India - Additional Tables" XLSX (district-wise crime against
                    children 2014-2024; crime-head-wise gender-wise child victims 2014-2024)
  ncrb_cii_pages/   text of CII Vol-1 Table 3A.3 (rape victims by age) and 4A.9 (POCSO victims by
                    age & sex), extracted with pdfplumber from the official PDFs (+ page PDFs)
  rajanand/         Kaggle rajanand/crime-in-india (NCRB district-wise crimes against children
                    2001-2013; victims of rape by age 2001-2010)

Outputs (data/interim/):
  minor_girls_district.csv, minor_girls_state.csv, minor_girls_allindia_victims.csv,
  minor_girls_rape_victims_age.csv, minor_girls_validation.csv
"""
import glob
import os
import re

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "raw", "minor_girls")
ADD = os.path.join(RAW, "ncrb_additional")
PAGES = os.path.join(RAW, "ncrb_cii_pages")
RAJ = os.path.join(RAW, "rajanand")

# ----------------------------------------------------------------------------- names
STATE_MAP = {
    "a & n islands": "Andaman & Nicobar Islands", "a&n islands": "Andaman & Nicobar Islands",
    "andaman & nicobar islands": "Andaman & Nicobar Islands",
    "d & n haveli": "Dadra & Nagar Haveli and Daman & Diu", "d&n haveli": "Dadra & Nagar Haveli and Daman & Diu",
    "dadra & nagar haveli": "Dadra & Nagar Haveli and Daman & Diu",
    "daman & diu": "Dadra & Nagar Haveli and Daman & Diu",
    "d&n haveli and daman & diu": "Dadra & Nagar Haveli and Daman & Diu",
    "dnh and dd": "Dadra & Nagar Haveli and Daman & Diu",
    "delhi ut": "Delhi", "delhi": "Delhi", "nct of delhi": "Delhi",
    "jammu & kashmir": "Jammu & Kashmir", "jammu and kashmir": "Jammu & Kashmir",
    "odisha": "Odisha", "orissa": "Odisha", "puducherry": "Puducherry", "pondicherry": "Puducherry",
}
# districts of the former J&K state that now belong to Ladakh UT
LADAKH_DISTRICTS = {"leh", "kargil", "leh-ladakh", "leh ladakh", "ladakh"}


def std_state(s):
    s0 = re.sub(r"\s+", " ", re.sub(r"[#*@$]", "", str(s))).strip()
    s0 = re.sub(r"^(state|ut)\s*:\s*", "", s0, flags=re.I).strip()
    k = s0.lower()
    if re.search(r"total\s*\(?\s*all\s*india", k):
        return "All India"
    if k in STATE_MAP:
        return STATE_MAP[k]
    return " ".join(w if w in ("&", "and") else w.capitalize() for w in k.split())


SPECIAL_UNIT = re.compile(r"rly|railway|grp|g\.r\.p|crime branch|\bcid\b|c\.i\.d|\beow\b|\bstf\b|\bcaw\b|airport|"
                          r"metro|cyber|commissionerate|\bsrp\b|special|\bcb\b|crime cell|police hq|ptc|\bbps\b",
                          re.I)

# --------------------------------------------------------- district file column maps
# (col index, crime_head label, crime_head_std, victim_sex)
FMT_2014 = [  # 2014-2015 (56 columns)
    (5, "Rape (Sec 376 IPC)", "rape_minor", "girl"),
    (6, "Assault on women with intent to outrage modesty (Sec 354 IPC)", "assault_modesty_minor", "girl"),
    (7, "Sexual harassment (Sec 354A IPC)", "sexual_harassment_minor", "girl"),
    (12, "Insult to the modesty of women (Sec 509 IPC)", "insult_modesty_minor", "girl"),
    (13, "Kidnapping & abduction of children (total)", "kidnap_children_total", "all"),
    (17, "Kidnapping & abduction of girls to compel marriage (Sec 366 IPC)", "kidnap_girls", "girl"),
    (22, "Procuration of minor girls (Sec 366A IPC)", "procuration_minor_girls", "girl"),
    (23, "Importation of girls from foreign country (Sec 366B IPC)", "importation_girls", "girl"),
    (24, "Buying of minors for prostitution (Sec 373 IPC)", "buying_minor_girls", "all"),
    (25, "Selling of minors for prostitution (Sec 372 IPC)", "selling_minor_girls", "all"),
    (26, "Prohibition of Child Marriage Act", "child_marriage", "all"),
    (19, "Foeticide (Sec 315-316 IPC)", "foeticide", "all"),
    (4, "Infanticide (Sec 315 IPC)", "infanticide", "all"),
    (44, "POCSO Act (total)", "pocso_total", "all"),
    ((45, 46), "POCSO Sec 4 + Sec 6 (summed)", "pocso_penetrative", "all"),
    ((47, 48), "POCSO Sec 8 + Sec 10 (summed)", "pocso_sexual_assault", "all"),
    (49, "POCSO Sec 14 & 15", "pocso_pornography", "all"),
    (50, "Other sections of POCSO Act", "pocso_other", "all"),
    (55, "Total crimes against children", "total_crimes_children", "all"),
]
FMT_2016 = [  # 2016 (27 columns)
    (5, "Rape (Sec 376 IPC)", "rape_minor", "girl"),
    (6, "Assault on women with intent to outrage modesty (Sec 354 IPC)", "assault_modesty_minor", "girl"),
    (7, "Insult to the modesty of women (Sec 509 IPC)", "insult_modesty_minor", "girl"),
    (8, "Kidnapping & abduction of children (total)", "kidnap_children_total", "all"),
    (12, "Procuration of minor girls (Sec 366A IPC)", "procuration_minor_girls", "girl"),
    (13, "Importation of girls from foreign country (Sec 366B IPC)", "importation_girls", "girl"),
    (14, "Buying of minors for prostitution (Sec 373 IPC)", "buying_minor_girls", "all"),
    (15, "Selling of minors for prostitution (Sec 372 IPC)", "selling_minor_girls", "all"),
    (16, "Prohibition of Child Marriage Act", "child_marriage", "all"),
    (9, "Foeticide (Sec 315-316 IPC)", "foeticide", "all"),
    (4, "Infanticide (Sec 315 IPC)", "infanticide", "all"),
    (21, "POCSO Act (total)", "pocso_total", "all"),
    (26, "Total crimes against children", "total_crimes_children", "all"),
]
FMT_2017 = [  # 2017-2023 (71 columns)
    (30, "Rape (Sec 376 IPC)", "rape_minor", "girl"),
    (31, "Attempt to commit rape (Sec 376/511 IPC)", "attempt_rape_minor", "girl"),
    (32, "Assault on women with intent to outrage modesty (Sec 354 IPC)", "assault_modesty_minor", "girl"),
    (33, "Insult to the modesty of women (Sec 509 IPC)", "insult_modesty_minor", "girl"),
    (3, "Murder with rape/POCSO", "murder_with_rape_pocso", "all"),
    (12, "Kidnapping & abduction of children (total)", "kidnap_children_total", "all"),
    (19, "Kidnapping & abduction of minor girls to compel marriage (Sec 366 IPC)", "kidnap_girls", "girl"),
    (20, "Procuration of minor girls (Sec 366A IPC)", "procuration_minor_girls", "girl"),
    (21, "Importation of girls from foreign country (Sec 366B IPC)", "importation_girls", "girl"),
    (24, "Selling of minors for prostitution (Sec 372 IPC) - total", "selling_minor_girls", "all"),
    (26, "Selling of minors for prostitution (Sec 372 IPC) - girls", "selling_minor_girls", "girl"),
    (27, "Buying of minors for prostitution (Sec 373 IPC) - total", "buying_minor_girls", "all"),
    (29, "Buying of minors for prostitution (Sec 373 IPC) - girls", "buying_minor_girls", "girl"),
    (63, "Prohibition of Child Marriage Act", "child_marriage", "all"),
    (8, "Foeticide (Sec 315-316 IPC)", "foeticide", "all"),
    (7, "Infanticide (Sec 315 IPC)", "infanticide", "all"),
    (36, "POCSO Act (total)", "pocso_total", "all"),
    ((38, 41, 44, 47, 50, 53), "POCSO Act - girl victims (sum of girl sub-heads)", "pocso_total", "girl"),
    (37, "POCSO Sec 4 & 6 - total", "pocso_penetrative", "all"),
    (38, "POCSO Sec 4 & 6 - girls", "pocso_penetrative", "girl"),
    (40, "POCSO Sec 8 & 10 - total", "pocso_sexual_assault", "all"),
    (41, "POCSO Sec 8 & 10 - girls", "pocso_sexual_assault", "girl"),
    (43, "POCSO Sec 12 - total", "pocso_harassment", "all"),
    (44, "POCSO Sec 12 - girls", "pocso_harassment", "girl"),
    (46, "POCSO Sec 14 & 15 - total", "pocso_pornography", "all"),
    (47, "POCSO Sec 14 & 15 - girls", "pocso_pornography", "girl"),
    (49, "POCSO r/w Sec 377 IPC - total", "pocso_unnatural_377", "all"),
    (50, "POCSO r/w Sec 377 IPC - girls", "pocso_unnatural_377", "girl"),
    (52, "POCSO Sec 17-22 - total", "pocso_other", "all"),
    (53, "POCSO Sec 17-22 - girls", "pocso_other", "girl"),
    (66, "Publishing/transmitting material depicting children in sexually explicit act (IT Act)",
     "cyber_child_sexual_material", "all"),
    (70, "Total crimes against children", "total_crimes_children", "all"),
]
FMT_2024 = [  # 2024 (76 columns, BNS + IPC)
    (2, "Rape of children (Sec 64-71 BNS / 376 IPC)", "rape_minor", "girl"),
    (3, "Attempt to commit rape (BNS/IPC)", "attempt_rape_minor", "girl"),
    (4, "Assault on children with intent to outrage her modesty (Sec 74 BNS / 354 IPC)", "assault_modesty_minor", "girl"),
    (5, "Sexual harassment of girls (Sec 75 BNS / 354A IPC)", "sexual_harassment_minor", "girl"),
    (9, "Insult to the modesty of women (Sec 79 BNS / 509 IPC)", "insult_modesty_minor", "girl"),
    (26, "Murder with rape/POCSO", "murder_with_rape_pocso", "all"),
    (31, "Kidnapping & abduction of children (total)", "kidnap_children_total", "all"),
    (10, "Kidnapping/abducting of girls to compel marriage (Sec 87 BNS / 366 IPC)", "kidnap_girls", "girl"),
    (15, "Procuration of children (Sec 96 BNS / 366A IPC) - total", "procuration_minor_girls", "all"),
    (16, "Procuration of children (Sec 96 BNS / 366A IPC) - girls", "procuration_minor_girls", "girl"),
    (40, "Importation of girls from foreign country", "importation_girls", "girl"),
    (19, "Selling of children for prostitution (Sec 98 BNS / 372 IPC) - total", "selling_minor_girls", "all"),
    (20, "Selling of children for prostitution (Sec 98 BNS / 372 IPC) - girls", "selling_minor_girls", "girl"),
    (22, "Buying of children for prostitution (Sec 99 BNS / 373 IPC) - total", "buying_minor_girls", "all"),
    (23, "Buying of children for prostitution (Sec 99 BNS / 373 IPC) - girls", "buying_minor_girls", "girl"),
    (68, "Prohibition of Child Marriage Act", "child_marriage", "all"),
    (11, "Foeticide (Sec 91 BNS / 315 IPC)", "foeticide", "all"),
    (12, "Infanticide (Sec 92 BNS / 316 IPC)", "infanticide", "all"),
    (44, "POCSO Act (total)", "pocso_total", "all"),
    ((46, 49, 52, 55, 58), "POCSO Act - girl victims (sum of girl sub-heads)", "pocso_total", "girl"),
    (45, "POCSO Sec 4 & 6 - total", "pocso_penetrative", "all"),
    (46, "POCSO Sec 4 & 6 - girls", "pocso_penetrative", "girl"),
    (48, "POCSO Sec 8 & 10 - total", "pocso_sexual_assault", "all"),
    (49, "POCSO Sec 8 & 10 - girls", "pocso_sexual_assault", "girl"),
    (51, "POCSO Sec 12 - total", "pocso_harassment", "all"),
    (52, "POCSO Sec 12 - girls", "pocso_harassment", "girl"),
    (54, "POCSO Sec 14 & 15 - total", "pocso_pornography", "all"),
    (55, "POCSO Sec 14 & 15 - girls", "pocso_pornography", "girl"),
    (57, "POCSO Sec 17-22 - total", "pocso_other", "all"),
    (58, "POCSO Sec 17-22 - girls", "pocso_other", "girl"),
    (71, "Publishing/transmitting material depicting children in sexually explicit act (IT Act)",
     "cyber_child_sexual_material", "all"),
    (75, "Total crimes against children", "total_crimes_children", "all"),
]


def fmt_for(year):
    if year <= 2015:
        return FMT_2014
    if year == 2016:
        return FMT_2016
    if year <= 2023:
        return FMT_2017
    return FMT_2024


def num(v):
    if pd.isna(v):
        return None
    s = str(v).replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def parse_district_file(path, year):
    d = pd.read_excel(path, sheet_name=0, header=None)
    fmt = fmt_for(year)
    rows, totals = [], []
    state = None
    for i in range(len(d)):
        c0, c1 = d.iat[i, 0], d.iat[i, 1]
        s0 = "" if pd.isna(c0) else str(c0).strip()
        s1 = "" if pd.isna(c1) else str(c1).strip()
        if re.match(r"^(state|ut)\s*:", s0, re.I):
            state = re.sub(r"^(state|ut)\s*:\s*", "", s0, flags=re.I).strip()
            continue
        if state is None:
            continue
        is_total = bool(re.match(r"^total", s1, re.I) or re.match(r"^total", s0, re.I))
        is_district = bool(re.match(r"^\d+(\.0)?$", s0)) and s1 != ""
        if not (is_total or is_district):
            continue
        for col, label, key, sex in fmt:
            cols = col if isinstance(col, tuple) else (col,)
            vals = [num(d.iat[i, c]) for c in cols]
            if all(v is None for v in vals):
                continue
            val = sum(v for v in vals if v is not None)
            rec = dict(year=year, state_raw=state, district=s1 if is_district else None,
                       crime_head=label, crime_head_std=key, count=val, victim_sex=sex,
                       derived_sum=len(cols) > 1)
            (totals if is_total else rows).append(rec)
    return pd.DataFrame(rows), pd.DataFrame(totals)


def district_year(path):
    m = re.search(r"(20\d\d)(?!.*20\d\d)", os.path.basename(path))
    return int(m.group(1))


def build_ncrb_district():
    dist, tot = [], []
    for f in sorted(glob.glob(os.path.join(ADD, "*istrict*.xls*"))):
        y = district_year(f)
        a, b = parse_district_file(f, y)
        a["source"] = b["source"] = "NCRB CII Additional Table: District-wise crime against children " + str(y)
        a["source_file"] = b["source_file"] = os.path.basename(f)
        dist.append(a)
        tot.append(b)
    return pd.concat(dist, ignore_index=True), pd.concat(tot, ignore_index=True)


def build_rajanand_district():
    """NCRB district-wise crimes against children 2001-2012 and 2013 (via Kaggle rajanand)."""
    heads = {
        "Rape": ("Rape (Sec 376 IPC)", "rape_minor", "girl"),
        "Kidnapping and Abduction": ("Kidnapping & abduction of children (total)", "kidnap_children_total", "all"),
        "Foeticide": ("Foeticide (Sec 315-316 IPC)", "foeticide", "all"),
        "Infanticid": ("Infanticide (Sec 315 IPC)", "infanticide", "all"),
        "Procuration of minor girls": ("Procuration of minor girls (Sec 366A IPC)", "procuration_minor_girls", "girl"),
        "Buying of girls for prostitution": ("Buying of girls for prostitution (Sec 373 IPC)", "buying_minor_girls", "girl"),
        "Selling of girls for prostitution": ("Selling of girls for prostitution (Sec 372 IPC)", "selling_minor_girls", "girl"),
        "Prohibition of child marriage act": ("Prohibition of Child Marriage Act", "child_marriage", "all"),
        "Total": ("Total crimes against children", "total_crimes_children", "all"),
    }
    out_d, out_t = [], []
    for fn in ["03_District_wise_crimes_committed_against_children_2001_2012.csv",
               "03_District_wise_crimes_committed_against_children_2013.csv"]:
        df = pd.read_csv(os.path.join(RAJ, fn))
        df["is_total"] = df["DISTRICT"].str.upper().str.contains("TOTAL")
        for col, (label, key, sex) in heads.items():
            if col not in df.columns:
                continue
            sub = df[["STATE/UT", "DISTRICT", "Year", col, "is_total"]].rename(columns={col: "count"})
            sub = sub.assign(crime_head=label, crime_head_std=key, victim_sex=sex, derived_sum=False)
            for is_t, target in [(False, out_d), (True, out_t)]:
                s = sub[sub.is_total == is_t].copy()
                s = s.rename(columns={"STATE/UT": "state_raw", "DISTRICT": "district", "Year": "year"})
                if is_t:
                    s["district"] = None
                s["source"] = "NCRB district-wise crimes against children (Kaggle rajanand/crime-in-india)"
                s["source_file"] = fn
                target.append(s.drop(columns="is_total"))
    return pd.concat(out_d, ignore_index=True), pd.concat(out_t, ignore_index=True)


# --------------------------------------------------------- all-India gender-wise victims
AI_MAP = [
    (r"^rape$|^rape of children", "rape_minor"),
    (r"^attempt to commit rape", "attempt_rape_minor"),
    (r"^assault on women with intent|^assault on children with intent", "assault_modesty_minor"),
    (r"^sexual harassment", "sexual_harassment_minor"),
    (r"^insult to the modesty", "insult_modesty_minor"),
    (r"minor girls to compel|girls to compel her for marriage", "kidnap_girls"),
    (r"^procuration of (minor )?girls", "procuration_minor_girls"),
    (r"^procuration of children", "procuration_children_total"),
    (r"^importation of girls", "importation_girls"),
    (r"^selling of (minors|children) for prostitution - girls", "selling_minor_girls"),
    (r"^selling of (minors|children) for prostitution$", "selling_minors_total"),
    (r"^buying of (minors|children) for prostitution - girls", "buying_minor_girls"),
    (r"^buying of (minors|children) for prostitution$", "buying_minors_total"),
    (r"^foeticide", "foeticide"),
    (r"^infanticide", "infanticide"),
    (r"^murder with rape", "murder_with_rape_pocso"),
    (r"^kidnapping and abduction of children$", "kidnap_children_total"),
    (r"^protection of children from sexual offences", "pocso_total"),
    (r"^section 4 & 6.* - girls", "pocso_penetrative_girls"),
    (r"^section 4 & 6", "pocso_penetrative"),
    (r"^section 8 & 10.* - girls", "pocso_sexual_assault_girls"),
    (r"^section 8 & 10", "pocso_sexual_assault"),
    (r"^section 12.* - girls", "pocso_harassment_girls"),
    (r"^section 12", "pocso_harassment"),
    (r"^section 14 & 15.* - girls", "pocso_pornography_girls"),
    (r"^section 14 & 15", "pocso_pornography"),
    (r"^pocso act\s+r/w section 377.* - girls", "pocso_unnatural_377_girls"),
    (r"^pocso act\s+r/w section 377", "pocso_unnatural_377"),
    (r"^sections 17 to 22.* - girls", "pocso_other_girls"),
    (r"^sections 17 to 22", "pocso_other"),
    (r"^prohibition of child marriage", "child_marriage"),
    (r"^publishing or transmitting of material depicting children", "cyber_child_sexual_material"),
    (r"^immoral traffic", "itpa_children"),
    (r"^human trafficking", "human_trafficking_children"),
    (r"^total crimes against children", "total_crimes_children"),
]


def ai_std(label):
    l = label.lower().strip()
    for pat, key in AI_MAP:
        if re.search(pat, l):
            return key
    return None


def parse_gender_victims(path):
    d = pd.read_excel(path, sheet_name=0, header=None)
    hdr_row = next(i for i in range(10) if d.iloc[i].astype(str).str.contains("Female").any())
    year_row = hdr_row - 1
    fem_cols = [j for j in range(d.shape[1]) if "Female" in str(d.iat[hdr_row, j])]
    out = []
    parent = None
    for i in range(hdr_row + 1, len(d)):
        sl, lab = d.iat[i, 0], d.iat[i, 1]
        if pd.isna(lab):
            continue
        sl = str(sl).strip()
        lab = re.sub(r"\s+", " ", str(lab)).strip()
        if re.fullmatch(r"(girls|boys|a\) girls|b\) boys)", lab, re.I):
            full = f"{parent} - {re.sub(r'^[ab]\) ', '', lab, flags=re.I).capitalize()}"
        else:
            full = lab
            parent = lab
        for fj in fem_cols:
            year = None
            for j in range(fj, -1, -1):
                v = d.iat[year_row, j]
                if pd.notna(v) and re.fullmatch(r"20\d\d(\.0)?", str(v).strip()):
                    year = int(float(v))
                    break
            vals = [num(d.iat[i, j]) for j in (fj - 2, fj - 1, fj, fj + 1, fj + 2)]
            if all(v is None for v in vals):
                continue
            out.append(dict(year=year, sl=sl, crime_head=full, crime_head_std=ai_std(full),
                            cases=vals[0], victims_boys=vals[1], victims_girls=vals[2],
                            victims_transgender=vals[3], victims_total=vals[4],
                            source_file=os.path.basename(path)))
    return pd.DataFrame(out)


def build_allindia_victims():
    frames = [parse_gender_victims(f) for f in sorted(glob.glob(os.path.join(ADD, "*Gender-wiseVictims*Children*.xlsx")))]
    df = pd.concat(frames, ignore_index=True)
    # 2014-2019 file and later single-year files do not overlap
    df = df.drop_duplicates(subset=["year", "sl", "crime_head"], keep="last")
    df["state_ut"] = "All India"
    df["source"] = "NCRB CII Additional Table: Crime head-wise gender-wise victims under crimes against children"
    return df


# --------------------------------------------------------- CII page text tables
NUM_TOKEN = re.compile(r"^-?\d+(\.\d+)?$")


def parse_state_lines(text, ncols):
    """Return list of (name, [numbers]) from a CII state-wise table page."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    out = []
    pending_prefix = None
    for k, l in enumerate(lines):
        toks = l.split()
        nums = []
        while toks and NUM_TOKEN.match(toks[-1].replace(",", "")):
            nums.insert(0, toks.pop().replace(",", ""))
        name_toks = toks
        if name_toks and NUM_TOKEN.match(name_toks[0]):
            name_toks = name_toks[1:]
        name = " ".join(name_toks)
        if len(nums) >= ncols + 1 and not name:
            # e.g. "31 9 0 0 ..." with name split onto surrounding lines (SL number is first numeric)
            nums = nums[1:]
        if len(nums) == ncols:
            if not name:
                prev = lines[k - 1] if k else ""
                nxt = lines[k + 1] if k + 1 < len(lines) else ""
                name = f"{prev} {nxt}".strip()
            out.append((name, [float(x) for x in nums]))
    return out


def clean_row_name(name):
    n = name.strip()
    if re.search(r"total\s*all\s*india", n, re.I):
        return "All India"
    if re.search(r"total\s*state", n, re.I):
        return "__TOTAL_STATES__"
    if re.search(r"total\s*u\.?t", n, re.I):
        return "__TOTAL_UTS__"
    return std_state(n)


def build_rape_age():
    rows = []
    rape_cols = ["cases_reported", "below_6", "6_12", "12_16", "16_18", "total_child_victims",
                 "18_30", "30_45", "45_60", "60_plus", "total_adult_victims", "total_victims"]
    for f in sorted(glob.glob(os.path.join(PAGES, "cii*_rape_age_p*.txt"))):
        y = int(re.search(r"cii(\d{4})", f).group(1))
        for name, nums in parse_state_lines(open(f, encoding="utf8").read(), 12):
            st = clean_row_name(name)
            for c, v in zip(rape_cols, nums):
                if c == "cases_reported":
                    continue
                rows.append(dict(year=y, state_ut=st, age_group=c, victims=v, victim_sex="girl/woman",
                                 table="CII Table 3A.3 victims of rape (Sec 376 IPC)",
                                 source_file=os.path.basename(f)))
            rows.append(dict(year=y, state_ut=st, age_group="cases_reported", victims=nums[0],
                             victim_sex="n/a", table="CII Table 3A.3 victims of rape (Sec 376 IPC)",
                             source_file=os.path.basename(f)))
    # POCSO age profile (Table 4A.9): two pages per year
    for y in range(2017, 2025):
        fs = sorted(glob.glob(os.path.join(PAGES, f"cii{y}_pocso_age_p*.txt")),
                    key=lambda p: int(re.search(r"_p(\d+)", p).group(1)))
        if len(fs) != 2:
            continue
        t1, t2 = (open(p, encoding="utf8").read() for p in fs)
        trans = "Trans" in t1
        per = 4 if trans else 3
        groups1 = ["below_6", "6_12", "12_16"]
        groups2 = ["16_18", "total_child_victims"]
        p1 = parse_state_lines(t1, per * 3)
        p2 = parse_state_lines(t2, per * 2)
        if len(p1) != len(p2):
            print("WARN pocso age pages differ in row count", y, len(p1), len(p2))
        for (name, nums), (name2, nums2) in zip(p1, p2):
            st = clean_row_name(name)
            if st != clean_row_name(name2):
                print("WARN pocso age row mismatch", y, name, name2)
                continue
            allnums = nums + nums2
            for gi, g in enumerate(groups1 + groups2):
                block = allnums[gi * per:(gi + 1) * per]
                boys, girls = block[0], block[1]
                total = block[-1]
                for sex, v in (("girl", girls), ("boy", boys), ("all", total)):
                    rows.append(dict(year=y, state_ut=st, age_group=g, victims=v, victim_sex=sex,
                                     table="CII Table 4A.9 age profile of child victims of POCSO Sec 4&6 (penetrative sexual assault)",
                                     source_file=os.path.basename(fs[0])))
    df = pd.DataFrame(rows)
    # pre-2020 tables list D&N Haveli and Daman & Diu separately: sum into the merged UT
    df = df.groupby(["year", "state_ut", "age_group", "victim_sex", "table"], as_index=False).agg(
        victims=("victims", "sum"), source_file=("source_file", "first"))
    # rajanand 2001-2010 (different age bins)
    r = pd.read_csv(os.path.join(RAJ, "20_Victims_of_rape.csv"), encoding="utf-8-sig")
    r = r[r.Subgroup == "Total Rape Victims"]
    bins = {"Victims_Upto_10_Yrs": "upto_10", "Victims_Between_10-14_Yrs": "10_14",
            "Victims_Between_14-18_Yrs": "14_18", "Victims_Between_18-30_Yrs": "18_30",
            "Victims_Between_30-50_Yrs": "30_50", "Victims_Above_50_Yrs": "50_plus",
            "Victims_of_Rape_Total": "total_victims", "Rape_Cases_Reported": "cases_reported"}
    rr = r.melt(id_vars=["Area_Name", "Year"], value_vars=list(bins), var_name="age_group", value_name="victims")
    rr["age_group"] = rr["age_group"].map(bins)
    rr = rr.rename(columns={"Area_Name": "state_ut", "Year": "year"})
    rr["state_ut"] = rr["state_ut"].map(std_state)
    rr["victim_sex"] = rr["age_group"].map(lambda a: "n/a" if a == "cases_reported" else "girl/woman")
    rr["table"] = "NCRB CII victims of rape by age group 2001-2010 (Kaggle rajanand 20_Victims_of_rape.csv)"
    rr["source_file"] = "20_Victims_of_rape.csv"
    # DNH and Daman & Diu were separate before 2020: sum to the merged UT
    rr = rr.groupby(["year", "state_ut", "age_group", "victim_sex", "table", "source_file"], as_index=False)["victims"].sum()
    rai = rr.groupby(["year", "age_group", "victim_sex", "table", "source_file"], as_index=False)["victims"].sum()
    rai["state_ut"] = "All India"  # sum of states/UTs (source file has no All-India row)
    rr = pd.concat([rr, rai], ignore_index=True)
    df = pd.concat([rr, df], ignore_index=True)
    return df


# --------------------------------------------------------------------------- main
def finalize_geo(df):
    df = df.copy()
    df["state_ut"] = df["state_raw"].map(std_state)
    if "district" in df.columns:
        m = df["district"].notna() & (df["state_ut"] == "Jammu & Kashmir") & \
            df["district"].astype(str).str.strip().str.lower().isin(LADAKH_DISTRICTS)
        df.loc[m, "state_ut"] = "Ladakh"
    return df


def main():
    nd, nt = build_ncrb_district()
    rd, rt = build_rajanand_district()
    dist = finalize_geo(pd.concat([rd, nd], ignore_index=True))
    dist["district"] = dist["district"].astype(str).str.strip()
    dist["special_police_unit"] = dist["district"].str.contains(SPECIAL_UNIT)
    dist["count"] = dist["count"].astype(float)

    # State rows (DNH + Daman & Diu summed into the merged UT; J&K before 2020 includes Leh & Kargil):
    #  * 2014-2024 (NCRB XLSX): sum of district rows. These reproduce NCRB's All-India crime-head table
    #    exactly, whereas at least one NCRB state "Total" row is wrong (Bihar 2017).
    #  * 2001-2013 (rajanand): NCRB state "TOTAL" rows, because some district rows are incomplete
    #    (e.g. Delhi 2007, Assam 2009); district sums only where no TOTAL row exists (Chhattisgarh 2001).
    keys = ["year", "state_ut", "crime_head", "crime_head_std", "victim_sex", "derived_sum", "source", "source_file"]
    tot_all = finalize_geo(pd.concat([rt, nt], ignore_index=True))
    tot_all = tot_all.drop_duplicates(subset=["year", "state_raw", "crime_head", "victim_sex"])  # Nagaland 2005 dup
    old = tot_all[tot_all.year <= 2013]
    state = old.groupby(keys, as_index=False, dropna=False)["count"].sum()
    state["state_value_basis"] = "ncrb_state_total_row"
    dsum = dist.copy()
    dsum.loc[dsum.state_ut == "Ladakh", "state_ut"] = dsum.loc[dsum.state_ut == "Ladakh"].apply(
        lambda r: "Jammu & Kashmir" if r["year"] < 2020 else "Ladakh", axis=1)
    dsum = dsum.groupby(keys, as_index=False, dropna=False)["count"].sum()
    have = set(zip(state.year, state.state_ut))
    fb = dsum[[(y, s) not in have for y, s in zip(dsum.year, dsum.state_ut)]].copy()
    fb["state_value_basis"] = "sum_of_district_rows"
    fb.loc[fb.year <= 2013, "state_value_basis"] = "sum_of_district_rows (no NCRB state TOTAL row in source)"
    state = pd.concat([state, fb], ignore_index=True)

    # Validation 1: district sums vs NCRB's own state "Total" rows (state names standardised,
    # J&K pre-2020 compared including Ladakh districts)
    tot = tot_all.groupby(["year", "state_ut", "crime_head_std", "victim_sex", "crime_head"], as_index=False)["count"].sum()
    chk = dist.copy()
    chk.loc[chk.state_ut == "Ladakh", "state_ut"] = chk.loc[chk.state_ut == "Ladakh"].apply(
        lambda r: "Jammu & Kashmir" if r["year"] < 2020 or r["source_file"].startswith("03_") else "Ladakh", axis=1)
    chk = chk.groupby(["year", "state_ut", "crime_head_std", "victim_sex", "crime_head"], as_index=False)["count"].sum()
    v1 = chk.merge(tot, on=["year", "state_ut", "crime_head_std", "victim_sex", "crime_head"], how="outer",
                   suffixes=("_district_sum", "_ncrb_state_total"))
    v1["diff"] = v1["count_district_sum"] - v1["count_ncrb_state_total"]

    # All-India = sum of states
    ai = state.groupby([k for k in keys if k != "state_ut"], as_index=False, dropna=False)["count"].sum()
    ai["state_value_basis"] = "sum_of_states"
    ai["state_ut"] = "All India"
    state = pd.concat([state, ai], ignore_index=True)
    state["measure"] = "cases_registered"
    dist["measure"] = "cases_registered"

    # All-India gender-wise victims table
    aiv = build_allindia_victims()

    # Validation 2: district-derived All-India cases vs NCRB All-India crime-head table (cases)
    comp_map = {  # state-file key/sex -> all-India table key
        ("rape_minor", "girl"): "rape_minor", ("kidnap_girls", "girl"): "kidnap_girls",
        ("procuration_minor_girls", "girl"): "procuration_minor_girls",
        ("child_marriage", "all"): "child_marriage", ("foeticide", "all"): "foeticide",
        ("infanticide", "all"): "infanticide", ("pocso_total", "all"): "pocso_total",
        ("pocso_penetrative", "all"): "pocso_penetrative", ("pocso_penetrative", "girl"): "pocso_penetrative_girls",
        ("pocso_sexual_assault", "girl"): "pocso_sexual_assault_girls",
        ("pocso_harassment", "girl"): "pocso_harassment_girls",
        ("pocso_pornography", "girl"): "pocso_pornography_girls",
        ("selling_minor_girls", "girl"): "selling_minor_girls", ("buying_minor_girls", "girl"): "buying_minor_girls",
        ("total_crimes_children", "all"): "total_crimes_children",
    }
    v2 = []
    for (k, sex), ak in comp_map.items():
        a = ai[(ai.crime_head_std == k) & (ai.victim_sex == sex) & (ai.year >= 2014)]
        b = aiv[aiv.crime_head_std == ak]
        for _, r in a.iterrows():
            bb = b[b.year == r["year"]]
            if len(bb):
                v2.append(dict(check="district-derived All India cases vs NCRB All-India crime-head table",
                               year=r["year"], crime_head_std=k, victim_sex=sex, derived=r["count"],
                               published=bb["cases"].iloc[0]))
    v2 = pd.DataFrame(v2)
    v2["diff"] = v2["derived"] - v2["published"]
    v2["pct_diff"] = (v2["diff"] / v2["published"].where(v2["published"] != 0) * 100).round(2)

    # Rape / POCSO victims by age
    age = build_rape_age()
    # Validation 3: sum of states == TOTAL ALL INDIA row in each CII page table
    v3 = []
    for (y, g, sex, tb), grp in age.groupby(["year", "age_group", "victim_sex", "table"]):
        states = grp[~grp.state_ut.isin(["All India", "__TOTAL_STATES__", "__TOTAL_UTS__"])]["victims"].sum()
        pub = grp[grp.state_ut == "All India"]["victims"]
        if len(pub):
            v3.append(dict(check="sum of states vs published All India (age tables)", year=y,
                           crime_head_std=f"{tb} | {g}", victim_sex=sex, derived=states, published=pub.iloc[0]))
    v3 = pd.DataFrame(v3)
    v3["diff"] = v3["derived"] - v3["published"]
    age = age[~age.state_ut.isin(["__TOTAL_STATES__", "__TOTAL_UTS__"])]
    # POCSO age-table girl victims vs All-India gender-wise table (Sec 4&6 girl victims)
    v4 = []
    for y in sorted(age.year.unique()):
        a = age[(age.year == y) & (age.state_ut == "All India") & (age.age_group == "total_child_victims") &
                (age.victim_sex == "girl") & age.table.str.contains("4A.9")]
        for key in ["pocso_penetrative", "pocso_total"]:
            b = aiv[(aiv.year == y) & (aiv.crime_head_std == key)]
            if len(a) and len(b):
                v4.append(dict(check=f"CII 4A.9 All-India girl victims vs gender-wise table {key} girl victims",
                               year=y, crime_head_std=key, victim_sex="girl", derived=a["victims"].iloc[0],
                               published=b["victims_girls"].iloc[0]))
    v4 = pd.DataFrame(v4)
    if len(v4):
        v4["diff"] = v4["derived"] - v4["published"]

    # ---------------- write
    out = HERE
    cols = ["year", "state_ut", "crime_head", "crime_head_std", "count", "victim_sex", "measure", "state_value_basis",
            "derived_sum", "source", "source_file"]
    state = state[cols].sort_values(["crime_head_std", "victim_sex", "year", "state_ut"])
    state.to_csv(os.path.join(out, "minor_girls_state.csv"), index=False)
    dcols = ["year", "state_ut", "district", "crime_head", "crime_head_std", "count", "victim_sex", "measure",
             "derived_sum", "special_police_unit", "source", "source_file"]
    dist[dcols].sort_values(["year", "state_ut", "district", "crime_head_std", "victim_sex"]).to_csv(
        os.path.join(out, "minor_girls_district.csv"), index=False)
    aiv[["year", "state_ut", "sl", "crime_head", "crime_head_std", "cases", "victims_girls", "victims_boys",
         "victims_transgender", "victims_total", "source", "source_file"]].to_csv(
        os.path.join(out, "minor_girls_allindia_victims.csv"), index=False)
    age[["year", "state_ut", "age_group", "victims", "victim_sex", "table", "source_file"]].sort_values(
        ["table", "year", "state_ut", "age_group"]).to_csv(os.path.join(out, "minor_girls_rape_victims_age.csv"), index=False)
    v1s = v1.assign(check="district sum vs NCRB state 'Total' row").rename(
        columns={"count_district_sum": "derived", "count_ncrb_state_total": "published"})
    val = pd.concat([v2, v3, v4, v1s[v1s["diff"].fillna(1) != 0]], ignore_index=True)
    val.to_csv(os.path.join(out, "minor_girls_validation.csv"), index=False)

    print("district rows", len(dist), "state rows", len(state), "allindia victims", len(aiv), "age rows", len(age))
    print("v1 mismatches (district sum vs state total):", int((v1["diff"].fillna(1) != 0).sum()), "of", len(v1))
    print(v2.to_string())
    print(v3[v3["diff"] != 0].to_string())
    print(v4.to_string())


if __name__ == "__main__":
    main()
