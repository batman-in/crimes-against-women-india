// Sequential colour scale for the choropleth: one hue, light -> dark, quantile classes.

// Red ramp, light -> dark (light theme).
export const RAMP_LIGHT = ['#fbd3cf', '#f6aba3', '#ef7f74', '#e3514a', '#c43333', '#9e2226', '#6e1519']
// Dark theme: same hue, ordered so "more" still reads as more prominent on a dark ground.
export const RAMP_DARK = ['#6e1519', '#8f1d22', '#b02a2c', '#d0413b', '#e8675c', '#f29488', '#fbc9c1']

export const NO_DATA = { light: '#e4e3df', dark: '#3a3a37' }

/** Quantile class breaks (upper bounds of all classes but the last). */
export function quantileBreaks(values: number[], classes = RAMP_LIGHT.length): number[] {
  const v = values.filter((x) => Number.isFinite(x)).sort((a, b) => a - b)
  if (v.length === 0) return []
  const breaks: number[] = []
  for (let i = 1; i < classes; i++) {
    const q = v[Math.min(v.length - 1, Math.floor((i / classes) * v.length))]
    if (!breaks.length || q > breaks[breaks.length - 1]) breaks.push(q)
  }
  return breaks
}

export function colorFor(value: number | undefined, breaks: number[], ramp: string[], noData: string) {
  if (value === undefined) return noData
  let i = 0
  while (i < breaks.length && value >= breaks[i]) i++
  // spread the classes that exist across the whole ramp
  const idx = breaks.length ? Math.round((i / breaks.length) * (ramp.length - 1)) : ramp.length - 1
  return ramp[idx]
}
