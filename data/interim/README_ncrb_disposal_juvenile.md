# NCRB: what happened to the accused, and juveniles, in crimes against women

Tidy, long-format CSVs built from NCRB *Crime in India* (CII) tables for the dashboard. The
columns are `year, state_ut, crime_head, crime_head_std, measure, count, unit, table, source, note`.

| File | Rows | Years | Content |
|---|---|---|---|
| `ncrb_disposal_persons_2001_2024.csv` | 67,127 | 2001-2010, 2014-2024 | Persons arrested, charge-sheeted, convicted, acquitted, discharged and so on (unit = persons) |
| `ncrb_disposal_police_cases_2014_2024.csv` | 18,368 | 2014-2024 | Police disposal of cases: reported, charge-sheeted, final reports, pending investigation, charge-sheeting rate |
| `ncrb_disposal_court_cases_2014_2024.csv` | 16,456 | 2014-2024 | Court disposal of cases: sent for trial, trials completed, convicted, acquitted, discharged, pending, conviction rate, pendency % |
| `ncrb_juvenile_caw_2014_2024.csv` | 7,474 | 2014-2024 | Children in conflict with law, for crime-against-women heads: cases registered against juveniles, and juveniles apprehended by age group and sex |
| `ncrb_disposal_validation.csv`, `ncrb_juvenile_validation.csv` | 25,011 / 1,090 | | One row per validation check, with the result |

There is no `ncrb_punishment_*` file. See **Punishment / sentence type** below.

Rebuild with `python data/interim/ncrb_build/run_disposal_juvenile.py`, or add `--fetch` to re-download first.
The scripts are `fetch_ncrb_catalog.py`, `fetch_disposal_juvenile.py`, `fetch_volume_pages.py`, `build_disposal.py`,
`disposal_2014_2015.py`, `build_juvenile.py` and `ncrb_cells.py`, all in `data/interim/ncrb_build/`.
Raw files are in `data/raw/ncrb_cii_tables/<year>/`, and every file's source URL is in `manifest.json`.
The catalogues of the NCRB pages are in `table_content_catalog*.json` and `additional_tables_catalog.json`.
The Kaggle file is `data/raw/rajanand_crime-in-india/43_Arrests_under_crime_against_women.csv`.

## Where the tables are on the NCRB site

* The chapter-3A (women) and chapter-5A (juveniles) tables for 2016-2024 are on the **Contents/Tables** page,
  `https://www.ncrb.gov.in/crime-in-india-table-content?year=YYYY`. They are not on the Additional Tables page,
  which for these chapters lists only the 34-metropolitan-city "B" tables.
  To get the page in English, POST `lang=en&slug=...&_csrf=<csrf-token meta>` to `/api/language/set`
  (form-encoded, with the `X-Requested-With: XMLHttpRequest` header).
* On that page each table title links to the PDF, and the `[ n KB ]` links after it are the PDF and XLSX.
  XLSX is used wherever it exists and opens. There are no XLSX files for 2016, for 2019 3A.5-3A.8, 3A.10, 5A.2 and 5A.3,
  or for 2020 3A.6, 3A.8 and 3A.10 (the listed links return 404), so those were parsed from the PDFs.
* Three tables are not linked as separate files:
  * The 2023 **5A.4A** (IPC juveniles) is on the server at `https://www.ncrb.gov.in/uploads/files/TABLE5A4A.xlsx`, but the page does not link it.
  * The 2022 and 2024 **SLL 5A.4 (5A.4B)** tables were cut out of the full CII volumes: CII 2022 Book 1, PDF pages 503-506, and CII 2024 Volume II, PDF pages 39-42.
    `fetch_volume_pages.py` saves only those pages.

## Tables used

| Topic | 2014-2015 (old numbering) | 2016-2024 |
|---|---|---|
| Police disposal of cases | 5.5 (All India, by crime head) | 3A.5 (All India, by crime head), 3A.6 (State/UT) |
| Court disposal of cases | 5.6 (All India, by crime head) | 3A.7 (All India, by crime head), 3A.8 (State/UT) |
| Disposal of persons | 5.7 (police), 5.8 (courts): All India, by crime head | 3A.9 (All India, by crime head), 3A.10 (State/UT) |
| Juveniles, cases (State/UT x crime head) | 10.2 (IPC), 10.3 (SLL) | 5A.2 (IPC/BNS), 5A.3 (SLL); none for 2016 |
| Juveniles apprehended (All India x crime head x age x sex) | 10.4 | 5A.4 (2016-2019), 5A.4A IPC and 5A.4B SLL (2020-2024) |

Kaggle `rajanand/crime-in-india` `43_Arrests_under_crime_against_women.csv` (NCRB data) covers 2001-2010
state-wise persons data for 12 crime groups. Rows where `Sub_Group_Name` contains an unquoted comma were re-joined.

Full per-file URL list: see the end of this file.

## Coverage actually obtained

| | State/UT-wise | All India by crime head |
|---|---|---|
| Persons (arrested ... acquitted) | 2001-2010 (Kaggle), 2016-2024 | 2001-2010 (Kaggle; no All-India row), 2014-2024 |
| Police disposal of cases | 2016-2024 (total crime against women only) | 2014-2024 |
| Court disposal of cases | 2016-2024 (total crime against women only) | 2014-2024 |
| Juveniles: cases against juveniles | 2014, 2015, 2017-2024 | 2014, 2015, 2017-2024 |
| Juveniles apprehended (persons), age and sex | — (not published state-wise by crime head) | 2014-2024 |

The State/UT tables (3A.6, 3A.8, 3A.10) give only the **total** for crimes against women. Breakdowns by crime head
(rape, 498A, 354, POCSO ...) exist **only at All-India level**.

### Measures

*Persons* (`unit = persons`): `arrested`, `chargesheeted`, `convicted`, `acquitted`, `discharged`, each also with
`_male`, `_female` and `_transgender` (transgender from 2021).
* 2014-2015 (Tables 5.7 and 5.8) add `released_before_trial` (released by police or magistrate before trial for want of evidence),
  `pending_investigation[_start]`, `total_under_trial`, `compounded`, `withdrawn`, `trials_completed`,
  `pending_trial[_start]`, and the `_custody` and `_bail` splits. NCRB prints only Male and Female there. The totals were added as
  male + female, and `pending_trial` / `pending_investigation` as custody + bail. The `note` column flags these rows.
* Kaggle 2001-2010 adds `trials_completed`, `pending_trial` (in custody or on bail at year end), `pending_trial_start`,
  `total_under_trial`, `released_before_trial`, `compounded_or_withdrawn`, `pending_investigation[_start]`.
* **2016-2024 NCRB publishes no persons-level `trials_completed` or `pending_trial`**. Only cases-level pendency exists.

*Police disposal of cases* (`unit = cases`, rates in `percent`): `cases_reported`, `cases_pending_investigation_start`,
`cases_reopened`, `cases_for_investigation`, `cases_transferred`, `cases_withdrawn_investigation`,
`cases_not_investigated_157_1_b`, `cases_fr_false`, `cases_fr_mistake_fact_law_civil`, `cases_fr_non_cognizable`,
`cases_fr_true_insufficient_evidence` (final report "true but insufficient evidence / untraced"), `cases_abated_investigation`,
`cases_final_report_total`, `cases_chargesheeted` (plus `_prev_year` / `_current_year`), `cases_disposed_police`,
`cases_quashed_investigation`, `cases_stayed_investigation`, `cases_pending_investigation`, `chargesheeting_rate`,
`pendency_pct_investigation`.

*Court disposal of cases*: `cases_pending_trial_start`, `cases_sent_for_trial`, `cases_for_trial`, `cases_abated_court`,
`cases_withdrawn_prosecution`, `cases_compounded`, `cases_plea_bargaining`, `cases_quashed`,
`cases_disposed_without_trial`, `cases_stayed_record_room`, `cases_convicted` (plus `_prev_year` / `_current_year`),
`cases_acquitted`, `cases_discharged`, `cases_trials_completed`, `cases_disposed_courts`, `cases_pending`
(pending trial at year end), `conviction_rate`, `pendency_pct`. For 2014-2016 NCRB prints `cases_acquitted_or_discharged`
as one column, and for 2014-2015 `cases_compounded_or_withdrawn`.

*Juveniles*: `cases_against_juveniles` (unit = cases; 5A.2, 5A.3, 10.2, 10.3, and the "cases reported" column of 5A.4),
`juveniles_apprehended` (unit = persons) with `_boys` / `_girls` / `_transgender`, and the age groups
`juveniles_age_below_12`, `juveniles_age_12_16`, `juveniles_age_16_18`, each with the sex splits.
NCRB's age bands are below 12, 12 to below 16, and 16 to below 18. Transgender is reported from 2021. 2014-2016 have no cases column in 10.4 / 5A.4.
**The State/UT juvenile tables count cases, not juveniles.** NCRB publishes juveniles apprehended by crime head only for All India.

`crime_head_std` uses the dashboard keys, plus the sub-keys already used in `ncrb_state_*` files
(`rape_minor`, `assault_minor`, `insult_minor`, `attempt_rape_minor`, `kidnap_marriage`, `import`, `disrobe`, `voyeurism`,
`pocso_penetrative`, `pocso_sexual_assault`, `pocso_harassment`, `pocso_pornography`, `procuration_minor_girls`,
`selling_minor_girls`, `buying_minor_girls`, `attempt_acid_attack`, `total_ipc`, `total_sll`). It is empty where nothing
fits. For the juvenile file, POCSO is left empty because the juvenile POCSO counts include boy victims, unlike `pocso_girls`
in the women chapter. The IPC/SLL "Total Cognizable" rows are kept for context.

State names follow the project convention (`common.std_state`). Before 2020, D&N Haveli and Daman & Diu are **summed**
into "Dadra & Nagar Haveli and Daman & Diu", and their rates recomputed with NCRB's own formula (flagged in `note`).
"Total (States)" and "Total (UTs)" rows are dropped. 2024 values are the combined IPC + BNS figures, as printed in 3A.5-3A.10.

## Headline All-India figures, 2024 (total crimes against women)

| Measure | 2024 | 2023 | 2022 |
|---|---|---|---|
| Persons arrested | 376,952 | 416,519 | 455,745 |
| Persons charge-sheeted | 602,307 | 667,940 | 623,785 |
| Persons convicted | 72,126 | 53,750 | 54,602 |
| Persons acquitted | 201,350 | 219,265 | 170,276 |
| Persons discharged | 12,411 | 11,271 | 11,964 |
| Cases sent for trial | 336,609 | 350,937 | 351,183 |
| Cases convicted / acquitted / discharged | 45,832 / 123,340 / 9,180 | 39,630 / 138,718 / 7,644 | 38,136 / 105,080 / 7,685 |
| Cases pending trial at year end | 2,432,527 | 2,303,657 | 2,184,769 |
| Conviction rate (cases) | 25.7% | 21.3% | 25.3% |
| Pendency % (courts) | 92.1% | 90.8% | 92.3% |
| Charge-sheeting rate (police) | 77.2% | 77.6% | 75.8% |
| Juveniles apprehended: rape / POCSO (all child victims) | 1,204 / 3,563 | 1,085 / 2,807 | 1,239 / 2,572 |

In 2024, 473 juveniles were apprehended for assault (s.74 BNS / 354 IPC only), 575 for kidnapping to compel marriage,
185 for sexual harassment and 133 for stalking.

## Punishment / sentence type

**NCRB Crime in India does not publish the type or length of sentence** (death, life, 10+ years, fine only and so on)
for crimes against women, or for any crime. The court tables stop at convicted, acquitted and discharged.
A full-text search of CII 2022 Books 1-2 and CII 2024 Volumes I-III found no sentence-type table. The only "Punishment"
matches are the section names in Table 3A.11. Chapter 18 (court disposal) has only duration of trials (18A.5) and period
of pendency (18A.7, 18A.8). Nothing was substituted. Sentence data would need another source, such as court records or
Prison Statistics India (which counts convicts by sentence period, but not cross-tabulated with crimes against women), and is out of scope here.

## Validation (see the `*_validation.csv` files; 26,101 checks, 0 failures)

* **States sum to All India**: every measure of 3A.6, 3A.8 and 3A.10 (2016-2024; 484 checks), and every head of 5A.2, 5A.3,
  10.2 and 10.3 (136 checks). All pass, with D&N Haveli + Daman & Diu summed before 2020 and J&K and Ladakh as printed.
* The crime-head table total equals the State/UT table All-India figure (3A.5 vs 3A.6, 3A.7 vs 3A.8, 3A.9 vs 3A.10; 520 checks).
  Afterwards only the State/UT version of the total is kept, so it is not duplicated.
* Total IPC + total SLL = total crime against women in the crime-head tables (444).
* Courts: convicted + acquitted + discharged = trials completed (889), cases for trial − disposed = pending (889), and the printed
  conviction rate matches convicted / trials completed within ±0.1 (874).
* Police: final reports + charge-sheets + not investigated + transferred = disposed (816).
* Persons: male + female (+ transgender) = total (4,045; the derived 2014-15 totals are excluded from this check);
  2014-15 convicted + acquitted + discharged = trials completed, under trial − disposed = pending, and pending investigation at start + arrested − released − charge-sheeted = pending at end (240 checks);
  Kaggle convicted + acquitted = trials completed, under trial at start + charge-sheeted = total under trial, total under
  trial − trials completed − compounded/withdrawn = pending trial, and crime heads sum to "Total Crime Against Women" (15,810).
* Juveniles: boys + girls (+ transgender) = total (708), the age groups sum to the total (177), and the State/UT All-India
  cases equal the "cases reported" column of 5A.4 (69).
* Parser sanity: every crime head has the full set of measures in every year, and no `crime_head_std` maps to two heads in one year and table.

## Caveats

* **Year-of-disposal counts.** Persons convicted or acquitted, and cases disposed, in year *t* are mostly from cases
  registered in earlier years (for example, cases convicted in 2024 "out of cases from previous year" = 40,422 of 45,832).
  Do not divide convictions by the same year's arrests and call it a conviction rate. NCRB's conviction rate is convicted ÷ trials
  completed in that year.
* **Persons and cases differ.** One case can have several accused. Persons charge-sheeted can exceed persons arrested
  (602,307 against 376,952 in 2024), because charge-sheets are also filed against people not arrested and against people
  arrested in earlier years.
* **Formula changes.** The charge-sheeting rate was charge-sheeted ÷ (charge-sheeted + FR true) for 2014-2016, and from 2017 it is
  charge-sheeted ÷ disposed by police. The column set of the police and court tables changed in 2017.
  The 2014-2015 data cover fewer heads (no POCSO or cyber rows).
* **2024 crime-head structure.** 354A-D (sexual harassment, disrobe, voyeurism, stalking) became separate top-level heads, so the
  2024 `assault` covers s.74 BNS / 354 only and is not comparable with earlier years. In 2024 `kidnap` (K&A of women,
  21.1-21.5) excludes kidnapping to compel marriage and procuration, which are listed separately.
* 2020 court numbers are depressed by COVID-19 court closures.
* NCRB notes that some states' data were carried over from an earlier year. For example, in 2019 West Bengal's figures are its 2018 figures.
  These are kept as printed.
* Pre-2019 "Jammu & Kashmir" includes Ladakh.
* The juvenile State/UT tables for 2014-2015 print some sub-heads that are not used here (for example the rape sub-types).
  2015 juvenile dowry-death cases (237) are as printed by NCRB, and the states sum to that figure.
* 2016 Table 3A.9 page 2 swaps the serial numbers of Acid Attack and Cruelty. Rows were matched by name, not number.
* Counts come as published. Nothing is estimated. The only derived values are the flagged sums (male + female,
  custody + bail, the merged D&N Haveli + Daman & Diu, and its recomputed rates).

## Gaps

* **2011-2013.** CII has no crimes-against-women-specific disposal tables (chapter 5 then had only incidence tables).
  Disposal of rape, molestation and other heads exists only inside the general IPC tables (4.1, 4.9, 12.10, 12.12, All India), which were not extracted.
  Juveniles 2011-2013 (chapter 10: 10.8, 10.9) were also not extracted.
* **2014-2015** disposal is All India only. There is no State/UT disposal for crimes against women in those editions.
* **2016** has no State/UT juvenile tables (5A.2 and 5A.3 are not on the site), and 5A.4 2016 has no cases column.
* **2001-2010 (Kaggle)** has no All-India row. It was not derived. 2008 lacks the "Total Crime Against Women" group in the source.
* No persons-level pending trial or trials completed for 2016-2024. No State/UT breakdown by crime head for disposal.
* No sentence-type or punishment-level data (see above).

## Source files (year, table, local file, URL)

| Year | Table | Local file | URL |
|---|---|---|---|
| 2014 | 10.2 | table-10.2_2014.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/table-10.2_2014.pdf |
| 2014 | 10.3 | table-10.3_2014.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/table-10.3_2014.pdf |
| 2014 | 10.4 | table-10.4_2014.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/table-10.4_2014.pdf |
| 2014 | 5.5 | Table-5.5_2014.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-5.5_2014.pdf |
| 2014 | 5.6 | Table-5.6_2017.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-5.6_2017.pdf |
| 2014 | 5.7 | Table-5.7-2014.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-5.7-2014.pdf |
| 2014 | 5.8 | Table-5.8_2014.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-5.8_2014.pdf |
| 2015 | 10.2 | table-10.2_2015.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/table-10.2_2015.pdf |
| 2015 | 10.3 | table-10.3_2015.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/table-10.3_2015.pdf |
| 2015 | 10.4 | table-10.4_2015.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/table-10.4_2015.pdf |
| 2015 | 5.5 | Table-5.5_2015.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-5.5_2015.pdf |
| 2015 | 5.6 | Table-5.6_2015.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-5.6_2015.pdf |
| 2015 | 5.7 | Table-5.7_2015.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-5.7_2015.pdf |
| 2015 | 5.8 | Table-5.8_2015.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-5.8_2015.pdf |
| 2016 | 3A.10 | 1679983631Table3A10.pdf | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/1679983631Table3A10.pdf |
| 2016 | 3A.5 | 1679982966Table3A5.pdf | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/1679982966Table3A5.pdf |
| 2016 | 3A.6 | 1679983444Table3A6.pdf | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/1679983444Table3A6.pdf |
| 2016 | 3A.7 | 1679983481Table3A7.pdf | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/1679983481Table3A7.pdf |
| 2016 | 3A.8 | 1679983519Table3A8.pdf | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/1679983519Table3A8.pdf |
| 2016 | 3A.9 | 1679983576Table3A9.pdf | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/1679983576Table3A9.pdf |
| 2016 | 5A.4 | table-5A.4-2016.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/table-5A.4-2016.pdf |
| 2017 | 3A.10 | Table-3A.10_1.xlsx | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-3A.10_1.xlsx |
| 2017 | 3A.5 | Table-3A.5_1.xlsx | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-3A.5_1.xlsx |
| 2017 | 3A.6 | Table-3A.6_1.xlsx | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-3A.6_1.xlsx |
| 2017 | 3A.7 | Table-3A.7_1.xlsx | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-3A.7_1.xlsx |
| 2017 | 3A.8 | Table-3A.8_1.xlsx | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-3A.8_1.xlsx |
| 2017 | 3A.9 | Table-3A.9_1.xlsx | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-3A.9_1.xlsx |
| 2017 | 5A.2 | table-5A.1_2-2018.xlsx | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/table-5A.1_2-2018.xlsx |
| 2017 | 5A.3 | table-5A.1_3-2018.xlsx | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/table-5A.1_3-2018.xlsx |
| 2017 | 5A.4 | table-5A.1_4-2018.xlsx | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/table-5A.1_4-2018.xlsx |
| 2018 | 3A.10 | Table-3A.10_0.xlsx | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-3A.10_0.xlsx |
| 2018 | 3A.5 | Table-3A.5_0.xlsx | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-3A.5_0.xlsx |
| 2018 | 3A.6 | Table-3A.6_0.xlsx | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-3A.6_0.xlsx |
| 2018 | 3A.7 | Table-3A.7_0.xlsx | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-3A.7_0.xlsx |
| 2018 | 3A.8 | Table3A.8_0.xlsx | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table3A.8_0.xlsx |
| 2018 | 3A.9 | 1679037858Table3A90.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/1679037858Table3A90.xlsx |
| 2018 | 5A.2 | table-5A.2_0-2018.xlsx | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/table-5A.2_0-2018.xlsx |
| 2018 | 5A.3 | table-5A.3_0-2018.xlsx | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/table-5A.3_0-2018.xlsx |
| 2018 | 5A.4 | table-5A.4_0-2018.xlsx | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/table-5A.4_0-2018.xlsx |
| 2019 | 3A.10 | Table-3A.10_2.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-3A.10_2.pdf |
| 2019 | 3A.5 | Table-3A.5_2.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-3A.5_2.pdf |
| 2019 | 3A.6 | Table-3A.6_2.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-3A.6_2.pdf |
| 2019 | 3A.7 | Table-3A.7_2.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-3A.7_2.pdf |
| 2019 | 3A.8 | Table-3A.8_2.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/Table-3A.8_2.pdf |
| 2019 | 3A.9 | 1681278820Table3A9.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/custom/1681278820Table3A9.xlsx |
| 2019 | 5A.2 | table-5A.2_2.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/table-5A.2_2.pdf |
| 2019 | 5A.3 | table-5A.3_2.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/table-5A.3_2.pdf |
| 2019 | 5A.4 | 1681716334Table5A4.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/custom/1681716334Table5A4.xlsx |
| 2020 | 3A.10 | TABLE-3A.10.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/TABLE-3A.10.pdf |
| 2020 | 3A.5 | 1680767206TABLE3A5.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/1680767206TABLE3A5.xlsx |
| 2020 | 3A.6 | TABLE-3A.6.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/TABLE-3A.6.pdf |
| 2020 | 3A.7 | 1680767275TABLE3A7.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/1680767275TABLE3A7.xlsx |
| 2020 | 3A.8 | TABLE-3A.8.pdf | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/TABLE-3A.8.pdf |
| 2020 | 3A.9 | 1680767421TABLE3A9.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/1680767421TABLE3A9.xlsx |
| 2020 | 5A.2 | table-5A.2-2020.xlsx | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/table-5A.2-2020.xlsx |
| 2020 | 5A.3 | table-5A.3-2020.xlsx | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/table-5A.3-2020.xlsx |
| 2020 | 5A.4 | 1680772567TABLE5A4A.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/1680772567TABLE5A4A.xlsx |
| 2020 | 5A.4 | table-5A.5-2020.xlsx | https://www.ncrb.gov.in/uploads/2022/July/11/custom/crime-in-india/table-5A.5-2020.xlsx |
| 2021 | 3A.10 | 1679653180TABLE3A10.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/1679653180TABLE3A10.xlsx |
| 2021 | 3A.5 | 1679652955TABLE3A5.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/1679652955TABLE3A5.xlsx |
| 2021 | 3A.6 | 1679653003TABLE3A6.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/1679653003TABLE3A6.xlsx |
| 2021 | 3A.7 | 1679653050TABLE3A7.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/1679653050TABLE3A7.xlsx |
| 2021 | 3A.8 | 1679653099TABLE3A8.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/1679653099TABLE3A8.xlsx |
| 2021 | 3A.9 | 1679653144TABLE3A9.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/1679653144TABLE3A9.xlsx |
| 2021 | 5A.2 | 1679656177TABLE5A2.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/1679656177TABLE5A2.xlsx |
| 2021 | 5A.3 | 1679656242TABLE5A3.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/1679656242TABLE5A3.xlsx |
| 2021 | 5A.4 | 1679656342TABLE5A4A.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/1679656342TABLE5A4A.xlsx |
| 2021 | 5A.4 | 1679656408TABLE5A4B.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/post/1679656408TABLE5A4B.xlsx |
| 2022 | 3A.10 | 1701935580TABLE3A10.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/custom/1701935580TABLE3A10.xlsx |
| 2022 | 3A.5 | 1701935331TABLE3A5.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/custom/1701935331TABLE3A5.xlsx |
| 2022 | 3A.6 | 1701935389TABLE3A6.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/custom/1701935389TABLE3A6.xlsx |
| 2022 | 3A.7 | 1701935422TABLE3A7.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/custom/1701935422TABLE3A7.xlsx |
| 2022 | 3A.8 | 1701935488TABLE3A8.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/custom/1701935488TABLE3A8.xlsx |
| 2022 | 3A.9 | 1701935526TABLE3A9.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/custom/1701935526TABLE3A9.xlsx |
| 2022 | 5A.2 | 1701944786TABLE5A2.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/custom/1701944786TABLE5A2.xlsx |
| 2022 | 5A.3 | 1701944918TABLE5A3.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/custom/1701944918TABLE5A3.xlsx |
| 2022 | 5A.4 | 1701944943TABLE5A4A.xlsx | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/custom/1701944943TABLE5A4A.xlsx |
| 2022 | 5A.4 | CII2022_Book1_p503-506_Table5A4_SLL.pdf | https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/custom/1701607577CrimeinIndia2022Book1.pdf (pages 503-506) |
| 2023 | 3A.10 | TABLE3A10.xlsx | https://www.ncrb.gov.in/uploads/files/TABLE3A10.xlsx |
| 2023 | 3A.5 | TABLE3A5.xlsx | https://www.ncrb.gov.in/uploads/files/TABLE3A5.xlsx |
| 2023 | 3A.6 | TABLE3A6.xlsx | https://www.ncrb.gov.in/uploads/files/TABLE3A6.xlsx |
| 2023 | 3A.7 | TABLE3A7.xlsx | https://www.ncrb.gov.in/uploads/files/TABLE3A7.xlsx |
| 2023 | 3A.8 | TABLE3A8.xlsx | https://www.ncrb.gov.in/uploads/files/TABLE3A8.xlsx |
| 2023 | 3A.9 | TABLE3A9.xlsx | https://www.ncrb.gov.in/uploads/files/TABLE3A9.xlsx |
| 2023 | 5A.2 | TABLE5A2.xlsx | https://www.ncrb.gov.in/uploads/files/TABLE5A2.xlsx |
| 2023 | 5A.3 | TABLE5A3.xlsx | https://www.ncrb.gov.in/uploads/files/TABLE5A3.xlsx |
| 2023 | 5A.4 | TABLE5A4A.xlsx | https://www.ncrb.gov.in/uploads/files/TABLE5A4A.xlsx |
| 2023 | 5A.4 | TABLE5A4B.xlsx | https://www.ncrb.gov.in/uploads/files/TABLE5A4B.xlsx |
| 2024 | 3A.10 | TABLE3A102.xlsx | https://www.ncrb.gov.in/uploads/files/TABLE3A102.xlsx |
| 2024 | 3A.5 | TABLE3A51.xlsx | https://www.ncrb.gov.in/uploads/files/TABLE3A51.xlsx |
| 2024 | 3A.6 | TABLE3A61.xlsx | https://www.ncrb.gov.in/uploads/files/TABLE3A61.xlsx |
| 2024 | 3A.7 | TABLE3A71.xlsx | https://www.ncrb.gov.in/uploads/files/TABLE3A71.xlsx |
| 2024 | 3A.8 | TABLE3A81.xlsx | https://www.ncrb.gov.in/uploads/files/TABLE3A81.xlsx |
| 2024 | 3A.9 | TABLE3A91.xlsx | https://www.ncrb.gov.in/uploads/files/TABLE3A91.xlsx |
| 2024 | 5A.2 | TABLE5A21.xlsx | https://www.ncrb.gov.in/uploads/files/TABLE5A21.xlsx |
| 2024 | 5A.3 | TABLE5A31.xlsx | https://www.ncrb.gov.in/uploads/files/TABLE5A31.xlsx |
| 2024 | 5A.4 | CII2024_VolII_p39-42_Table5A4B_SLL.pdf | https://www.ncrb.gov.in/uploads/files/2CrimeinIndia2024-VolumeII.pdf (pages 39-42) |
| 2024 | 5A.4 | TABLE5A4A2.xlsx | https://www.ncrb.gov.in/uploads/files/TABLE5A4A2.xlsx |

Kaggle: https://www.kaggle.com/datasets/rajanand/crime-in-india (file `43_Arrests_under_crime_against_women.csv`).
