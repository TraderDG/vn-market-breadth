export interface BreadthDay {
  date: string
  vnindex_close: number | null

  // Raw
  advances: number | null
  declines: number | null
  unchanged: number | null
  total_stocks: number | null
  new_highs: number | null
  new_lows: number | null
  up_volume: number | null
  down_volume: number | null

  // Group A
  ad_line: number | null
  mcclellan_osc: number | null
  mcclellan_sum: number | null
  ad_ratio_5d: number | null
  ad_ratio_10d: number | null
  breadth_thrust: number | null
  ad_oscillator: number | null
  abs_breadth_index: number | null
  roc5_ad: number | null

  // Group B
  nh_nl_line: number | null
  nh_nl_osc: number | null
  nh_nl_ratio: number | null
  hindenburg_omen: boolean | null

  // Group C
  uv_dv_ratio: number | null
  up_volume_pct: number | null
  net_up_volume_ema10: number | null
  volume_thrust_signal: boolean | null

  // Group D
  pct_above_ma10: number | null
  pct_above_ma20: number | null
  pct_above_ma50: number | null
  pct_above_ma100: number | null
  pct_above_ma200: number | null
  participation_index: number | null
  disparity_index: number | null

  // Group E
  daily_ad_ratio_2pct: number | null
  quarterly_breadth_up: number | null
  quarterly_breadth_down: number | null
}

export interface OverviewResponse {
  latest: BreadthDay
  breadth_score: number
  breadth_label: string
  signals_active: string[]
}

export interface IndicatorSeries {
  indicator: string
  label: string
  dates: string[]
  values: (number | null)[]
  vnindex_dates: string[]
  vnindex_values: (number | null)[]
}

export interface IndicatorMeta {
  id: string
  label: string
  column: string
}

export interface SignalEvent {
  id: number
  date: string
  signal_type: string
  vnindex_at_signal: number | null
  fwd_return_1m: number | null
  fwd_return_3m: number | null
  fwd_return_6m: number | null
  fwd_return_1y: number | null
}

export interface SignalStats {
  [signalType: string]: {
    count: number
    avg_fwd_1m?: number | null
    avg_fwd_3m?: number | null
    avg_fwd_6m?: number | null
    avg_fwd_1y?: number | null
    win_rate_1m?: number | null
    win_rate_3m?: number | null
    win_rate_6m?: number | null
    win_rate_1y?: number | null
  }
}
