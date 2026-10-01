import { BarChart3, Gavel, LifeBuoy } from 'lucide-react'
import { useEffect, useState } from 'react'
import { cn } from '@/lib/utils'

export type Page = 'stats' | 'help' | 'justice'

const PAGES: { key: Page; label: string; icon: typeof BarChart3 }[] = [
  { key: 'stats', label: 'Statistics', icon: BarChart3 },
  { key: 'help', label: 'Get help', icon: LifeBuoy },
  { key: 'justice', label: 'Arrest to verdict', icon: Gavel },
]

const readPage = (): Page => {
  const h = window.location.hash.replace(/^#\/?/, '')
  return h === 'help' || h === 'justice' ? h : 'stats'
}

/** The current page, kept in the URL hash (#/help, #/justice) so pages can be linked and shared. */
export function useHashPage() {
  const [page, setPage] = useState<Page>(readPage)
  useEffect(() => {
    const on = () => setPage(readPage())
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  const go = (p: Page) => {
    window.location.hash = p === 'stats' ? '/' : `/${p}`
  }
  return [page, go] as const
}

export function PageTabs({ page, setPage, mobile }: { page: Page; setPage: (p: Page) => void; mobile?: boolean }) {
  return (
    <nav aria-label="Pages" className={cn('flex border-b', mobile ? 'border-[var(--m-border)]' : 'px-2')}>
      {PAGES.map(({ key, label, icon: Icon }) => (
        <a
          key={key}
          href={key === 'stats' ? '#/' : `#/${key}`}
          onClick={(e) => {
            e.preventDefault()
            setPage(key)
          }}
          aria-current={page === key ? 'page' : undefined}
          className={cn(
            'page-tab inline-flex items-center justify-center gap-1.5 border-b-2 border-transparent font-medium whitespace-nowrap',
            mobile ? 'flex-1 px-1 py-2.5 text-[13px]' : 'px-4 py-2.5 text-sm',
            page === key ? 'page-tab-on' : 'text-muted-foreground hover:text-foreground',
          )}
        >
          <Icon className={cn('size-4 shrink-0', mobile && 'hidden min-[420px]:inline')} aria-hidden />
          {label}
        </a>
      ))}
    </nav>
  )
}
