import { useState } from 'react'
import { useSectors } from '../hooks/useQueries'
import MultiLineChart from '../components/MultiLineChart'
import Loader, { ErrorMsg } from '../components/Loader'
import type { SectorData } from '../api/types'

const PERIOD_OPTIONS: { key: keyof SectorData; label: string }[] = [
  { key: 'chg_1d', label: '1D' },
  { key: 'chg_1w', label: '1W' },
  { key: 'chg_1m', label: '1M' },
  { key: 'chg_3m', label: '3M' },
  { key: 'chg_6m', label: '6M' },
  { key: 'chg_1y', label: '1Y' },
]

const SECTOR_COLORS: Record<string, string> = {
  VNFIN:  '#388bfd',
  VNMAT:  '#3fb950',
  VNIND:  '#d29922',
  VNHEAL: '#a371f7',
  VNENE:  '#f85149',
  VNCONS: '#79c0ff',
  VNCOND: '#56d364',
  VNUTI:  '#ffa657',
  VNIT:   '#ff7b72',
  VNREAL: '#e3b341',
}

function heatColor(value: number | null): string {
  if (value == null) return 'bg-brand-surface border-brand-border'
  if (value > 5)  return 'bg-green-700/60 border-green-600'
  if (value > 2)  return 'bg-green-800/50 border-green-700'
  if (value > 0)  return 'bg-green-900/40 border-green-800'
  if (value > -2) return 'bg-red-900/40 border-red-800'
  if (value > -5) return 'bg-red-800/50 border-red-700'
  return 'bg-red-700/60 border-red-600'
}

function textColor(value: number | null): string {
  if (value == null) return 'text-brand-muted'
  if (value > 0) return 'text-green-400'
  if (value < 0) return 'text-red-400'
  return 'text-brand-muted'
}

function fmtChg(value: number | null): string {
  if (value == null) return '—'
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

function SectorCard({ s, period }: { s: SectorData; period: keyof SectorData }) {
  const chg = s[period] as number | null
  return (
    <div className={`rounded-lg border p-3 flex flex-col gap-1 transition-all ${heatColor(chg)}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono font-bold text-brand-text">{s.code}</span>
        <span className={`text-sm font-mono font-bold ${textColor(chg)}`}>{fmtChg(chg)}</span>
      </div>
      <div className="text-xs text-brand-muted">{s.label}</div>
      <div className="text-xs font-mono text-brand-muted mt-1">
        Ratio: {s.current != null ? s.current.toFixed(3) : '—'}
      </div>
    </div>
  )
}

function RankTable({ sectors, period }: { sectors: SectorData[]; period: keyof SectorData }) {
  const sorted = [...sectors].sort((a, b) => {
    const av = a[period] as number | null
    const bv = b[period] as number | null
    if (av == null) return 1
    if (bv == null) return -1
    return bv - av
  })

  return (
    <div className="card">
      <div className="text-sm font-semibold text-brand-text mb-3">Sector Ranking</div>
      <table className="w-full text-xs font-mono">
        <thead>
          <tr className="text-brand-muted border-b border-brand-border">
            <th className="text-left py-1.5 font-normal">#</th>
            <th className="text-left py-1.5 font-normal">Sector</th>
            <th className="text-right py-1.5 pr-2 font-normal">Change</th>
            <th className="text-right py-1.5 font-normal">Ratio</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((s, i) => {
            const chg = s[period] as number | null
            return (
              <tr key={s.code} className="border-b border-brand-border/40 hover:bg-brand-surface/50">
                <td className="py-1.5 text-brand-muted pr-2">{i + 1}</td>
                <td className="py-1.5">
                  <span className="font-bold text-brand-text">{s.code}</span>
                  <span className="text-brand-muted ml-2">{s.label}</span>
                </td>
                <td className={`py-1.5 pr-2 text-right font-bold ${textColor(chg)}`}>{fmtChg(chg)}</td>
                <td className="py-1.5 text-right text-brand-muted">{s.current != null ? s.current.toFixed(3) : '—'}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export default function Sectors() {
  const { data, isLoading, isError } = useSectors()
  const [period, setPeriod] = useState<keyof SectorData>('chg_1m')

  if (isLoading) return <Loader />
  if (isError || !data) return <ErrorMsg message="Không thể tải dữ liệu ngành" />

  const chartSeries = Object.entries(data.series).map(([code, values]) => ({
    label: code,
    color: SECTOR_COLORS[code] ?? '#8b949e',
    dates: data.dates,
    values,
    lineWidth: 1.5,
  }))

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-lg font-semibold text-brand-text">Sector Relative Performance</h1>
          <p className="text-xs text-brand-muted mt-0.5">
            Hiệu suất 10 ngành so với VNINDEX (ratio) — dữ liệu đến {data.last_date ?? '—'}
          </p>
        </div>
        <div className="flex gap-1">
          {PERIOD_OPTIONS.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setPeriod(key)}
              className={`px-3 py-1 text-xs font-mono rounded transition-colors ${
                period === key
                  ? 'bg-brand-accent text-white'
                  : 'bg-brand-surface text-brand-muted border border-brand-border hover:text-brand-text'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Heatmap grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
        {data.sectors.map(s => (
          <SectorCard key={s.code} s={s} period={period} />
        ))}
      </div>

      {/* Ranking table + chart */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <RankTable sectors={data.sectors} period={period} />
        <MultiLineChart
          series={chartSeries}
          title="Relative Performance vs VNINDEX (2Y)"
          height={300}
        />
      </div>
    </div>
  )
}
