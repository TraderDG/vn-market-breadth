import axios from 'axios'
import type {
  OverviewResponse, BreadthDay, IndicatorSeries,
  IndicatorMeta, SignalEvent, SignalStats,
} from './types'

const BASE = (import.meta.env.VITE_API_URL ?? '') + '/api/v1'
const api = axios.create({ baseURL: BASE })

export const fetchOverview = (): Promise<OverviewResponse> =>
  api.get('/breadth/overview').then(r => r.data)

export const fetchHistorical = (days = 504): Promise<BreadthDay[]> =>
  api.get('/breadth/historical', { params: { days } }).then(r => r.data)

export const fetchLatestN = (n = 1): Promise<BreadthDay[]> =>
  api.get('/breadth/latest-n', { params: { n } }).then(r => r.data)

export const fetchIndicatorList = (): Promise<IndicatorMeta[]> =>
  api.get('/indicators/list').then(r => r.data)

export const fetchIndicatorSeries = (
  name: string, days = 504,
): Promise<IndicatorSeries> =>
  api.get(`/indicators/${name}`, { params: { days } }).then(r => r.data)

export const fetchActiveSignals = () =>
  api.get('/signals/active').then(r => r.data)

export const fetchSignalHistory = (signalType?: string): Promise<SignalEvent[]> =>
  api.get('/signals/history', { params: signalType ? { signal_type: signalType } : {} })
    .then(r => r.data)

export const fetchSignalStats = (): Promise<SignalStats> =>
  api.get('/signals/stats').then(r => r.data)

export const triggerRefresh = () =>
  api.post('/data/refresh').then(r => r.data)
