"""
data_loader.py — rewritten to match actual VMT CSV column names.

CSV files in backend/data/:
  VNINDEX_A-D_line_Data.csv              → Date, VNINDEX, AD_Line
  NH_NL_Subtraction_VNINDEX_Data.csv     → Date, VNINDEX, NH, NL, Net_High_Low, Indicator_MA21
  Market_Breadth__aboveMA_VNINDEX_Data.csv → Date, VNINDEX, MA10, MA20, MA50, MA100, MA200
  market_breadth_vn100_returndaily_ADratio.csv → Date, Number_of_stocks_up_2pct, ..., AD_ratio_5day, AD_ratio_10day
  market_breadth_vn100_quarterlyreturn.csv → Date, Number_of_stocks_up_10pct_quarterly, ..., Total_stocks
  UpVolume_pct_merged.csv                → date, UpVolume, TotalVolume, UpVolume_pct, Close
  VNINDEX_processed_with_volume_thrust.csv → Date, Close, ..., up_volume, percent_up_volume, Volume
"""

import pandas as pd
import numpy as np
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.database import sync_engine, SyncSessionLocal
from app.models import MarketBreadthDaily, SignalEvent, Base
from app.config import settings
import logging

logger = logging.getLogger(__name__)
DATA_DIR = settings.DATA_DIR


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _read(filename: str, **kwargs) -> pd.DataFrame:
    path = DATA_DIR / filename
    if not path.exists():
        logger.warning(f"Missing CSV: {path}")
        return pd.DataFrame()
    df = pd.read_csv(path, **kwargs)
    return df


def _parse_dates(df: pd.DataFrame, col: str = "Date") -> pd.DataFrame:
    """Normalize date column to date objects, rename to 'date'."""
    if col not in df.columns:
        for c in df.columns:
            if c.lower() in ("date", "datetime"):
                col = c
                break
    df = df.copy()
    df[col] = pd.to_datetime(df[col]).dt.normalize().dt.date
    df.rename(columns={col: "date"}, inplace=True)
    return df


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False, min_periods=1).mean()


def _sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=1).mean()


# ---------------------------------------------------------------------------
# Individual loaders — map actual columns to standard names
# ---------------------------------------------------------------------------

def load_ad_line() -> pd.DataFrame:
    """Date, VNINDEX, AD_Line → date, vnindex_close, ad_line"""
    df = _read("VNINDEX_A-D_line_Data.csv")
    if df.empty:
        return df
    df = _parse_dates(df)
    df.rename(columns={"VNINDEX": "vnindex_close", "AD_Line": "ad_line"}, inplace=True)
    return df[["date", "vnindex_close", "ad_line"]]


def load_nh_nl() -> pd.DataFrame:
    """Date, VNINDEX, NH, NL, Net_High_Low, Indicator_MA21 → date, new_highs, new_lows, nh_nl_line"""
    df = _read("NH_NL_Subtraction_VNINDEX_Data.csv")
    if df.empty:
        return df
    df = _parse_dates(df)
    df.rename(columns={
        "NH": "new_highs",
        "NL": "new_lows",
        "Net_High_Low": "nh_nl_line",
    }, inplace=True)
    return df[["date", "new_highs", "new_lows", "nh_nl_line"]]


def load_above_ma() -> pd.DataFrame:
    """Date, VNINDEX, MA10-MA200 → date, pct_above_ma*"""
    df = _read("Market_Breadth__aboveMA_VNINDEX_Data.csv")
    if df.empty:
        return df
    df = _parse_dates(df)
    df.rename(columns={
        "MA10": "pct_above_ma10",
        "MA20": "pct_above_ma20",
        "MA50": "pct_above_ma50",
        "MA100": "pct_above_ma100",
        "MA200": "pct_above_ma200",
    }, inplace=True)
    keep = ["date"] + [c for c in ["pct_above_ma10","pct_above_ma20","pct_above_ma50","pct_above_ma100","pct_above_ma200"] if c in df.columns]
    return df[keep]


def load_ad_ratio() -> pd.DataFrame:
    """Date, Number_of_stocks_up_2pct, Number_of_stocks_down_2pct, AD_ratio_5day, AD_ratio_10day"""
    df = _read("market_breadth_vn100_returndaily_ADratio.csv")
    if df.empty:
        return df
    df = _parse_dates(df)
    df.rename(columns={
        "Number_of_stocks_up_2pct": "stocks_up_2pct",
        "Number_of_stocks_down_2pct": "stocks_down_2pct",
        "AD_ratio_5day": "ad_ratio_5d",
        "AD_ratio_10day": "ad_ratio_10d",
    }, inplace=True)
    df["daily_ad_ratio_2pct"] = df["stocks_up_2pct"] / df["stocks_down_2pct"].replace(0, np.nan)
    return df[["date", "ad_ratio_5d", "ad_ratio_10d", "daily_ad_ratio_2pct"]]


def load_quarterly() -> pd.DataFrame:
    """Date, Number_of_stocks_up_10pct_quarterly, ..., Total_stocks"""
    df = _read("market_breadth_vn100_quarterlyreturn.csv")
    if df.empty:
        return df
    df = _parse_dates(df)
    df.rename(columns={
        "Number_of_stocks_up_10pct_quarterly": "qup",
        "Number_of_stocks_down_10pct_quarterly": "qdown",
        "Total_stocks": "qtotal",
    }, inplace=True)
    df["quarterly_breadth_up"]   = df["qup"]   / df["qtotal"].replace(0, np.nan) * 100
    df["quarterly_breadth_down"] = df["qdown"] / df["qtotal"].replace(0, np.nan) * 100
    df["total_stocks"] = df["qtotal"]
    return df[["date", "quarterly_breadth_up", "quarterly_breadth_down", "total_stocks"]]


def load_up_volume() -> pd.DataFrame:
    """date, UpVolume, TotalVolume, UpVolume_pct, Close"""
    df = _read("UpVolume_pct_merged.csv")
    if df.empty:
        return df
    df = _parse_dates(df, col="date")
    df.rename(columns={
        "UpVolume": "up_volume",
        "TotalVolume": "total_volume",
        "UpVolume_pct": "up_volume_pct",
    }, inplace=True)
    df["down_volume"] = df["total_volume"] - df["up_volume"]
    return df[["date", "up_volume", "down_volume", "up_volume_pct"]]


# ---------------------------------------------------------------------------
# Compute indicators from merged DataFrame
# ---------------------------------------------------------------------------

def _compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().sort_values("date").reset_index(drop=True)

    # --- net A/D from AD_Line diff (proxy for Advances - Declines each day) ---
    if "ad_line" in df.columns:
        net_ad = df["ad_line"].diff().fillna(0)
    else:
        net_ad = pd.Series(np.zeros(len(df)), index=df.index)

    # --- McClellan Oscillator & Summation ---
    df["mcclellan_osc"] = _ema(net_ad, 19) - _ema(net_ad, 39)
    df["mcclellan_sum"] = df["mcclellan_osc"].cumsum()

    # --- A/D Line Oscillator (MA10 - MA30 of AD_Line) ---
    if "ad_line" in df.columns:
        df["ad_oscillator"] = _sma(df["ad_line"], 10) - _sma(df["ad_line"], 30)
        df["roc5_ad"] = (df["ad_line"] - df["ad_line"].shift(5)) / df["ad_line"].shift(5).abs().replace(0, np.nan) * 100

    # --- Absolute Breadth Index ---
    df["abs_breadth_index"] = _ema(net_ad.abs(), 21)

    # --- Breadth Thrust: use up_volume_pct / 100 as proxy for A/(A+D) ---
    if "up_volume_pct" in df.columns:
        df["breadth_thrust"] = _ema(df["up_volume_pct"] / 100, 10)
    elif "ad_ratio_5d" in df.columns:
        df["breadth_thrust"] = df["ad_ratio_5d"]

    # --- NH-NL Oscillator & Ratio (if not already loaded) ---
    if "new_highs" in df.columns and "new_lows" in df.columns:
        if "nh_nl_line" not in df.columns:
            df["nh_nl_line"] = (df["new_highs"] - df["new_lows"]).cumsum()
        nh_nl_net = (df["new_highs"] - df["new_lows"]).astype(float)
        df["nh_nl_osc"] = _ema(nh_nl_net, 10)
        total_hl = df["new_highs"] + df["new_lows"]
        df["nh_nl_ratio"] = (df["new_highs"] / total_hl.replace(0, np.nan)).rolling(10, min_periods=1).mean()

        # --- Hindenburg Omen ---
        if "total_stocks" in df.columns:
            nh_pct = df["new_highs"] / df["total_stocks"].replace(0, np.nan)
            nl_pct = df["new_lows"]  / df["total_stocks"].replace(0, np.nan)
        else:
            total_hl_sum = df["new_highs"] + df["new_lows"]
            nh_pct = df["new_highs"] / total_hl_sum.replace(0, np.nan)
            nl_pct = df["new_lows"]  / total_hl_sum.replace(0, np.nan)

        vnindex_rising = df["vnindex_close"] > df["vnindex_close"].rolling(50, min_periods=1).min()
        df["hindenburg_omen"] = (
            (nh_pct > 0.022) & (nl_pct > 0.022) &
            (df["mcclellan_osc"] < 0) & vnindex_rising
        ).fillna(False)

    # --- Up/Down Volume ---
    if "up_volume" in df.columns and "down_volume" in df.columns:
        df["uv_dv_ratio"] = df["up_volume"] / df["down_volume"].replace(0, np.nan)
        net_uv = (df["up_volume"] - df["down_volume"]).astype(float)
        df["net_up_volume_ema10"] = _ema(net_uv, 10)
        if "up_volume_pct" not in df.columns:
            total_v = df["up_volume"] + df["down_volume"]
            df["up_volume_pct"] = df["up_volume"] / total_v.replace(0, np.nan) * 100

    # --- Volume Thrust Signal: up_volume_pct > 90 in 10-day window ---
    if "up_volume_pct" in df.columns:
        df["volume_thrust_signal"] = df["up_volume_pct"].rolling(10, min_periods=1).max() > 90

    # --- Disparity Index ---
    if "vnindex_close" in df.columns:
        ma150 = df["vnindex_close"].rolling(150, min_periods=1).mean()
        df["disparity_index"] = (df["vnindex_close"] / ma150 - 1) * 100

    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    return df


# ---------------------------------------------------------------------------
# Build master DataFrame
# ---------------------------------------------------------------------------

def build_master_dataframe() -> pd.DataFrame:
    loaders = [
        ("ad_line",   load_ad_line),
        ("nh_nl",     load_nh_nl),
        ("above_ma",  load_above_ma),
        ("ad_ratio",  load_ad_ratio),
        ("quarterly", load_quarterly),
        ("up_volume", load_up_volume),
    ]

    frames = {}
    for key, fn in loaders:
        df = fn()
        if df.empty:
            logger.warning(f"Empty frame: {key}")
        else:
            frames[key] = df
            logger.info(f"Loaded {key}: {len(df)} rows, cols={list(df.columns)}")

    if not frames:
        logger.error("No data loaded!")
        return pd.DataFrame()

    # Start from ad_line (longest history)
    base = frames.pop("ad_line", None)
    if base is None or base.empty:
        base = next(iter(frames.values()))

    for key, df in frames.items():
        new_cols = [c for c in df.columns if c not in base.columns or c == "date"]
        base = base.merge(df[new_cols], on="date", how="outer")

    base.sort_values("date", inplace=True)
    base.reset_index(drop=True, inplace=True)

    logger.info(f"Master DataFrame: {len(base)} rows, {len(base.columns)} columns")
    logger.info(f"Cols: {list(base.columns)}")

    base = _compute_indicators(base)
    return base


# ---------------------------------------------------------------------------
# Upsert to DB
# ---------------------------------------------------------------------------

def upsert_to_db(df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    model_cols = {c.name for c in MarketBreadthDaily.__table__.columns if c.name != "id"}
    df_cols = [c for c in df.columns if c in model_cols]

    records = df[df_cols].where(pd.notna(df[df_cols]), other=None).to_dict(orient="records")

    # convert date objects to strings for sqlalchemy
    for r in records:
        if hasattr(r.get("date"), "isoformat"):
            r["date"] = r["date"]

    stmt = pg_insert(MarketBreadthDaily).values(records)
    stmt = stmt.on_conflict_do_update(
        index_elements=["date"],
        set_={col: stmt.excluded[col] for col in df_cols if col != "date"},
    )

    with SyncSessionLocal() as session:
        session.execute(stmt)
        session.commit()

    logger.info(f"Upserted {len(records)} rows")
    return len(records)


def compute_and_upsert_signals(df: pd.DataFrame) -> int:
    events = []

    # Breadth Thrust events
    if "breadth_thrust" in df.columns:
        for i in range(10, len(df)):
            window = df["breadth_thrust"].iloc[i-10:i+1]
            if pd.notna(window.min()) and pd.notna(window.iloc[-1]):
                if window.min() < 0.40 and window.iloc[-1] > 0.615:
                    events.append({
                        "date": df["date"].iloc[i],
                        "signal_type": "BREADTH_THRUST",
                        "vnindex_at_signal": df.get("vnindex_close", pd.Series([None]*len(df))).iloc[i],
                    })

    # Hindenburg Omen
    if "hindenburg_omen" in df.columns:
        for _, row in df[df["hindenburg_omen"] == True].iterrows():
            events.append({
                "date": row["date"],
                "signal_type": "HINDENBURG_OMEN",
                "vnindex_at_signal": row.get("vnindex_close"),
            })

    # Volume Thrust
    if "volume_thrust_signal" in df.columns:
        for _, row in df[df["volume_thrust_signal"] == True].iterrows():
            events.append({
                "date": row["date"],
                "signal_type": "VOLUME_THRUST",
                "vnindex_at_signal": row.get("vnindex_close"),
            })

    if not events:
        return 0

    # Compute forward returns
    if "vnindex_close" in df.columns:
        vnindex = df.set_index("date")["vnindex_close"].dropna()
        all_dates = list(vnindex.index)

        for event in events:
            sig_date = event["date"]
            sig_price = event.get("vnindex_at_signal")
            if not sig_price or (isinstance(sig_price, float) and np.isnan(sig_price)):
                continue
            future = [d for d in all_dates if d > sig_date]

            def fwd(days):
                if len(future) >= days:
                    return round((vnindex[future[min(days-1, len(future)-1)]] / sig_price - 1) * 100, 2)
                return None

            event["fwd_return_1m"] = fwd(21)
            event["fwd_return_3m"] = fwd(63)
            event["fwd_return_6m"] = fwd(126)
            event["fwd_return_1y"] = fwd(252)

    if events:
        stmt = pg_insert(SignalEvent).values(events)
        stmt = stmt.on_conflict_do_nothing()
        with SyncSessionLocal() as session:
            session.execute(stmt)
            session.commit()
        logger.info(f"Upserted {len(events)} signal events")

    return len(events)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_full_import():
    logger.info("=== Full import start ===")
    Base.metadata.create_all(sync_engine)

    df = build_master_dataframe()
    if df.empty:
        logger.error("Empty DataFrame — abort")
        return 0, 0

    rows = upsert_to_db(df)
    signals = compute_and_upsert_signals(df)
    logger.info(f"=== Done: {rows} rows, {signals} signals ===")
    return rows, signals
