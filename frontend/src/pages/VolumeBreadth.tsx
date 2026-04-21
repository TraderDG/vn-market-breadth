import { useState } from 'react'
import { useIndicatorSeries, useSignalHistory } from '../hooks/useQueries'
import DualChart from '../components/DualChart'
import Loader, { ErrorMsg } from '../components/Loader'
import { fmt, retColor } from '../utils/format'

const DAYS_OPTIONS = [252, 504, 1260, 3000]
const INDICATORS = [
  { id: 'up_volume_pct',       label: 'Up Volume % of Total',          color: '#3fb950', zero: false },
  { id: 'uv_dv_ratio',         label: 'Up / Down Volume Ratio',         color: '#58a6ff', zero: false },
  { id: 'net_up_volume_ema10', label: 'Net Up Volume (10d EMA)',         color: '#a371f7', zero: true  },
]

function IndicatorPanel({ id, label, color, zero, days }: {
  id: string; label: string; color: string; zero: boolean; days: number
}) {
  const { data, isLoading, isError } = useIndicatorSeries(id, days)
  if (isLoading) return <Loader />
  if (isError || !data) return <ErrorMsg />
  return (
    <DualChart
      dates={data.dates} values={data.values}
      vnindexDates={data.vnindex_dates} vnindexValues={data.vnindex_values}
      label={label} indicatorColor={color} zeroLine={zero}
    />
  )
}

export default function VolumeBreadth() {
  const [days, setDays] = useState(504)
  const { data: volumeThrust } = useSignalHistory('VOLUME_THRUST')

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-brand-text">Volume Breadth</h1>
          <p className="text-xs text-brand-muted mt-0.5">Group C — Up/Down Volume phân tích theo ngày</p>
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

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {INDICATORS.map(ind => <IndicatorPanel key={ind.id} {...ind} days={days} />)}
      </div>

      {/* Volume Thrust events */}
      {volumeThrust && volumeThrust.length > 0 && (
        <div className="card">
          <div className="text-sm font-semibold text-brand-accent mb-3">Volume Thrust Events — Forward Returns</div>
          <table className="w-full text-xs font-mono">
            <thead>
              <tr className="text-brand-muted border-b border-brand-border">
                <th className="text-left py-1.5 pr-4">Ngày</th>
                <th className="text-right pr-4">VNINDEX</th>
                <th className="text-right pr-4">+1M</th>
                <th className="text-right pr-4">+3M</th>
                <th className="text-right pr-4">+6M</th>
                <th className="text-right">+1Y</th>
              </tr>
            </thead>
            <tbody>
              {volumeThrust.map(e => (
                <tr key={e.id} className="border-b border-brand-border/30 hover:bg-brand-border/20">
                  <td className="py-1.5 pr-4 text-brand-accent">{e.date}</td>
                  <td className="text-right pr-4">{fmt(e.vnindex_at_signal, 0)}</td>
                  <td className={`text-right pr-4 ${retColor(e.fwd_return_1m)}`}>{e.fwd_return_1m != null ? `${e.fwd_return_1m >= 0 ? '+' : ''}${e.fwd_return_1m.toFixed(1)}%` : '—'}</td>
                  <td className={`text-right pr-4 ${retColor(e.fwd_return_3m)}`}>{e.fwd_return_3m != null ? `${e.fwd_return_3m >= 0 ? '+' : ''}${e.fwd_return_3m.toFixed(1)}%` : '—'}</td>
                  <td className={`text-right pr-4 ${retColor(e.fwd_return_6m)}`}>{e.fwd_return_6m != null ? `${e.fwd_return_6m >= 0 ? '+' : ''}${e.fwd_return_6m.toFixed(1)}%` : '—'}</td>
                  <td className={`text-right ${retColor(e.fwd_return_1y)}`}>{e.fwd_return_1y != null ? `${e.fwd_return_1y >= 0 ? '+' : ''}${e.fwd_return_1y.toFixed(1)}%` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
