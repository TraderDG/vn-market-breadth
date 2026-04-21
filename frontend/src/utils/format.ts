export const fmt = (v: number | null | undefined, decimals = 2): string => {
  if (v == null || isNaN(v)) return '—'
  return v.toFixed(decimals)
}

export const fmtPct = (v: number | null | undefined): string => {
  if (v == null || isNaN(v)) return '—'
  return `${v.toFixed(1)}%`
}

export const fmtScore = (v: number): string => v.toFixed(1)

export const scoreColor = (score: number): string => {
  if (score >= 70) return 'text-brand-bull'
  if (score >= 55) return 'text-green-400'
  if (score >= 45) return 'text-brand-text'
  if (score >= 30) return 'text-orange-400'
  return 'text-brand-bear'
}

export const labelColor = (label: string): string => {
  if (label.includes('Extremely Bullish')) return 'text-brand-bull'
  if (label.includes('Bullish')) return 'text-green-400'
  if (label.includes('Neutral')) return 'text-brand-neutral'
  if (label.includes('Bearish') && !label.includes('Extremely')) return 'text-orange-400'
  return 'text-brand-bear'
}

export const signalColor = (type: string): string => {
  if (type === 'BREADTH_THRUST') return 'text-brand-bull'
  if (type === 'HINDENBURG_OMEN') return 'text-brand-bear'
  if (type === 'VOLUME_THRUST') return 'text-brand-accent'
  return 'text-brand-muted'
}

export const retColor = (v: number | null | undefined): string => {
  if (v == null) return 'text-brand-muted'
  return v >= 0 ? 'text-brand-bull' : 'text-brand-bear'
}
