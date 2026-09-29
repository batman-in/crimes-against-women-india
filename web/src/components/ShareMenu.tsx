import { Check, Link, Share2 } from 'lucide-react'
import { DropdownMenu } from 'radix-ui'
import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'

const SHARE_TEXT = 'Project Durga: an interactive map of crimes against women in India, by state and district, from NCRB police records.'
const SHARE_IMAGE = `${import.meta.env.BASE_URL}share.png`

const siteUrl = () => `${window.location.origin}${import.meta.env.BASE_URL}`

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

async function copyLink() {
  try {
    await navigator.clipboard.writeText(siteUrl())
    return true
  } catch {
    return false
  }
}

/** Instagram has no web share link: hand the screenshot to the phone's share sheet, else download it and copy the link. */
async function shareToInstagram(): Promise<string | null> {
  const blob = await fetch(SHARE_IMAGE).then((r) => r.blob())
  const file = new File([blob], 'project-durga.png', { type: 'image/png' })
  if (navigator.canShare?.({ files: [file] })) {
    try {
      await navigator.share({ files: [file], text: `${SHARE_TEXT} ${siteUrl()}` })
    } catch {
      // cancelled
    }
    return null
  }
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = file.name
  a.click()
  URL.revokeObjectURL(a.href)
  const copied = await copyLink()
  return copied
    ? 'Screenshot downloaded and link copied. Post the image on Instagram and paste the link in your caption or story.'
    : 'Screenshot downloaded. Post it on Instagram with a link to this page.'
}

const itemClass =
  'flex cursor-pointer items-center gap-2.5 rounded-sm px-2.5 py-2 text-sm outline-none select-none data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground'

/** Header button: share the site to Facebook or Instagram, or copy its link. */
export function ShareMenu() {
  const [notice, setNotice] = useState<string | null>(null)
  useEffect(() => {
    if (!notice) return
    const t = setTimeout(() => setNotice(null), 6000)
    return () => clearTimeout(t)
  }, [notice])

  const facebook = () => {
    const url = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(siteUrl())}`
    window.open(url, 'share-facebook', 'width=600,height=560,noopener')
  }
  const instagram = () => {
    shareToInstagram().then(setNotice, () => setNotice('Could not load the screenshot. Please try again.'))
  }
  const link = () => {
    copyLink().then((ok) => setNotice(ok ? 'Link copied.' : `Copy this link: ${siteUrl()}`))
  }

  return (
    <>
      <DropdownMenu.Root>
        <DropdownMenu.Trigger asChild>
          <Button variant="ghost" size="icon" className="shrink-0" aria-label="Share">
            <Share2 />
          </Button>
        </DropdownMenu.Trigger>
        <DropdownMenu.Portal>
          <DropdownMenu.Content
            align="end"
            sideOffset={6}
            className="z-50 w-64 overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md"
          >
            <img src={SHARE_IMAGE} alt="Screenshot of the Project Durga homepage" className="mb-1 aspect-[1600/838] w-full rounded-sm border object-cover" />
            <DropdownMenu.Item className={itemClass} onSelect={facebook}>
              <FacebookIcon /> Share on Facebook
            </DropdownMenu.Item>
            <DropdownMenu.Item className={itemClass} onSelect={instagram}>
              <InstagramIcon /> Share on Instagram
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
          className="fixed inset-x-4 bottom-24 z-50 mx-auto flex max-w-sm items-start gap-2 rounded-md border bg-popover p-3 text-sm text-popover-foreground shadow-lg lg:bottom-6"
        >
          <Check className="mt-0.5 size-4 shrink-0" aria-hidden />
          <span>{notice}</span>
        </div>
      )}
    </>
  )
}
