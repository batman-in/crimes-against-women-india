# ADR: sitting MPs/MLAs with declared cases related to crimes against women

Aggregate counts only. **No individual names are stored in these CSVs.**

## Methodology note (please show this on the dashboard)
- Source: Association for Democratic Reforms (ADR) and National Election Watch (NEW) analysis of the **self-declared election affidavits (Form 26)** that sitting MPs and MLAs filed with the Election Commission of India when they were elected (the last ~5 years of elections before each report, including bye-elections).
- These are **declared pending cases (charges), not convictions.** ADR itself notes that the current status of each case is not known and may have changed since the affidavit was filed.
- Each report is a snapshot of the legislators sitting at that time. The coverage differs (the number of affidavits analysed and the list of IPC sections counted), so compare years with care.
- Counts are **legislators**, not cases. One legislator can face several charges and appear under several IPC sections in the charge table.

## Reports covered
| report_year | Release date | Scope | Source | Raw file (`data/raw/adr/`) |
|---|---|---|---|---|
| 2024 | 21 Aug 2024 | 755/776 MPs, 3,938/4,033 MLAs (28 states, 8 UTs; affidavits 2019-2024) | https://adrindia.org/Analysis_of_Sitting_MPs_and_MLAs_with_Declared_Cases_Related_to_Crimes_against_Women_2024 · PDF: https://adrindia.org/sites/default/files/Analysis_of_Sitting_MPs_and_MLAs_with_Declared_Cases_Related_to_Crimes_against_Women_2024_FinalVer_English.pdf | `adr_2024_crimes_against_women.pdf`, `adr_2024_page.html` |
| 2023 | ~10 Aug 2023 | 762/776 MPs, 4,001/4,033 MLAs (affidavits 2018-2023) | Report PDF **not found**. Figures come from press coverage that ADR reposted: https://adrindia.org/content/134-sitting-mps-mlas-accused-crimes-against-women-report and https://adrindia.org/content/%E2%80%98134-mps-mlas-have-cases-crime-against-women | none |
| 2018 | 19 Apr 2018 | 768/776 MPs, 4,077/4,120 MLAs | https://adrindia.org/content/analysis-mpsmlas-declared-cases-related-crimes-against-women-1 · PDF: https://adrindia.org/sites/default/files/Analysis_of_MPs_MLAs_with_Declared_Cases_Related_to_Crimes_against_Women_2018_0.pdf | `adr_2018_crimes_against_women.pdf`, `adr_2018_page.html` |
| 2017 | 30 Aug 2017 | 774/776 MPs, 4,078/4,120 MLAs | https://adrindia.org/content/analysis-mpsmlas-declared-cases-related-crimes-against-women · PDF: https://adrindia.org/sites/default/files/Analysis_of_MPsMLAs_with_Declared_Cases_Related_to_Crimes_against_Women.pdf | `adr_2017_crimes_against_women.pdf`, `adr_2017_page.html` |

No ADR report from around 2020 on this topic could be found. The reports found are from 2017, 2018, 2023 (press coverage only) and 2024.

## Headline totals
| Year | Total | MLAs | MPs (LS + RS) | With rape cases |
|---|---|---|---|---|
| 2024 | 151 | 135 | 16 (15 LS + 1 RS) | 16 (14 MLAs, 2 MPs) |
| 2023 | 134 | 113 | 21 | 18 (14 MLAs, 4 MPs) |
| 2018 | 48 | 45 | 3 (2 LS + 1 RS) | 3 (all MLAs) |
| 2017 | 51 | 48 | 3 (2 LS + 1 RS) | 4 (all MLAs) |

## Files
All files share the columns `report_year`, `report_date` and `method`. The `method` column says whether a number is:
- **`published`**: copied from the report's own aggregate table;
- **`derived`**: counted by us from the report's per-legislator detail pages. The names were dropped in the process and only the counts were kept. Every derived split was checked against the published totals, and they all match;
- **`press_headline_only`**: a partial figure from 2023 press coverage.

- **`adr_legislators_by_state.csv`** has the columns `state_ut, house, legislators_with_cases, rape_cases_legislators`.
  - 2024: the MLA/MP split per state is published. Of the MPs, only one sits in the Rajya Sabha (from Maharashtra), which we found from the detail pages. All other MPs are Lok Sabha members.
  - 2017/2018: the state totals are published. We derived the house split from the detail pages. We aggregated rape counts from the report's short list of MLAs facing rape cases.
  - 2023: only the top 3 states are given (West Bengal 26, Maharashtra 14, Odisha 14), with `house = "All houses (split not published)"`. **Don't add these rows to other house rows.**
- **`adr_legislators_by_party.csv`** has the columns `party` (ADR's abbreviation), `party_full`, `house`, `legislators_with_cases` and `rape_cases_legislators`.
  - 2024 gives a published split between the State Assembly and Parliament (LS + RS).
  - 2017/2018 give totals only.
  - 2023 gives the top parties only: BJP 44 (7 with rape cases), INC 25 (6), AAP 13.
  - In 2024 ADR's "SHS" row covers both Shiv Sena factions.
- **`adr_legislators_by_house.csv`** gives counts by State Assembly, Lok Sabha, Rajya Sabha and Parliament (LS + RS), plus `legislators_analysed` (the denominator ADR used). Use this to compute rates, for example 16/755 MPs in 2024. The "Parliament (LS+RS)" row is the sum of the LS and RS rows, so don't add all four rows together.
- **`adr_legislators_by_charge.csv`** has the columns `house, ipc_section, charge_label, charge_group, legislators_with_charge, total_charges_published`.
  - `legislators_with_charge` is **derived** from each legislator's "Brief Details of IPCs" summary. It counts the legislators who have at least one charge under that section. One legislator can appear under several sections, so the column does not add up to the total number of legislators.
  - The derived rape count matches ADR's published count for every year: 16 in 2024, 3 in 2018 and 4 in 2017.
  - 2017 also has ADR's own published table in `total_charges_published` (354: 36, 509: 16, 376: 4, 366: 2, 498A: 1, 373: 1). Our derived counts match it, and also find one 354B that the published table leaves out.
  - In 2024, 4 MLAs appear in ADR's list of 151 only because of IPC 313 (causing miscarriage without the woman's consent). They are kept under the charge group "Miscarriage without consent".
  - The IPC sections ADR's 2024 list covers with no matching legislator (so there are no rows for them): 326A/326B (acid attack), 304B (dowry death), 366B, 375/376A-E, 494.

## Gaps and caveats
- **2023 report PDF not located.** Only the headline, top-3 state and top-party figures from press coverage are included. There is no full state or party table and no charge breakdown for 2023.
- **No report around 2020** was found.
- **ADR publishes no breakdown by charge type for 2018 or 2024.** The charge table for those years is our count from ADR's per-legislator pages, labelled as derived.
- There is no party-by-house split for 2017/2018 and no party-by-charge or state-by-charge table in any report (we did not build one).
- ADR reports "Andhra Pradesh" for elections held after the 2014 bifurcation, so there is no need to adjust it. State names use the current forms (Odisha; "Dadra & Nagar Haveli and Daman & Diu" for the merged UT). The state GeoJSON in `data/geo` has separate polygons for Dadra & Nagar Haveli and for Daman & Diu, so the dashboard needs a mapping for the merged UT.
- Our derived counts depend on parsing text out of the PDFs. We checked them against every published total (house, state, rape), and all match.
- The parsing and build scripts (`parse_details.py`, `build_adr.py`) were kept outside the project, in the session scratchpad, as instructed. They can be recreated if needed.
