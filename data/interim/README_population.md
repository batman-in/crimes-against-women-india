# Female population denominators (India)

Built by `build_population.py` (in this folder). Raw inputs are in `data/raw/population/`.

## Files
| File | Rows | Content |
|---|---|---|
| `female_pop_state.csv` | 1,016 | `state_ut, year, female_pop, source`. Year 2011 = Census 2011 PCA (41 rows). Years 2012-2036 = MoHFW projections (39 rows/year). |
| `female_pop_district_2011.csv` | 640 | `state_ut, district, census_code, female_pop, total_pop, state_ut_2011` |

## Sources
1. **Census 2011 PCA, district-wise**: Kaggle `danofer/india-census`, file `india-districts-census-2011.csv`, copied to `raw/population/danofer_india-census/`. It has 640 districts and uses the 2011 census codes. Summed over districts, it gives persons 1,210,854,977, males 623,270,258 and females 587,584,719, which match the final PCA totals.
2. **Projections**: *Population Projections for India and States 2011-2036, Report of the Technical Group on Population Projections* (National Commission on Population, MoHFW, July 2020). PDF from nhm.gov.in: `raw/population/TG_population_projections_2011_2036.pdf`. The script uses **Table 11, "Projected total population by sex as on 1st July"** (mid-year, pp. 82-94). The full parse is in `raw/population/TG_table11_1july_parsed.csv`, with persons for 2011-2036.

## State construction (2011)
- **Telangana** = 10 districts: Adilabad, Nizamabad, Karimnagar, Medak, Hyderabad, Rangareddy, Mahbubnagar, Nalgonda, Warangal, Khammam. The other 13 AP districts form **Andhra Pradesh**.
- **Ladakh** = Leh (Ladakh) + Kargil. The other 20 districts form **Jammu & Kashmir**.
- Helper rows for older crime data: `Andhra Pradesh (undivided, 2011)`, `Jammu & Kashmir (incl. Ladakh, 2011 state)`, and `Dadra & Nagar Haveli and Daman & Diu`. The combined DNH+DD row exists for every year. DNH and Daman & Diu are also kept as separate rows.
- The India total is in the row `India`. **To sum states, exclude the helper rows and `India`.** 37 base units remain.
- Names: Odisha, Uttarakhand, Puducherry, Andaman & Nicobar Islands, and Delhi (census name "NCT of Delhi").

## Validation
- The 2011 state sum and the district sum both equal **587,584,719**. This is the final Census 2011 PCA figure for females; total persons is 1,210,854,977.
- The expected figure **587,447,730 is not the PCA total**. It is the female total *excluding the Mao-Maram, Paomata and Purul sub-divisions of Senapati district, Manipur*. Some Census tables and MoSPI's *Women & Men in India* exclude these sub-divisions (MoSPI gives 587.45 M females and 1,210.57 M persons). The difference is 136,989 females. Manipur excluding these sub-divisions would be 1,417,208 - 136,989 = 1,280,219. This file keeps the full PCA count, which includes Senapati.
- Projections: for each year, the states sum to within ±20,000 of the India row. This is rounding, because the report gives figures in thousands.

## Caveats
- **Projection figures are rounded to the nearest 1,000.** They were multiplied by 1,000 here. They are dated 1 July, not 1 March like the census. Rows for 2024-2036 are also included beyond the 2012-2023 requested.
- The 2011 projection row (1 July 2011) is dropped to avoid a duplicate key with the census row. It is in the raw parse.
- In the projections, the seven NE states other than Assam were projected as one block and split pro-rata by 2011 shares. Goa and the small UTs were projected with exponential growth. Ladakh is a residual: J&K (state) minus J&K (UT).
- The Telangana/AP split uses whole 2011 districts. It ignores the 2014 transfer of seven Khammam mandals (the Polavaram area) to AP. As a result, 2011 Telangana (17.49 M) is slightly above the projection's recast base (17.43 M on 1 July 2011).
- NCRB's published rates may use a slightly different vintage or date of these projections, so small differences from NCRB rates are expected.
- District names follow the census spelling (e.g. "Leh(Ladakh)", "Y.S.R.", "Sri Potti Sriramulu Nellore"). Six names repeat across states (Hamirpur, Bilaspur, Pratapgarh, Aurangabad, Raigarh, Bijapur), so join on `state_ut` + `district` or on `census_code`. The 640 districts are the 2011 boundaries. Districts created after 2011 are not present.
- No values were interpolated or estimated beyond what the sources publish.
