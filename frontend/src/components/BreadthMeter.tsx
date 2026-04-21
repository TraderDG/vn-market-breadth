import { scoreColor, labelColor } from '../utils/format'

interface Props {
  score: number
  label: string
  signalsActive: string[]
}

export default function BreadthMeter({ score, label, signalsActive }: Props) {
  // SVG arc gauge: 0=left(bear), 100=right(bull), 0° start=180°
  const clampedScore = Math.max(0, Math.min(100, score))
  const angle = (clampedScore / 100) * 180 - 90 // -90° (bear) → +90° (bull)

  const polarToXY = (angleDeg: number, r: number) => {
    const rad = ((angleDeg - 90) * Math.PI) / 180
    return { x: 120 + r * Math.cos(rad), y: 110 + r * Math.sin(rad) }
  }

  void angle // used via clampedScore in transform below
  void polarToXY

  const signalLabels: Record<string, string> = {
    BREADTH_THRUST: 'Breadth Thrust',
    HINDENBURG_OMEN: 'Hindenburg Omen',
    VOLUME_THRUST: 'Volume Thrust',
  }

  const signalBadgeClass: Record<string, string> = {
    BREADTH_THRUST: 'badge-bull',
    HINDENBURG_OMEN: 'badge-bear',
    VOLUME_THRUST: 'text-xs font-mono px-2 py-0.5 rounded bg-brand-accent/15 text-brand-accent border border-brand-accent/30',
  }

  return (
    <div className="card flex flex-col items-center gap-3">
      <div className="text-brand-muted text-xs font-mono uppercase tracking-widest">Breadth Score</div>

      {/* SVG Gauge */}
      <svg width="240" height="130" viewBox="0 0 240 130">
        {/* Background arc track */}
        <path
          d="M 20 110 A 100 100 0 0 1 220 110"
          fill="none" stroke="#30363d" strokeWidth="16" strokeLinecap="round"
        />
        {/* Bear zone (red) */}
        <path
          d="M 20 110 A 100 100 0 0 1 70 27"
          fill="none" stroke="#f85149" strokeWidth="16" strokeLinecap="round" opacity="0.6"
        />
        {/* Neutral zone (yellow) */}
        <path
          d="M 70 27 A 100 100 0 0 1 170 27"
          fill="none" stroke="#d29922" strokeWidth="16" strokeLinecap="round" opacity="0.6"
        />
        {/* Bull zone (green) */}
        <path
          d="M 170 27 A 100 100 0 0 1 220 110"
          fill="none" stroke="#3fb950" strokeWidth="16" strokeLinecap="round" opacity="0.6"
        />

        {/* Needle — rotates from -90° (score=0) to +90° (score=100) around center */}
        <g transform={`rotate(${(clampedScore / 100) * 180 - 90}, 120, 110)`}>
          <line x1="120" y1="110" x2="120" y2="32" stroke="#e6edf3" strokeWidth="2.5" strokeLinecap="round" />
          <circle cx="120" cy="110" r="5" fill="#e6edf3" />
        </g>

        {/* Zone labels */}
        <text x="12" y="128" fill="#f85149" fontSize="9" fontFamily="monospace">BEAR</text>
        <text x="103" y="22" fill="#d29922" fontSize="9" fontFamily="monospace" textAnchor="middle">NEUTRAL</text>
        <text x="218" y="128" fill="#3fb950" fontSize="9" fontFamily="monospace" textAnchor="end">BULL</text>
      </svg>

      {/* Score number */}
      <div className={`text-5xl font-mono font-bold ${scoreColor(score)}`}>
        {score.toFixed(1)}
      </div>

      {/* Label */}
      <div className={`text-sm font-semibold ${labelColor(label)}`}>{label}</div>

      {/* Active signals */}
      {signalsActive.length > 0 && (
        <div className="flex flex-wrap gap-1.5 justify-center mt-1">
          {signalsActive.map(s => (
            <span key={s} className={signalBadgeClass[s] ?? 'badge-neutral'}>
              {signalLabels[s] ?? s}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
