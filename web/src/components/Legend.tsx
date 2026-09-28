import { formatValue, metricUnit, type Metric } from '@/lib/data'

interface Props {
  title: string
  breaks: number[]
  ramp: string[]
  metric: Metric
  noData: string
  heat: boolean
  unit?: string
  compact?: boolean
}

export function Legend({ title, breaks, ramp, metric, noData, heat, unit, compact }: Props) {
  if (heat) {
    return (
      <div className="flex flex-col gap-1.5">
        <span className="text-xs font-medium">{title}</span>
        <div className="h-2.5 w-full rounded-full" style={{ background: 'linear-gradient(90deg, rgba(252,196,120,.55), #f59e4c, #eb6834, #d0412a, #8f1d1d)' }} />
        <div className="flex justify-between text-[11px] text-muted-foreground"><span>Lower</span><span>Higher concentration</span></div>
      </div>
    )
  }
  const n = breaks.length + 1
  const colors = Array.from({ length: n }, (_, i) => ramp[n === 1 ? ramp.length - 1 : Math.round((i / (n - 1)) * (ramp.length - 1))])
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-xs font-medium">{title} <span className="font-normal text-muted-foreground">({unit ?? metricUnit(metric)})</span></span>
      <div className="flex gap-0.5">
        {colors.map((c, i) => <span key={i} className="h-2.5 flex-1 first:rounded-l-full last:rounded-r-full" style={{ background: c }} />)}
      </div>
      <div className="relative flex text-[11px] text-muted-foreground tabular-nums">
        {breaks.map((b, i) => (
          <span key={i} className="absolute -translate-x-1/2" style={{ left: `${((i + 1) / n) * 100}%` }}>{formatValue(b, metric)}</span>
        ))}
        <span className="invisible">0</span>
      </div>
      <div className={`${compact ? 'hidden' : 'flex'} items-center gap-1.5 text-[11px] text-muted-foreground`}>
        <span className="size-2.5 rounded-sm" style={{ background: noData }} /> No data for this filter
      </div>
    </div>
  )
}
