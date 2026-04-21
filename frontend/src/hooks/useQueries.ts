import { useQuery } from '@tanstack/react-query'
import {
  fetchOverview, fetchHistorical, fetchIndicatorSeries,
  fetchIndicatorList, fetchSignalHistory, fetchSignalStats, fetchActiveSignals,
} from '../api/breadth'

export const useOverview = () =>
  useQuery({ queryKey: ['overview'], queryFn: fetchOverview, refetchInterval: 60_000 })

export const useHistorical = (days = 504) =>
  useQuery({ queryKey: ['historical', days], queryFn: () => fetchHistorical(days) })

export const useIndicatorSeries = (name: string, days = 504) =>
  useQuery({
    queryKey: ['indicator', name, days],
    queryFn: () => fetchIndicatorSeries(name, days),
    enabled: !!name,
  })

export const useIndicatorList = () =>
  useQuery({ queryKey: ['indicator-list'], queryFn: fetchIndicatorList, staleTime: Infinity })

export const useSignalHistory = (signalType?: string) =>
  useQuery({ queryKey: ['signals', signalType], queryFn: () => fetchSignalHistory(signalType) })

export const useSignalStats = () =>
  useQuery({ queryKey: ['signal-stats'], queryFn: fetchSignalStats })

export const useActiveSignals = () =>
  useQuery({ queryKey: ['active-signals'], queryFn: fetchActiveSignals, refetchInterval: 60_000 })
