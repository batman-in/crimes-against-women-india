import { cn } from '@/lib/utils'

const base = import.meta.env.BASE_URL

function Themed({ name, alt, className }: { name: string; alt: string; className?: string }) {
  return (
    <span className={cn('inline-block shrink-0', className)}>
      <img src={`${base}${name}-light.png`} alt={alt} className="brand-on-light h-full w-auto" />
      <img src={`${base}${name}-dark.png`} alt={alt} className="brand-on-dark h-full w-auto" />
    </span>
  )
}

/** Her profile against the rising sun. The artwork has one cut for light grounds and one for dark; CSS shows the one for the theme. */
export function BrandMark({ className }: { className?: string }) {
  return <Themed name="brand-mark" alt="" className={className} />
}

/** Full logo: the mark over the wordmark, for the footer. */
export function BrandLockup({ className }: { className?: string }) {
  return <Themed name="brand-lockup" alt="Project Durga" className={className} />
}

/** Header logo: the mark beside the wordmark. */
export function BrandTitle({ size = 'md' }: { size?: 'sm' | 'md' }) {
  return (
    <h1 className="flex items-center gap-2">
      <BrandMark className={size === 'sm' ? 'h-9' : 'h-11'} />
      <Themed name="brand-word" alt="Project Durga" className={size === 'sm' ? 'h-7' : 'h-8'} />
    </h1>
  )
}
