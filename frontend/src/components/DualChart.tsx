import { useEffect, useRef } from 'react'
import {
  createChart, ColorType, LineStyle,
  type IChartApi, type ISeriesApi, type LineData,
} from 'lightweight-charts'

interface Props {
  dates: string[]
  values: (number | null)[]
  vnindexDates: string[]
  vnindexValues: (number | null)[]
  label: string
  indicatorColor?: string
  zeroLine?: boolean         // vẽ đường zero ngang
  height?: number
}

const CHART_THEME = {
  background: { type: ColorType.Solid, color: '#161b22' },
  textColor: '#8b949e',
  grid: { vertLines: { color: '#21262d' }, horzLines: { color: '#21262d' } },
  crosshair: { mode: 0 },
  rightPriceScale: { borderColor: '#30363d' },
  timeScale: { borderColor: '#30363d', timeVisible: true },
}

export default function DualChart({
  dates, values, vnindexDates, vnindexValues,
  label, indicatorColor = '#388bfd', zeroLine = false, height = 340,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const indicatorRef = useRef<ISeriesApi<'Line'> | null>(null)
  const vnindexRef = useRef<ISeriesApi<'Line'> | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    const chart = createChart(containerRef.current, {
      ...CHART_THEME,
      width: containerRef.current.clientWidth,
      height,
      layout: { ...CHART_THEME },
    })
    chartRef.current = chart

    // VNINDEX — top pane (right price scale, secondary color)
    const vnSeries = chart.addLineSeries({
      color: '#8b949e',
      lineWidth: 1,
      priceScaleId: 'left',
      title: 'VNINDEX',
    })
    chart.priceScale('left').applyOptions({
      visible: true, borderColor: '#30363d', scaleMargins: { top: 0.05, bottom: 0.5 },
    })
    vnindexRef.current = vnSeries

    // Indicator — bottom half
    const indSeries = chart.addLineSeries({
      color: indicatorColor,
      lineWidth: 2,
      priceScaleId: 'right',
      title: label,
    })
    chart.priceScale('right').applyOptions({
      scaleMargins: { top: 0.55, bottom: 0.05 },
    })
    indicatorRef.current = indSeries

    // Zero line baseline
    if (zeroLine) {
      chart.addLineSeries({
        color: '#30363d',
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
        priceScaleId: 'right',
        lastValueVisible: false,
        priceLineVisible: false,
      }).setData(dates.map(d => ({ time: d, value: 0 })) as LineData[])
    }

    // Resize observer
    const ro = new ResizeObserver(() => {
      if (containerRef.current) chart.applyOptions({ width: containerRef.current.clientWidth })
    })
    if (containerRef.current) ro.observe(containerRef.current)

    return () => {
      ro.disconnect()
      chart.remove()
    }
  }, [height])

  // Update data when props change
  useEffect(() => {
    if (!vnindexRef.current || !indicatorRef.current) return

    const vnData = vnindexDates
      .map((d, i) => ({ time: d, value: vnindexValues[i] }))
      .filter(p => p.value != null) as LineData[]
    vnindexRef.current.setData(vnData)

    const indData = dates
      .map((d, i) => ({ time: d, value: values[i] }))
      .filter(p => p.value != null) as LineData[]
    indicatorRef.current.setData(indData)

    chartRef.current?.timeScale().fitContent()
  }, [dates, values, vnindexDates, vnindexValues])

  return (
    <div className="card">
      <div className="text-sm font-semibold text-brand-text mb-2">{label}</div>
      <div ref={containerRef} style={{ height }} />
    </div>
  )
}
