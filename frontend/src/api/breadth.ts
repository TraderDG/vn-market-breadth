import type {
  OverviewResponse, BreadthDay, IndicatorSeries,
  IndicatorMeta, SignalEvent, SignalStats, SectorsResponse,
} from './types'

const DATA = import.meta.env.BASE_URL.replace(/\/$/, '') + '/data'

const _cache = new Map<string, unknown>()

async function fetchJSON<T>(file: string): Promise<T> {
  if (_cache.has(file)) return _cache.get(file) as T
  const res = await fetch(`${DATA}/${file}`)
  if (!res.ok) throw new Error(`Failed to load ${file}: HTTP ${res.status}`)
  const data = await res.json() as T
  _cache.set(file, data)
  return data
}

async function getHistorical(): Promise<BreadthDay[]> {
  return fetchJSON<BreadthDay[]>('historical.json')
}

// ---------------------------------------------------------------------------

export const fetchOverview = (): Promise<OverviewResponse> =>
  fetchJSON<OverviewResponse>('overview.json')

export const fetchHistorical = async (days = 504): Promise<BreadthDay[]> => {
  const all = await getHistorical()
  return days >= 10000 ? all : all.slice(-days)
}

export const fetchLatestN = async (n = 1): Promise<BreadthDay[]> => {
  const all = await getHistorical()
  return all.slice(-n)
}

export const fetchIndicatorList = (): Promise<IndicatorMeta[]> =>
  fetchJSON<IndicatorMeta[]>('indicator_list.json')

export const fetchIndicatorSeries = async (
  name: string,
  days = 504,
): Promise<IndicatorSeries> => {
  const [all, list] = await Promise.all([getHistorical(), fetchIndicatorList()])
  const meta = list.find(i => i.id === name)
  const label = meta?.label ?? name
  const slice = days >= 10000 ? all : all.slice(-days)
  return {
    indicator: name,
    label,
    dates: slice.map(r => r.date),
    values: slice.map(r => ((r as unknown) as Record<string, number | null>)[name] ?? null),
    vnindex_dates: slice.map(r => r.date),
    vnindex_values: slice.map(r => r.vnindex_close),
  }
}

export const fetchActiveSignals = async (): Promise<SignalEvent[]> => {
  const signals = await fetchJSON<SignalEvent[]>('signals.json')
  const cutoff = new Date()
  cutoff.setDate(cutoff.getDate() - 30)
  return signals.filter(s => new Date(s.date) >= cutoff)
}

export const fetchSignalHistory = async (signalType?: string): Promise<SignalEvent[]> => {
  const signals = await fetchJSON<SignalEvent[]>('signals.json')
  return signalType ? signals.filter(s => s.signal_type === signalType) : signals
}

export const fetchSignalStats = async (): Promise<SignalStats> => {
  const signals = await fetchJSON<SignalEvent[]>('signals.json')
  const byType: Record<string, SignalEvent[]> = {}
  signals.forEach(s => {
    if (!byType[s.signal_type]) byType[s.signal_type] = []
    byType[s.signal_type].push(s)
  })

  const avg = (vals: (number | null | undefined)[]): number | null => {
    const nums = vals.filter((v): v is number => v != null)
    return nums.length ? Math.round(nums.reduce((a, b) => a + b, 0) / nums.length * 100) / 100 : null
  }
  const winRate = (evts: SignalEvent[], key: keyof SignalEvent): number | null => {
    const valid = evts.filter(e => e[key] != null)
    if (!valid.length) return null
    return Math.round(valid.filter(e => (e[key] as number) > 0).length / valid.length * 100)
  }

  const stats: SignalStats = {}
  for (const [type, evts] of Object.entries(byType)) {
    stats[type] = {
      count: evts.length,
      avg_fwd_1m: avg(evts.map(e => e.fwd_return_1m)),
      avg_fwd_3m: avg(evts.map(e => e.fwd_return_3m)),
      avg_fwd_6m: avg(evts.map(e => e.fwd_return_6m)),
      avg_fwd_1y: avg(evts.map(e => e.fwd_return_1y)),
      win_rate_1m: winRate(evts, 'fwd_return_1m'),
      win_rate_3m: winRate(evts, 'fwd_return_3m'),
      win_rate_6m: winRate(evts, 'fwd_return_6m'),
      win_rate_1y: winRate(evts, 'fwd_return_1y'),
    }
  }
  return stats
}

export const fetchSectors = (): Promise<SectorsResponse> =>
  fetchJSON<SectorsResponse>('sectors.json')

export const triggerRefresh = async () =>
  ({ message: 'Data is updated daily at 18:30 via GitHub Actions' })
