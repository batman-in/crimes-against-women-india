// Portrait share card (1080×1350, Instagram's 4:5 feed size; WhatsApp and Facebook show it whole)
// for whatever the viewer is looking at: place, crime type, year, headline figure and the map.

export interface ShareCardInfo {
  place: string // "India", "Maharashtra", "Pune, Maharashtra"
  subtitle: string // "All crimes against women · 2024"
  value: string // "64.6"
  unit?: string // "per 1 lakh women"
  secondary?: string // "4,41,534 cases"
  change?: number // vs the previous year with data, as a fraction
  prevYear?: number
  legendTitle: string
  ramp: string[] // legend colours, low to high
  heat: boolean
}

export const CARD_W = 1080
export const CARD_H = 1350

const THEMES = {
  light: { bg: '#fff7ee', ink: '#1f1f1f', soft: '#6b625a', border: '#ebe0d2', glass: 'rgba(255,255,255,0.9)', link: '#c62828' },
  dark: { bg: '#1a1a1a', ink: '#fff7ee', soft: '#b8afa5', border: '#383431', glass: 'rgba(36,36,36,0.9)', link: '#ff7a3d' },
}
const RED = '#c62828'
const CREAM = '#fff7ee'
const RISE = { light: '#b3261e', dark: '#ff8a80' }
const FALL = { light: '#0f6e63', dark: '#5fd4c4' }
const SANS = '"Inter Variable", Inter, system-ui, sans-serif'

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = reject
    img.src = src
  })
}

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath()
  ctx.roundRect(x, y, w, h, r)
}

/** Shrink the font until the text fits, then cut it with an ellipsis if it still doesn't. */
function fitText(ctx: CanvasRenderingContext2D, text: string, maxWidth: number, weight: number, size: number, minSize: number) {
  let s = size
  ctx.font = `${weight} ${s}px ${SANS}`
  while (ctx.measureText(text).width > maxWidth && s > minSize) {
    s -= 2
    ctx.font = `${weight} ${s}px ${SANS}`
  }
  let t = text
  while (ctx.measureText(t).width > maxWidth && t.length > 1) t = t.slice(0, -2) + '…'
  return t
}

export async function renderShareCard(
  info: ShareCardInfo,
  map: HTMLCanvasElement | null,
  theme: 'light' | 'dark',
  siteLabel: string,
): Promise<Blob> {
  const base = import.meta.env.BASE_URL
  const c = THEMES[theme]
  await Promise.all([
    document.fonts.load(`400 64px Anton`),
    document.fonts.load(`500 34px ${SANS}`),
    document.fonts.load(`800 140px ${SANS}`),
  ]).catch(() => undefined)
  const [mark, word] = await Promise.all([
    loadImage(`${base}brand-mark-${theme}.png`),
    loadImage(`${base}brand-word-${theme}.png`),
  ])

  const canvas = document.createElement('canvas')
  canvas.width = CARD_W
  canvas.height = CARD_H
  const ctx = canvas.getContext('2d')!
  const M = 60 // side margin

  ctx.fillStyle = c.bg
  ctx.fillRect(0, 0, CARD_W, CARD_H)

  // Slogan band with the sunrise rule
  ctx.fillStyle = RED
  ctx.fillRect(0, 0, CARD_W, 116)
  const rule = ctx.createLinearGradient(0, 0, CARD_W, 0)
  rule.addColorStop(0, '#ffc857')
  rule.addColorStop(0.45, '#ff7a3d')
  rule.addColorStop(1, RED)
  ctx.fillStyle = rule
  ctx.fillRect(0, 116, CARD_W, 8)
  ctx.font = '400 66px Anton, Impact, sans-serif'
  ctx.textBaseline = 'middle'
  ctx.textAlign = 'left'
  if ('letterSpacing' in ctx) ctx.letterSpacing = '3px'
  const words = ['EDUCATE', 'AGITATE', 'ORGANISE']
  const dot = '  ·  '
  const total = words.reduce((w, s) => w + ctx.measureText(s).width, 0) + 2 * ctx.measureText(dot).width
  let x = (CARD_W - total) / 2
  words.forEach((s, i) => {
    ctx.fillStyle = CREAM
    ctx.fillText(s, x, 62)
    x += ctx.measureText(s).width
    if (i < words.length - 1) {
      ctx.fillStyle = '#ffc857'
      ctx.fillText(dot, x, 62)
      x += ctx.measureText(dot).width
    }
  })
  if ('letterSpacing' in ctx) ctx.letterSpacing = '0px'

  // Logo
  const markH = 92
  const markW = (mark.width / mark.height) * markH
  ctx.drawImage(mark, M, 150, markW, markH)
  const wordH = 64
  ctx.drawImage(word, M + markW + 16, 150 + (markH - wordH) / 2, (word.width / word.height) * wordH, wordH)

  // Place and what
  ctx.textBaseline = 'alphabetic'
  ctx.fillStyle = c.ink
  ctx.fillText(fitText(ctx, info.place, CARD_W - 2 * M, 700, 60, 40), M, 330)
  ctx.fillStyle = c.soft
  ctx.fillText(fitText(ctx, info.subtitle, CARD_W - 2 * M, 500, 34, 26), M, 382)

  // Headline figure
  ctx.fillStyle = c.ink
  ctx.font = `800 132px ${SANS}`
  ctx.fillText(info.value, M - 4, 520)
  const valueW = ctx.measureText(info.value).width
  if (info.unit) {
    ctx.fillStyle = c.soft
    ctx.fillText(fitText(ctx, info.unit, CARD_W - 2 * M - valueW - 20, 500, 38, 26), M + valueW + 18, 520)
  }
  let sx = M
  if (info.secondary) {
    ctx.fillStyle = c.soft
    ctx.font = `500 32px ${SANS}`
    ctx.fillText(info.secondary, sx, 578)
    sx += ctx.measureText(info.secondary).width + 20
  }
  if (info.change !== undefined && info.prevYear !== undefined) {
    const up = info.change > 0
    const label = `${up ? '↗' : '↘'} ${up ? '+' : '−'}${Math.abs(info.change * 100).toFixed(1)}% vs ${info.prevYear}`
    ctx.font = `600 28px ${SANS}`
    const w = ctx.measureText(label).width + 32
    const col = up ? RISE[theme] : FALL[theme]
    ctx.fillStyle = col + '22'
    roundRect(ctx, sx, 546, w, 44, 22)
    ctx.fill()
    ctx.fillStyle = col
    ctx.fillText(label, sx + 16, 578)
  }

  // Map, shown whole: the frame takes the map's own shape within the available area
  const area = { x: M, y: 620, w: CARD_W - 2 * M, h: 590 }
  const aspect = map && map.width && map.height ? map.width / map.height : area.w / area.h
  const bw = Math.min(area.w, area.h * aspect)
  const bh = Math.min(area.h, bw / aspect)
  const box = { x: area.x + (area.w - bw) / 2, y: area.y + (area.h - bh) / 2, w: bw, h: bh }
  ctx.save()
  roundRect(ctx, box.x, box.y, box.w, box.h, 24)
  ctx.clip()
  ctx.fillStyle = c.border
  ctx.fillRect(box.x, box.y, box.w, box.h)
  if (map && map.width && map.height) ctx.drawImage(map, box.x, box.y, box.w, box.h)
  ctx.restore()
  ctx.strokeStyle = c.border
  ctx.lineWidth = 2
  roundRect(ctx, box.x, box.y, box.w, box.h, 24)
  ctx.stroke()

  // Legend, bottom-left of the map
  const lg = { x: box.x + 20, y: box.y + box.h - 112, w: Math.min(440, box.w - 40), h: 92 }
  ctx.fillStyle = c.glass
  roundRect(ctx, lg.x, lg.y, lg.w, lg.h, 14)
  ctx.fill()
  ctx.fillStyle = c.ink
  ctx.fillText(fitText(ctx, info.legendTitle, lg.w - 32, 600, 22, 16), lg.x + 16, lg.y + 32)
  const sw = (lg.w - 32) / info.ramp.length
  info.ramp.forEach((col, i) => {
    ctx.fillStyle = col
    ctx.fillRect(lg.x + 16 + i * sw, lg.y + 44, sw - 3, 14)
  })
  ctx.fillStyle = c.soft
  ctx.font = `500 18px ${SANS}`
  ctx.fillText('Lower', lg.x + 16, lg.y + 80)
  const hi = info.heat ? 'Higher concentration' : 'Higher'
  ctx.textAlign = 'right'
  ctx.fillText(hi, lg.x + lg.w - 16, lg.y + 80)
  ctx.textAlign = 'left'

  // Footer
  ctx.fillStyle = c.soft
  ctx.font = `500 26px ${SANS}`
  ctx.fillText('Cases registered by police · Source: NCRB, Crime in India', M, 1262)
  ctx.fillStyle = c.link
  ctx.font = `700 32px ${SANS}`
  ctx.fillText(siteLabel, M, 1308)

  return new Promise((resolve, reject) => canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('toBlob failed'))), 'image/png'))
}
