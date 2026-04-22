import { useHistorical } from '../hooks/useQueries'
import Loader, { ErrorMsg } from '../components/Loader'
import type { BreadthDay } from '../api/types'

const RSI_25_COLS = [
  { key: 'rsi_25_vnindex', label: 'VNINDEX' },
  { key: 'rsi_25_vn100',   label: 'VN100' },
  { key: 'rsi_25_vn30',    label: 'VN30' },
  { key: 'rsi_25_hnx30',   label: 'HNX30' },
  { key: 'rsi_25_hnx',     label: 'HNX' },
]
const RSI_75_COLS = [
  { key: 'rsi_75_vnindex', label: 'VNINDEX' },
  { key: 'rsi_75_vn100',   label: 'VN100' },
  { key: 'rsi_75_vn30',    label: 'VN30' },
  { key: 'rsi_75_hnx30',   label: 'HNX30' },
  { key: 'rsi_75_hnx',     label: 'HNX' },
]

function rsi25Color(v: number | null): string {
  if (v == null) return 'text-brand-muted'
  if (v > 30) return 'text-brand-bear font-semibold'
  if (v > 15) return 'text-brand-bear'
  if (v > 5)  return 'text-brand-muted'
  return 'text-brand-bull'
}

function rsi75Color(v: number | null): string {
  if (v == null) return 'text-brand-muted'
  if (v > 40) return 'text-brand-bull font-semibold'
  if (v > 20) return 'text-brand-bull'
  if (v > 10) return 'text-brand-muted'
  return 'text-brand-bear'
}

function maColor(v: number | null): string {
  if (v == null) return 'text-brand-muted'
  if (v > 70) return 'text-brand-bull font-semibold'
  if (v > 50) return 'text-brand-bull'
  if (v > 30) return 'text-brand-bear'
  return 'text-brand-bear font-semibold'
}

function dispColor(v: number | null): string {
  if (v == null) return 'text-brand-muted'
  if (v > 5)   return 'text-brand-bull font-semibold'
  if (v > 0)   return 'text-brand-bull'
  if (v > -5)  return 'text-brand-bear'
  return 'text-brand-bear font-semibold'
}

function fmt(v: number | null, decimals = 1): string {
  if (v == null) return '—'
  return `${v.toFixed(decimals)}%`
}

function fmtDisp(v: number | null): string {
  if (v == null) return '—'
  return `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`
}

export default function AboveMA() {
  const { data: history, isLoading, isError } = useHistorical(60)

  if (isLoading) return <Loader />
  if (isError || !history) return <ErrorMsg message="Không thể kết nối API" />

  const rows = [...history].reverse()
  const latest = rows[0]

  const r = (latest as unknown as Record<string, number | null>)

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-brand-text">% Above MA & RSI Breadth</h1>
        <p className="text-xs text-brand-muted mt-0.5">
          % cổ phiếu trên MA100 (VN100), RSI quá bán / quá mua theo 5 chỉ số — 60 phiên gần nhất
        </p>
      </div>

      {/* Current snapshot */}
      {latest && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* % Above MA100 */}
          <div className="card">
            <div className="text-xs text-brand-muted font-mono mb-2">% ABOVE MA100 (VN100)</div>
            <div className={`text-3xl font-mono font-bold ${maColor(r['above_ma100_vn100'])}`}>
              {fmt(r['above_ma100_vn100'])}
            </div>
            <div className="text-xs text-brand-muted mt-1">
              Disparity: <span className={dispColor(r['disparity_index'])}>{fmtDisp(r['disparity_index'])}</span>
            </div>
          </div>

          {/* RSI < 25 summary */}
          <div className="card">
            <div className="text-xs text-brand-muted font-mono mb-2">% RSI &lt; 25 (OVERSOLD)</div>
            <div className="grid grid-cols-3 gap-1 text-xs font-mono">
              {RSI_25_COLS.map(({ key, label }) => (
                <div key={key} className="text-center">
                  <div className={`text-base font-bold ${rsi25Color(r[key])}`}>{fmt(r[key], 1)}</div>
                  <div className="text-brand-muted text-xs">{label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* RSI > 75 summary */}
          <div className="card">
            <div className="text-xs text-brand-muted font-mono mb-2">% RSI &gt; 75 (OVERBOUGHT)</div>
            <div className="grid grid-cols-3 gap-1 text-xs font-mono">
              {RSI_75_COLS.map(({ key, label }) => (
                <div key={key} className="text-center">
                  <div className={`text-base font-bold ${rsi75Color(r[key])}`}>{fmt(r[key], 1)}</div>
                  <div className="text-brand-muted text-xs">{label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Historical table */}
      <div className="card overflow-x-auto">
        <div className="text-sm font-semibold text-brand-text mb-3">Lịch sử 60 phiên</div>
        <table className="w-full text-xs font-mono border-collapse">
          <thead>
            <tr className="border-b border-brand-border text-brand-muted text-right">
              <th className="text-left py-2 pr-3 font-normal sticky left-0 bg-brand-surface">Date</th>
              <th className="py-2 px-2 font-normal">VNIndex</th>
              <th className="py-2 px-2 font-normal whitespace-nowrap">MA100%</th>
              <th className="py-2 px-2 font-normal whitespace-nowrap">Disp</th>
              <th className="py-2 px-2 font-normal text-brand-bear whitespace-nowrap">R&lt;25 VNI</th>
              <th className="py-2 px-2 font-normal text-brand-bear whitespace-nowrap">R&lt;25 V100</th>
              <th className="py-2 px-2 font-normal text-brand-bear whitespace-nowrap">R&lt;25 V30</th>
              <th className="py-2 px-2 font-normal text-brand-bear whitespace-nowrap">R&lt;25 HNX</th>
              <th className="py-2 px-2 font-normal text-brand-bull whitespace-nowrap">R&gt;75 VNI</th>
              <th className="py-2 px-2 font-normal text-brand-bull whitespace-nowrap">R&gt;75 V100</th>
              <th className="py-2 px-2 font-normal text-brand-bull whitespace-nowrap">R&gt;75 V30</th>
              <th className="py-2 px-2 font-normal text-brand-bull whitespace-nowrap">R&gt;75 HNX</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row: BreadthDay, i: number) => {
              const rv = row as unknown as Record<string, number | null>
              return (
                <tr
                  key={row.date}
                  className={`border-b border-brand-border/40 hover:bg-brand-surface/60 ${i === 0 ? 'bg-brand-surface' : ''}`}
                >
                  <td className={`py-1.5 pr-3 text-left sticky left-0 ${i === 0 ? 'bg-brand-surface text-brand-accent font-semibold' : 'text-brand-muted'}`}>
                    {row.date}
                  </td>
                  <td className="py-1.5 px-2 text-right text-brand-text">
                    {row.vnindex_close ? row.vnindex_close.toLocaleString('vi-VN') : '—'}
                  </td>
                  <td className={`py-1.5 px-2 text-right ${maColor(rv['above_ma100_vn100'])}`}>
                    {fmt(rv['above_ma100_vn100'])}
                  </td>
                  <td className={`py-1.5 px-2 text-right ${dispColor(rv['disparity_index'])}`}>
                    {fmtDisp(rv['disparity_index'])}
                  </td>
                  <td className={`py-1.5 px-2 text-right ${rsi25Color(rv['rsi_25_vnindex'])}`}>{fmt(rv['rsi_25_vnindex'])}</td>
                  <td className={`py-1.5 px-2 text-right ${rsi25Color(rv['rsi_25_vn100'])}`}>{fmt(rv['rsi_25_vn100'])}</td>
                  <td className={`py-1.5 px-2 text-right ${rsi25Color(rv['rsi_25_vn30'])}`}>{fmt(rv['rsi_25_vn30'])}</td>
                  <td className={`py-1.5 px-2 text-right ${rsi25Color(rv['rsi_25_hnx'])}`}>{fmt(rv['rsi_25_hnx'])}</td>
                  <td className={`py-1.5 px-2 text-right ${rsi75Color(rv['rsi_75_vnindex'])}`}>{fmt(rv['rsi_75_vnindex'])}</td>
                  <td className={`py-1.5 px-2 text-right ${rsi75Color(rv['rsi_75_vn100'])}`}>{fmt(rv['rsi_75_vn100'])}</td>
                  <td className={`py-1.5 px-2 text-right ${rsi75Color(rv['rsi_75_vn30'])}`}>{fmt(rv['rsi_75_vn30'])}</td>
                  <td className={`py-1.5 px-2 text-right ${rsi75Color(rv['rsi_75_hnx'])}`}>{fmt(rv['rsi_75_hnx'])}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
