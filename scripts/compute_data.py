#!/usr/bin/env python3
"""
Standalone script: read CSVs from backend/data/csv2/, compute all indicators,
write JSON files to frontend/public/data/.
Run from project root: python scripts/compute_data.py
"""
import sys, json, math
from pathlib import Path

import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).parent.parent
CSV2_DIR = ROOT / "backend" / "data" / "csv2"
DATA_DIR = ROOT / "backend" / "data"
OUT_DIR = ROOT / "frontend" / "public" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _read_csv2(name):
    p = CSV2_DIR / name
    if not p.exists():
        print(f"  MISSING: {p}")
        return pd.DataFrame(columns=["date", "value"])
    df = pd.read_csv(p)
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df.rename(columns={"Date": "date", "Value": "value"}, inplace=True)
    return df[["date", "value"]].dropna(subset=["date"])


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
# CSV2 source files (22 usable files, 4 all-zero excluded)
# ---------------------------------------------------------------------------
CSV2_FILES = [
    ("ADLines_VN30.csv",                  "adline_vn30"),
    ("McClellanOsc_ratio_VN100.csv",       "mcclellan_osc_vn100"),
    ("Declines_VN30.csv",                  "declines_vn30"),
    ("New_High_52_VN30_week.csv",          "new_high_52w_vn30"),
    ("New_High_1_HNX30_month.csv",         "new_high_1m_hnx30"),
    ("UpVolume_Hnx.csv",                   "up_vol_hnx"),
    ("DownVolume_HNX30_percent.csv",       "down_vol_hnx30"),
    ("Unchanged_Upcom.csv",                "unchanged_upcom"),
    ("Above_Ma_100_VN100.csv",             "above_ma100_vn100"),
    ("RSI_25_Vnindex.csv",                 "rsi_25_vnindex"),
    ("RSI_25_VN100.csv",                   "rsi_25_vn100"),
    ("RSI_25_VN30.csv",                    "rsi_25_vn30"),
    ("RSI_25_HNX30.csv",                   "rsi_25_hnx30"),
    ("RSI_25_Hnx.csv",                     "rsi_25_hnx"),
    ("RSI_75_Vnindex.csv",                 "rsi_75_vnindex"),
    ("RSI_75_VN100.csv",                   "rsi_75_vn100"),
    ("RSI_75_VN30.csv",                    "rsi_75_vn30"),
    ("RSI_75_HNX30.csv",                   "rsi_75_hnx30"),
    ("RSI_75_Hnx.csv",                     "rsi_75_hnx"),
    ("under_std_2_Hnx.csv",                "bb_under_2std_hnx"),
    ("Return_12_VNALL_month.csv",          "return_12m_vnall"),
    ("Return_12_percent_VN30_month.csv",   "return_12m_vn30"),
]


# ---------------------------------------------------------------------------
# Build merged DataFrame
# ---------------------------------------------------------------------------
def build_df():
    # Load VNINDEX close for reference (old file, up to 2026-03-16)
    vnindex_df = pd.DataFrame()
    vnindex_path = DATA_DIR / "VNINDEX_A-D_line_Data.csv"
    if vnindex_path.exists():
        vn = pd.read_csv(vnindex_path)
        vn["Date"] = pd.to_datetime(vn["Date"]).dt.date
        vn.rename(columns={"Date": "date", "VNINDEX": "vnindex_close"}, inplace=True)
        vnindex_df = vn[["date", "vnindex_close"]].dropna(subset=["date"])

    # Load all CSV2 indicator files
    frames = []
    for fname, colname in CSV2_FILES:
        df = _read_csv2(fname)
        df.rename(columns={"value": colname}, inplace=True)
        frames.append(df)

    base = frames[0].copy()
    for df in frames[1:]:
        base = base.merge(df, on="date", how="outer")

    if not vnindex_df.empty:
        base = base.merge(vnindex_df, on="date", how="outer")
    else:
        base["vnindex_close"] = np.nan

    base.sort_values("date", inplace=True)
    base.reset_index(drop=True, inplace=True)
    return base


# ---------------------------------------------------------------------------
# Compute derived indicators
# ---------------------------------------------------------------------------
def compute_indicators(df):
    df = df.copy().sort_values("date").reset_index(drop=True)

    # McClellan Summation = cumulative sum of McClellan Oscillator
    if "mcclellan_osc_vn100" in df.columns:
        df["mcclellan_sum"] = df["mcclellan_osc_vn100"].fillna(0).cumsum()

    # Derived from VN30 A/D Line
    if "adline_vn30" in df.columns:
        adline = df["adline_vn30"].astype(float)
        daily_chg = adline.diff().fillna(0)
        df["ad_oscillator"] = _ema(adline, 10) - _ema(adline, 30)
        df["roc5_ad"] = (
            (adline - adline.shift(5))
            / adline.shift(5).abs().replace(0, np.nan) * 100
        )
        df["abs_breadth_index"] = _ema(daily_chg.abs(), 21)

    # Volume derived (Up=HNX, Down=HNX30 — same exchange family)
    if "up_vol_hnx" in df.columns and "down_vol_hnx30" in df.columns:
        uv = df["up_vol_hnx"].astype(float)
        dv = df["down_vol_hnx30"].astype(float)
        total = uv + dv
        df["up_volume_pct"] = uv / total.replace(0, np.nan) * 100
        df["uv_dv_ratio"] = uv / dv.replace(0, np.nan)
        df["net_up_volume_ema10"] = _ema((uv - dv), 10)

    # Disparity index from VNINDEX close
    if "vnindex_close" in df.columns:
        vc = df["vnindex_close"].astype(float)
        ma150 = vc.rolling(150, min_periods=1).mean()
        df["disparity_index"] = (vc / ma150.replace(0, np.nan) - 1) * 100

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

    s("mcclellan_osc_vn100", lambda v: v > 0)
    s("mcclellan_sum",       lambda v: v > 0)
    s("ad_oscillator",       lambda v: v > 0)
    s("roc5_ad",             lambda v: v > 0)
    s("new_high_52w_vn30",   lambda v: v > 0)
    s("up_volume_pct",       lambda v: v > 50)
    s("uv_dv_ratio",         lambda v: v > 1)
    s("above_ma100_vn100",   lambda v: v > 50)
    s("rsi_25_vnindex",      lambda v: v < 20)  # many oversold = contrarian bull
    s("rsi_75_vnindex",      lambda v: v > 20)  # many overbought = bull momentum
    s("rsi_75_vn30",         lambda v: v > 20)
    s("disparity_index",     lambda v: v > 0)
    s("return_12m_vn30",     lambda v: v > 0)

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
    vnindex = (
        df.set_index("date")["vnindex_close"].dropna()
        if "vnindex_close" in df.columns else pd.Series(dtype=float)
    )
    all_dates = list(vnindex.index)

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

    # RSI Oversold Reversal: rsi_25_vnindex crosses above 30% (many oversold → potential bounce)
    if "rsi_25_vnindex" in df.columns and "vnindex_close" in df.columns:
        col = df["rsi_25_vnindex"]
        for i in range(1, len(df)):
            if pd.notna(col.iloc[i - 1]) and pd.notna(col.iloc[i]):
                if col.iloc[i - 1] < 30 and col.iloc[i] >= 30:
                    add(df["date"].iloc[i], "RSI_OVERSOLD_REVERSAL",
                        df["vnindex_close"].iloc[i])

    # Volume Thrust: up_volume_pct surges from below 40 to above 70 in 10-day window
    if "up_volume_pct" in df.columns:
        col = df["up_volume_pct"]
        for i in range(10, len(df)):
            w = col.iloc[i - 10:i + 1]
            if pd.notna(w.min()) and w.min() < 40 and col.iloc[i] > 70:
                add(df["date"].iloc[i], "VOLUME_THRUST",
                    df["vnindex_close"].iloc[i] if "vnindex_close" in df.columns else None)

    # Deduplicate by (date, signal_type)
    seen = set()
    deduped = []
    for e in events:
        k = (e["date"], e["signal_type"])
        if k not in seen:
            seen.add(k)
            deduped.append(e)

    for i, e in enumerate(deduped):
        e["id"] = i + 1

    return sorted(deduped, key=lambda e: e["date"])


# ---------------------------------------------------------------------------
# Indicator list (based strictly on CSV2 sources + derived)
# ---------------------------------------------------------------------------
INDICATOR_LIST = [
    # A/D
    {"id": "adline_vn30",         "label": "A/D Line (VN30)",               "column": "adline_vn30",         "group": "A/D"},
    {"id": "mcclellan_osc_vn100", "label": "McClellan Oscillator (VN100)",  "column": "mcclellan_osc_vn100", "group": "A/D"},
    {"id": "mcclellan_sum",       "label": "McClellan Summation (VN100)",   "column": "mcclellan_sum",        "group": "A/D"},
    {"id": "ad_oscillator",       "label": "A/D Oscillator (VN30)",         "column": "ad_oscillator",        "group": "A/D"},
    {"id": "roc5_ad",             "label": "ROC5 A/D Line (VN30)",          "column": "roc5_ad",              "group": "A/D"},
    {"id": "abs_breadth_index",   "label": "Absolute Breadth Index (VN30)", "column": "abs_breadth_index",    "group": "A/D"},
    {"id": "declines_vn30",       "label": "Declines Count (VN30)",         "column": "declines_vn30",        "group": "A/D"},
    # NH-NL
    {"id": "new_high_52w_vn30",   "label": "New 52W High (VN30)",           "column": "new_high_52w_vn30",    "group": "NH-NL"},
    {"id": "new_high_1m_hnx30",   "label": "New 1M High (HNX30)",           "column": "new_high_1m_hnx30",    "group": "NH-NL"},
    # Volume
    {"id": "up_vol_hnx",          "label": "Up Volume (HNX)",               "column": "up_vol_hnx",           "group": "Volume"},
    {"id": "down_vol_hnx30",      "label": "Down Volume (HNX30)",           "column": "down_vol_hnx30",       "group": "Volume"},
    {"id": "up_volume_pct",       "label": "Up Volume % (HNX)",             "column": "up_volume_pct",        "group": "Volume"},
    {"id": "uv_dv_ratio",         "label": "Up/Down Volume Ratio (HNX)",    "column": "uv_dv_ratio",          "group": "Volume"},
    {"id": "net_up_volume_ema10", "label": "Net Up Volume 10d EMA",         "column": "net_up_volume_ema10",  "group": "Volume"},
    {"id": "unchanged_upcom",     "label": "Unchanged Stocks (UPCOM)",      "column": "unchanged_upcom",      "group": "Volume"},
    # % Above MA
    {"id": "above_ma100_vn100",   "label": "% Above MA100 (VN100)",         "column": "above_ma100_vn100",    "group": "Above MA"},
    {"id": "disparity_index",     "label": "Disparity Index (VNINDEX)",     "column": "disparity_index",      "group": "Above MA"},
    # RSI
    {"id": "rsi_25_vnindex",      "label": "% RSI<25 (VNINDEX)",            "column": "rsi_25_vnindex",       "group": "RSI"},
    {"id": "rsi_25_vn100",        "label": "% RSI<25 (VN100)",              "column": "rsi_25_vn100",         "group": "RSI"},
    {"id": "rsi_25_vn30",         "label": "% RSI<25 (VN30)",               "column": "rsi_25_vn30",          "group": "RSI"},
    {"id": "rsi_25_hnx30",        "label": "% RSI<25 (HNX30)",              "column": "rsi_25_hnx30",         "group": "RSI"},
    {"id": "rsi_25_hnx",          "label": "% RSI<25 (HNX)",                "column": "rsi_25_hnx",           "group": "RSI"},
    {"id": "rsi_75_vnindex",      "label": "% RSI>75 (VNINDEX)",            "column": "rsi_75_vnindex",       "group": "RSI"},
    {"id": "rsi_75_vn100",        "label": "% RSI>75 (VN100)",              "column": "rsi_75_vn100",         "group": "RSI"},
    {"id": "rsi_75_vn30",         "label": "% RSI>75 (VN30)",               "column": "rsi_75_vn30",          "group": "RSI"},
    {"id": "rsi_75_hnx30",        "label": "% RSI>75 (HNX30)",              "column": "rsi_75_hnx30",         "group": "RSI"},
    {"id": "rsi_75_hnx",          "label": "% RSI>75 (HNX)",                "column": "rsi_75_hnx",           "group": "RSI"},
    # Bollinger
    {"id": "bb_under_2std_hnx",   "label": "% Below -2σ BB (HNX)",          "column": "bb_under_2std_hnx",    "group": "Bollinger"},
    # Return
    {"id": "return_12m_vnall",    "label": "12M Return Count (VNALL)",      "column": "return_12m_vnall",     "group": "Return"},
    {"id": "return_12m_vn30",     "label": "12M Return % (VN30)",           "column": "return_12m_vn30",      "group": "Return"},
]


# ---------------------------------------------------------------------------
# Sectors (kept from original sectors_relative_performance.csv)
# ---------------------------------------------------------------------------
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
    p = DATA_DIR / "sectors_relative_performance.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p)
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df.rename(columns={"Date": "date"}, inplace=True)
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

        def pct_chg(n, s=series):
            if len(s) <= n:
                return None
            prev = s.iloc[-n - 1]
            if prev == 0 or (isinstance(prev, float) and math.isnan(prev)):
                return None
            return round((float(s.iloc[-1]) / float(prev) - 1) * 100, 2)

        sector_data.append({
            "code": code, "label": label,
            "current": clean(cur),
            "chg_1d": pct_chg(1),  "chg_1w": pct_chg(5),
            "chg_1m": pct_chg(21), "chg_3m": pct_chg(63),
            "chg_6m": pct_chg(126),"chg_1y": pct_chg(252),
        })

    slice_df = df.tail(504)
    dates = [str(d) for d in slice_df["date"]]
    series_out = {code: [clean(v) for v in slice_df[code].tolist()] for code, _ in SECTORS}

    return {
        "sectors": sector_data,
        "dates": dates,
        "series": series_out,
        "last_date": str(df["date"].iloc[-1]) if not df.empty else None,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=== VN Market Breadth — compute static data ===")

    print("Loading CSV2 files...")
    df = build_df()
    print(f"  Merged: {len(df)} rows, {len(df.columns)} cols")
    print(f"  Date range: {df['date'].iloc[0]} → {df['date'].iloc[-1]}")

    print("Computing derived indicators...")
    df = compute_indicators(df)
    print(f"  Total columns: {len(df.columns)}")

    df["date"] = df["date"].astype(str)
    records = [{k: clean(v) for k, v in row.items()} for _, row in df.iterrows()]

    # historical.json
    out = OUT_DIR / "historical.json"
    out.write_text(json.dumps(records, separators=(",", ":")), encoding="utf-8")
    print(f"  historical.json: {len(records)} rows ({out.stat().st_size // 1024} KB)")

    # overview.json
    latest = records[-1] if records else {}
    score = calc_breadth_score(latest)
    (OUT_DIR / "overview.json").write_text(json.dumps({
        "latest": latest,
        "breadth_score": score,
        "breadth_label": get_label(score),
        "signals_active": [],
        "total_rows": len(records),
    }, separators=(",", ":")), encoding="utf-8")
    print(f"  overview.json: score={score}, label={get_label(score)}")

    # signals.json
    df_sig = df.copy()
    df_sig["date"] = pd.to_datetime(df_sig["date"]).dt.date
    signals = compute_signals(df_sig)
    (OUT_DIR / "signals.json").write_text(json.dumps(signals, separators=(",", ":")), encoding="utf-8")
    print(f"  signals.json: {len(signals)} events")

    # indicator_list.json
    (OUT_DIR / "indicator_list.json").write_text(
        json.dumps(INDICATOR_LIST, separators=(",", ":")), encoding="utf-8"
    )
    print(f"  indicator_list.json: {len(INDICATOR_LIST)} indicators")

    # sectors.json
    print("Computing sectors...")
    sectors_data = compute_sectors()
    if sectors_data:
        (OUT_DIR / "sectors.json").write_text(
            json.dumps(sectors_data, separators=(",", ":")), encoding="utf-8"
        )
        print(f"  sectors.json: {len(sectors_data['sectors'])} sectors, last={sectors_data['last_date']}")
    else:
        print("  sectors.json: SKIPPED (no data)")

    print(f"=== Done! {len(INDICATOR_LIST)} indicators from CSV2 data ===")


if __name__ == "__main__":
    main()
