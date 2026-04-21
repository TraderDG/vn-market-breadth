import { useHistorical } from '../hooks/useQueries'
import Loader, { ErrorMsg } from '../components/Loader'
import type { BreadthDay } from '../api/types'

const MA_COLS = [
  { key: 'pct_above_ma10',  label: 'MA10',  short: '10' },
  { key: 'pct_above_ma20',  label: 'MA20',  short: '20' },
  { key: 'pct_above_ma50',  label: 'MA50',  short: '50' },
  { key: 'pct_above_ma100', label: 'MA100', short: '100' },
  { key: 'pct_above_ma200', label: 'MA200', short: '200' },
  { key: 'disparity_index', label: 'Disparity', short: 'Disp', isDisparity: true },
]

function cellColor(value: number | null, isDisparity = false): string {
  if (value == null) return 'text-brand-muted'
  const bull = isDisparity ? value > 0 : value > 50
  const strong = isDisparity ? Math.abs(value) > 5 : (value > 70 || value < 30)
  if (bull) return strong ? 'text-brand-bull font-semibold' : 'text-brand-bull'
  return strong ? 'text-brand-bear font-semibold' : 'text-brand-bear'
}

function cellBg(value: number | null, isDisparity = false): string {
  if (value == null) return ''
  const bull = isDisparity ? value > 0 : value > 50
  if (bull) return 'bg-green-900/20'
  return 'bg-red-900/20'
}

function fmt(value: number | null, isDisparity = false): string {
  if (value == null) return '—'
  if (isDisparity) return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`
  return `${value.toFixed(1)}%`
}

export default function AboveMA() {
  const { data: history, isLoading, isError } = useHistorical(60)

  if (isLoading) return <Loader />
  if (isError || !history) return <ErrorMsg message="Không thể kết nối API" />

  const rows = [...history].reverse()
  const latest = rows[0]

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-brand-text">% Stocks Above Moving Average</h1>
        <p className="text-xs text-brand-muted mt-0.5">Group D — % cổ phiếu trên MA10 / MA20 / MA50 / MA100 / MA200 và Disparity Index</p>
      </div>

      {/* Current values summary */}
      {latest && (
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
          {MA_COLS.map(({ key, label, isDisparity }) => {
            const val = (latest as unknown as Record<string, number | null>)[key]
            return (
              <div key={key} className="card text-center py-3">
                <div className="text-xs text-brand-muted font-mono mb-1">% {label}</div>
                <div className={`text-xl font-mono font-bold ${cellColor(val, isDisparity)}`}>
                  {fmt(val, isDisparity)}
                </div>
                <div className={`text-xs mt-1 ${val != null && (isDisparity ? val > 0 : val > 50) ? 'text-brand-bull' : 'text-brand-bear'}`}>
                  {val != null ? (isDisparity ? (val > 0 ? 'Bull' : 'Bear') : (val > 50 ? 'Bull' : 'Bear')) : '—'}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Historical table */}
      <div className="card overflow-x-auto">
        <div className="text-sm font-semibold text-brand-text mb-3">Lịch sử 60 phiên gần nhất</div>
        <table className="w-full text-xs font-mono border-collapse">
          <thead>
            <tr className="border-b border-brand-border text-brand-muted text-right">
              <th className="text-left py-2 pr-4 font-normal">Date</th>
              <th className="py-2 px-3 font-normal">VNIndex</th>
              {MA_COLS.map(({ key, label }) => (
                <th key={key} className="py-2 px-3 font-normal whitespace-nowrap">% {label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row: BreadthDay, i: number) => {
              const r = row as unknown as Record<string, number | null>
              return (
                <tr
                  key={row.date}
                  className={`border-b border-brand-border/40 hover:bg-brand-surface/60 transition-colors ${i === 0 ? 'bg-brand-surface' : ''}`}
                >
                  <td className={`py-1.5 pr-4 text-left ${i === 0 ? 'text-brand-accent font-semibold' : 'text-brand-muted'}`}>
                    {row.date}
                  </td>
                  <td className="py-1.5 px-3 text-right text-brand-text">
                    {row.vnindex_close ? row.vnindex_close.toLocaleString('vi-VN') : '—'}
                  </td>
                  {MA_COLS.map(({ key, isDisparity }) => {
                    const val = r[key]
                    return (
                      <td key={key} className={`py-1.5 px-3 text-right ${cellColor(val, isDisparity)} ${cellBg(val, isDisparity)}`}>
                        {fmt(val, isDisparity)}
                      </td>
                    )
                  })}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
