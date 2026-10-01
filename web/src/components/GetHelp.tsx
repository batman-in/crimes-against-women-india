import { ExternalLink, Globe, LifeBuoy, Loader2, Mail, MapPin, MessageCircle, Phone, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { cn } from '@/lib/utils'

// ---- data (built by scripts/build_support.py from data/support/*.csv) ----------------------
interface Entry {
  c: string // category
  n: string // name
  p?: string[] // phones: 'as printed|dialable|label' (label optional)
  w?: string // WhatsApp
  e?: string[] // emails
  u?: string // website
  a?: string // address
  h?: string // hours
  o?: string // notes
  s?: string // source
  v?: string // checked on
  d?: string // district as the source spells it
  g?: number // map district id
}
export interface Support {
  updated: string
  categories: Record<string, string>
  national: Entry[]
  states: Record<string, { state: Entry[]; district: Entry[] }>
}

let cache: Promise<Support> | null = null
export const loadSupport = () => (cache ??= fetch(`${import.meta.env.BASE_URL}data/support.json`).then((r) => r.json() as Promise<Support>))

// Numbers everyone should see first. Each is also in national.csv with its source.
const EMERGENCY = [
  { num: '112', label: 'Emergency', sub: 'Police, ambulance, fire' },
  { num: '181', label: 'Women Helpline', sub: '24x7, toll-free' },
  { num: '14490', label: 'NCW Helpline', sub: 'National Commission for Women' },
  { num: '1098', label: 'Child Helpline', sub: 'Girls under 18' },
]

const tel = (p: string) => `tel:${p.replace(/[^\d+]/g, '')}`
const wa = (p: string) => {
  const d = p.replace(/\D/g, '')
  return `https://wa.me/${d.length === 10 ? `91${d}` : d}`
}
const mapLink = (e: Entry) => `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${e.n}, ${e.a}`)}`
const fmtDate = (d?: string) => (d ? new Date(`${d}T00:00:00`).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '')

function EntryCard({ e }: { e: Entry }) {
  return (
    <li className="rounded-lg border bg-card p-3 text-card-foreground">
      <p className="font-semibold leading-snug">{e.n}</p>
      {e.h && <p className="mt-0.5 text-xs text-muted-foreground">{e.h}</p>}
      {(e.p?.length || e.w) && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {e.p?.map((p) => {
            const [shown, dial, label] = p.split('|')
            return (
              <a key={p} href={`tel:${dial ?? shown}`} className="help-call inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-semibold tabular-nums">
                <Phone className="size-3.5" aria-hidden /> {shown}
                {label && <span className="text-xs font-normal opacity-80">{label}</span>}
              </a>
            )
          })}
          {e.w && (
            <a href={wa(e.w)} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium">
              <MessageCircle className="size-3.5 text-[#25d366]" aria-hidden /> WhatsApp
            </a>
          )}
        </div>
      )}
      {e.o && <p className="mt-2 text-sm text-muted-foreground">{e.o}</p>}
      <div className="mt-2 flex flex-col gap-1 text-sm">
        {e.e?.map((m) => (
          <a key={m} href={`mailto:${m}`} className="inline-flex items-center gap-1.5 break-all underline-offset-2 hover:underline">
            <Mail className="size-3.5 shrink-0" aria-hidden /> {m}
          </a>
        ))}
        {e.u && (
          <a href={e.u} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 underline-offset-2 hover:underline">
            <Globe className="size-3.5 shrink-0" aria-hidden /> Website
          </a>
        )}
        {e.a && (
          <a href={mapLink(e)} target="_blank" rel="noopener noreferrer" className="inline-flex items-start gap-1.5 underline-offset-2 hover:underline">
            <MapPin className="mt-0.5 size-3.5 shrink-0" aria-hidden /> <span>{e.a}</span>
          </a>
        )}
      </div>
      {e.s && (
        <p className="mt-2 text-[11px] text-muted-foreground">
          <a href={e.s} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 underline-offset-2 hover:underline">
            Source <ExternalLink className="size-3" aria-hidden />
          </a>
          {e.v && ` · checked ${fmtDate(e.v)}`}
        </p>
      )}
    </li>
  )
}

function Section({ title, entries, categories }: { title: string; entries: Entry[]; categories: Record<string, string> }) {
  if (!entries.length) return null
  const groups = Object.keys(categories).map((c) => [c, entries.filter((e) => e.c === c)] as const).filter(([, es]) => es.length)
  return (
    <section className="flex flex-col gap-3">
      <h3 className="text-base font-bold">{title}</h3>
      {groups.map(([c, es]) => (
        <div key={c} className="flex flex-col gap-2">
          <h4 className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">{categories[c]}</h4>
          <ul className="flex flex-col gap-2">
            {es.map((e, i) => <EntryCard key={`${e.n}-${i}`} e={e} />)}
          </ul>
        </div>
      ))}
    </section>
  )
}

/** Load the directory once; null until it arrives. */
export function useSupport(enabled: boolean) {
  const [data, setData] = useState<Support | null>(null)
  const [failed, setFailed] = useState(false)
  useEffect(() => {
    if (!enabled || data) return
    loadSupport().then(setData, () => setFailed(true))
  }, [enabled, data])
  return { data, failed }
}

export type Coverage = 'phone' | 'address' | 'legal' | 'none'

/** What the directory lists in each map district: a One Stop Centre with a phone, one with an address only, or legal aid only. */
export function coverageByDistrict(data: Support): Record<string, Coverage> {
  const out: Record<string, Coverage> = {}
  const rank: Record<Coverage, number> = { none: 0, legal: 1, address: 2, phone: 3 }
  for (const st of Object.values(data.states))
    for (const e of st.district) {
      if (e.g === undefined) continue
      const c: Coverage = e.c === 'one_stop_centre' ? (e.p?.length ? 'phone' : 'address') : e.c === 'legal_aid' ? 'legal' : 'none'
      const g = String(e.g)
      if (!out[g] || rank[c] > rank[out[g]]) out[g] = c
    }
  return out
}

export const COVERAGE_LABEL: Record<Coverage, string> = {
  phone: 'One Stop Centre with phone',
  address: 'One Stop Centre, address only',
  legal: 'Legal aid only',
  none: 'Nothing listed yet',
}

/** Header button: opens the Get help page. */
export function GetHelpButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="get-help inline-flex h-9 shrink-0 items-center gap-1.5 rounded-full px-3.5 text-sm font-semibold shadow-sm"
    >
      <LifeBuoy className="size-4" aria-hidden />
      Get help
    </button>
  )
}

export interface HelpDirectoryProps {
  data: Support | null
  failed: boolean
  stateNames: string[]
  state: string | null
  district: string | null // map district id
  onState: (state: string | null) => void
  onDistrict: (gid: string | null) => void
  districtsOf: (state: string) => string[]
  districtName: (gid: string) => string
}

/**
 * The Get help page's panel: emergency numbers first, then the One Stop Centre, legal aid,
 * helplines and NGOs for the district and state chosen here or on the map, then national services.
 */
export function HelpDirectory({ data, failed, stateNames, state, district, onState, onDistrict, districtsOf, districtName }: HelpDirectoryProps) {
  const st = state ?? ''
  const dist = district ?? ''
  const districts = useMemo(
    () => (st ? districtsOf(st).map((g) => ({ g, n: districtName(g).split(',')[0] })).sort((a, b) => a.n.localeCompare(b.n)) : []),
    [st, districtsOf, districtName],
  )
  const stData = st ? data?.states[st] : undefined
  const here = dist && stData ? stData.district.filter((e) => String(e.g) === dist) : []
  const othersByDistrict = useMemo(() => {
    const m = new Map<string, Entry[]>()
    for (const e of stData?.district ?? []) if (!dist || String(e.g) !== dist) m.set(e.d ?? '', [...(m.get(e.d ?? '') ?? []), e])
    return [...m.entries()]
  }, [stData, dist])
  const distLabel = dist ? districtName(dist).split(',')[0] : ''

  const quickExit = () => window.location.replace('https://www.google.com/')

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold">Get help</h2>
          <p className="text-sm text-muted-foreground">Free services for women and girls facing violence or harassment.</p>
        </div>
        <button
          type="button"
          onClick={quickExit}
          className="inline-flex shrink-0 items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold"
          title="Leaves this site straight away and opens Google"
        >
          <X className="size-3.5" aria-hidden /> Quick exit
        </button>
      </div>

      <section aria-label="Emergency numbers">
        <p className="mb-2 text-sm font-semibold">In danger right now? Call 112.</p>
        <div className="grid grid-cols-2 gap-2">
          {EMERGENCY.map((x, i) => (
            <a key={x.num} href={tel(x.num)} className={cn('flex flex-col rounded-lg p-3', i === 0 ? 'help-sos' : 'border bg-card')}>
              <span className="flex items-center gap-1.5 text-2xl font-extrabold tabular-nums">
                <Phone className="size-4" aria-hidden /> {x.num}
              </span>
              <span className="text-sm font-semibold">{x.label}</span>
              <span className={cn('text-xs', i === 0 ? 'opacity-90' : 'text-muted-foreground')}>{x.sub}</span>
            </a>
          ))}
        </div>
      </section>

      <section className="flex flex-col gap-2" aria-label="Your area">
        <p className="text-sm font-semibold">
          Find help near you <span className="font-normal text-muted-foreground">(or tap the map)</span>
        </p>
        <div className="grid grid-cols-2 gap-2">
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            State / UT
            <select
              value={st}
              onChange={(e) => onState(e.target.value || null)}
              className="h-10 rounded-md border bg-background px-2 text-sm text-foreground"
            >
              <option value="">Choose…</option>
              {stateNames.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            District
            <select
              value={dist}
              onChange={(e) => onDistrict(e.target.value || null)}
              disabled={!st}
              className="h-10 rounded-md border bg-background px-2 text-sm text-foreground disabled:opacity-50"
            >
              <option value="">All districts</option>
              {districts.map((d) => <option key={d.g} value={d.g}>{d.n}</option>)}
            </select>
          </label>
        </div>
      </section>

      {!data && !failed && (
        <p className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" aria-hidden /> Loading the directory…
        </p>
      )}
      {failed && <p className="text-sm">Could not load the directory. The numbers above always work.</p>}

      {data && (
        <>
          {dist &&
            (here.length ? (
              <Section title={`In ${distLabel}`} entries={here} categories={data.categories} />
            ) : (
              <p className="rounded-lg border border-dashed p-3 text-sm text-muted-foreground">
                We have no district-level listing for {distLabel} yet. Call 181 and ask for the nearest One Stop Centre, or
                see the state services and other districts below.
              </p>
            ))}
          {stData && <Section title={`Across ${st}`} entries={stData.state} categories={data.categories} />}
          <Section title="Anywhere in India" entries={data.national} categories={data.categories} />
          {st && othersByDistrict.length > 0 && (
            <section className="flex flex-col gap-2">
              <h3 className="text-base font-bold">{dist ? `Other districts in ${st}` : `Districts in ${st}`}</h3>
              {othersByDistrict.map(([d, es]) => (
                <details key={d} className="rounded-lg border">
                  <summary className="cursor-pointer px-3 py-2 text-sm font-semibold">
                    {d} <span className="font-normal text-muted-foreground">({es.length})</span>
                  </summary>
                  <ul className="flex flex-col gap-2 p-2">
                    {es.map((e, i) => <EntryCard key={`${e.n}-${i}`} e={e} />)}
                  </ul>
                </details>
              ))}
            </section>
          )}
          <p className="text-xs leading-relaxed text-muted-foreground">
            Contacts come from official government sources and the organisations' own websites, checked on the date shown
            with each one ({fmtDate(data.updated)} most recently). Numbers change, so if one doesn't work, call 181 or 112.
            This is information to help you find support; it is not legal advice. A lawyer from legal aid (15100) can
            advise you for free.
          </p>
        </>
      )}
    </div>
  )
}
