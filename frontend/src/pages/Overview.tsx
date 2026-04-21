import { useOverview, useHistorical } from '../hooks/useQueries'
import BreadthMeter from '../components/BreadthMeter'
import IndicatorCard from '../components/IndicatorCard'
import Loader, { ErrorMsg } from '../components/Loader'
import { retColor } from '../utils/format'
import type { BreadthDay } from '../api/types'

const GROUP_A = [
  { key: 'mcclellan_osc',  label: 'McClellan Osc',    bull: (v: number) => v > 0 },
  { key: 'mcclellan_sum',  label: 'McClellan Sum',     bull: (v: number) => v > 0 },
  { key: 'ad_ratio_5d',    label: 'A/D Ratio 5d',      bull: (v: number) => v > 0.5 },
  { key: 'ad_ratio_10d',   label: 'A/D Ratio 10d',     bull: (v: number) => v > 0.5 },
  { key: 'breadth_thrust', label: 'Breadth Thrust',    bull: (v: number) => v > 0.5 },
  { key: 'ad_oscillator',  label: 'A/D Oscillator',    bull: (v: number) => v > 0 },
  { key: 'roc5_ad',        label: 'ROC5 A/D',          bull: (v: number) => v > 0 },
]
const GROUP_B = [
  { key: 'nh_nl_osc',      label: 'NH-NL Osc',         bull: (v: number) => v > 0 },
  { key: 'nh_nl_ratio',    label: 'NH-NL Ratio',        bull: (v: number) => v > 0.5 },
]
const GROUP_C = [
  { key: 'uv_dv_ratio',        label: 'UV/DV Ratio',       bull: (v: number) => v > 1 },
  { key: 'up_volume_pct',      label: 'Up Volume %',        bull: (v: number) => v > 50, format: 'pct' as const },
]
const GROUP_D = [
  { key: 'pct_above_ma10',   label: '% > MA10',   bull: (v: number) => v > 50, format: 'pct' as const },
  { key: 'pct_above_ma20',   label: '% > MA20',   bull: (v: number) => v > 50, format: 'pct' as const },
  { key: 'pct_above_ma50',   label: '% > MA50',   bull: (v: number) => v > 50, format: 'pct' as const },
  { key: 'pct_above_ma100',  label: '% > MA100',  bull: (v: number) => v > 50, format: 'pct' as const },
  { key: 'pct_above_ma200',  label: '% > MA200',  bull: (v: number) => v > 50, format: 'pct' as const },
  { key: 'disparity_index',  label: 'Disparity',  bull: (v: number) => v > 0 },
]
const GROUP_E = [
  { key: 'daily_ad_ratio_2pct',   label: 'Daily AD ±2%',        bull: (v: number) => v > 1 },
  { key: 'quarterly_breadth_up',  label: 'Qtrly Breadth Up',    bull: (v: number) => v > 50, format: 'pct' as const },
  { key: 'quarterly_breadth_down',label: 'Qtrly Breadth Down',  bull: (v: number) => v < 30, format: 'pct' as const },
]

function SectionHeader({ title, count }: { title: string; count: number }) {
  return (
    <div className="flex items-center gap-2 mt-6 mb-3">
      <span className="text-xs font-mono text-brand-muted uppercase tracking-widest">{title}</span>
      <span className="text-xs font-mono text-brand-muted">({count})</span>
      <div className="flex-1 border-t border-brand-border" />
    </div>
  )
}

type GroupItem = { key: string; label: string; bull: (v: number) => boolean; format?: 'pct' | 'number' }

function CardGrid({ items, row }: { items: GroupItem[]; row: BreadthDay }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-7 gap-2">
      {items.map(({ key, label, bull, format }) => (
        <IndicatorCard
          key={key}
          label={label}
          value={(row as unknown as Record<string, number | null>)[key]}
          bullCondition={bull}
          format={format ?? 'number'}
        />
      ))}
    </div>
  )
}

export default function Overview() {
  const { data: overview, isLoading, isError } = useOverview()
  const { data: history } = useHistorical(252)

  if (isLoading) return <Loader />
  if (isError || !overview) return <ErrorMsg message="Không thể kết nối API" />

  const row = overview.latest
  const prev = history?.[history.length - 6]  // ~1 tuần trước
  const vnChange = row.vnindex_close && prev?.vnindex_close
    ? ((row.vnindex_close / prev.vnindex_close - 1) * 100)
    : null

  return (
    <div className="space-y-2">
      {/* Header row */}
      <div className="flex items-start gap-4 flex-wrap">
        {/* Gauge */}
        <BreadthMeter
          score={overview.breadth_score}
          label={overview.breadth_label}
          signalsActive={overview.signals_active}
        />

        {/* Market snapshot */}
        <div className="card flex-1 min-w-[240px] space-y-3">
          <div className="text-brand-muted text-xs font-mono uppercase tracking-widest">Market Snapshot</div>
          <div>
            <div className="text-brand-muted text-xs">VNINDEX</div>
            <div className="text-2xl font-mono font-bold text-brand-text">
              {row.vnindex_close ? row.vnindex_close.toLocaleString('vi-VN') : '—'}
            </div>
            {vnChange != null && (
              <div className={`text-sm font-mono ${retColor(vnChange)}`}>
                {vnChange >= 0 ? '+' : ''}{vnChange.toFixed(2)}% (5d)
              </div>
            )}
          </div>

          <div className="grid grid-cols-3 gap-3 text-center pt-2 border-t border-brand-border">
            <div>
              <div className="text-brand-bull text-lg font-mono font-bold">{row.advances ?? '—'}</div>
              <div className="text-xs text-brand-muted">Advances</div>
            </div>
            <div>
              <div className="text-brand-muted text-lg font-mono font-bold">{row.unchanged ?? '—'}</div>
              <div className="text-xs text-brand-muted">Unchanged</div>
            </div>
            <div>
              <div className="text-brand-bear text-lg font-mono font-bold">{row.declines ?? '—'}</div>
              <div className="text-xs text-brand-muted">Declines</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-center pt-2 border-t border-brand-border">
            <div>
              <div className="text-brand-bull text-base font-mono font-bold">{row.new_highs ?? '—'}</div>
              <div className="text-xs text-brand-muted">New Highs</div>
            </div>
            <div>
              <div className="text-brand-bear text-base font-mono font-bold">{row.new_lows ?? '—'}</div>
              <div className="text-xs text-brand-muted">New Lows</div>
            </div>
          </div>

          <div className="text-xs text-brand-muted text-right font-mono">{row.date}</div>
        </div>
      </div>

      {/* Indicator groups */}
      <SectionHeader title="Group A — Advance / Decline" count={GROUP_A.length} />
      <CardGrid items={GROUP_A} row={row} />

      <SectionHeader title="Group B — New High / New Low" count={GROUP_B.length} />
      <CardGrid items={GROUP_B} row={row} />

      <SectionHeader title="Group C — Volume Breadth" count={GROUP_C.length} />
      <CardGrid items={GROUP_C} row={row} />

      <SectionHeader title="Group D — % Above Moving Average" count={GROUP_D.length} />
      <CardGrid items={GROUP_D} row={row} />

      <SectionHeader title="Group E — Return-Based Breadth" count={GROUP_E.length} />
      <CardGrid items={GROUP_E} row={row} />
    </div>
  )
}
