import { useState } from 'react'
import { useHistorical } from '../hooks/useQueries'
import MultiLineChart from '../components/MultiLineChart'
import DualChart from '../components/DualChart'
import Loader from '../components/Loader'
import type { BreadthDay } from '../api/types'

const DAYS_OPTIONS = [252, 504, 1260, 3000]

const MA_LINES = [
  { key: 'pct_above_ma10',  label: '% > MA10',  color: '#ffa657' },
  { key: 'pct_above_ma20',  label: '% > MA20',  color: '#d29922' },
  { key: 'pct_above_ma50',  label: '% > MA50',  color: '#3fb950' },
  { key: 'pct_above_ma100', label: '% > MA100', color: '#388bfd' },
  { key: 'pct_above_ma200', label: '% > MA200', color: '#a371f7' },
]

export default function AboveMA() {
  const [days, setDays] = useState(504)
  const { data: history, isLoading } = useHistorical(days)

  if (isLoading || !history) return <Loader />

  const dates = history.map((r: BreadthDay) => r.date)

  const multiSeries = MA_LINES.map(({ key, label, color }) => ({
    label, color, dates,
    values: history.map((r: BreadthDay) => (r as unknown as Record<string, number | null>)[key]),
  }))

  const participationSeries = {
    dates,
    values: history.map((r: BreadthDay) => r.participation_index),
    vnindexDates: dates,
    vnindexValues: history.map((r: BreadthDay) => r.vnindex_close),
  }

  const disparitySeries = {
    dates,
    values: history.map((r: BreadthDay) => r.disparity_index),
    vnindexDates: dates,
    vnindexValues: history.map((r: BreadthDay) => r.vnindex_close),
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-brand-text">% Stocks Above Moving Average</h1>
          <p className="text-xs text-brand-muted mt-0.5">Group D — Non-internal breadth: % cổ phiếu trên MA10/20/50/100/200</p>
        </div>
        <div className="flex gap-1">
          {DAYS_OPTIONS.map(d => (
            <button key={d} onClick={() => setDays(d)}
              className={`px-3 py-1 text-xs font-mono rounded transition-colors ${
                days === d ? 'bg-brand-accent text-white' : 'bg-brand-surface text-brand-muted border border-brand-border hover:text-brand-text'
              }`}>
              {d === 252 ? '1Y' : d === 504 ? '2Y' : d === 1260 ? '5Y' : 'All'}
            </button>
          ))}
        </div>
      </div>

      {/* All 5 MAs on one chart */}
      <MultiLineChart series={multiSeries} title="% Stocks Above Moving Averages (MA10 / 20 / 50 / 100 / 200)" height={380} />

      {/* Individual panels */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <DualChart
          {...participationSeries}
          label="Participation Index"
          indicatorColor="#f0883e"
        />
        <DualChart
          {...disparitySeries}
          label="Disparity Index (vs MA150)"
          indicatorColor="#79c0ff"
          zeroLine
        />
      </div>
    </div>
  )
}
