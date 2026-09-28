"""Parse per-legislator detail sections of ADR crimes-against-women reports
into anonymous records (house, state, party, set of women-related IPC sections).
Names are never stored or written."""
import re, json, sys
from collections import Counter
from pathlib import Path

# Working folder for text extracted from the ADR PDFs (t<year>.txt) and intermediate files
S = str(Path(__file__).resolve().parents[2] / "data" / "raw" / "adr" / "work") + "/"

# women-related sections per ADR 2024 list (+366 which ADR cites in every report)
WOMEN = {"313", "326A/B", "326A", "326B", "375", "376", "376A", "376B", "376C", "376D", "376E", "376(2)(n)",
         "354", "354A", "354B", "354C", "354D", "366", "366A", "366B", "509", "372", "373",
         "498A", "498", "493", "304B", "494"}

# charge-descriptor phrases (robust to the section number being split by the 2-column layout)
DESC = {
    r"outrage her\s+modesty": "354",
    r"insult the\s+modesty of a\s+woman": "509",
    r"related to\s+(?:Punishment for\s+)?rape": "376",
    r"commits rape\s+repeatedly": "376(2)(n)",
    r"subjecting her\s+to\s+cruelty": "498A",
    r"inducing\s+woman\s+to\s+compel\s+her\s+marriage": "366",
    r"Buying minor for purposes of\s+prostitution": "373",
    r"Selling minor for purposes of\s+prostitution": "372",
    r"Sexual harassment": "354A",
    r"intent to\s+disrobe": "354B",
    r"Voyeurism": "354C",
    r"Stalking": "354D",
    r"criminal intent a\s+married\s+woman": "498",
    r"belief of\s+lawful\s+marriage": "493",
    r"Marrying again during": "494",
    r"Dowry death": "304B",
    r"acid": "326A/B",
    r"miscarriage without\s+woman's\s+consent": "313",
}

CFG = {
    2017: dict(start="Details of All MPs/MLAs with Declared Cases", end="Table: Details of all MPs/MLAs"),
    2018: dict(start="Details of All MPs with Declared Cases", end="Table: Details of all MLAs"),
    2024: dict(start="Details of All Sitting MPs with Declared Cases", end="CONTACT DETAILS|Contact Details"),
}
NAME_RE = re.compile(r"^\s*\d+\.?\s+N\s?ame\s*:", re.M)
SEC_RE = re.compile(r"Section-\s*([0-9]+[A-Z]?(?:\s*\([0-9a-z]+\))*)\s*\)")


def records(year):
    t = open(S + f"t{year}.txt", encoding="utf-8").read()
    i = t.index(CFG[year]["start"])
    m = re.search(CFG[year]["end"], t[i:])
    body = t[i:i + m.start()] if m else t[i:]
    # house markers
    marks = []
    for mm in re.finditer(r"^(LOK SABHA|RAJYA SABHA|MPs|MLAs|Details of All (?:Sitting )?MLAs.*)$", body, re.M):
        lab = mm.group(1)
        h = {"LOK SABHA": "Lok Sabha", "RAJYA SABHA": "Rajya Sabha", "MPs": "MP", "MLAs": "State Assembly"}.get(lab, "State Assembly")
        marks.append((mm.start(), h))
    starts = [mm.start() for mm in NAME_RE.finditer(body)] + [len(body)]
    out = []
    for a, b in zip(starts, starts[1:]):
        blk = body[a:b]
        house = "MP"
        for pos, h in marks:
            if pos <= a:
                house = h
        joined = re.sub(r"\s+", " ", blk)
        if house == "MP":  # 2017/2018: infer LS vs RS from constituency text
            house = "Rajya Sabha" if re.search(r"Rajya\s*Sabha", joined, re.I) else "Lok Sabha"
        st = re.search(r"State(?:/District)?\s*:\s*([A-Z][A-Z &\-]+?)(?= [A-Z][a-z]| \d|$)", joined)
        state = st.group(1).strip() if st else None
        if not state:
            c = re.search(r"Constituency\s*:\s*[^()]*\(([A-Za-z &]+?)\s*(?:\d{4})?\)", joined)
            state = c.group(1).strip() if c else None
        pt = re.search(r"Party\s*:\s*(.+?)\s+(?:\d+ charges?|Total Cases|between|[A-Z][a-z]+ [a-z])", joined)
        party = pt.group(1).strip() if pt else None
        secs = {re.sub(r"\s+", "", s) for s in SEC_RE.findall(joined)}
        for pat, sec in DESC.items():
            if re.search(pat, joined, re.I):
                secs.add(sec)
        out.append(dict(house=house, state=state, party=party,
                        women_secs=sorted(s for s in secs if s in WOMEN)))
    return out


if __name__ == "__main__":
    for y in (2017, 2018, 2024):
        r = records(y)
        print(y, len(r), Counter(x["house"] for x in r))
        print(" states", Counter(x["state"] for x in r))
        print(" parties", Counter(x["party"] for x in r))
        print(" none-women", sum(1 for x in r if not x["women_secs"]))
        c = Counter(s for x in r for s in x["women_secs"])
        print(" secs", c)
        json.dump(r, open(S + f"anon_{y}.json", "w"))
