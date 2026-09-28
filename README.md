# Crimes Against Women in India: interactive dashboard

An interactive map of crimes against women registered by police in India, drawn from NCRB's
*Crime in India* data. You can zoom from the whole country into a state and its districts, filter by
year, crime type and offender, switch between case counts and rates per 1 lakh women, and switch
between filled areas and a heatmap.

## Project layout

```
data/
  raw/            downloads as received (Kaggle, ADR PDFs, population tables)
  interim/        cleaned tidy CSVs produced by the collection scripts
  geo/            state + district boundaries (TopoJSON), interior points
scripts/
  build_data.py      raw + interim -> web/public/data/*.json   (run after any data change)
  district_match.py  NCRB police-district names -> map districts
  adr/               ADR report parsing (aggregates only, no names)
web/              React + Vite + TypeScript app (MapLibre, Tailwind, shadcn/ui, Recharts)
netlify.toml      Netlify build settings
```

## Run it

```bash
python scripts/parse_ncrb_xlsx.py 2023 2024   # NCRB XLSX -> data/interim (needs openpyxl)
python scripts/build_data.py        # needs pandas; writes web/public/data/
cd web
npm install
npm run dev                         # http://localhost:5173
npm run build                       # production build in web/dist
```

## Deploy to Netlify

`netlify.toml` builds `web/` and publishes `web/dist`. Either connect the repository in the Netlify
UI, or from the project root run `npx netlify deploy --build` (add `--prod` when ready). The data
JSON is committed under `web/public/data/`, so Netlify does not need Python.

## Data sources

| Layer | Source | Coverage |
|---|---|---|
| State-wise cases by crime head | NCRB via Kaggle `ayuxsh/crime-against-women-2001-2025` | 2001–2014 |
| State-wise cases by crime head | NCRB Crime in India Additional Tables (Table 3A.2), `scripts/parse_ncrb_xlsx.py` | 2015–2024, incl. POCSO and under-18 victims |
| District-wise cases | NCRB via Kaggle `rajanand/crime-in-india` (table 42) | 2001–2014, 7 IPC heads |
| District-wise cases | NCRB district-wise crime against women workbooks | 2015–2024, all heads |
| Offender relation to rape victim | NCRB table 21 (Kaggle `rajanand`) to 2010; NCRB Table 5.4 / 3A.4 after | 2001–2024, state level (categories change over time) |
| Custodial rape | NCRB detailed heads; custody type (police, armed forces, public servant, jail, hospital) from 2017 | 2014–2022 |
| Arrests, charge-sheets, trials, convictions | NCRB Tables 3A.5–3A.10 (`data/interim/ncrb_disposal_*`) | National by crime type 2014–2024; state totals 2001–2010, 2016–2024. NCRB publishes no sentence types. |
| Juveniles (under 18) | NCRB chapter 5A (`data/interim/ncrb_juvenile_*`) | Juveniles apprehended by crime type and age, national, 2014–2024; cases against juveniles by state |
| Crimes against minor girls | NCRB crimes-against-children tables (`data/interim/minor_girls_*`) | POCSO 2017–2024; rape of girls, child marriage, foeticide 2001–2024 |
| Female population | Census 2011 PCA; MoHFW population projections (2020) | 2011; 2012–2036 |
| Legislators with declared cases | ADR analyses of election affidavits | 2017, 2018, 2024; 2025 (MLAs only, from ADR's all-India sitting MLAs report); 2023 headline only |
| State boundaries | Survey of India based (`datta07/INDIAN-SHAPEFILES`) | current 36 states/UTs |
| District boundaries | GADM via `geohacker/india` | c. 2010 (≈594 districts) |

See `data/interim/README_*.md` for details on each collected dataset.

## Caveats (also shown in the app)

- **Registered cases, not incidence.** Numbers reflect reporting and police registration as well as crime.
  Higher figures can mean better reporting.
- **2013 break.** The Criminal Law (Amendment) Act 2013 widened the definitions of rape and sexual
  harassment, and NCRB added heads, so figures jump from 2013. Don't read the 2012→2013 rise as a
  real change on its own.
- **National totals.** From 2013 the source repeats the all-India total as State + UT + All-India
  rows. The build uses only the all-India row, because summing all three double-counts.
- **Splits.** Before Telangana (2014) and Ladakh (2020) reported separately, both are shown with
  the figure for their parent state, labelled as undivided. Dadra & Nagar Haveli and Daman & Diu
  share the merged UT's figure from 2020.
- **Districts.** NCRB police districts (commissionerates, rural/urban splits) are folded into
  c. 2010 map districts. Districts created later are counted in their parent. Railway police,
  CID and similar units have no geography and are left off the district map (≈0.6% of volume).
  District totals cover the 7 major IPC heads. District rates use Census 2011 population.
- **2024 (BNS).** From July 2024 the Bharatiya Nyaya Sanhita replaced the IPC; NCRB reports IPC + BNS
  cases together. 2024 lists sexual harassment, disrobing, voyeurism and stalking beside the 354 head
  instead of inside it; the build adds them back so "Molestation" stays comparable.
- **Rates.** 2012 onwards uses MoHFW projected female population; 2001–2011 uses Census 2011.
- **Offender relation.** NCRB publishes it only for rape. "Strangers" is total rape cases minus cases
  where the offender was known.
- **ADR.** These are self-declared pending cases in affidavits, not convictions. Only aggregates
  (by state, party, house and charge) are stored.
- **No pincode level.** No public source publishes crime data below the district.

## Licence

The code (`scripts/`, `web/`) is under the MIT licence; see `LICENSE`. The data comes from the
sources listed above and stays under their own terms. Please cite the original sources (NCRB,
Census of India, MoHFW, ADR) when reusing figures.

Live dashboard: https://crimesagainstwomeninindia.netlify.app
