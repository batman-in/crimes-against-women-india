"""Build web/public/data/support.json from the support directory CSVs in data/support/.

Checks every row against data/support/SCHEMA.md, matches district names to map districts
(the same matcher the crime data uses), and reports rows it had to skip. District entries that
don't match a map district (newer districts, spelling) stay in their state's list.
"""
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from district_match import match, norm  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "support"
OUT = ROOT / "web" / "public" / "data"

COLUMNS = "level,state,district,category,name,phones,whatsapp,email,website,address,hours,notes,source_url,verified_on".split(",")
CATEGORIES = {
    "emergency": "Emergency",
    "women_helpline": "Women helplines",
    "one_stop_centre": "One Stop Centres (Sakhi)",
    "police_women": "Police help for women",
    "legal_aid": "Free legal aid",
    "commission": "Women's commissions",
    "protection_officer": "Protection Officers (domestic violence)",
    "shelter": "Shelter",
    "child": "Children and girls under 18",
    "cyber": "Online harassment and cyber crime",
    "mental_health": "Counselling and mental health",
    "ngo": "NGOs and support groups",
}
STATES = [
    "Andaman & Nicobar", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chandigarh", "Chhattisgarh",
    "Dadra & Nagar Haveli", "Daman & Diu", "Delhi", "Goa", "Gujarat", "Haryana", "Himachal Pradesh",
    "Jammu & Kashmir", "Jharkhand", "Karnataka", "Kerala", "Ladakh", "Lakshadweep", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Puducherry", "Punjab", "Rajasthan",
    "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
]
# Districts created after the map boundaries (c. 2010), or spelt differently in the directories,
# folded into the map district that covers them. Keys are norm()'d source names.
SUPPORT_ALIAS = {
    # Chhattisgarh
    "BALODA BAZAR BHATAPARA": "RAIPUR", "GARIABAND": "RAIPUR", "BALRAMPUR RAMANUJGANJ": "SURGUJA",
    "GAURELA PENDRA MARWAHI": "BILASPUR", "KOREA": "KORIYA", "MOHLA MANPUR AMBAGARH CHOWKI": "RAJ NANDGAON",
    # Karnataka
    "CHIKKAMANGALORE": "CHIKMAGALUR", "KALBURGI": "GULBARGA", "YADAGIRI": "GULBARGA",
    # Telangana
    "BHADRADI KOTHAGUDEM": "KHAMMAM", "JAYASHANKAR BHUPALAPALLY": "WARANGAL", "MEDCHAL MALKAJIGIRI": "RANGAREDDI",
    "PEDDAPALLY": "KARIMNAGAR", "RAJANNA SIRCILLA": "KARIMNAGAR",
    # Andhra Pradesh
    "ANANTHAPURAMU": "ANANTAPUR", "DR YSR KADAPA": "CUDDAPAH",
    # Gujarat
    "CHHOTA UDAIPUR": "VADODARA", "CHHOTA UDEPUR": "VADODARA",
    # Tamil Nadu
    "TIRUPATHUR": "VELLORE",
    # Sikkim (districts renamed / carved out in 2021)
    "GYALSHING": "WEST SIKKIM", "SORENG": "WEST SIKKIM", "MANGAN": "NORTH SIKKIM",
    # Punjab
    "ROOP NAGAR": "RUPNAGAR", "S A S NAGAR MOHALI": "RUPNAGAR", "SHRI MUKTSAR SAHIB": "MUKTSAR",
    "SRI MUKTSAR SAHIB": "MUKTSAR",
    # Nagaland (districts created 2021-22, folded into the district they were carved from)
    "CHUMOUKEDIMA": "DIMAPUR", "NIULAND": "DIMAPUR", "TSEMINYU": "KOHIMA", "MELURI": "PHEK",
    "NOKLAK": "TUENSANG", "SHAMATOR": "TUENSANG",
}
NUMBER = re.compile(r"\+?\d[\d \-()]{1,}\d(?:\s*/\s*\d+)*")


def parse_phone(raw):
    """'Helpline 01282-250322' -> ('01282-250322', '01282250322', 'Helpline').

    Returns (as printed, dialable, label) or None if there's no number. Only the first of
    '080-25492781/82/83' is dialled; '+91 0241...' and '0091-(0)-...' lose the trunk 0.
    """
    m = NUMBER.search(raw)
    if not m:
        return None
    shown = m.group().strip()
    label = (raw[: m.start()] + " " + raw[m.end():]).strip(" ()[]:,-–")
    label = re.sub(r"^\(|\)$", "", re.sub(r"\s+", " ", label)).strip()
    first = shown.split("/")[0].replace("(0)", "")
    dial = re.sub(r"[^\d+]", "", first)
    if dial.startswith("0091"):
        dial = "+91" + dial[4:]
    if dial.startswith("+910"):
        dial = "+91" + dial[4:]
    if len(re.sub(r"\D", "", dial)) < 3:
        return None
    return shown, dial, label


def split(v):
    return [x.strip() for x in re.split(r"[;\n]", v or "") if x.strip()]


def district_index():
    topo = json.loads((OUT / "districts.topo.json").read_text())
    by_state = {}
    for g in topo["objects"]["districts"]["geometries"]:
        p = g["properties"]
        by_state.setdefault(p["st"], {})[norm(p["name"])] = p["gid"]
    return by_state, {norm(s): s for s in by_state}


def load_rows():
    files = [SRC / "national.csv", SRC / "ngos.csv", *sorted((SRC / "states").glob("*.csv"))]
    for f in files:
        if not f.exists():
            continue
        with f.open(encoding="utf-8-sig", newline="") as fh:
            r = csv.DictReader(fh)
            if r.fieldnames != COLUMNS:
                raise SystemExit(f"{f.name}: header {r.fieldnames} does not match SCHEMA.md")
            for i, row in enumerate(r, start=2):
                yield f.name, i, {k: (v or "").strip() for k, v in row.items()}


def main():
    by_state, state_norm = district_index()
    out = {"categories": CATEGORIES, "national": [], "states": {}}
    skipped, unmatched, seen = [], [], set()
    newest = ""

    for fname, line, r in load_rows():
        where = f"{fname}:{line}"
        problems = []
        if r["level"] not in ("national", "state", "district"):
            problems.append(f"level {r['level']!r}")
        if r["category"] not in CATEGORIES:
            problems.append(f"category {r['category']!r}")
        if r["level"] != "national" and r["state"] not in STATES:
            problems.append(f"state {r['state']!r}")
        if r["level"] == "district" and not r["district"]:
            problems.append("district level without a district")
        raw_phones = split(r["phones"])
        parsed = [parse_phone(p) for p in raw_phones]
        bad = [p for p, x in zip(raw_phones, parsed) if x is None]
        if bad:
            problems.append(f"phone {bad}")
        # "as printed|dialable|label", label optional
        phones = ["|".join(x).rstrip("|") for x in parsed if x]
        if not (phones or r["whatsapp"] or r["email"] or r["website"] or r["address"]):
            problems.append("no way to contact")
        if not r["source_url"].startswith("http"):
            problems.append("no source")
        if problems:
            skipped.append(f"{where} {r['name']!r}: {', '.join(problems)}")
            continue
        key = (r["level"], r["state"], r["district"].lower(), r["category"], r["name"].lower())
        if key in seen:
            continue
        seen.add(key)
        newest = max(newest, r["verified_on"])

        e = {"c": r["category"], "n": r["name"]}
        for k, v in (("p", phones), ("e", split(r["email"]))):
            if v:
                e[k] = v
        for k, col in (("w", "whatsapp"), ("u", "website"), ("a", "address"), ("h", "hours"),
                       ("o", "notes"), ("s", "source_url"), ("v", "verified_on")):
            if r[col]:
                e[k] = r[col]

        if r["level"] == "national":
            out["national"].append(e)
            continue
        st = out["states"].setdefault(r["state"], {"state": [], "district": []})
        if r["level"] == "state":
            st["state"].append(e)
            continue
        e["d"] = r["district"]
        name = SUPPORT_ALIAS.get(norm(r["district"]), r["district"])
        gid = match(norm(r["state"]), name, by_state, state_norm)
        if isinstance(gid, int):
            e["g"] = gid
        else:
            unmatched.append(f"{r['state']} / {r['district']}")
        st["district"].append(e)

    order = list(CATEGORIES)
    for st in out["states"].values():
        st["state"].sort(key=lambda e: order.index(e["c"]))
        st["district"].sort(key=lambda e: (e["d"].lower(), order.index(e["c"])))
    out["updated"] = newest
    (OUT / "support.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    n_d = sum(len(s["district"]) for s in out["states"].values())
    n_s = sum(len(s["state"]) for s in out["states"].values())
    print(f"support.json: {len(out['national'])} national, {n_s} state, {n_d} district entries "
          f"across {len(out['states'])} states/UTs")
    if unmatched:
        print(f"{len(set(unmatched))} district names not on the map (listed under their state): "
              + "; ".join(sorted(set(unmatched))))
    if skipped:
        print(f"skipped {len(skipped)} rows:")
        for s in skipped:
            print("  " + s)


if __name__ == "__main__":
    main()
