import clsx from 'clsx'
import { fmt, fmtPct } from '../utils/format'

interface Props {
  label: string
  value: number | null | undefined
  format?: 'number' | 'pct' | 'ratio'
  bullCondition?: (v: number) => boolean  // nếu true → màu xanh
  decimals?: number
  description?: string
}

export default function IndicatorCard({
  label, value, format = 'number', bullCondition, decimals = 2, description,
}: Props) {
  const isBull = value != null && bullCondition ? bullCondition(value) : null
  const displayVal =
    format === 'pct' ? fmtPct(value) :
    format === 'ratio' ? fmt(value, decimals) :
    fmt(value, decimals)

  return (
    <div className="card flex flex-col gap-1 min-w-0">
      <div className="text-brand-muted text-xs font-mono truncate" title={label}>{label}</div>
      <div className={clsx('text-xl font-mono font-bold', {
        'text-brand-bull': isBull === true,
        'text-brand-bear': isBull === false,
        'text-brand-text': isBull === null,
      })}>
        {displayVal}
      </div>
      {description && <div className="text-brand-muted text-xs">{description}</div>}
    </div>
  )
}
