# NCRB Crime in India: crimes against women by crime head, 2015–2022

Every number comes from NCRB *Crime in India* (CII) tables. Nothing is estimated or imputed. The only arithmetic applied is listed under "Transformations".
Years 2023–2024 are **deliberately excluded** from these files. The coordinator parses them separately into `ncrb_state_2023_2024.csv`, `ncrb_district_2023_2024.csv` and `ncrb_relation_2023_2024.csv`, and those files were not touched here.

## Output files (`data/interim/`)

| File | Columns | Years | Rows |
|---|---|---|---|
| `ncrb_state_crime_heads_2015_2022.csv` | year, state_ut, crime_head, crime_head_std, count, source | 2015–2022 | 14,850 |
| `ncrb_district_crime_heads_2015_2022.csv` | year, state_ut, district, crime_head, crime_head_std, count, source | 2015–2022 | 329,915 |
| `ncrb_rape_offender_relation_2011_2022.csv` | year, state_ut, relation, relation_std, count, source | 2011–2022 | 2,919 |
| `ncrb_custodial_rape_2015_2022.csv` | year, state_ut, crime_head, custody_type, count, source | 2015–2022 | 1,458 |
| `ncrb_rape_sectionwise_3A11_2017_2022.csv` | year, state_ut, crime_head, custody_type, count, source | 2017–2022 | 5,732 |
| `ncrb_state_totals_3A1_2015_2022.csv` | year, state_ut, metric, value, cii_edition, source | 2015–2022 (CII editions 2017–2022) | 1,305 |
| `ncrb_build/*.py` | scripts that rebuild everything from `data/raw` (`python run_all.py`) | | |

`count` holds cases registered (incidence, "I"). Victims (V) and crime rates (R) are not included, except that `ncrb_state_totals_3A1_*` also carries NCRB's crime rate, female population, % share and chargesheeting rate as `metric` values.
State rows use current names (Odisha, Delhi, Andaman & Nicobar Islands, Dadra & Nagar Haveli and Daman & Diu, Jammu & Kashmir, Ladakh). NCRB's `Total (States)` and `Total (UTs)` rows are dropped. NCRB's `Total (All India)` row is kept as `state_ut = "All India"`.

### crime_head_std coverage (All-India counts, state file)

| key | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 |
|---|---|---|---|---|---|---|---|---|
| rape | 34,651 | 38,947 | 32,559 | 33,356 | 32,033 | 28,046 | 31,677 | 31,516 |
| attempt_rape | 4,437 | 5,729 | 4,154 | 4,097 | 3,944 | 3,741 | 3,800 | 3,288 |
| kidnap (K&A of women, total) | 59,277 | 64,519 | 66,333 | 72,751 | 72,780 | 62,300 | 75,369 | 85,310 |
| dowry (deaths) | 7,634 | 7,621 | 7,466 | 7,166 | 7,115 | 6,966 | 6,753 | 6,450 |
| assault (354 total) | 82,422 | 84,746 | 86,001 | 89,097 | 88,367 | 85,392 | 89,200 | 83,344 |
| sexual_harassment (354A) | 24,041 | 27,344 | – | – | – | – | – | – |
| voyeurism (354C) | 838 | 932 | – | – | – | – | – | – |
| stalking (354D) | 6,266 | 7,190 | – | – | – | – | – | – |
| insult (509) | 8,685 | 7,305 | 7,451 | 6,992 | 6,939 | 7,065 | 7,788 | 8,972 |
| cruelty (498A) | 113,403 | 110,378 | 104,551 | 103,272 | 125,298 | 111,549 | 136,234 | 140,019 |
| abetment_suicide | 4,060 | 4,466 | 5,282 | 5,037 | 5,009 | 5,040 | 5,292 | 4,963 |
| acid_attack (326A) | 139 | – * | 148 | 131 | 150 | 105 | 102 | 124 |
| dowry_act | 9,894 | 9,683 | 10,189 | 12,826 | 13,297 | 10,366 | 13,568 | 13,479 |
| dv_act | 461 | 437 | 616 | 579 | 553 | 446 | 507 | 468 |
| itpa | 2,424 | 2,214 | 1,536 | 1,459 | 1,185 | 868 | 1,071 | 946 |
| pocso_girls | – | – | 31,668 | 38,802 | 46,005 | 46,123 | 52,836 | 62,095 |
| total (IPC+SLL) | 327,394 | 338,954 | 359,849 | 378,277 | 405,861 | 371,503 | 428,278 | 445,256 |

\* In 2016 NCRB reports acid attack and attempted acid attack together as one head, `Acid Attack (Sec. 326 A IPC) & Attempt to Acid Attack (Sec. 326 B IPC)`, with 125 cases. That head is kept, but it is not mapped to `acid_attack`.
"Disrobe" (354B) is available for 2015 and 2016 under its NCRB name, with no std key because the key list has none for it. The 2015 and 2016 data also include custodial rape, gang rape, the kidnapping sub-heads, the ITPA sections, cyber (67A), miscarriage and human trafficking. The 2017–2022 data include the age splits (women 18+ / girls <18), the kidnapping sub-heads, murder with rape, selling and buying of minor girls, the ITPA sections, the cyber sub-heads, the POCSO sub-heads and the Indecent Representation Act.

## Sources

### Where the data came from
* **NCRB website, table-wise downloads** (primary source). There are two catalogue pages, both rendered by JavaScript:
  * https://www.ncrb.gov.in/crime-in-india-table-content.html?year=YYYY&category= (the CII chapter tables: 3A.1, 3A.2, 3A.4 and 3A.11)
  * https://www.ncrb.gov.in/crime-in-india-additional-table.html?year=YYYY&category= (the "additional tables", which include the district-wise CAW files)

  How the pages work: they list records only in the **English** locale. The locale is set by `POST /api/language/set` (lang=en, with the CSRF token and a session cookie). Category values come from `POST /api/category/get` (taxonomyId 37 for tables, 36 for additional tables). Querying with `category=` empty returns every table for the year. The full crawled catalogue of 2011–2024 file links is saved in `data/raw/ncrb_cii_tables/manifest.json`.
* **data.gov.in**, found through its public search API `https://www.data.gov.in/backend/dmspublic/v1/resources?query=...&format=json`. No API key was needed because the files are direct downloads. The files used are all "Offenders relation to rape victims" tables:
  * https://data.gov.in/files/ogdpv2dms/s3fs-public/dataurl07092016/Table_5.4-2015.csv (2015)
  * https://data.gov.in/files/ogdpv2dms/s3fs-public/dataurl11012018/Table_3A.4_2016.csv (2016)
  * https://data.gov.in/files/ogdpv2dms/s3fs-public/dataurl05032021/NCRB_CII-2019_Table_3A.4.csv (2019)
  * https://data.gov.in/files/ogdpv2dms/s3fs-public/dataurl06122021/NCRB_CII-2020_Table.No-3A.4.csv (2020)

  These were downloaded for cross-checks only and are not used in the outputs: `Offenders_relation_to_rape_victim.csv` (2001–2012), `..._2013.csv`, `NCRB_2011_Table_5.4.csv`, and `NCRB_Table_3A.2.csv` / `NCRB_Table_3A.4.csv` (2022). All of these are saved in `data/raw/datagovin/`.
* **Reviewed, not used:** Kaggle `ananya0001/crimes-against-women-in-india-2022`, which has 2022 only and a subset of heads with no provenance. Dataful (factly) has NCRB-derived CAW datasets for 2001–2024, but it is a secondary source and NCRB's own files were available.

### NCRB files used (raw copies in `data/raw/ncrb_cii_tables/<year>/`)
| Local file | URL |
|---|---|
| `2015/6-Data-Analysis-on-Crime-against-Women-Crimeheads-under-Various-Heads-during-2010-2015(StateUT).xlsx` | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/6-Data-Analysis-on-Crime-against-Women-Crimeheads-under-Various-Heads-during-2010-2015(StateUT).xlsx |
| `2015/5-District-wise-Crimes-committed-against-Women_2015.xlsx` | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/5-District-wise-Crimes-committed-against-Women_2015.xlsx |
| `2016/1683013216Table3A2.pdf` | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/custom/1683013216Table3A2.pdf |
| `2016/District-wise-Crimes-committed-against-Women_2016.xlsx` | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/District-wise-Crimes-committed-against-Women_2016.xlsx |
| `2017/Table-3A.1_1.xlsx`, `Table-3A.2_1.xlsx`, `Table-3A.4_1.xlsx`, `Table-3A.11_1.xlsx` | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/ + the same file names |
| `2017/District-wise-Crime-against-Women - 2017.xlsx` | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/District-wise-Crime-against-Women - 2017.xlsx |
| `2018/Table-3A.1_0.xlsx`, `Table-3A.2_0.xlsx`, `Table-3A.4_0.xlsx`, `Table-3A.11_0.xlsx` | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/ + the same file names |
| `2018/3-District-wise-Crime-against-Women - 2018.xlsx` | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/3-District-wise-Crime-against-Women - 2018.xlsx |
| `2019/Table-3A.2_2.pdf`, `TABLE-3A.1.xlsx`, `TABLE-3A.11.xlsx` | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/ + the same file names |
| `2019/3-District-wise-Crime-against-Women - 2019.xlsx` | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/3-District-wise-Crime-against-Women - 2019.xlsx |
| `2020/TABLE-3A.2.xlsx` | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/TABLE-3A.2.xlsx |
| `2020/1680767998TABLE3A1.xlsx`, `1680767960TABLE3A11.xlsx` | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/ + the same file names |
| `2020/Districtwise-Crime-against-Women_2020.xlsx` | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Districtwise-Crime-against-Women_2020.xlsx |
| `2021/1679652741TABLE3A1.xlsx`, `1679652792TABLE3A2.xlsx`, `1679652892TABLE3A4.xlsx`, `1679653232TABLE3A11.xlsx`, `16730066503DistrictwiseCrimeagainstWomen2021.xlsx` | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/ + the same file names |
| `2022/1701935121TABLE3A1.xlsx`, `1701935197TABLE3A2.xlsx`, `1701935296TABLE3A4.xlsx`, `1701935624TABLE3A11.xlsx`, `17016840143DistrictwiseCrimeagainstWomen2022.xlsx` | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/custom/ + the same file names |
| `2011/Table-5.4_2011.pdf`, `2012/Table-5.4.pdf`, `2013/Table-5.4_2013.pdf`, `2014/Table-5.4_2014.pdf` | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/ + the same file names |

Other files in `data/raw/ncrb_cii_tables/` were downloaded for reference and are not used in the outputs. They include the 2023–2024 tables, the PDFs that duplicate the XLSX files, and the 2011–2013 custodial-rape tables 13.5/13.6.

### Source used per year and topic
| Topic | 2015 | 2016 | 2017–2018 | 2019 | 2020–2022 |
|---|---|---|---|---|---|
| State × crime head | Additional table "CAW crime heads, State/UT 2010–2015" (sheet 2015, CR) for the 15 main heads. The sub-heads come from the state `Total District(s)` rows of the 2015 district-wise file. | Table 3A.2 **PDF** (no XLSX published), parsed with pdfplumber | 3A.2 XLSX | 3A.2 **PDF** † | 3A.2 XLSX |
| District | district-wise XLSX | district-wise XLSX | XLSX | XLSX | XLSX |
| Offender relation | data.gov.in CSV (CII 2015 T5.4) | data.gov.in CSV (CII 2016 T3A.4) | 3A.4 XLSX | data.gov.in CSV (CII 2019 T3A.4) † | 2020: data.gov.in CSV †. 2021–22: 3A.4 XLSX |

For offender relations, 2011–2014 come from the CII Table 5.4 PDFs. Those PDFs are text-based, so no OCR was needed.
† NCRB's 2019 page links `TABLE-3A.2.xlsx` and `TABLE-3A.4.xlsx`. Both URLs were overwritten by the 2020 files: the xlsx header reads "- 2020", and the 3A.4 link returns 404. So 2019 3A.2 was parsed from the 2019 PDF. The 2019 and 2020 3A.4 tables were taken from the data.gov.in copies of those tables.

## Validation
* **State file:** in every year and for every one of the 408 year × head combinations, the sum of the state and UT rows equals NCRB's All-India row exactly (difference 0).
* **Reference totals:** the state file's 2022 total is 445,256 ✔. For 2015 the state file gives 327,394, which is the CII 2015 figure. The reference 329,243 is the *revised* 2015 figure printed in CII 2017 Table 3A.1, and it is in `ncrb_state_totals_3A1_*` (edition 2017). For 2018 the state file gives 378,277 (CII 2018). The reference 378,236 is the revised figure in CII 2019 and 2020 Table 3A.1, which is also in the 3A.1 file. The editions disagree on these years:

  | year | ed.2017 | ed.2018 | ed.2019 | ed.2020 | ed.2021 | ed.2022 |
  |---|---|---|---|---|---|---|
  | 2015 | 329,243 | | | | | |
  | 2016 | 338,954 | 338,954 | | | | |
  | 2017 | 359,849 | 359,849 | 359,849 | | | |
  | 2018 | | 378,277 | 378,236 | 378,236 | | |
  | 2019 | | | 405,861 | 405,326 | 405,326 | |
  | 2020 | | | | 371,503 | 371,503 | 371,503 |
  | 2021 | | | | | 428,278 | 428,278 |
  | 2022 | | | | | | 445,256 |

  The crime-head breakdown exists only in the original edition's 3A.2, so revised totals cannot be split by head.
* **Offender relation, 3A.11 and 3A.1:** the sum of states equals All India exactly for every year and category.
* **Offender relation vs rape counts:** `total_cases` in the offender file equals the 3A.2 rape count for every year from 2015 to 2022.
* **District vs state:** district rows sum exactly to NCRB's per-state `Total District(s)` rows in 2015 and 2017–2022. The one exception is 2016's "Total Crimes against Women" column: there NCRB's state total exceeds the sum of districts by a small amount in 28 states/UTs (Assam +114, Maharashtra +83, and so on). The 2016 workbook has an unexplained "Sheet1" that lists these per-state gaps, so this looks like a known NCRB discrepancy. Per-state totals from the district files match 3A.2 exactly for 2016, 2017 and 2019–2022. The exceptions are 2015 Bihar (−712) and Karnataka (+12), which is why the district file was not used for 2015's main heads, and 2018 Assam (+11), where the file notes "clarification on district data pending from Assam".

## Gaps and caveats
* **The 354 sub-heads** (sexual harassment, disrobe, voyeurism, stalking) are published state-wise only for 2015 and 2016. The 2017–2022 CII Table 3A.2 reports only the 354 total, split by age. For 2017–2022 these sub-heads are **not available** from CII tables, so they are left out.
* **POCSO (girl victims)** is included in Crime against Women only from 2017. Before 2017 it was not part of CAW tables, so 2015 and 2016 have no `pocso_girls`. This change also makes totals before and after 2017 not directly comparable. From 2017 NCRB also moved POCSO-related child rape out of IPC rape, which lowered the rape figures (38,947 in 2016 vs 32,559 in 2017).
* **Custodial rape by type of custody** (police, public servant, armed forces, jail/remand home, hospital) is available from 3A.11 for 2017–2022 only. For 2015 there are only totals: custodial rape (95 All-India), split into gang rape and other, from the district-file state totals. For 2016 there is only "Custodial Rape (Sec. 376C IPC)" (10), which NCRB footnotes as "may include rapes in police station/jail/hospital". No state-wise custody-type table was published for 2015 or 2016. 3A.11 also has a column labelled "Other Custodial Rapes" under the "Other than custodial rape (376(2))" group. It is kept under its NCRB name in `ncrb_rape_sectionwise_*`, but because its meaning is ambiguous it was not given a custody_type.
* **Offender relation categories change over time.** For 2011–2013 they are known total / parents and close family / relatives / neighbours / other known, with no "unknown" and no total-cases figure. 2014 has a finer split of known offenders. 2015–2016 add live-in partner/ex-husband and promise-to-marry, plus "unknown". From 2017 NCRB uses only three buckets: family members; family friends/neighbours/employer/other known; friends/online friends/live-in partners/separated husband. `relation_std` keeps these distinct and does not force them into one scheme. NCRB's percentage column was dropped.
* **Jammu & Kashmir** before 2020 includes Ladakh. Ladakh appears from 2020.
* **Dadra & Nagar Haveli and Daman & Diu:** before 2020 these were separate UTs. They are summed into the merged UT (addition of NCRB figures). In the district file the districts keep their own names under the merged UT. Non-additive 3A.1 metrics (rates, population) for the separate pre-2020 UTs were dropped.
* **Andhra Pradesh and Telangana:** Telangana appears from 2014, so the 2011–2013 offender rows have 35 states/UTs.
* **2019 West Bengal:** NCRB notes that WB 2019 data was not received in time and that 2018 figures were used (3A.2 2019 footnote).
* **District files** include police-district units that are not geographic districts, such as GRP/Railways, CID, Crime Branch and STF, exactly as NCRB lists them. District names are NCRB's spellings, and their boundaries change between years. They have not been matched to the GeoJSON in `data/geo/`.
* **Labelling fixes:** NCRB labelling slips in the source files were corrected as follows.
  * **2017 district file:** the Uttarakhand block is headed "State : Uttar Pradesh" and the Puducherry block is headed "UT : Lakshadweep". These were relabelled after checking the district names (Almora…, Karaikal…).
  * **2017 and 2018 district file titles:** both say "…2017", and the 2021 file's title says "2020". Their state totals match the correct year's 3A.2, so the data is for the year in the file name.
  * **Typos kept verbatim:** "Sec. 336 IPC", "Sexual Harrassment" and "Protection of Women from Domestic Offences Act" (2019) are NCRB's own spellings.
* **2023–2024:** excluded on the coordinator's instruction; see the note at the top.

## Transformations (the only arithmetic applied)
1. Summing the two pre-2020 UTs (D&N Haveli + Daman & Diu) into the merged UT.
2. 2015 All-India values for the sub-heads that come from the district file are the sum of state `Total District(s)` rows, because that file has no All-India row. They are flagged in `source`. The 2015 main heads use NCRB's published All-India row.
3. The 2016 and 2019 3A.2 tables and the 2011–2014 Table 5.4 were extracted from text PDFs with pdfplumber. Two wrapped rows in the 2014 PDF (Arunachal Pradesh and the All-India row) were re-joined before parsing. Every PDF-parsed year passes the state-sum = All-India check.
