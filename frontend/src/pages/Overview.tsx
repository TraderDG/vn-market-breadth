import { useOverview, useHistorical } from '../hooks/useQueries'
import BreadthMeter from '../components/BreadthMeter'
import IndicatorCard from '../components/IndicatorCard'
import Loader, { ErrorMsg } from '../components/Loader'
import { retColor } from '../utils/format'
import type { BreadthDay } from '../api/types'

const GROUP_AD = [
  { key: 'mcclellan_osc_vn100', label: 'McClellan Osc (VN100)', bull: (v: number) => v > 0 },
  { key: 'mcclellan_sum',       label: 'McClellan Sum',          bull: (v: number) => v > 0 },
  { key: 'ad_oscillator',       label: 'A/D Oscillator',         bull: (v: number) => v > 0 },
  { key: 'roc5_ad',             label: 'ROC5 A/D',               bull: (v: number) => v > 0 },
  { key: 'declines_vn30',       label: 'Declines (VN30)',        bull: (v: number) => v < 15 },
]

const GROUP_NHNH = [
  { key: 'new_high_52w_vn30',  label: 'New 52W High VN30',  bull: (v: number) => v > 0 },
  { key: 'new_high_1m_hnx30', label: 'New 1M High HNX30',  bull: (v: number) => v > 3 },
]

const GROUP_VOL = [
  { key: 'up_volume_pct', label: 'Up Volume %',     bull: (v: number) => v > 50, format: 'pct' as const },
  { key: 'uv_dv_ratio',   label: 'UV/DV Ratio',     bull: (v: number) => v > 1 },
  { key: 'unchanged_upcom', label: 'Unchanged UPCOM', bull: (v: number) => v < 500 },
]

const GROUP_MA = [
  { key: 'above_ma100_vn100', label: '% > MA100 (VN100)', bull: (v: number) => v > 50, format: 'pct' as const },
  { key: 'disparity_index',   label: 'Disparity Index',    bull: (v: number) => v > 0 },
]

const GROUP_RSI = [
  { key: 'rsi_25_vnindex', label: '% RSI<25 VNIdx',  bull: (v: number) => v < 10, format: 'pct' as const },
  { key: 'rsi_75_vnindex', label: '% RSI>75 VNIdx',  bull: (v: number) => v > 20, format: 'pct' as const },
  { key: 'rsi_25_vn30',    label: '% RSI<25 VN30',   bull: (v: number) => v < 10, format: 'pct' as const },
  { key: 'rsi_75_vn30',    label: '% RSI>75 VN30',   bull: (v: number) => v > 20, format: 'pct' as const },
  { key: 'bb_under_2std_hnx', label: '% Below -2σ HNX', bull: (v: number) => v < 5, format: 'pct' as const },
]

const GROUP_RET = [
  { key: 'return_12m_vn30',  label: '12M Return % VN30',   bull: (v: number) => v > 0, format: 'pct' as const },
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
  const prev = history?.[history.length - 6]
  const vnChange = row.vnindex_close && prev?.vnindex_close
    ? ((row.vnindex_close / prev.vnindex_close - 1) * 100)
    : null

  return (
    <div className="space-y-2">
      {/* Header row */}
      <div className="flex items-start gap-4 flex-wrap">
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

          <div className="grid grid-cols-2 gap-3 text-center pt-2 border-t border-brand-border">
            <div>
              <div className="text-brand-bear text-lg font-mono font-bold">
                {row.declines_vn30 ?? '—'}
              </div>
              <div className="text-xs text-brand-muted">Declines VN30</div>
            </div>
            <div>
              <div className="text-brand-muted text-lg font-mono font-bold">
                {row.unchanged_upcom ?? '—'}
              </div>
              <div className="text-xs text-brand-muted">Unchanged UPCOM</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-center pt-2 border-t border-brand-border">
            <div>
              <div className="text-brand-bull text-base font-mono font-bold">
                {row.new_high_52w_vn30 ?? '—'}
              </div>
              <div className="text-xs text-brand-muted">52W High VN30</div>
            </div>
            <div>
              <div className="text-brand-bull text-base font-mono font-bold">
                {row.new_high_1m_hnx30 ?? '—'}
              </div>
              <div className="text-xs text-brand-muted">1M High HNX30</div>
            </div>
          </div>

          <div className="text-xs text-brand-muted text-right font-mono">{row.date}</div>
        </div>
      </div>

      <SectionHeader title="A / D — Advance/Decline" count={GROUP_AD.length} />
      <CardGrid items={GROUP_AD} row={row} />

      <SectionHeader title="NH-NL — New High / New Low" count={GROUP_NHNH.length} />
      <CardGrid items={GROUP_NHNH} row={row} />

      <SectionHeader title="Volume Breadth (HNX)" count={GROUP_VOL.length} />
      <CardGrid items={GROUP_VOL} row={row} />

      <SectionHeader title="% Above MA & Disparity" count={GROUP_MA.length} />
      <CardGrid items={GROUP_MA} row={row} />

      <SectionHeader title="RSI Breadth & Bollinger" count={GROUP_RSI.length} />
      <CardGrid items={GROUP_RSI} row={row} />

      <SectionHeader title="Return Breadth" count={GROUP_RET.length} />
      <CardGrid items={GROUP_RET} row={row} />
    </div>
  )
}
