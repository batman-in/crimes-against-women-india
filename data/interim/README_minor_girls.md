# Crimes against minor girls (under 18): NCRB data

Built by `build_minor_girls.py`. Raw inputs are in `data/raw/minor_girls/`. Every number comes from an NCRB primary table. Nothing is estimated or imputed. The only derived values are:

- sums of published sub-heads (flagged `derived_sum=True`),
- state and All-India totals built from district rows (`state_value_basis`),
- merges of former units into current UTs (explained below).

## Output files

| File | Rows | Content |
|---|---|---|
| `minor_girls_state.csv` | 14,852 | `year,state_ut,crime_head,crime_head_std,count,victim_sex,measure,state_value_basis,derived_sum,source,source_file`. Cases registered, state/UT-wise, plus `state_ut="All India"`. There are no Total (States) or Total (UTs) rows. |
| `minor_girls_district.csv` | 348,967 | Same fields plus `district` and `special_police_unit`. Special police units are rows such as GRP/Railway, CID, Crime Branch and STF, which NCRB lists as if they were districts. |
| `minor_girls_allindia_victims.csv` | 658 | All-India only, by crime head, 2014-2024: `cases`, `victims_girls`, `victims_boys`, `victims_transgender`, `victims_total`. This is the only table with true girl **victim** counts across all crime heads. |
| `minor_girls_rape_victims_age.csv` | 11,143 | `year,state_ut,age_group,victims,victim_sex,table,source_file`. Contains three different tables; see topic 4. |
| `minor_girls_validation.csv` | 517 | All checks, including the rows that matched exactly. |

### `victim_sex` values

- `girl`: the head is female-only by law (IPC 376, 354, 366, 366A, 366B, 509), or NCRB publishes a separate "Girls" sub-head. Examples of the second kind: POCSO sections from 2017, and selling/buying of minors from 2017.
- `all`: NCRB does not split the head by sex. This applies to POCSO totals before 2017, child marriage, foeticide, infanticide, kidnapping total, and selling/buying before 2017. Girl victims for these heads exist **only at All-India level**, in `minor_girls_allindia_victims.csv`.
- Counts in the state and district files are **cases**, not victims. For the POCSO girl sub-heads, a case is classed by the victim's sex.

### Geography

- Names follow current usage: Odisha, Delhi, Jammu & Kashmir, Ladakh, and "Dadra & Nagar Haveli and Daman & Diu".
- Before 2020, D&N Haveli and Daman & Diu were separate. Their figures are summed into the merged UT.
- At district level, Leh and Kargil are assigned to Ladakh in every year.
- At state level, Jammu & Kashmir before 2020 still includes Leh and Kargil. Ladakh has its own state rows only from 2020.
- Telangana appears from 2014.

## Coverage by topic

1. **POCSO with girl victims, state-wise (2017-2024).**
   - Heads: `pocso_total` (girl = sum of the girl sub-heads), `pocso_penetrative` (Sec 4 & 6), `pocso_sexual_assault` (Sec 8 & 10), `pocso_harassment` (Sec 12), `pocso_pornography` (Sec 14 & 15), `pocso_unnatural_377` (2017-2023 only) and `pocso_other` (Sec 17-22).
   - POCSO totals with `victim_sex=all` cover 2014-2024. Sections without a sex split cover 2014-2015 (Sec 4+6 and Sec 8+10 are summed). 2016 has the total only.
   - District-level data is available for the same years.
2. **Other crimes against girl children, state and district.**
   - `rape_minor`, `procuration_minor_girls`, `selling_minor_girls`, `buying_minor_girls`, `child_marriage`, `foeticide`, `infanticide` and `total_crimes_children` cover 2001-2024. Selling and buying are girl-specific in 2001-2013 and 2017-2024; in 2014-2016 they are all minors.
   - `kidnap_girls` (Sec 366, to compel marriage) covers 2014, 2015 and 2017-2024. It is missing from the 2016 district file and from the 2001-2013 source.
   - Also included: `assault_modesty_minor`, `insult_modesty_minor` and `importation_girls` (2014-2024); `attempt_rape_minor` and `murder_with_rape_pocso` (2017-2024); `sexual_harassment_minor` (2014, 2015, 2024); `cyber_child_sexual_material` (2017-2024).
   - Infanticide: 2001-2012 has no infanticide column; the 2001-2012 "Murder" column was not used.
3. **District-wise data** runs from 2001 to 2024.
   - 2001-2013 comes from Kaggle `rajanand/crime-in-india`, file 03. It has no POCSO data and no sex split beyond heads that are female-only by law.
   - 2014-2024 comes from NCRB XLSX files, with 666 to 941 units per year.
4. **Victims by age.** The age file contains three separate tables:
   - **CII Table 3A.3** (2016-2024, state-wise): rape victims under Sec 376 IPC by age group (below 6, 6-12, 12-16, 16-18, 18-30, 30-45, 45-60, 60+). **Caveat:** from 2017, child rapes are counted under POCSO. The child age bands in 3A.3 therefore hold only the few cases booked under IPC 376 alone (1,017 child victims in 2022).
   - **CII Table 4A.9** (2017-2024, state-wise): age profile of child victims of POCSO Sec 4 & 6, for girls, boys and all. The age bands are below 6, 6-12, 12-16 and 16-18. **Use this table for the age of girls who were raped.** Its All-India girl totals equal the Sec 4 & 6 girl victims exactly for every year.
   - **2001-2010 (Kaggle rajanand, file 20):** different age bands (up to 10, 10-14, 14-18, 18-30, 30-50, 50+). There is no All-India row in this file, so All India is the sum of states.

## Validation

- **District-derived All-India cases vs NCRB's All-India crime-head table (2014-2024):** exact match for 2017-2024 on every POCSO girl sub-head, `rape_minor`, `kidnap_girls` and `procuration_minor_girls`. Differences:
  - 2020 foeticide: -21 (109 vs 130).
  - 2024 total crimes against children: -406 (0.2%).
  - 2015: -35 on `kidnap_girls` and -33 on the total.
  - 2016: +5 or +6 on some heads.
  - 2014-2015 POCSO: the district files hold POCSO-only cases (8,904 in 2014). NCRB's later 2014-2019 table re-counts all POCSO cases, including those read with IPC sections (34,449). Because of this, **pre-2017 POCSO figures cannot be compared with 2017 onwards.** Child rape before 2017 sits partly under `rape_minor`.
- **Sum of states = published All India** in every CII 3A.3 and 4A.9 table, 2016-2024: 0 differences.
- **District sums vs NCRB state total rows:** 50 of 14,443 differ.
  - Bihar 2017: NCRB's state total row is lower than the sum of its district rows. The district sum matches the All-India figure, so district sums are used for 2014-2024.
  - Delhi 2007 and Assam 2009 have incomplete district rows in rajanand, so 2001-2013 uses NCRB's state TOTAL rows.
  - Chhattisgarh 2001 and Assam 2009 have no TOTAL row; district sums are used and flagged.

## Gaps

- State-wise **victim** counts by sex exist only as POCSO Sec 4 & 6 age-profile victims (4A.9, 2017-2024). For other heads, the state data holds case counts only.
- There are no state-wise girl/boy splits of POCSO before 2017.
- State-wise rape victims by age are missing for 2011-2015. CII 2011-2015 volumes are not on ncrb.gov.in (only snapshots). The data.gov.in resources ("Age-group-wise Victims of (Incest, Other and Total) Rape Cases") returned HTTP 403 without an API key.
- District-wise victim age is not published.
- dataful.in dataset 21841 (state x crime head x gender, 2001-2023) is a paid product and was not used.

## Sources

- NCRB Crime in India, Additional Tables: https://www.ncrb.gov.in/crime-in-india-additional-table.html?year=YYYY . Switch the site language to English first. The index of every table and its URL is saved as `raw/minor_girls/ncrb_additional/_ncrb_additional_tables_index.csv`. Tables used:
  - "District-wise Crime against Children" (2014-2024 XLSX)
  - "Gender-wise Victims under Crimes against Children" (2014-2019 and 2020-2024 XLSX)
- NCRB Crime in India Volume I PDFs, 2016-2024: https://www.ncrb.gov.in/crime-in-india-year-wise.html?year=YYYY . Tables 3A.3 and 4A.9 were extracted with pdfplumber. The page PDFs and extracted text are in `raw/minor_girls/ncrb_cii_pages/`. Volume URLs:
  - 2024: https://www.ncrb.gov.in/uploads/files/11CrimeinIndia2024-VolumeI.pdf
  - 2023: https://www.ncrb.gov.in/uploads/files/1CrimeinIndia2023PartI1.pdf
  - 2022: https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/custom/1701607577CrimeinIndia2022Book1.pdf
  - 2021: https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/custom/1696831798CII2021Volume1.pdf
  - 2020: https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/16959885631653645869CII2020Volume1.pdf
  - 2019: https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/custom/1653730573_CII%202019%20Volume%201.pdf
  - 2018: https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/custom/1653734481_Crime%20in%20India%202018%20-%20Volume%201_3_0_0.pdf
  - 2017: https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/16959893381653885627CrimeinIndia2017-Volume100.pdf
  - 2016: https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/custom/1653886924_Crime%20in%20India%20-%202016%20Complete%20PDF%20291117.pdf
- Kaggle `rajanand/crime-in-india` (NCRB data via data.gov.in), files `03_District_wise_crimes_committed_against_children_2001_2012.csv`, `..._2013.csv` and `20_Victims_of_rape.csv`.

## Other caveats

- NCRB counts cases under the "principal offence" rule. From 2017, POCSO cases read with IPC 376/354/509 are counted under POCSO, not IPC. This is why `rape_minor` falls sharply from 2017 to 2019 and later.
- 2024 figures mix IPC and BNS: the new criminal laws took effect on 1 July 2024.
- 2019 district file: NCRB notes that data was not received from some units.
- Nagaland has "clarifications pending" in some CII years.
- The 2023 child marriage count (6,038) is as published and is much higher than in other years.
- Railway, CID and similar units appear as separate district rows. Filter on `special_police_unit` before mapping.
