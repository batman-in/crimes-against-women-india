"""Add ADR's 2025 all-India sitting MLAs report (crimes-against-women table) to the ADR CSVs.

Source: https://adrindia.org/sites/default/files/All_India_Sitting_MLAs_Report_2025_English.pdf
(pages 10-11, "State wise number of MLAs with declared cases related to Murder, attempt to
murder and crime against women"). MLAs only (no MPs); aggregates only, no names.
States absent from ADR's table have no such MLAs.
"""
from pathlib import Path

import pandas as pd
import pdfplumber

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "data" / "raw" / "adr" / "All_India_Sitting_MLAs_Report_2025_English.pdf"
INTERIM = ROOT / "data" / "interim"
YEAR, DATE = 2025, "2025"
METHOD = "published: ADR All-India Sitting MLAs 2025 report, state table (MLAs only)"
NAMES = {"Jammu Kashmir": "Jammu & Kashmir"}


def cells(row):
    return [c for c in row if c not in (None, "")]


def main():
    rows = []
    with pdfplumber.open(PDF) as pdf:
        for i in (9, 10):
            for table in pdf.pages[i].extract_tables():
                for r in table:
                    c = cells(r)
                    # "<State> <election year>", murder, attempt to murder, crimes against women, rape
                    if len(c) == 5 and c[0][-4:].isdigit() and all(x.isdigit() for x in c[1:]):
                        state = NAMES.get(c[0][:-5].strip(), c[0][:-5].strip())
                        rows.append((state, int(c[3]), int(c[4])))
    df = pd.DataFrame(rows, columns=["state_ut", "legislators_with_cases", "rape_cases_legislators"])
    total, rape = df.legislators_with_cases.sum(), df.rape_cases_legislators.sum()
    assert (total, rape) == (127, 13), f"expected ADR totals 127 / 13, got {total} / {rape}"

    by_state = INTERIM / "adr_legislators_by_state.csv"
    s = pd.read_csv(by_state)
    s = s[s.report_year != YEAR]
    add = df.assign(report_year=YEAR, report_date=DATE, house="State Assembly", method=METHOD)
    pd.concat([s, add[s.columns]], ignore_index=True).to_csv(by_state, index=False)

    by_house = INTERIM / "adr_legislators_by_house.csv"
    h = pd.read_csv(by_house)
    h = h[h.report_year != YEAR]
    h.loc[len(h)] = {"report_year": YEAR, "report_date": DATE, "house": "State Assembly",
                     "legislators_with_cases": total, "rape_cases_legislators": rape,
                     "legislators_analysed": 4092, "method": METHOD}
    h.to_csv(by_house, index=False)
    print(f"ADR 2025: {len(df)} states, {total} MLAs with cases, {rape} with rape charges")


if __name__ == "__main__":
    main()
