import { Check, Download, Link, Loader2, Share2 } from 'lucide-react'
import { DropdownMenu } from 'radix-ui'
import { useEffect, useRef, useState } from 'react'
import { renderShareCard, type ShareCardInfo } from '@/lib/shareCard'
import { cn } from '@/lib/utils'

const siteUrl = () => `${window.location.origin}${import.meta.env.BASE_URL}`
const siteLabel = () => `${window.location.host}${import.meta.env.BASE_URL}`.replace(/\/$/, '')

// Brand marks (lucide no longer ships them)
function FacebookIcon() {
  return (
    <svg viewBox="0 0 24 24" className="size-4" aria-hidden fill="currentColor">
      <path d="M24 12.07C24 5.41 18.63 0 12 0S0 5.4 0 12.07C0 18.1 4.39 23.1 10.13 24v-8.44H7.08v-3.49h3.04V9.41c0-3.02 1.8-4.7 4.54-4.7 1.31 0 2.68.24 2.68.24v2.97h-1.5c-1.5 0-1.96.93-1.96 1.89v2.26h3.32l-.53 3.5h-2.8V24C19.62 23.1 24 18.1 24 12.07" />
    </svg>
  )
}

function InstagramIcon() {
  return (
    <svg viewBox="0 0 24 24" className="size-4" aria-hidden fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="2" y="2" width="20" height="20" rx="5" />
      <circle cx="12" cy="12" r="4.5" />
      <circle cx="17.5" cy="6.5" r="0.5" fill="currentColor" />
    </svg>
  )
}

function WhatsAppIcon() {
  return (
    <svg viewBox="0 0 24 24" className="size-4" aria-hidden fill="currentColor">
      <path d="M17.47 14.38c-.3-.15-1.76-.87-2.03-.97-.27-.1-.47-.15-.67.15-.2.3-.77.97-.94 1.17-.17.2-.35.22-.64.07-.3-.15-1.26-.46-2.4-1.48-.89-.79-1.49-1.77-1.66-2.07-.17-.3-.02-.46.13-.61.13-.13.3-.35.45-.52.15-.17.2-.3.3-.5.1-.2.05-.37-.02-.52-.08-.15-.67-1.62-.92-2.22-.24-.58-.49-.5-.67-.51h-.57c-.2 0-.52.07-.79.37-.27.3-1.04 1.02-1.04 2.48 0 1.46 1.07 2.88 1.21 3.07.15.2 2.1 3.2 5.08 4.49.71.31 1.26.49 1.7.63.71.23 1.36.2 1.87.12.57-.09 1.76-.72 2-1.41.25-.7.25-1.29.17-1.41-.07-.13-.27-.2-.57-.35M12.05 21.5h-.01a9.4 9.4 0 0 1-4.8-1.31l-.34-.2-3.56.93.95-3.47-.22-.36a9.4 9.4 0 0 1-1.44-5.02c0-5.2 4.24-9.43 9.44-9.43 2.52 0 4.89.99 6.67 2.77a9.37 9.37 0 0 1 2.76 6.67c0 5.2-4.23 9.43-9.44 9.43m8.03-17.46A11.28 11.28 0 0 0 12.05.72C5.8.72.7 5.8.7 12.07c0 2 .52 3.95 1.52 5.67L.6 23.7l6.1-1.6a11.3 11.3 0 0 0 5.35 1.36h.01c6.26 0 11.35-5.09 11.35-11.35 0-3.03-1.18-5.88-3.33-8.03" />
    </svg>
  )
}

export interface ShareFabProps {
  info: ShareCardInfo
  shareText: string
  theme: 'light' | 'dark'
  snapshot: () => Promise<HTMLCanvasElement | null>
  mobile: boolean
}

function fileName(info: ShareCardInfo) {
  const slug = `${info.place} ${info.subtitle}`.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
  return `project-durga-${slug}.png`
}

function download(blob: Blob, name: string) {
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = name
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 1000)
}

async function copyLink() {
  try {
    await navigator.clipboard.writeText(siteUrl())
    return true
  } catch {
    return false
  }
}

/** Hand the card to the phone's share sheet (WhatsApp, Instagram, …). False where files can't be shared. */
async function shareFile(file: File, text: string) {
  if (!navigator.canShare?.({ files: [file] })) return false
  try {
    await navigator.share({ files: [file], text })
  } catch {
    // cancelled
  }
  return true
}

const itemClass =
  'flex cursor-pointer items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium outline-none select-none data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground'

/**
 * Floating share button, bottom right. Opening it draws a portrait card of the current view
 * (place, crime type, year, figure and map) that the menu shares or downloads.
 */
export function ShareFab({ info, shareText, theme, snapshot, mobile }: ShareFabProps) {
  const [open, setOpen] = useState(false)
  const [card, setCard] = useState<{ blob: Blob; url: string; file: File } | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const latest = useRef({ info, theme, snapshot })
  latest.current = { info, theme, snapshot }

  // Draw a fresh card each time the menu opens, so it matches what's on screen.
  useEffect(() => {
    if (!open) return
    let alive = true
    let url: string | null = null
    const { info, theme, snapshot } = latest.current
    snapshot()
      .catch(() => null)
      .then((map) => renderShareCard(info, map, theme, siteLabel()))
      .then((blob) => {
        if (!alive) return
        url = URL.createObjectURL(blob)
        setCard({ blob, url, file: new File([blob], fileName(info), { type: 'image/png' }) })
      })
      .catch(() => alive && setNotice('Could not draw the share image. Please try again.'))
    return () => {
      alive = false
      if (url) URL.revokeObjectURL(url)
    }
  }, [open])

  useEffect(() => {
    if (!notice) return
    const t = setTimeout(() => setNotice(null), 6000)
    return () => clearTimeout(t)
  }, [notice])

  const text = `${shareText} ${siteUrl()}`

  const whatsapp = async () => {
    if (card && mobile && (await shareFile(card.file, text))) return
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank', 'noopener')
    if (card && !mobile) {
      download(card.blob, card.file.name)
      setNotice('Image downloaded. Attach it to your WhatsApp message.')
    }
  }
  const instagram = async () => {
    if (!card) return
    if (await shareFile(card.file, text)) return
    download(card.blob, card.file.name)
    const copied = await copyLink()
    setNotice(
      copied
        ? 'Image downloaded and link copied. Post the image on Instagram and paste the link in your caption or story.'
        : 'Image downloaded. Post it on Instagram with a link to this page.',
    )
  }
  const facebook = () => {
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(siteUrl())}`, 'share-facebook', 'width=600,height=560,noopener')
  }
  const save = () => {
    if (!card) return
    download(card.blob, card.file.name)
    setNotice('Image downloaded.')
  }
  const link = () => {
    copyLink().then((ok) => setNotice(ok ? 'Link copied.' : `Copy this link: ${siteUrl()}`))
  }

  const bottom = mobile ? 'bottom-[calc(76px+env(safe-area-inset-bottom))]' : 'bottom-6'

  return (
    <>
      <DropdownMenu.Root
        open={open}
        onOpenChange={(o) => {
          if (o) setCard(null)
          setOpen(o)
        }}
      >
        <DropdownMenu.Trigger asChild>
          <button
            type="button"
            className={cn(
              'share-fab fixed right-4 z-40 flex h-14 items-center gap-2 rounded-full pr-6 pl-5 text-base font-semibold shadow-lg transition-transform active:scale-95 sm:right-6',
              bottom,
            )}
            aria-label="Share this view"
          >
            <Share2 className="size-5" aria-hidden />
            Share
          </button>
        </DropdownMenu.Trigger>
        <DropdownMenu.Portal>
          <DropdownMenu.Content
            side="top"
            align="end"
            sideOffset={10}
            collisionPadding={12}
            className="z-50 w-[min(20rem,calc(100vw-24px))] overflow-hidden rounded-xl border bg-popover p-2 text-popover-foreground shadow-xl"
          >
            <div className="mb-2 flex justify-center">
              {card ? (
                <img
                  src={card.url}
                  alt={`Share image: ${info.place}, ${info.subtitle}`}
                  className="max-h-[38svh] w-auto max-w-full rounded-lg border"
                />
              ) : (
                <div className="grid aspect-[4/5] h-[38svh] max-w-full place-items-center rounded-lg border bg-muted">
                  <Loader2 className="size-6 animate-spin text-muted-foreground" aria-label="Drawing the share image" />
                </div>
              )}
            </div>
            <DropdownMenu.Item className={itemClass} onSelect={whatsapp}>
              <span className="text-[#25d366]"><WhatsAppIcon /></span> WhatsApp
            </DropdownMenu.Item>
            <DropdownMenu.Item className={itemClass} onSelect={instagram} disabled={!card}>
              <span className="text-[#e1306c]"><InstagramIcon /></span> Instagram
            </DropdownMenu.Item>
            <DropdownMenu.Item className={itemClass} onSelect={facebook}>
              <span className="text-[#1877f2]"><FacebookIcon /></span> Facebook
            </DropdownMenu.Item>
            <DropdownMenu.Separator className="my-1 h-px bg-border" />
            <DropdownMenu.Item className={itemClass} onSelect={save} disabled={!card}>
              <Download className="size-4" aria-hidden /> Download image
            </DropdownMenu.Item>
            <DropdownMenu.Item className={itemClass} onSelect={link}>
              <Link className="size-4" aria-hidden /> Copy link
            </DropdownMenu.Item>
          </DropdownMenu.Content>
        </DropdownMenu.Portal>
      </DropdownMenu.Root>
      {notice && (
        <div
          role="status"
          className={cn(
            'fixed inset-x-4 z-50 mx-auto flex max-w-sm items-start gap-2 rounded-md border bg-popover p-3 text-sm text-popover-foreground shadow-lg',
            mobile ? 'bottom-[calc(144px+env(safe-area-inset-bottom))]' : 'bottom-24',
          )}
        >
          <Check className="mt-0.5 size-4 shrink-0" aria-hidden />
          <span>{notice}</span>
        </div>
      )}
    </>
  )
}
