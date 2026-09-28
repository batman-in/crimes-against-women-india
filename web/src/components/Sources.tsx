// Links to every source behind the dashboard, so anyone can check a figure.

const NCRB_YEAR = (y: number) => `https://www.ncrb.gov.in/crime-in-india-year-wise.html?year=${y}`
const NCRB_ADDITIONAL = (y: number) => `https://www.ncrb.gov.in/crime-in-india-additional-table.html?year=${y}&category=`
const range = (a: number, b: number) => Array.from({ length: b - a + 1 }, (_, i) => a + i)

/** ADR report behind each report year shown on the dashboard. */
export const ADR_REPORT_URL: Record<number, string> = {
  2017: 'https://adrindia.org/sites/default/files/Analysis_of_MPsMLAs_with_Declared_Cases_Related_to_Crimes_against_Women.pdf',
  2018: 'https://adrindia.org/sites/default/files/Analysis_of_MPs_MLAs_with_Declared_Cases_Related_to_Crimes_against_Women_2018_0.pdf',
  2023: 'https://adrindia.org/content/%E2%80%98134-mps-mlas-have-cases-crime-against-women',
  2024: 'https://adrindia.org/sites/default/files/Analysis_of_Sitting_MPs_and_MLAs_with_Declared_Cases_Related_to_Crimes_against_Women_2024_FinalVer_English.pdf',
  2025: 'https://adrindia.org/sites/default/files/All_India_Sitting_MLAs_Report_2025_English.pdf',
}

interface Item {
  label: string
  href: string
  note?: string
}

const GROUPS: { title: string; items: Item[] }[] = [
  {
    title: 'Crime figures (National Crime Records Bureau)',
    items: [
      { label: 'NCRB, Crime in India (all annual reports)', href: 'https://www.ncrb.gov.in/crime-in-india.html', note: 'State-wise cases by crime head, offender relation, custodial rape' },
      { label: 'Crime in India 2024, Volume I (PDF)', href: 'https://www.ncrb.gov.in/uploads/files/11CrimeinIndia2024-VolumeI.pdf', note: 'Chapter 3A: crime against women' },
      { label: 'Crime in India 2023, Volume I (PDF)', href: 'https://www.ncrb.gov.in/uploads/files/1CrimeinIndia2023PartI1.pdf' },
      { label: 'NCRB tables on Open Government Data (data.gov.in)', href: 'https://www.data.gov.in/catalog/crime-against-women', note: 'District-wise tables 2001–2014, offender relation tables' },
      { label: 'NCRB Crime in India tables (Contents page), 2024', href: 'https://www.ncrb.gov.in/crime-in-india-table-content.html?year=2024', note: 'Tables 3A.5–3A.10: arrests, charge-sheets, trials and convictions; 5A: juveniles. Change the year in the link for other years.' },
    ],
  },
  {
    title: 'Population (for rates per lakh women)',
    items: [
      { label: 'Census of India 2011, Primary Census Abstract', href: 'https://censusindia.gov.in/census.website/data/census-tables', note: 'Female population by state and district, used for 2001–2011 and for district rates' },
      { label: 'Population Projections for India and States 2011–2036 (MoHFW, July 2020)', href: 'https://nhm.gov.in/New_Updates_2018/Report_Population_Projection_2019.pdf', note: 'Table 11, projected female population, used for 2012 onwards' },
    ],
  },
  {
    title: 'Public representatives (Association for Democratic Reforms)',
    items: [
      { label: 'ADR 2024: sitting MPs/MLAs with declared cases of crimes against women', href: ADR_REPORT_URL[2024] },
      { label: 'Same 2024 report, copy on PARI (People’s Archive of Rural India)', href: 'https://ruralindiaonline.org/en/library/resource/analysis-of-sitting-mpsmlas-with-declared-cases-related-to-crimes-against-women-2024/' },
      { label: 'ADR 2025: all-India sitting MLAs (pages 10–11, crimes against women)', href: ADR_REPORT_URL[2025] },
      { label: 'ADR 2023 (headline figures, press release)', href: ADR_REPORT_URL[2023] },
      { label: 'ADR 2018 report', href: ADR_REPORT_URL[2018] },
      { label: 'ADR 2017 report', href: ADR_REPORT_URL[2017] },
    ],
  },
  {
    title: 'Maps',
    items: [
      { label: 'State boundaries (Survey of India based)', href: 'https://github.com/datta07/INDIAN-SHAPEFILES' },
      { label: 'District boundaries (GADM, c. 2010)', href: 'https://github.com/geohacker/india' },
      { label: 'Basemap: OpenFreeMap, © OpenStreetMap contributors', href: 'https://openfreemap.org/' },
    ],
  },
]

function A({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className="text-foreground underline decoration-muted-foreground/50 underline-offset-2 hover:decoration-foreground">
      {children}
    </a>
  )
}

export function Sources() {
  return (
    <section aria-labelledby="sources-title" className="flex flex-col gap-4">
      <div>
        <h3 id="sources-title" className="text-sm font-medium text-foreground">Sources — check the figures yourself</h3>
        <p className="mt-1">Every number on this page comes from the published sources below. Links open the original documents.</p>
      </div>

      <div className="flex flex-col gap-2">
        <h4 className="text-xs font-medium text-foreground">NCRB Crime in India, by year</h4>
        <YearLinks years={range(2001, 2024)} href={NCRB_YEAR} />
        <h4 className="mt-1 text-xs font-medium text-foreground">NCRB Additional Tables (state and district tables), by year</h4>
        <YearLinks years={range(2015, 2024)} href={NCRB_ADDITIONAL} />
      </div>

      {GROUPS.map((g) => (
        <div key={g.title} className="flex flex-col gap-1.5">
          <h4 className="text-xs font-medium text-foreground">{g.title}</h4>
          <ul className="flex flex-col gap-1.5">
            {g.items.map((i) => (
              <li key={i.href + i.label}>
                <A href={i.href}>{i.label}</A>
                {i.note && <span className="block">{i.note}</span>}
              </li>
            ))}
          </ul>
        </div>
      ))}

      <p>
        The processed figures shown here are in one file: <A href={`${import.meta.env.BASE_URL}data/data.json`}>data.json</A>.
      </p>
    </section>
  )
}

function YearLinks({ years, href }: { years: number[]; href: (y: number) => string }) {
  return (
    <ul className="flex flex-wrap gap-1">
      {years.map((y) => (
        <li key={y}>
          <a
            href={href(y)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block rounded border px-1.5 py-0.5 tabular-nums text-foreground hover:bg-accent focus-visible:outline-2 focus-visible:outline-ring"
          >
            {y}
          </a>
        </li>
      ))}
    </ul>
  )
}
