"""Build aggregate ADR CSVs (no individual names) for the dashboard."""
import re
from collections import Counter
from pathlib import Path
import pandas as pd
import parse_details as p

OUT = str(Path(__file__).resolve().parents[2] / "data" / "interim") + "/"
DNH = "Dadra & Nagar Haveli and Daman & Diu"

REPORTS = {
    2017: dict(date="2017-08-30", src="adr_2017_crimes_against_women.pdf", kind="report_pdf"),
    2018: dict(date="2018-04-19", src="adr_2018_crimes_against_women.pdf", kind="report_pdf"),
    2023: dict(date="2023-08-10", src="ADR news repost (ETV Bharat / Siasat / IANS); report PDF not located", kind="press_headline_only"),
    2024: dict(date="2024-08-21", src="adr_2024_crimes_against_women.pdf", kind="report_pdf"),
}

# ---------------- published tables (transcribed from PDFs) ----------------
# 2024 state table: state -> (MLAs, MPs)   [PDF p.9]
st24 = {"West Bengal": (21, 4), "Andhra Pradesh": (21, 0), "Odisha": (16, 1), "Delhi": (13, 0),
        "Maharashtra": (12, 1), "Bihar": (8, 1), "Karnataka": (7, 0), "Rajasthan": (6, 0),
        "Madhya Pradesh": (5, 0), "Kerala": (3, 2), "Telangana": (2, 3), "Gujarat": (4, 0),
        "Tamil Nadu": (3, 1), "Uttar Pradesh": (3, 1), "Jharkhand": (2, 1), "Punjab": (3, 0),
        "Assam": (2, 0), "Goa": (2, 0), "Himachal Pradesh": (1, 0), "Manipur": (1, 0), DNH: (0, 1)}
# 2024 rape by state: (MLAs, MPs)  [p.10]
rape24 = {"Madhya Pradesh": (2, 0), "West Bengal": (1, 1), "Andhra Pradesh": (1, 0), "Assam": (1, 0),
          "Delhi": (1, 0), "Goa": (1, 0), "Gujarat": (1, 0), "Jharkhand": (1, 0), "Karnataka": (1, 0),
          "Kerala": (1, 0), "Maharashtra": (1, 0), "Odisha": (1, 0), "Tamil Nadu": (1, 0), "Telangana": (0, 1)}
# 2024 party table: party -> (MLAs, MPs)  [p.7]
pt24 = {"BJP": (44, 10), "INC": (22, 1), "TDP": (17, 0), "AAP": (13, 0), "AITC": (10, 0),
        "Independent": (5, 1), "RJD": (4, 1), "SHS": (2, 1), "BJD": (2, 0), "DMK": (2, 0),
        "Janasena Party": (2, 0), "SP": (1, 1), "YSRCP": (2, 0), "AIUDF": (1, 0),
        "Bharat Adivasi Party": (1, 0), "CPI(M)": (1, 0), "CPI(ML)(L)": (1, 0),
        "Hindustani Awam Morcha (Secular)": (1, 0), "JD(U)": (1, 0), "NCP": (1, 0),
        "Prahar Janshakti Party": (1, 0), "Rashtriya Samaj Paksha": (1, 0),
        "Viduthalai Chiruthaigal Katchi": (0, 1)}
# 2024 rape by party (MLAs, MPs) [p.11-12]
prape24 = {"BJP": (3, 2), "INC": (5, 0), "AAP": (1, 0), "AITC": (1, 0), "AIUDF": (1, 0),
           "Bharat Adivasi Party": (1, 0), "BJD": (1, 0), "TDP": (1, 0)}
# 2018 state totals [p.10]; party totals [p.6-7]
st18 = {"Maharashtra": 12, "West Bengal": 11, "Andhra Pradesh": 5, "Odisha": 5, "Jharkhand": 3,
        "Uttarakhand": 3, "Bihar": 2, "Tamil Nadu": 2, "Gujarat": 1, "Karnataka": 1,
        "Madhya Pradesh": 1, "Uttar Pradesh": 1, "Kerala": 1}
pt18 = {"BJP": 12, "SHS": 7, "AITC": 6, "INC": 4, "TDP": 5, "BJD": 4, "Independent": 3,
        "JMM": 2, "RJD": 2, "DMK": 2, "CPI(M)": 1}
# 2017 state totals [p.9-10]; party totals [p.7]
st17 = {"Maharashtra": 12, "West Bengal": 11, "Odisha": 6, "Andhra Pradesh": 5, "Jharkhand": 3,
        "Uttarakhand": 3, "Gujarat": 2, "Madhya Pradesh": 2, "Bihar": 2, "Tamil Nadu": 2,
        "Karnataka": 1, "Uttar Pradesh": 1, "Kerala": 1}
pt17 = {"BJP": 14, "SHS": 7, "AITC": 6, "INC": 5, "TDP": 5, "BJD": 4, "Independent": 3,
        "JMM": 2, "RJD": 2, "DMK": 2, "CPI(M)": 1}
# rape (all MLAs) - aggregated from the report's named lists (2017 p.3-4; 2018 p.3-4, 13)
rape_state17 = {"Andhra Pradesh": 1, "Odisha": 1, "Gujarat": 1, "Bihar": 1}
rape_party17 = {"TDP": 1, "INC": 1, "BJP": 1, "RJD": 1}
rape_state18 = {"Andhra Pradesh": 1, "Gujarat": 1, "Bihar": 1}
rape_party18 = {"TDP": 1, "BJP": 1, "RJD": 1}
# 2017 published charge table (total charges per section) [p.5]
charges17_pub = {"354": 36, "366": 2, "376": 4, "498A": 1, "373": 1, "509": 16}

PARTY_FULL = {"BJP": "Bharatiya Janata Party", "INC": "Indian National Congress", "TDP": "Telugu Desam Party",
              "AAP": "Aam Aadmi Party", "AITC": "All India Trinamool Congress", "RJD": "Rashtriya Janata Dal",
              "SHS": "Shiv Sena", "BJD": "Biju Janata Dal", "DMK": "Dravida Munnetra Kazhagam",
              "SP": "Samajwadi Party", "YSRCP": "Yuvajana Sramika Rythu Congress Party",
              "AIUDF": "All India United Democratic Front", "CPI(M)": "Communist Party of India (Marxist)",
              "CPI(ML)(L)": "Communist Party of India (Marxist-Leninist) Liberation", "JD(U)": "Janata Dal (United)",
              "NCP": "Nationalist Congress Party", "JMM": "Jharkhand Mukti Morcha", "Independent": "Independent"}

# ---------------- derived per-legislator info (anonymous) ----------------
STATES = ["Andhra Pradesh", "Assam", "Bihar", "Goa", "Gujarat", "Himachal Pradesh", "Jharkhand", "Karnataka",
          "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Odisha", "Punjab", "Rajasthan", "Tamil Nadu",
          "Telangana", "Uttar Pradesh", "Uttarakhand", "West Bengal", "Delhi", "Dadra"]
ST_ALT = "|".join(STATES)


def recs_with_state(y):
    txt = open(p.S + f"t{y}.txt", encoding="utf-8").read()
    i = txt.index(p.CFG[y]["start"]); m = re.search(p.CFG[y]["end"], txt[i:]); body = txt[i:i + m.start()]
    st = [mm.start() for mm in p.NAME_RE.finditer(body)] + [len(body)]
    recs = p.records(y)
    for k, (a, b) in enumerate(zip(st, st[1:])):
        j = re.sub(r"\s+", " ", body[a:b])
        mm = (re.search(r"State(?:/District)?\s*:\s*(" + ST_ALT + ")", j, re.I)
              or re.search(r"\([^()]*?(" + ST_ALT + r")[^()]*\d{4}\)", j, re.I)
              or re.search(r"\b(" + ST_ALT + r")\b", j[:600], re.I))
        s = mm.group(1).title() if mm else None
        recs[k]["state"] = DNH if s == "Dadra" else s
        recs[k].pop("party", None)
    return recs


R = {y: recs_with_state(y) for y in (2017, 2018, 2024)}
for y in R:
    assert len(R[y]) == {2017: 51, 2018: 48, 2024: 151}[y]

rows_state = []
def add_state(y, s, house, n, rape, method):
    rows_state.append(dict(report_year=y, report_date=REPORTS[y]["date"], state_ut=s, house=house,
                           legislators_with_cases=n, rape_cases_legislators=rape, method=method))

# 2024: published MLA/MP split; MP -> LS/RS from details (only RS member is from Maharashtra)
rs24 = Counter(r["state"] for r in R[2024] if r["house"] == "Rajya Sabha")
ls24 = Counter(r["state"] for r in R[2024] if r["house"] == "Lok Sabha")
for s, (mla, mp) in st24.items():
    rm, rp = rape24.get(s, (0, 0))
    if mla: add_state(2024, s, "State Assembly", mla, rm, "published")
    if mp:
        assert ls24[s] + rs24[s] == mp, (s, ls24[s], rs24[s], mp)
        rape_rs = sum(1 for r in R[2024] if r["house"] == "Rajya Sabha" and r["state"] == s and any(x.startswith("376") for x in r["women_secs"]))
        if ls24[s]: add_state(2024, s, "Lok Sabha", ls24[s], rp - rape_rs, "published MP count; LS/RS split derived from per-member details")
        if rs24[s]: add_state(2024, s, "Rajya Sabha", rs24[s], rape_rs, "published MP count; LS/RS split derived from per-member details")
# 2017/2018: published state totals; house split derived from details (verified to sum to totals)
for y, tot, rst in ((2017, st17, rape_state17), (2018, st18, rape_state18)):
    c = Counter((r["state"], r["house"]) for r in R[y])
    for s, n in tot.items():
        parts = {h: c[(s, h)] for h in ("State Assembly", "Lok Sabha", "Rajya Sabha") if c[(s, h)]}
        assert sum(parts.values()) == n, (y, s, parts, n)
        for h, k in parts.items():
            add_state(y, s, h, k, rst.get(s, 0) if h == "State Assembly" else 0,
                      "published state total; house split derived from per-member details")
# 2023: only top-3 states reported in press coverage; no house split
for s, n in {"West Bengal": 26, "Maharashtra": 14, "Odisha": 14}.items():
    add_state(2023, s, "All houses (split not published)", n, None, "press_headline_only (top 3 states only)")
dfs = pd.DataFrame(rows_state)

# ---------------- party ----------------
rows_party = []
def add_party(y, party, house, n, rape, method):
    rows_party.append(dict(report_year=y, report_date=REPORTS[y]["date"], party=party,
                           party_full=PARTY_FULL.get(party, party), house=house,
                           legislators_with_cases=n, rape_cases_legislators=rape, method=method))
for pa, (mla, mp) in pt24.items():
    rm, rp = prape24.get(pa, (0, 0))
    if mla: add_party(2024, pa, "State Assembly", mla, rm, "published")
    if mp: add_party(2024, pa, "Parliament (LS+RS)", mp, rp, "published")
for y, tot, rp in ((2017, pt17, rape_party17), (2018, pt18, rape_party18)):
    for pa, n in tot.items():
        add_party(y, pa, "All houses (split not published)", n, rp.get(pa, 0), "published total; rape count aggregated from report's list")
for pa, (n, r) in {"BJP": (44, 7), "INC": (25, 6), "AAP": (13, None)}.items():
    add_party(2023, pa, "All houses (split not published)", n, r, "press_headline_only (top parties only)")
dfp = pd.DataFrame(rows_party)

# ---------------- house totals ----------------
rows_house = []
def add_house(y, h, n, rape, analysed, method):
    rows_house.append(dict(report_year=y, report_date=REPORTS[y]["date"], house=h, legislators_with_cases=n,
                           rape_cases_legislators=rape, legislators_analysed=analysed, method=method))
for y, mp_an, mla_an in ((2017, 774, 4078), (2018, 768, 4077), (2024, 755, 3938)):
    c = Counter(r["house"] for r in R[y])
    cr = Counter(r["house"] for r in R[y] if any(x.startswith("376") for x in r["women_secs"]))
    add_house(y, "State Assembly", c["State Assembly"], cr["State Assembly"], mla_an, "published")
    add_house(y, "Lok Sabha", c["Lok Sabha"], cr["Lok Sabha"], None, "derived from per-member details (MP total published)")
    add_house(y, "Rajya Sabha", c["Rajya Sabha"], cr["Rajya Sabha"], None, "derived from per-member details (MP total published)")
    add_house(y, "Parliament (LS+RS)", c["Lok Sabha"] + c["Rajya Sabha"], cr["Lok Sabha"] + cr["Rajya Sabha"], mp_an, "published")
add_house(2023, "State Assembly", 113, 14, 4001, "press_headline_only")
add_house(2023, "Parliament (LS+RS)", 21, 4, 762, "press_headline_only")
dfh = pd.DataFrame(rows_house)
# sanity vs published headline totals
exp = {2017: (48, 3, 4), 2018: (45, 3, 3), 2024: (135, 16, 16)}
for y, (mla, mp, rape) in exp.items():
    d = dfh[dfh.report_year == y].set_index("house")
    assert d.loc["State Assembly", "legislators_with_cases"] == mla
    assert d.loc["Parliament (LS+RS)", "legislators_with_cases"] == mp
    assert d.loc["State Assembly", "rape_cases_legislators"] + d.loc["Parliament (LS+RS)", "rape_cases_legislators"] == rape, y

# ---------------- charges ----------------
LABEL = {"376": ("Rape", "Rape"), "376(2)(n)": ("Repeated rape on the same woman", "Rape"),
         "354": ("Assault/criminal force to outrage modesty", "Assault / outraging modesty"),
         "354A": ("Sexual harassment", "Sexual harassment"),
         "354B": ("Assault with intent to disrobe", "Assault / outraging modesty"),
         "354C": ("Voyeurism", "Voyeurism / stalking"), "354D": ("Stalking", "Voyeurism / stalking"),
         "509": ("Word, gesture or act to insult modesty of a woman", "Insult to modesty"),
         "498A": ("Cruelty by husband or his relatives", "Cruelty / marital offences"),
         "498": ("Enticing/detaining a married woman", "Cruelty / marital offences"),
         "493": ("Cohabitation by deceitfully inducing belief of lawful marriage", "Cruelty / marital offences"),
         "366": ("Kidnapping/abducting woman to compel marriage", "Kidnapping / abduction of women"),
         "372": ("Selling minor for prostitution", "Trafficking of minors"),
         "373": ("Buying minor for prostitution", "Trafficking of minors"),
         "313": ("Causing miscarriage without woman's consent", "Miscarriage without consent")}
rows_ch = []
for y in (2017, 2018, 2024):
    c = Counter((r["house"], s) for r in R[y] for s in r["women_secs"])
    for (h, s), n in sorted(c.items()):
        rows_ch.append(dict(report_year=y, report_date=REPORTS[y]["date"], house=h, ipc_section=s,
                            charge_label=LABEL[s][0], charge_group=LABEL[s][1], legislators_with_charge=n,
                            total_charges_published=None,
                            method="derived: legislators whose declared charge summary lists this section"))
    # all-rape union row
    rp = Counter(r["house"] for r in R[y] if any(x.startswith("376") for x in r["women_secs"]))
for s, n in charges17_pub.items():
    rows_ch.append(dict(report_year=2017, report_date=REPORTS[2017]["date"], house="All houses", ipc_section=s,
                        charge_label=LABEL[s][0], charge_group=LABEL[s][1], legislators_with_charge=None,
                        total_charges_published=n, method="published (Table: Type and Number of charges)"))
dfc = pd.DataFrame(rows_ch)

for df in (dfs, dfp, dfh, dfc):
    for col in ("rape_cases_legislators", "legislators_analysed", "legislators_with_charge", "total_charges_published"):
        if col in df: df[col] = df[col].astype("Int64")
dfs.sort_values(["report_year", "state_ut", "house"]).to_csv(OUT + "adr_legislators_by_state.csv", index=False)
dfp.sort_values(["report_year", "legislators_with_cases"], ascending=[True, False]).to_csv(OUT + "adr_legislators_by_party.csv", index=False)
dfh.to_csv(OUT + "adr_legislators_by_house.csv", index=False)
dfc.to_csv(OUT + "adr_legislators_by_charge.csv", index=False)
for n, df in (("state", dfs), ("party", dfp), ("house", dfh), ("charge", dfc)):
    print(n, len(df)); print(df.groupby("report_year")[[c for c in df.columns if c in ("legislators_with_cases", "legislators_with_charge")]].sum())
