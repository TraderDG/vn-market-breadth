#!/usr/bin/env python3
"""
Standalone script: read CSVs from backend/data/, compute all indicators,
write JSON files to frontend/public/data/.
Run from project root: python scripts/compute_data.py
"""
import sys, json, math
from pathlib import Path

import pandas as pd
import numpy as np

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "backend" / "data"
OUT_DIR = ROOT / "frontend" / "public" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _read(name, **kw):
    p = DATA_DIR / name
    if not p.exists():
        print(f"  MISSING: {p}")
        return pd.DataFrame()
    return pd.read_csv(p, **kw)


def _dates(df, col="Date"):
    for c in df.columns:
        if c.lower() in ("date", "datetime"):
            col = c
            break
    df = df.copy()
    df[col] = pd.to_datetime(df[col]).dt.normalize().dt.date
    df.rename(columns={col: "date"}, inplace=True)
    return df


def _ema(s, span):
    return s.ewm(span=span, adjust=False, min_periods=1).mean()


def _sma(s, w):
    return s.rolling(w, min_periods=1).mean()


def clean(v):
    if v is None:
        return None
    if isinstance(v, (bool, np.bool_)):
        return bool(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        if math.isnan(v) or math.isinf(v):
            return None
        return round(float(v), 6)
    if hasattr(v, "isoformat"):
        return str(v)
    return v


# ---------------------------------------------------------------------------
# CSV Loaders
# ---------------------------------------------------------------------------
def load_ad_line():
    df = _read("VNINDEX_A-D_line_Data.csv")
    if df.empty:
        return df
    df = _dates(df)
    df.rename(columns={"VNINDEX": "vnindex_close", "AD_Line": "ad_line"}, inplace=True)
    return df[["date", "vnindex_close", "ad_line"]]


def load_nh_nl():
    df = _read("NH_NL_Subtraction_VNINDEX_Data.csv")
    if df.empty:
        return df
    df = _dates(df)
    df.rename(columns={"NH": "new_highs", "NL": "new_lows", "Net_High_Low": "nh_nl_line"}, inplace=True)
    return df[["date", "new_highs", "new_lows", "nh_nl_line"]]


def load_above_ma():
    df = _read("Market_Breadth__aboveMA_VNINDEX_Data.csv")
    if df.empty:
        return df
    df = _dates(df)
    df.rename(columns={
        "MA10": "pct_above_ma10", "MA20": "pct_above_ma20",
        "MA50": "pct_above_ma50", "MA100": "pct_above_ma100", "MA200": "pct_above_ma200",
    }, inplace=True)
    cols = ["date"] + [c for c in ["pct_above_ma10", "pct_above_ma20", "pct_above_ma50",
                                    "pct_above_ma100", "pct_above_ma200"] if c in df.columns]
    return df[cols]


def load_ad_ratio():
    df = _read("market_breadth_vn100_returndaily_ADratio.csv")
    if df.empty:
        return df
    df = _dates(df)
    df.rename(columns={
        "Number_of_stocks_up_2pct": "up2",
        "Number_of_stocks_down_2pct": "dn2",
        "AD_ratio_5day": "ad_ratio_5d",
        "AD_ratio_10day": "ad_ratio_10d",
    }, inplace=True)
    df["daily_ad_ratio_2pct"] = df["up2"] / df["dn2"].replace(0, np.nan)
    return df[["date", "ad_ratio_5d", "ad_ratio_10d", "daily_ad_ratio_2pct"]]


def load_quarterly():
    df = _read("market_breadth_vn100_quarterlyreturn.csv")
    if df.empty:
        return df
    df = _dates(df)
    df.rename(columns={
        "Number_of_stocks_up_10pct_quarterly": "qup",
        "Number_of_stocks_down_10pct_quarterly": "qdn",
        "Total_stocks": "qtotal",
    }, inplace=True)
    df["quarterly_breadth_up"] = df["qup"] / df["qtotal"].replace(0, np.nan) * 100
    df["quarterly_breadth_down"] = df["qdn"] / df["qtotal"].replace(0, np.nan) * 100
    df["total_stocks"] = df["qtotal"]
    return df[["date", "quarterly_breadth_up", "quarterly_breadth_down", "total_stocks"]]


def load_up_volume():
    df = _read("UpVolume_pct_merged.csv")
    if df.empty:
        return df
    df = _dates(df, col="date")
    df.rename(columns={
        "UpVolume": "up_volume",
        "TotalVolume": "total_volume",
        "UpVolume_pct": "up_volume_pct",
    }, inplace=True)
    df["down_volume"] = df["total_volume"] - df["up_volume"]
    return df[["date", "up_volume", "down_volume", "up_volume_pct"]]


# ---------------------------------------------------------------------------
# Build merged DataFrame
# ---------------------------------------------------------------------------
def build_df():
    loaders = [load_ad_line, load_nh_nl, load_above_ma, load_ad_ratio, load_quarterly, load_up_volume]
    frames = [fn() for fn in loaders]
    frames = [f for f in frames if not f.empty]

    if not frames:
        print("ERROR: no data loaded")
        return pd.DataFrame()

    base = frames[0]
    for df in frames[1:]:
        new_cols = [c for c in df.columns if c not in base.columns or c == "date"]
        base = base.merge(df[new_cols], on="date", how="outer")

    base.sort_values("date", inplace=True)
    base.reset_index(drop=True, inplace=True)
    return base


# ---------------------------------------------------------------------------
# Compute indicators
# ---------------------------------------------------------------------------
def compute_indicators(df):
    df = df.copy().sort_values("date").reset_index(drop=True)

    net_ad = df["ad_line"].diff().fillna(0) if "ad_line" in df.columns else pd.Series(0.0, index=df.index)

    df["mcclellan_osc"] = _ema(net_ad, 19) - _ema(net_ad, 39)
    df["mcclellan_sum"] = df["mcclellan_osc"].cumsum()

    if "ad_line" in df.columns:
        df["ad_oscillator"] = _sma(df["ad_line"], 10) - _sma(df["ad_line"], 30)
        df["roc5_ad"] = (
            (df["ad_line"] - df["ad_line"].shift(5))
            / df["ad_line"].shift(5).abs().replace(0, np.nan)
            * 100
        )

    df["abs_breadth_index"] = _ema(net_ad.abs(), 21)

    if "up_volume_pct" in df.columns:
        df["breadth_thrust"] = _ema(df["up_volume_pct"] / 100, 10)
    elif "ad_ratio_5d" in df.columns:
        df["breadth_thrust"] = df["ad_ratio_5d"]

    if "new_highs" in df.columns and "new_lows" in df.columns:
        if "nh_nl_line" not in df.columns:
            df["nh_nl_line"] = (df["new_highs"] - df["new_lows"]).cumsum()
        nh_nl_net = (df["new_highs"] - df["new_lows"]).astype(float)
        df["nh_nl_osc"] = _ema(nh_nl_net, 10)
        total_hl = df["new_highs"] + df["new_lows"]
        df["nh_nl_ratio"] = (df["new_highs"] / total_hl.replace(0, np.nan)).rolling(10, min_periods=1).mean()

        if "total_stocks" in df.columns:
            nh_pct = df["new_highs"] / df["total_stocks"].replace(0, np.nan)
            nl_pct = df["new_lows"] / df["total_stocks"].replace(0, np.nan)
        else:
            denom = (df["new_highs"] + df["new_lows"]).replace(0, np.nan)
            nh_pct = df["new_highs"] / denom
            nl_pct = df["new_lows"] / denom

        vnindex_rising = df["vnindex_close"] > df["vnindex_close"].rolling(50, min_periods=1).min()
        df["hindenburg_omen"] = (
            (nh_pct > 0.022) & (nl_pct > 0.022) &
            (df["mcclellan_osc"] < 0) & vnindex_rising
        ).fillna(False)

    if "up_volume" in df.columns and "down_volume" in df.columns:
        df["uv_dv_ratio"] = df["up_volume"] / df["down_volume"].replace(0, np.nan)
        df["net_up_volume_ema10"] = _ema((df["up_volume"] - df["down_volume"]).astype(float), 10)
        if "up_volume_pct" not in df.columns:
            total_v = df["up_volume"] + df["down_volume"]
            df["up_volume_pct"] = df["up_volume"] / total_v.replace(0, np.nan) * 100

    if "up_volume_pct" in df.columns:
        df["volume_thrust_signal"] = df["up_volume_pct"].rolling(10, min_periods=1).max() > 90

    if "vnindex_close" in df.columns:
        ma150 = df["vnindex_close"].rolling(150, min_periods=1).mean()
        df["disparity_index"] = (df["vnindex_close"] / ma150 - 1) * 100

    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    return df


# ---------------------------------------------------------------------------
# Breadth score
# ---------------------------------------------------------------------------
def calc_breadth_score(row):
    score = []

    def s(key, bull_fn):
        v = row.get(key)
        if v is not None and not (isinstance(v, float) and math.isnan(v)):
            score.append(1.0 if bull_fn(v) else 0.0)

    s("mcclellan_osc", lambda v: v > 0)
    s("mcclellan_sum", lambda v: v > 0)
    s("ad_ratio_5d", lambda v: v > 0.5)
    s("ad_ratio_10d", lambda v: v > 0.5)
    s("breadth_thrust", lambda v: v > 0.5)
    s("ad_oscillator", lambda v: v > 0)
    s("roc5_ad", lambda v: v > 0)
    s("nh_nl_osc", lambda v: v > 0)
    s("nh_nl_ratio", lambda v: v > 0.5)
    s("uv_dv_ratio", lambda v: v > 1.0)
    s("up_volume_pct", lambda v: v > 50.0)
    for ma in ["pct_above_ma10", "pct_above_ma20", "pct_above_ma50", "pct_above_ma100", "pct_above_ma200"]:
        s(ma, lambda v: v > 50.0)
    s("disparity_index", lambda v: v > 0)
    s("daily_ad_ratio_2pct", lambda v: v > 1.0)

    return round(sum(score) / len(score) * 100, 1) if score else 50.0


def get_label(score):
    if score >= 75: return "Extremely Bullish"
    if score >= 60: return "Bullish"
    if score >= 40: return "Neutral"
    if score >= 25: return "Bearish"
    return "Extremely Bearish"


# ---------------------------------------------------------------------------
# Signal detection
# ---------------------------------------------------------------------------
def compute_signals(df):
    events = []
    vnindex = df.set_index("date")["vnindex_close"].dropna() if "vnindex_close" in df.columns else None
    all_dates = list(vnindex.index) if vnindex is not None else []

    def fwd_ret(sig_date, sig_price, days):
        if sig_price is None or (isinstance(sig_price, float) and math.isnan(sig_price)):
            return None
        future = [d for d in all_dates if d > sig_date]
        if len(future) >= days:
            px = float(vnindex[future[min(days - 1, len(future) - 1)]])
            return round((px / float(sig_price) - 1) * 100, 2)
        return None

    def add(date, sig_type, price):
        p = float(price) if price is not None and not (isinstance(price, float) and math.isnan(price)) else None
        events.append({
            "date": str(date),
            "signal_type": sig_type,
            "vnindex_at_signal": p,
            "fwd_return_1m": fwd_ret(date, p, 21),
            "fwd_return_3m": fwd_ret(date, p, 63),
            "fwd_return_6m": fwd_ret(date, p, 126),
            "fwd_return_1y": fwd_ret(date, p, 252),
        })

    if "breadth_thrust" in df.columns:
        bt = df["breadth_thrust"]
        for i in range(10, len(df)):
            w = bt.iloc[i - 10:i + 1]
            if pd.notna(w.min()) and w.min() < 0.40 and w.iloc[-1] > 0.615:
                add(df["date"].iloc[i], "BREADTH_THRUST",
                    df["vnindex_close"].iloc[i] if "vnindex_close" in df.columns else None)

    # Rising-edge only: fire once when condition transitions False→True
    def rising_edge_rows(col):
        sig = df[col].astype(bool)
        prev = sig.shift(1).infer_objects(copy=False).fillna(False).astype(bool)
        edge = sig & ~prev
        return df[edge]

    if "hindenburg_omen" in df.columns:
        for _, row in rising_edge_rows("hindenburg_omen").iterrows():
            add(row["date"], "HINDENBURG_OMEN", row.get("vnindex_close"))

    if "volume_thrust_signal" in df.columns:
        for _, row in rising_edge_rows("volume_thrust_signal").iterrows():
            add(row["date"], "VOLUME_THRUST", row.get("vnindex_close"))

    # Deduplicate by (date, signal_type)
    seen = set()
    deduped = []
    for e in events:
        k = (e["date"], e["signal_type"])
        if k not in seen:
            seen.add(k)
            deduped.append(e)

    # Add synthetic id
    for i, e in enumerate(deduped):
        e["id"] = i + 1

    return sorted(deduped, key=lambda e: e["date"])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
INDICATOR_LIST = [
    {"id": "ad_line",              "label": "A/D Line",                      "column": "ad_line",              "group": "A/D"},
    {"id": "mcclellan_osc",        "label": "McClellan Oscillator",           "column": "mcclellan_osc",        "group": "A/D"},
    {"id": "mcclellan_sum",        "label": "McClellan Summation Index",      "column": "mcclellan_sum",        "group": "A/D"},
    {"id": "ad_ratio_5d",          "label": "A/D Ratio (5-day)",              "column": "ad_ratio_5d",          "group": "A/D"},
    {"id": "ad_ratio_10d",         "label": "A/D Ratio (10-day)",             "column": "ad_ratio_10d",         "group": "A/D"},
    {"id": "breadth_thrust",       "label": "Breadth Thrust (Zweig)",         "column": "breadth_thrust",       "group": "A/D"},
    {"id": "ad_oscillator",        "label": "A/D Line Oscillator",            "column": "ad_oscillator",        "group": "A/D"},
    {"id": "abs_breadth_index",    "label": "Absolute Breadth Index",         "column": "abs_breadth_index",    "group": "A/D"},
    {"id": "roc5_ad",              "label": "ROC5 of A/D Line",               "column": "roc5_ad",              "group": "A/D"},
    {"id": "nh_nl_line",           "label": "New High-New Low Line",          "column": "nh_nl_line",           "group": "NH-NL"},
    {"id": "nh_nl_osc",            "label": "NH-NL Oscillator",               "column": "nh_nl_osc",            "group": "NH-NL"},
    {"id": "nh_nl_ratio",          "label": "NH-NL Ratio",                    "column": "nh_nl_ratio",          "group": "NH-NL"},
    {"id": "uv_dv_ratio",          "label": "Up/Down Volume Ratio",           "column": "uv_dv_ratio",          "group": "Volume"},
    {"id": "up_volume_pct",        "label": "Up Volume %",                    "column": "up_volume_pct",        "group": "Volume"},
    {"id": "net_up_volume_ema10",  "label": "Net Up Volume (10d EMA)",        "column": "net_up_volume_ema10",  "group": "Volume"},
    {"id": "pct_above_ma10",       "label": "% Stocks above MA10",            "column": "pct_above_ma10",       "group": "Above MA"},
    {"id": "pct_above_ma20",       "label": "% Stocks above MA20",            "column": "pct_above_ma20",       "group": "Above MA"},
    {"id": "pct_above_ma50",       "label": "% Stocks above MA50",            "column": "pct_above_ma50",       "group": "Above MA"},
    {"id": "pct_above_ma100",      "label": "% Stocks above MA100",           "column": "pct_above_ma100",      "group": "Above MA"},
    {"id": "pct_above_ma200",      "label": "% Stocks above MA200",           "column": "pct_above_ma200",      "group": "Above MA"},
    {"id": "disparity_index",      "label": "Disparity Index",                "column": "disparity_index",      "group": "Above MA"},
    {"id": "daily_ad_ratio_2pct",  "label": "Daily Return AD Ratio (±2%)",    "column": "daily_ad_ratio_2pct",  "group": "Return"},
    {"id": "quarterly_breadth_up", "label": "Quarterly Breadth (Up ≥10%)",    "column": "quarterly_breadth_up", "group": "Return"},
    {"id": "quarterly_breadth_down","label": "Quarterly Breadth (Down ≤-10%)","column": "quarterly_breadth_down","group": "Return"},
]


SECTORS = [
    ("VNFIN",  "Financials"),
    ("VNMAT",  "Materials"),
    ("VNIND",  "Industrials"),
    ("VNHEAL", "Healthcare"),
    ("VNENE",  "Energy"),
    ("VNCONS", "Consumer Staples"),
    ("VNCOND", "Consumer Disc."),
    ("VNUTI",  "Utilities"),
    ("VNIT",   "Technology"),
    ("VNREAL", "Real Estate"),
]


def compute_sectors():
    df = _read("sectors_relative_performance.csv")
    if df.empty:
        return None
    df = _dates(df)
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    cols = [s[0] for s in SECTORS]
    for c in cols:
        if c not in df.columns:
            df[c] = np.nan

    sector_data = []
    for code, label in SECTORS:
        series = df[code].astype(float)
        cur = series.iloc[-1] if not series.empty else None

        def pct_chg(n):
            if len(series) <= n or series.iloc[-1] is None:
                return None
            prev = series.iloc[-n - 1]
            if prev == 0 or np.isnan(prev):
                return None
            return round((float(series.iloc[-1]) / float(prev) - 1) * 100, 2)

        sector_data.append({
            "code": code,
            "label": label,
            "current": clean(cur),
            "chg_1d":  pct_chg(1),
            "chg_1w":  pct_chg(5),
            "chg_1m":  pct_chg(21),
            "chg_3m":  pct_chg(63),
            "chg_6m":  pct_chg(126),
            "chg_1y":  pct_chg(252),
        })

    # Build time series for chart (last 504 rows)
    slice_df = df.tail(504)
    dates = [str(d) for d in slice_df["date"]]
    series_out = {}
    for code, _ in SECTORS:
        series_out[code] = [clean(v) for v in slice_df[code].tolist()]

    return {
        "sectors": sector_data,
        "dates": dates,
        "series": series_out,
        "last_date": str(df["date"].iloc[-1]) if not df.empty else None,
    }


def main():
    print("=== VN Market Breadth — compute static data ===")

    print("Loading CSVs...")
    df = build_df()
    if df.empty:
        print("ERROR: no data, aborting")
        sys.exit(1)
    print(f"  Merged: {len(df)} rows, {len(df.columns)} cols")

    print("Computing indicators...")
    df = compute_indicators(df)
    print(f"  Computed: {len(df.columns)} total cols")

    # Convert date column to string
    df["date"] = df["date"].astype(str)

    # Serialize all rows
    records = []
    for _, row in df.iterrows():
        records.append({k: clean(v) for k, v in row.items()})

    # --- historical.json ---
    out = OUT_DIR / "historical.json"
    out.write_text(json.dumps(records, separators=(",", ":")))
    print(f"  historical.json: {len(records)} rows ({out.stat().st_size // 1024} KB)")

    # --- overview.json ---
    latest = records[-1] if records else {}
    score = calc_breadth_score(latest)
    (OUT_DIR / "overview.json").write_text(json.dumps({
        "latest": latest,
        "breadth_score": score,
        "breadth_label": get_label(score),
        "signals_active": [],
        "total_rows": len(records),
    }, separators=(",", ":")))
    print(f"  overview.json: score={score}, label={get_label(score)}")

    # --- signals.json ---
    df_for_sig = df.copy()
    df_for_sig["date"] = pd.to_datetime(df_for_sig["date"]).dt.date
    signals = compute_signals(df_for_sig)
    (OUT_DIR / "signals.json").write_text(json.dumps(signals, separators=(",", ":")))
    print(f"  signals.json: {len(signals)} events")

    # --- indicator_list.json ---
    (OUT_DIR / "indicator_list.json").write_text(json.dumps(INDICATOR_LIST, separators=(",", ":")))
    print(f"  indicator_list.json: {len(INDICATOR_LIST)} indicators")

    # --- sectors.json ---
    print("Computing sectors...")
    sectors_data = compute_sectors()
    if sectors_data:
        (OUT_DIR / "sectors.json").write_text(json.dumps(sectors_data, separators=(",", ":")))
        print(f"  sectors.json: {len(sectors_data['sectors'])} sectors, last={sectors_data['last_date']}")
    else:
        print("  sectors.json: SKIPPED (no data)")

    print("=== Done! ===")


if __name__ == "__main__":
    main()
