import { useState } from 'react'
import { useSignalHistory, useSignalStats } from '../hooks/useQueries'
import Loader from '../components/Loader'
import { fmt, retColor, signalColor } from '../utils/format'

type SigType = 'ALL' | 'BREADTH_THRUST' | 'HINDENBURG_OMEN' | 'VOLUME_THRUST'

const SIGNAL_META: Record<string, { label: string; description: string }> = {
  BREADTH_THRUST: {
    label: 'Breadth Thrust (Zweig)',
    description: 'Breadth Thrust < 0.40 rồi vượt > 0.615 trong 10 ngày — tín hiệu momentum cực mạnh'
  },
  HINDENBURG_OMEN: {
    label: 'Hindenburg Omen',
    description: 'NH% > 2.2% VÀ NL% > 2.2% VÀ McClellan Osc < 0 — cảnh báo thị trường phân kỳ'
  },
  VOLUME_THRUST: {
    label: 'Volume Thrust',
    description: 'Up Volume % > 90% trong cửa sổ 10 ngày — thanh khoản tích lũy cực mạnh'
  },
}

function StatBox({ label, value, isGood }: { label: string; value: string; isGood?: boolean }) {
  return (
    <div className="text-center">
      <div className={`text-lg font-mono font-bold ${isGood === true ? 'text-brand-bull' : isGood === false ? 'text-brand-bear' : 'text-brand-text'}`}>
        {value}
      </div>
      <div className="text-xs text-brand-muted">{label}</div>
    </div>
  )
}

function fmtRet(v: number | null | undefined) {
  if (v == null) return '—'
  return `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`
}

export default function Signals() {
  const [filter, setFilter] = useState<SigType>('ALL')
  const { data: stats, isLoading: statsLoading } = useSignalStats()
  const { data: events, isLoading: eventsLoading } = useSignalHistory(
    filter === 'ALL' ? undefined : filter
  )

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-brand-text">Signal Events & Statistics</h1>
        <p className="text-xs text-brand-muted mt-0.5">Lịch sử tất cả tín hiệu đặc biệt và forward returns</p>
      </div>

      {/* Signal stats cards */}
      {statsLoading ? <Loader /> : stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(SIGNAL_META).map(([type, meta]) => {
            const s = stats[type]
            if (!s) return null
            const isBullSignal = type !== 'HINDENBURG_OMEN'
            return (
              <div key={type} className="card space-y-3">
                <div>
                  <div className={`text-sm font-semibold ${signalColor(type)}`}>{meta.label}</div>
                  <div className="text-xs text-brand-muted mt-1">{meta.description}</div>
                </div>
                <div className="text-xs font-mono text-brand-muted">
                  {s.count} sự kiện trong lịch sử
                </div>
                <div className="grid grid-cols-4 gap-2 pt-2 border-t border-brand-border">
                  <StatBox label="+1M avg" value={fmtRet(s.avg_fwd_1m)} isGood={s.avg_fwd_1m != null ? (isBullSignal ? s.avg_fwd_1m > 0 : s.avg_fwd_1m < 0) : undefined} />
                  <StatBox label="+3M avg" value={fmtRet(s.avg_fwd_3m)} isGood={s.avg_fwd_3m != null ? (isBullSignal ? s.avg_fwd_3m > 0 : s.avg_fwd_3m < 0) : undefined} />
                  <StatBox label="+6M avg" value={fmtRet(s.avg_fwd_6m)} isGood={s.avg_fwd_6m != null ? (isBullSignal ? s.avg_fwd_6m > 0 : s.avg_fwd_6m < 0) : undefined} />
                  <StatBox label="+1Y avg" value={fmtRet(s.avg_fwd_1y)} isGood={s.avg_fwd_1y != null ? (isBullSignal ? s.avg_fwd_1y > 0 : s.avg_fwd_1y < 0) : undefined} />
                </div>
                <div className="grid grid-cols-4 gap-2">
                  <StatBox label="+1M win" value={s.win_rate_1m != null ? `${s.win_rate_1m}%` : '—'} />
                  <StatBox label="+3M win" value={s.win_rate_3m != null ? `${s.win_rate_3m}%` : '—'} />
                  <StatBox label="+6M win" value={s.win_rate_6m != null ? `${s.win_rate_6m}%` : '—'} />
                  <StatBox label="+1Y win" value={s.win_rate_1y != null ? `${s.win_rate_1y}%` : '—'} />
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Filter */}
      <div className="flex gap-2 flex-wrap">
        {(['ALL', 'BREADTH_THRUST', 'HINDENBURG_OMEN', 'VOLUME_THRUST'] as SigType[]).map(t => (
          <button key={t} onClick={() => setFilter(t)}
            className={`px-3 py-1 text-xs font-mono rounded transition-colors ${
              filter === t ? 'bg-brand-accent text-white' : 'bg-brand-surface text-brand-muted border border-brand-border hover:text-brand-text'
            }`}>
            {t === 'ALL' ? 'All Signals' : SIGNAL_META[t]?.label ?? t}
          </button>
        ))}
      </div>

      {/* Events table */}
      {eventsLoading ? <Loader /> : (
        <div className="card overflow-x-auto">
          <table className="w-full text-xs font-mono min-w-[640px]">
            <thead>
              <tr className="text-brand-muted border-b border-brand-border">
                <th className="text-left py-2 pr-4">Ngày</th>
                <th className="text-left pr-4">Signal</th>
                <th className="text-right pr-4">VNINDEX</th>
                <th className="text-right pr-4">+1M</th>
                <th className="text-right pr-4">+3M</th>
                <th className="text-right pr-4">+6M</th>
                <th className="text-right">+1Y</th>
              </tr>
            </thead>
            <tbody>
              {events?.map(e => (
                <tr key={e.id} className="border-b border-brand-border/30 hover:bg-brand-border/20">
                  <td className="py-1.5 pr-4 text-brand-text">{e.date}</td>
                  <td className={`pr-4 ${signalColor(e.signal_type)}`}>
                    {SIGNAL_META[e.signal_type]?.label ?? e.signal_type}
                  </td>
                  <td className="text-right pr-4">{fmt(e.vnindex_at_signal, 0)}</td>
                  <td className={`text-right pr-4 ${retColor(e.fwd_return_1m)}`}>{fmtRet(e.fwd_return_1m)}</td>
                  <td className={`text-right pr-4 ${retColor(e.fwd_return_3m)}`}>{fmtRet(e.fwd_return_3m)}</td>
                  <td className={`text-right pr-4 ${retColor(e.fwd_return_6m)}`}>{fmtRet(e.fwd_return_6m)}</td>
                  <td className={`text-right ${retColor(e.fwd_return_1y)}`}>{fmtRet(e.fwd_return_1y)}</td>
                </tr>
              ))}
              {(!events || events.length === 0) && (
                <tr><td colSpan={7} className="text-center py-8 text-brand-muted">Không có signal events</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
