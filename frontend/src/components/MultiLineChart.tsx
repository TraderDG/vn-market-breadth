import { useEffect, useRef } from 'react'
import { createChart, ColorType, type LineData } from 'lightweight-charts'

export interface LineSeries {
  label: string
  dates: string[]
  values: (number | null)[]
  color: string
  lineWidth?: number
}

interface Props {
  series: LineSeries[]
  title: string
  height?: number
}

const COLORS = ['#388bfd', '#3fb950', '#f85149', '#d29922', '#a371f7', '#79c0ff']

export default function MultiLineChart({ series, title, height = 340 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!containerRef.current || series.length === 0) return

    const chart = createChart(containerRef.current, {
      layout: { background: { type: ColorType.Solid, color: '#161b22' }, textColor: '#8b949e' },
      grid: { vertLines: { color: '#21262d' }, horzLines: { color: '#21262d' } },
      rightPriceScale: { borderColor: '#30363d', scaleMargins: { top: 0.05, bottom: 0.05 } },
      timeScale: { borderColor: '#30363d', timeVisible: true },
      width: containerRef.current.clientWidth,
      height,
    })

    series.forEach((s, i) => {
      const lineSeries = chart.addLineSeries({
        color: s.color ?? COLORS[i % COLORS.length],
        lineWidth: (s.lineWidth ?? 2) as 1 | 2 | 3 | 4,
        title: s.label,
      })
      const data = s.dates
        .map((d, idx) => ({ time: d, value: s.values[idx] }))
        .filter(p => p.value != null) as LineData[]
      lineSeries.setData(data)
    })

    chart.timeScale().fitContent()

    const ro = new ResizeObserver(() => {
      if (containerRef.current) chart.applyOptions({ width: containerRef.current.clientWidth })
    })
    if (containerRef.current) ro.observe(containerRef.current)

    return () => { ro.disconnect(); chart.remove() }
  }, [series, height])

  return (
    <div className="card">
      <div className="text-sm font-semibold text-brand-text mb-2">{title}</div>
      <div ref={containerRef} style={{ height }} />
    </div>
  )
}
