// Site-wide visit counter. POST counts one visit and returns the total; GET only reads it.
// Stores a single number in Netlify Blobs: no IP addresses, cookies or anything about visitors.
import { getStore } from '@netlify/blobs'
import type { Config, Context } from '@netlify/functions'

const KEY = 'total'
// Search-engine crawlers, link previewers and headless browsers are not counted
const BOT = /bot|crawl|spider|slurp|preview|facebookexternalhit|whatsapp|telegram|headless|lighthouse|curl|wget|python|node-fetch|axios/i

export default async (req: Request, _context: Context) => {
  const store = getStore({ name: 'visits', consistency: 'strong' })
  const current = Number((await store.get(KEY)) ?? 0) || 0

  let total = current
  const isBot = BOT.test(req.headers.get('user-agent') ?? '')
  if (req.method === 'POST' && !isBot) {
    total = current + 1
    await store.set(KEY, String(total))
  }

  return new Response(JSON.stringify({ total }), {
    headers: { 'content-type': 'application/json', 'cache-control': 'no-store' },
  })
}

export const config: Config = { path: '/api/visits', method: ['GET', 'POST'] }
