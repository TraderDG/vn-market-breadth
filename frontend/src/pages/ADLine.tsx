import { useState } from 'react'
import { useIndicatorSeries } from '../hooks/useQueries'
import DualChart from '../components/DualChart'
import Loader, { ErrorMsg } from '../components/Loader'

const DAYS_OPTIONS = [252, 504, 1260, 3000]
const INDICATORS = [
  { id: 'adline_vn30',         label: 'A/D Line (VN30)',               color: '#388bfd', zero: false },
  { id: 'mcclellan_osc_vn100', label: 'McClellan Oscillator (VN100)',  color: '#a371f7', zero: true  },
  { id: 'mcclellan_sum',       label: 'McClellan Summation (VN100)',   color: '#79c0ff', zero: true  },
  { id: 'ad_oscillator',       label: 'A/D Line Oscillator (VN30)',    color: '#d29922', zero: true  },
  { id: 'abs_breadth_index',   label: 'Absolute Breadth Index (VN30)', color: '#f0883e', zero: false },
  { id: 'roc5_ad',             label: 'ROC5 of A/D Line (VN30)',       color: '#ffa657', zero: true  },
  { id: 'declines_vn30',       label: 'Declines Count (VN30)',         color: '#f85149', zero: false },
]

function IndicatorPanel({ id, label, color, zero, days }: {
  id: string; label: string; color: string; zero: boolean; days: number
}) {
  const { data, isLoading, isError } = useIndicatorSeries(id, days)
  if (isLoading) return <Loader />
  if (isError || !data) return <ErrorMsg />
  return (
    <DualChart
      dates={data.dates}
      values={data.values}
      vnindexDates={data.vnindex_dates}
      vnindexValues={data.vnindex_values}
      label={label}
      indicatorColor={color}
      zeroLine={zero}
    />
  )
}

export default function ADLine() {
  const [days, setDays] = useState(504)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-brand-text">Advance / Decline Indicators</h1>
          <p className="text-xs text-brand-muted mt-0.5">
            A/D Line và McClellan — VN30 (A/D) và VN100 (McClellan)
          </p>
        </div>
        <div className="flex gap-1">
          {DAYS_OPTIONS.map(d => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1 text-xs font-mono rounded transition-colors ${
                days === d ? 'bg-brand-accent text-white' : 'bg-brand-surface text-brand-muted border border-brand-border hover:text-brand-text'
              }`}
            >
              {d === 252 ? '1Y' : d === 504 ? '2Y' : d === 1260 ? '5Y' : 'All'}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {INDICATORS.map(ind => (
          <IndicatorPanel key={ind.id} {...ind} days={days} />
        ))}
      </div>
    </div>
  )
}
