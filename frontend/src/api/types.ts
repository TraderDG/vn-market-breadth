export interface BreadthDay {
  date: string
  vnindex_close: number | null

  // A/D — from CSV2: ADLines_VN30, McClellanOsc_ratio_VN100, Declines_VN30
  adline_vn30: number | null
  mcclellan_osc_vn100: number | null
  mcclellan_sum: number | null
  ad_oscillator: number | null
  roc5_ad: number | null
  abs_breadth_index: number | null
  declines_vn30: number | null

  // NH-NL — from CSV2: New_High_52_VN30_week, New_High_1_HNX30_month
  new_high_52w_vn30: number | null
  new_high_1m_hnx30: number | null

  // Volume — from CSV2: UpVolume_Hnx, DownVolume_HNX30, Unchanged_Upcom
  up_vol_hnx: number | null
  down_vol_hnx30: number | null
  unchanged_upcom: number | null
  up_volume_pct: number | null
  uv_dv_ratio: number | null
  net_up_volume_ema10: number | null

  // % Above MA — from CSV2: Above_Ma_100_VN100
  above_ma100_vn100: number | null
  disparity_index: number | null

  // RSI — from CSV2: RSI_25/75 × 5 indices
  rsi_25_vnindex: number | null
  rsi_25_vn100: number | null
  rsi_25_vn30: number | null
  rsi_25_hnx30: number | null
  rsi_25_hnx: number | null
  rsi_75_vnindex: number | null
  rsi_75_vn100: number | null
  rsi_75_vn30: number | null
  rsi_75_hnx30: number | null
  rsi_75_hnx: number | null

  // Bollinger — from CSV2: under_std_2_Hnx
  bb_under_2std_hnx: number | null

  // Return — from CSV2: Return_12_VNALL_month, Return_12_percent_VN30_month
  return_12m_vnall: number | null
  return_12m_vn30: number | null
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
  group?: string
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

export interface SectorData {
  code: string
  label: string
  current: number | null
  chg_1d: number | null
  chg_1w: number | null
  chg_1m: number | null
  chg_3m: number | null
  chg_6m: number | null
  chg_1y: number | null
}

export interface SectorsResponse {
  sectors: SectorData[]
  dates: string[]
  series: Record<string, (number | null)[]>
  last_date: string | null
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
