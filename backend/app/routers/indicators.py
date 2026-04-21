from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from datetime import date, timedelta
from typing import Optional

from app.database import get_db
from app.models import MarketBreadthDaily
from app.schemas import IndicatorSeries

router = APIRouter(prefix="/indicators", tags=["indicators"])

# Map tên indicator → cột trong DB + label đẹp
INDICATOR_MAP = {
    # Group A
    "ad_line":            ("ad_line", "A/D Line"),
    "mcclellan_osc":      ("mcclellan_osc", "McClellan Oscillator"),
    "mcclellan_sum":      ("mcclellan_sum", "McClellan Summation Index"),
    "ad_ratio_5d":        ("ad_ratio_5d", "A/D Ratio (5-day)"),
    "ad_ratio_10d":       ("ad_ratio_10d", "A/D Ratio (10-day)"),
    "breadth_thrust":     ("breadth_thrust", "Breadth Thrust (Zweig)"),
    "ad_oscillator":      ("ad_oscillator", "A/D Line Oscillator"),
    "abs_breadth_index":  ("abs_breadth_index", "Absolute Breadth Index"),
    "roc5_ad":            ("roc5_ad", "ROC5 of A/D Line"),
    # Group B
    "nh_nl_line":         ("nh_nl_line", "New High-New Low Line"),
    "nh_nl_osc":          ("nh_nl_osc", "NH-NL Oscillator"),
    "nh_nl_ratio":        ("nh_nl_ratio", "NH-NL Ratio"),
    # Group C
    "uv_dv_ratio":        ("uv_dv_ratio", "Up/Down Volume Ratio"),
    "up_volume_pct":      ("up_volume_pct", "Up Volume %"),
    "net_up_volume_ema10":("net_up_volume_ema10", "Net Up Volume (10d EMA)"),
    # Group D
    "pct_above_ma10":     ("pct_above_ma10", "% Stocks above MA10"),
    "pct_above_ma20":     ("pct_above_ma20", "% Stocks above MA20"),
    "pct_above_ma50":     ("pct_above_ma50", "% Stocks above MA50"),
    "pct_above_ma100":    ("pct_above_ma100", "% Stocks above MA100"),
    "pct_above_ma200":    ("pct_above_ma200", "% Stocks above MA200"),
    "participation_index":("participation_index", "Participation Index"),
    "disparity_index":    ("disparity_index", "Disparity Index"),
    # Group E
    "daily_ad_ratio_2pct":("daily_ad_ratio_2pct", "Daily Return AD Ratio (±2%)"),
    "quarterly_breadth_up":("quarterly_breadth_up", "Quarterly Breadth (Up ≥10%)"),
    "quarterly_breadth_down":("quarterly_breadth_down", "Quarterly Breadth (Down ≤-10%)"),
}


@router.get("/list")
async def list_indicators():
    """Trả về danh sách tất cả indicators available."""
    return [
        {"id": k, "label": v[1], "column": v[0]}
        for k, v in INDICATOR_MAP.items()
    ]


@router.get("/{name}", response_model=IndicatorSeries)
async def get_indicator_series(
    name: str,
    days: int = Query(default=504, ge=1, le=10000),
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Lấy time series của 1 indicator kèm VNINDEX để overlay chart."""
    if name not in INDICATOR_MAP:
        raise HTTPException(status_code=404, detail=f"Indicator '{name}' không tồn tại. Dùng /indicators/list để xem danh sách.")

    col_name, label = INDICATOR_MAP[name]
    col = getattr(MarketBreadthDaily, col_name)

    query = select(
        MarketBreadthDaily.date,
        col,
        MarketBreadthDaily.vnindex_close,
    ).order_by(MarketBreadthDaily.date)

    if from_date and to_date:
        query = query.where(
            and_(MarketBreadthDaily.date >= from_date, MarketBreadthDaily.date <= to_date)
        )
    elif from_date:
        query = query.where(MarketBreadthDaily.date >= from_date)
    else:
        cutoff = date.today() - timedelta(days=days)
        query = query.where(MarketBreadthDaily.date >= cutoff)

    result = await db.execute(query)
    rows = result.all()

    dates = [str(r[0]) for r in rows]
    values = [r[1] for r in rows]
    vnindex_values = [r[2] for r in rows]

    return IndicatorSeries(
        indicator=name,
        label=label,
        dates=dates,
        values=values,
        vnindex_dates=dates,
        vnindex_values=vnindex_values,
    )
