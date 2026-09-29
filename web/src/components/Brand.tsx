import { cn } from '@/lib/utils'

const base = import.meta.env.BASE_URL

/** Durga, lion and trishul. The artwork has one cut for light grounds and one for dark; CSS shows the one for the theme. */
export function BrandMark({ className }: { className?: string }) {
  return (
    <span className={cn('inline-block shrink-0', className)}>
      <img src={`${base}brand-mark-light.png`} alt="" className="brand-on-light h-full w-auto" />
      <img src={`${base}brand-mark-dark.png`} alt="" className="brand-on-dark h-full w-auto" />
    </span>
  )
}

/** Full logo with the stacked wordmark, for the footer. */
export function BrandLockup({ className }: { className?: string }) {
  return (
    <span className={cn('inline-block', className)}>
      <img src={`${base}brand-lockup-light.png`} alt="Project Durga" className="brand-on-light h-full w-auto" />
      <img src={`${base}brand-lockup-dark.png`} alt="Project Durga" className="brand-on-dark h-full w-auto" />
    </span>
  )
}

/** Header logo: the mark with the wordmark set in type, so it stays sharp at any size. */
export function BrandTitle({ size = 'md' }: { size?: 'sm' | 'md' }) {
  return (
    <h1 className="flex items-center gap-2" aria-label="Project Durga">
      <BrandMark className={size === 'sm' ? 'h-10' : 'h-12'} />
      <span aria-hidden className={cn('brand-word flex flex-col', size === 'sm' ? 'text-[1.35rem]' : 'text-[1.6rem]')}>
        <span className="brand-word-project">Project</span>
        <span className="brand-word-durga">Durga</span>
      </span>
    </h1>
  )
}
