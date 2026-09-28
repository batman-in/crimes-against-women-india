"""Build the dashboard data files in web/public/data/ from the raw sources.

Inputs
  data/raw/ayuxsh_crime-against-women-2001-2025/   NCRB state-wise, 2001-2023 (heads to 2014)
  data/raw/rajanand_crime-in-india/                 NCRB district-wise 2001-2014, rape offenders 2001-2010
  data/interim/female_pop_*.csv                     Census 2011 + MoHFW projections (build_population.py)
  data/interim/ncrb_*.csv                           NCRB 2015+ by crime head / relation (optional)
  data/interim/adr_*.csv                            ADR legislators with declared cases (optional)
  data/geo/*.topo.json, district_official_state.csv boundaries

Run from the project root:  python scripts/build_data.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from district_match import DROP, match, norm  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
GEO = ROOT / "data" / "geo"
OUT = ROOT / "web" / "public" / "data"

# key -> (label shown in the filter, legal description)
CATS = {
    "total": ("All crimes against women", "All IPC and special-law heads"),
    "rape": ("Rape", "IPC 376"),
    "attempt_rape": ("Attempt to rape", "IPC 376/511"),
    "custodial_rape": ("Custodial rape", "Rape by police or public servants in custody, IPC 376(2)"),
    "assault": ("Molestation", "Assault to outrage modesty, IPC 354"),
    "sexual_harassment": ("Sexual harassment", "IPC 354A"),
    "disrobe": ("Assault to disrobe", "IPC 354B"),
    "voyeurism": ("Voyeurism", "IPC 354C"),
    "stalking": ("Stalking", "IPC 354D"),
    "insult": ("Eve teasing", "Insult to the modesty of women, IPC 509"),
    "cruelty": ("Domestic violence", "Cruelty by husband or relatives, IPC 498A"),
    "dv_act": ("Domestic Violence Act cases", "Protection of Women from DV Act, 2005"),
    "dowry": ("Dowry deaths", "IPC 304B"),
    "dowry_act": ("Dowry Prohibition Act", "Dowry Prohibition Act, 1961"),
    "kidnap": ("Kidnapping & abduction", "IPC 363-369"),
    "abetment_suicide": ("Abetment of suicide", "IPC 306"),
    "acid_attack": ("Acid attack", "IPC 326A"),
    "itpa": ("Trafficking", "Immoral Traffic (Prevention) Act"),
    "import": ("Importation of girls", "IPC 366B"),
    "indecent_rep": ("Indecent representation", "Indecent Representation of Women Act, 1986"),
    "pocso_girls": ("POCSO, all (girl victims)", "POCSO Act, 2012"),
    "murder_rape": ("Murder with rape / gang rape", "IPC 302 with 376 / BNS 103"),
    "cyber": ("Cyber crimes against women", "IT Act, women-centric offences"),
    "trafficking": ("Human trafficking", "IPC 370/370A"),
    "attempt_acid_attack": ("Attempted acid attack", "IPC 326B"),
    "rape_minor": ("Rape of girls under 18 (IPC)", "IPC 376 / BNS 64-71, victims below 18. From 2017 most child rape is recorded under POCSO Sec 4 & 6 instead"),
    "attempt_rape_minor": ("Attempt to rape, girls under 18", "IPC 376/511, victims below 18"),
    "assault_minor": ("Molestation of girls under 18", "IPC 354 / BNS 74, victims below 18"),
    "insult_minor": ("Eve teasing of girls under 18", "IPC 509 / BNS 79, victims below 18"),
    "kidnap_marriage_girls": ("Kidnapping girls to force marriage", "IPC 366 / BNS 87, victims below 18"),
    "procuration_minor_girls": ("Procuration of minor girls", "IPC 366A"),
    "selling_minor_girls": ("Selling girls for prostitution", "IPC 372 / BNS 98"),
    "buying_minor_girls": ("Buying girls for prostitution", "IPC 373 / BNS 99"),
    "pocso_penetrative": ("POCSO: penetrative sexual assault", "POCSO Sec 4 & 6"),
    "pocso_sexual_assault": ("POCSO: sexual assault", "POCSO Sec 8 & 10"),
    "pocso_harassment": ("POCSO: sexual harassment", "POCSO Sec 12"),
    "pocso_pornography": ("POCSO: child pornography", "POCSO Sec 14 & 15"),
    "kidnap_girls": ("Kidnapping & abduction of girls", "IPC 363-369 / BNS, victims below 18"),
    "child_marriage": ("Child marriage (all children)", "Prohibition of Child Marriage Act, 2006"),
    "foeticide": ("Foeticide (all)", "IPC 315/316"),
    "infanticide": ("Infanticide (all)", "IPC 315"),
}
CAT_GROUPS = {
    "Overview": ["total"],
    "Sexual violence": ["rape", "murder_rape", "attempt_rape", "custodial_rape", "assault", "sexual_harassment",
                        "disrobe", "voyeurism", "stalking", "insult"],
    "Domestic violence & dowry": ["cruelty", "dv_act", "dowry", "dowry_act", "abetment_suicide"],
    "Kidnapping & trafficking": ["kidnap", "trafficking", "itpa", "import"],
    "Minor girls (under 18)": ["pocso_girls", "pocso_penetrative", "pocso_sexual_assault", "pocso_harassment",
                               "pocso_pornography", "rape_minor", "attempt_rape_minor", "assault_minor", "insult_minor",
                               "kidnap_girls", "kidnap_marriage_girls", "procuration_minor_girls",
                               "selling_minor_girls", "buying_minor_girls", "child_marriage", "foeticide",
                               "infanticide"],
    "Other": ["acid_attack", "attempt_acid_attack", "cyber", "indecent_rep"],
}
DISTRICT_KEYS = ["rape", "kidnap", "dowry", "assault", "insult", "cruelty", "import"]

STD_TO_KEY = {
    "Total Crimes against Women": "total", "Rape": "rape", "Attempt to Commit Rape": "attempt_rape",
    "Kidnapping & Abduction of Women": "kidnap", "Dowry Deaths": "dowry",
    "Assault on Women with Intent to Outrage Modesty": "assault", "Insult to Modesty of Women": "insult",
    "Cruelty by Husband or Relatives": "cruelty", "Importation of Girls from Foreign Country": "import",
    "Abetment of Suicide of Women": "abetment_suicide", "Dowry Prohibition Act": "dowry_act",
    "Protection of Women from Domestic Violence Act": "dv_act", "Immoral Traffic (Prevention) Act": "itpa",
    "Indecent Representation of Women (Prevention) Act": "indecent_rep",
}
# 2014 detailed sub-heads, matched on the raw "n.n - " prefix
DETAIL_PREFIX = {"1.1 ": "custodial_rape", "5.1 ": "sexual_harassment", "5.2 ": "disrobe",
                 "5.3 ": "voyeurism", "5.4 ": "stalking"}

# Crime-data state names -> names used by states.topo.json
STATE_TO_GEO = {
    "Andaman & Nicobar Islands": ["Andaman & Nicobar"],
    "Dadra & Nagar Haveli (pre-2020, separate UT)": ["Dadra & Nagar Haveli"],
    "Daman & Diu (pre-2020, separate UT)": ["Daman & Diu"],
    "Dadra & Nagar Haveli and Daman & Diu": ["Dadra & Nagar Haveli", "Daman & Diu"],
}
# Map state -> reporting parent before a split, with the last year the parent reported for it
SPLITS = {"Telangana": ("Andhra Pradesh", 2013, "Andhra Pradesh (undivided)"),
          "Ladakh": ("Jammu & Kashmir", 2019, "Jammu & Kashmir (incl. Ladakh)")}
GEO_TO_POP = {"Andaman & Nicobar": "Andaman & Nicobar Islands"}


# ----------------------------------------------------------------- population
class Population:
    def __init__(self):
        df = pd.read_csv(INTERIM / "female_pop_state.csv")
        self.p = {(r.state_ut, int(r.year)): int(r.female_pop) for r in df.itertuples()}

    def get(self, name, year):
        name = GEO_TO_POP.get(name, name)
        y = year if year >= 2012 else 2011  # census for 2001-2011, projections after
        if name == "Andhra Pradesh (undivided)":
            return self._sum(["Andhra Pradesh", "Telangana"], y)
        if name == "Jammu & Kashmir (incl. Ladakh)":
            return self._sum(["Jammu & Kashmir", "Ladakh"], y)
        if name == "Dadra & Nagar Haveli and Daman & Diu":
            return self._sum(["Dadra & Nagar Haveli", "Daman & Diu"], y) or self.p.get((name, y))
        return self.p.get((name, y))

    def _sum(self, names, y):
        vals = [self.p.get((n, y)) for n in names]
        return sum(vals) if all(vals) else None


# ---------------------------------------------------------------- state level
def record_from(g):
    rec = {}
    main = g[~g.Is_Detailed_Subcategory]
    for std, v in main.groupby("Crime_Head_Standardized")["Count"].sum(min_count=1).items():
        if std in STD_TO_KEY and pd.notna(v):
            rec[STD_TO_KEY[std]] = int(v)
    for raw, v in zip(g.Crime_Head_Raw, g.Count):
        for pre, key in DETAIL_PREFIX.items():
            if raw.startswith(pre) and pd.notna(v):
                rec[key] = int(v)
    return rec


def build_states(pop):
    df = pd.read_csv(RAW / "ayuxsh_crime-against-women-2001-2025" / "combined_crime_against_women_full.csv")
    df = df[df.Year <= 2023]

    states = {}
    for (state, year), g in df[df.Row_Type == "State/UT"].groupby(["State_UT", "Year"]):
        rec = record_from(g)
        if not rec:
            continue
        geos = STATE_TO_GEO.get(state, [state])
        if len(geos) > 1:
            rec["via"] = state
        rec["pop"] = pop.get(state if len(geos) > 1 else geos[0], int(year))
        for gname in geos:
            states.setdefault(gname, {})[str(year)] = dict(rec)

    for child, (parent, last, label) in SPLITS.items():
        for y, rec in states.get(parent, {}).items():
            if int(y) <= last and y not in states.get(child, {}):
                shared = {**rec, "via": label, "pop": pop.get(label, int(y))}
                states.setdefault(child, {})[y] = shared
                states[parent][y] = dict(shared)

    # National: all-India rows, minus the state/UT subtotals that exist from 2013 on.
    # (2001-2012 spread the all-India row over inconsistent raw labels.)
    subtotal = df.State_UT_Raw.str.contains(r"Total \((?:State|States|UTs)\)", regex=True)
    nat = df[(df.State_UT == "All India (Total)") & ~subtotal]
    national = {}
    for year, g in nat.groupby("Year"):
        rec = record_from(g)
        if rec:
            rec["pop"] = pop.get("India", int(year))
            national[str(year)] = rec
    return states, national


# data/interim/minor_girls_*.csv heads -> dashboard keys (girl victims unless noted)
MINOR_GIRLS_STD = {
    ("rape_minor", "girl"): "rape_minor", ("attempt_rape_minor", "girl"): "attempt_rape_minor",
    ("assault_modesty_minor", "girl"): "assault_minor", ("insult_modesty_minor", "girl"): "insult_minor",
    ("kidnap_girls", "girl"): "kidnap_girls", ("procuration_minor_girls", "girl"): "procuration_minor_girls",
    ("selling_minor_girls", "girl"): "selling_minor_girls", ("buying_minor_girls", "girl"): "buying_minor_girls",
    ("pocso_total", "girl"): "pocso_girls", ("pocso_penetrative", "girl"): "pocso_penetrative",
    ("pocso_sexual_assault", "girl"): "pocso_sexual_assault", ("pocso_harassment", "girl"): "pocso_harassment",
    ("pocso_pornography", "girl"): "pocso_pornography",
    ("child_marriage", "all"): "child_marriage", ("foeticide", "all"): "foeticide", ("infanticide", "all"): "infanticide",
}


def minor_girls(level):
    f = INTERIM / f"minor_girls_{level}.csv"
    if not f.exists():
        f = f.with_suffix(".csv.gz")  # large tables are kept gzipped in the repository
    if not f.exists():
        return None
    df = pd.read_csv(f, usecols=lambda c: c not in ("source", "source_file"))
    if "special_police_unit" in df.columns:
        df = df[~df.special_police_unit.astype(bool)]
    df = df[df.measure == "cases_registered"]
    df["crime_head_std"] = [MINOR_GIRLS_STD.get((k, v)) for k, v in zip(df.crime_head_std, df.victim_sex)]
    return df.dropna(subset=["crime_head_std", "count"])


def extra_state_frames():
    for f in sorted(INTERIM.glob("ncrb_*.csv")):
        df = pd.read_csv(f)
        if {"year", "state_ut", "crime_head_std", "count"} <= set(df.columns) and "district" not in df.columns:
            yield f.name, df
    mg = minor_girls("state")
    if mg is not None:
        yield "minor_girls_state.csv", mg


def merge_extra_state_heads(states, national, pop):
    """Fill crime heads from data/interim (NCRB 2015+ tables, minor-girls tables); earlier sources win."""
    added = 0
    for name, df in extra_state_frames():
        for r in df.dropna(subset=["crime_head_std", "count"]).itertuples():
            key, year = r.crime_head_std, str(int(r.year))
            if key not in CATS:
                continue
            if r.state_ut in ("All India", "India"):
                target = [national.setdefault(year, {"pop": pop.get("India", int(year))})]
            else:
                geos = STATE_TO_GEO.get(r.state_ut, [r.state_ut])
                target = []
                for gname in geos:
                    rec = states.setdefault(gname, {}).setdefault(year, {})
                    rec.setdefault("pop", pop.get(r.state_ut if len(geos) > 1 else gname, int(year)))
                    target.append(rec)
            for rec in target:
                if key not in rec:  # the primary dataset wins where both have a value
                    rec[key] = int(r.count)
                    added += 1
        print(f"  merged heads from {name}")
    print(f"extra state/national head values added: {added}")


# ------------------------------------------------------------- offenders (rape)
REL_KEYS = {
    "No_of_Cases_in_which_offenders_were_Parentsclose_family_members": "family",
    "No_of_Cases_in_which_offenders_were_Relatives": "relatives",
    "No_of_Cases_in_which_offenders_were_Neighbours": "neighbours",
    "No_of_Cases_in_which_offenders_were_Other_Known_persons": "other_known",
    "No_of_Cases_in_which_offenders_were_known_to_the_Victims": "known",
}


# NCRB relation categories (they change over the years) -> dashboard offender keys
RELATION_STD = {
    "known_total": "known",
    "parents_close_family": "family", "family": "family",
    "grandfather_father_brother_son": "father_brother", "close_family_other": "family_other",
    "relatives": "relatives", "neighbours": "neighbours", "employer_coworkers": "employers",
    "other_known_persons": "other_known",
    "friends_online_friends_livein_partners_separated_husband": "friends",
    "livein_partner_separated_ex_husband": "friends", "known_person_on_promise_to_marry": "friends",
    "family_friends_neighbours_employer_other_known": "acquaintances",
    "unknown": "unknown",
}
# armed forces are counted with police personnel (one "police / security" option)
CUSTODY_STD = {"police_personnel": "custodial_police", "armed_forces": "custodial_police",
               "public_servant": "custodial_public_servant", "jail_remand_home_place_of_custody": "custodial_jail",
               "hospital": "custodial_hospital"}


def merge_custodial_totals(states, national, pop):
    """Custodial rape totals 2015+ into the state records (key custodial_rape)."""
    for f in sorted(INTERIM.glob("ncrb_custodial_rape_*.csv")):
        cr = pd.read_csv(f)
        cr = cr[cr.custody_type == "custodial_total"].dropna(subset=["count"])
        for r in cr.itertuples():
            y = str(int(r.year))
            if r.state_ut in ("All India", "India"):
                national.setdefault(y, {}).setdefault("custodial_rape", int(r.count))
                continue
            for gname in STATE_TO_GEO.get(r.state_ut, [r.state_ut]):
                rec = states.setdefault(gname, {}).setdefault(y, {"pop": pop.get(gname, int(y))})
                rec.setdefault("custodial_rape", int(r.count))
        if "All India" not in set(cr.state_ut):
            for y, g in cr.groupby("year"):
                national.setdefault(str(int(y)), {}).setdefault("custodial_rape", int(g["count"].sum()))


def build_offenders():
    df = pd.read_csv(RAW / "rajanand_crime-in-india" / "21_Offenders_known_to_the_victim.csv")
    out = {}
    for r in df.itertuples(index=False):
        rec = {REL_KEYS[c]: int(getattr(r, c)) for c in REL_KEYS}
        for gname in STATE_TO_GEO.get(r.Area_Name, [r.Area_Name]):
            out.setdefault(gname, {})[str(r.Year)] = rec
    def put(name, year, key, value):
        name = "India" if name in ("All India", "India") else name
        for gname in STATE_TO_GEO.get(name, [name]):
            rec = out.setdefault(gname, {}).setdefault(str(int(year)), {})
            rec[key] = rec.get(key, 0) + int(value)

    for f in sorted(INTERIM.glob("ncrb_*relation*.csv")):
        rel = pd.read_csv(f)
        if not {"year", "state_ut", "relation_std", "count"} <= set(rel.columns):
            continue
        for r in rel.dropna(subset=["count"]).itertuples():
            key = RELATION_STD.get(r.relation_std)
            if key:
                put(r.state_ut, r.year, key, r.count)
        print(f"  merged offender relations from {f.name}")
    # Custodial rape by type of custody (2017+): the "police / security" offender options
    for f in sorted(INTERIM.glob("ncrb_custodial_rape_*.csv")):
        cr = pd.read_csv(f)
        for r in cr.dropna(subset=["count"]).itertuples():
            key = CUSTODY_STD.get(r.custody_type)
            if key:
                put(r.state_ut, r.year, key, r.count)
        print(f"  merged custody types from {f.name}")
    # 2014-2016 split "family" in two; add them up so the family series is continuous
    for years in out.values():
        for rec in years.values():
            if "family" not in rec and ("father_brother" in rec or "family_other" in rec):
                rec["family"] = rec.get("father_brother", 0) + rec.get("family_other", 0)
    for child, (parent, last, _label) in SPLITS.items():
        for y, rec in out.get(parent, {}).items():
            if int(y) <= last and y not in out.get(child, {}):
                out.setdefault(child, {})[y] = rec
    national = {}
    for gname, years in out.items():
        if gname in SPLITS:
            continue  # shares its parent's record; don't count twice
        if gname == "India":
            continue
        for y, rec in years.items():
            n = national.setdefault(y, {})
            for k, v in rec.items():
                n[k] = n.get(k, 0) + v
    national.update(out.pop("India", {}))
    return out, national


# ------------------------------------------------------------- district level
def load_districts_raw():
    d = RAW / "rajanand_crime-in-india"
    a = pd.read_csv(d / "42_District_wise_crimes_committed_against_women_2001_2012.csv")
    b = pd.read_csv(d / "42_District_wise_crimes_committed_against_women_2013.csv")
    old_cols = ["Rape", "Kidnapping and Abduction", "Dowry Deaths",
                "Assault on women with intent to outrage her modesty", "Insult to modesty of Women",
                "Cruelty by Husband or his Relatives", "Importation of Girls"]
    ab = pd.concat([a, b]).rename(columns={"STATE/UT": "state", "DISTRICT": "district",
                                          **dict(zip(old_cols, DISTRICT_KEYS))})
    c = pd.read_csv(d / "42_District_wise_crimes_committed_against_women_2014.csv")
    new_cols = ["Rape", "Kidnapping & Abduction_Total", "Dowry Deaths",
                "Assault on Women with intent to outrage her Modesty_Total",
                "Insult to the Modesty of Women_Total", "Cruelty by Husband or his Relatives",
                "Importation of Girls from Foreign Country"]
    c = c.rename(columns={"States/UTs": "state", "District": "district", "Custodial Rape": "custodial_rape",
                          **dict(zip(new_cols, DISTRICT_KEYS))})
    cols = ["state", "district", "Year"] + DISTRICT_KEYS
    df = pd.concat([ab[cols], c[cols + ["custodial_rape"]]])
    df["state"] = df.state.map(norm)
    df["district"] = df.district.astype(str)
    return df


def district_index(geoms):
    by_state = {}
    for i, g in enumerate(geoms):
        by_state.setdefault(g["properties"]["st"], {})[norm(g["properties"]["name"])] = i
    return by_state, {norm(s): s for s in by_state}


def build_districts(geoms):
    by_state, state_norm = district_index(geoms)
    df = load_districts_raw()
    cache = {}
    gids = []
    for st, dist in zip(df.state, df.district):
        if (st, dist) not in cache:
            cache[(st, dist)] = match(st, dist, by_state, state_norm)
        gid = cache[(st, dist)]
        gids.append(gid if isinstance(gid, int) else None)
    df["gid"] = gids
    ok = df[df.gid.notna()].astype({"gid": int})
    keys = DISTRICT_KEYS + ["custodial_rape"]
    ok = ok.assign(total=ok[DISTRICT_KEYS].sum(axis=1, min_count=1))  # 2001-2014: 7 IPC heads
    extra = load_ncrb_districts(by_state, state_norm)
    if extra is not None:
        ok = pd.concat([ok, extra], ignore_index=True)
        keys = keys + [k for k in extra.columns if k in CATS and k not in keys]
    keys = list(dict.fromkeys(keys + ["total"]))
    agg = ok.groupby(["gid", "Year"])[keys].sum(min_count=1)
    out = {}
    for (gid, year), row in agg.iterrows():
        rec = {k: int(row[k]) for k in keys if pd.notna(row[k])}
        out.setdefault(str(gid), {})[str(year)] = rec
    real = df[~df.district.str.upper().str.contains("TOTAL")]
    old = ok[ok.Year <= 2014]
    print(f"districts: {len(out)} with data; 2001-2014: {old[DISTRICT_KEYS].sum().sum() / real[DISTRICT_KEYS].sum().sum():.1%}"
          " of district-reported volume placed on the map")
    return out


DNHDD_GADM = {"D AND N HAVELI": "Dadra and Nagar Haveli", "DADRA AND NAGAR HAVELI": "Dadra and Nagar Haveli", "DAMAN": "Daman and Diu", "DIU": "Daman and Diu"}


def load_ncrb_districts(by_state, state_norm):
    """NCRB district-wise tables (2015+) from data/interim/ncrb_district_*.csv, matched to map districts."""
    files = {}
    for f in sorted(INTERIM.glob("ncrb_district_*.csv*")):  # .csv or gzipped .csv.gz
        files.setdefault(f.name.removesuffix(".gz"), f)
    frames = [pd.read_csv(f) for f in files.values()]
    mg = minor_girls("district")
    if mg is not None:
        frames.append(mg[["year", "state_ut", "district", "crime_head_std", "count"]])
    if not frames:
        return None
    # NCRB women tables first, so they win over the children tables for shared heads
    df = pd.concat(frames).drop_duplicates(["year", "state_ut", "district", "crime_head_std"])
    wide = df.pivot_table(index=["year", "state_ut", "district"], columns="crime_head_std", values="count",
                          aggfunc="sum").reset_index()
    cache, gids = {}, []
    for st, dist in zip(wide.state_ut, wide.district):
        key = (st, dist)
        if key not in cache:
            n_st, n_d = norm(st), norm(dist)
            if n_st == norm("Dadra & Nagar Haveli and Daman & Diu"):
                gs = next((v for k, v in DNHDD_GADM.items() if k in n_d), None)
                cache[key] = next(iter(by_state[gs].values())) if gs == "Dadra and Nagar Haveli" else (
                    match(norm("Daman & Diu"), dist, by_state, state_norm) if gs else None)
            else:
                cache[key] = match(n_st, dist, by_state, state_norm)
        g = cache[key]
        gids.append(g if isinstance(g, int) else None)
    wide["gid"] = gids
    wide = wide.rename(columns={"year": "Year"})
    dropped = wide.district.map(lambda d: bool(DROP.search(norm(d))))
    miss = wide[wide.gid.isna() & ~dropped]
    placed = wide.loc[wide.gid.notna(), "total"].sum() / wide.loc[~dropped, "total"].sum()
    print(f"NCRB districts {sorted(wide.Year.unique())}: {wide.district.nunique()} names, "
          f"{placed:.1%} of volume placed; top unmatched:")
    top = miss.groupby(["state_ut", "district"])["total"].sum().sort_values(ascending=False).head(25)
    print(top.to_string())
    return wide[wide.gid.notna()].astype({"gid": int})


def build_district_pop(geoms):
    by_state, state_norm = district_index(geoms)
    df = pd.read_csv(INTERIM / "female_pop_district_2011.csv")
    pops, missed = {}, []
    for r in df.itertuples():
        st = norm(r.state_ut_2011 if isinstance(r.state_ut_2011, str) else r.state_ut)
        gid = match(st, r.district, by_state, state_norm)
        if isinstance(gid, int):
            pops[str(gid)] = pops.get(str(gid), 0) + int(r.female_pop)
        else:
            missed.append(f"{r.state_ut}/{r.district}")
    print(f"district population: {len(pops)} map districts; unmatched census districts: {missed}")
    return pops


# ---------------------------------------------------------------------- ADR
def build_adr():
    out = {}
    for f in sorted(INTERIM.glob("adr_*.csv")):
        out[f.stem.removeprefix("adr_")] = json.loads(pd.read_csv(f).to_json(orient="records"))
    return out


def coverage(states, districts):
    """Years with data per crime head, at state and district level (drives the UI's availability notes)."""
    out = {}
    for level, recs in (("state", states), ("district", districts)):
        for ent in recs.values():
            for y, rec in ent.items():
                for k in rec:
                    if k in CATS:
                        out.setdefault(k, {}).setdefault(level, set()).add(int(y))
    return {k: {lvl: sorted(ys) for lvl, ys in v.items()} for k, v in out.items()}


def main():
    pop = Population()
    states, national = build_states(pop)
    merge_extra_state_heads(states, national, pop)
    merge_custodial_totals(states, national, pop)
    offenders, offenders_nat = build_offenders()

    topo = json.loads((GEO / "districts.topo.json").read_text())
    geoms = topo["objects"]["districts"]["geometries"]
    official = pd.read_csv(GEO / "district_official_state.csv").set_index("gid")["name"].to_dict()
    for i, g in enumerate(geoms):
        g["properties"]["gid"] = i
        g["properties"]["ost"] = official.get(i) if isinstance(official.get(i), str) else "Lakshadweep"
    districts = build_districts(geoms)
    district_pop = build_district_pop(geoms)

    points = {
        "states": {r.name: [r.x, r.y] for r in pd.read_csv(GEO / "state_points.csv").itertuples()},
        "districts": {str(r.gid): [r.x, r.y] for r in pd.read_csv(GEO / "district_points.csv").itertuples()},
    }
    years = sorted({int(y) for s in states.values() for y in s} | {int(y) for y in national})
    data = {
        "cats": {k: {"label": a, "legal": b} for k, (a, b) in CATS.items()},
        "catGroups": CAT_GROUPS,
        "coverage": coverage(states, districts),
        "points": points,
        "years": years,
        "national": national,
        "states": states,
        "districts": districts,
        "districtPop": district_pop,
        "offenders": offenders,
        "offendersNational": offenders_nat,
        "adr": build_adr(),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "data.json").write_text(json.dumps(data, separators=(",", ":")))
    (OUT / "districts.topo.json").write_text(json.dumps(topo, separators=(",", ":")))
    (OUT / "states.topo.json").write_text((GEO / "states.topo.json").read_text())
    # National outline (all states dissolved, full detail) drawn as the official boundary line
    (OUT / "india.topo.json").write_text((GEO / "india_outline.topo.json").read_text())
    # Simplified outline used to keep only basemap labels that fall inside India
    (OUT / "india_mask.json").write_text((GEO / "india_label_mask.geojson").read_text())
    print(f"wrote {OUT}: {len(states)} states, years {years[0]}-{years[-1]}, national years {len(national)}, "
          f"offender states {len(offenders)}, ADR tables {list(data['adr'])}")
    print(f"data.json {(OUT / 'data.json').stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
