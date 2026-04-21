from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional


class BreadthDaySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    vnindex_close: Optional[float] = None

    # Raw
    advances: Optional[int] = None
    declines: Optional[int] = None
    unchanged: Optional[int] = None
    total_stocks: Optional[int] = None
    new_highs: Optional[int] = None
    new_lows: Optional[int] = None
    up_volume: Optional[float] = None
    down_volume: Optional[float] = None

    # Group A
    ad_line: Optional[float] = None
    mcclellan_osc: Optional[float] = None
    mcclellan_sum: Optional[float] = None
    ad_ratio_5d: Optional[float] = None
    ad_ratio_10d: Optional[float] = None
    breadth_thrust: Optional[float] = None
    ad_oscillator: Optional[float] = None
    abs_breadth_index: Optional[float] = None
    roc5_ad: Optional[float] = None

    # Group B
    nh_nl_line: Optional[float] = None
    nh_nl_osc: Optional[float] = None
    nh_nl_ratio: Optional[float] = None
    hindenburg_omen: Optional[bool] = None

    # Group C
    uv_dv_ratio: Optional[float] = None
    up_volume_pct: Optional[float] = None
    net_up_volume_ema10: Optional[float] = None
    volume_thrust_signal: Optional[bool] = None

    # Group D
    pct_above_ma10: Optional[float] = None
    pct_above_ma20: Optional[float] = None
    pct_above_ma50: Optional[float] = None
    pct_above_ma100: Optional[float] = None
    pct_above_ma200: Optional[float] = None
    participation_index: Optional[float] = None
    disparity_index: Optional[float] = None

    # Group E
    daily_ad_ratio_2pct: Optional[float] = None
    quarterly_breadth_up: Optional[float] = None
    quarterly_breadth_down: Optional[float] = None


class OverviewResponse(BaseModel):
    latest: BreadthDaySchema
    breadth_score: float          # 0–100 composite score
    breadth_label: str            # "Extremely Bullish" / "Bullish" / "Neutral" / "Bearish" / "Extremely Bearish"
    signals_active: list[str]     # e.g. ["HINDENBURG_OMEN", "VOLUME_THRUST"]


class IndicatorSeries(BaseModel):
    dates: list[str]
    values: list[Optional[float]]
    indicator: str
    label: str
    vnindex_dates: list[str]
    vnindex_values: list[Optional[float]]


class SignalEventSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date
    signal_type: str
    vnindex_at_signal: Optional[float] = None
    fwd_return_1m: Optional[float] = None
    fwd_return_3m: Optional[float] = None
    fwd_return_6m: Optional[float] = None
    fwd_return_1y: Optional[float] = None
