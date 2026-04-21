"""
calculator.py
Tính toán tất cả 26 Market Breadth Indicators từ raw DataFrame.

Input DataFrame cần có các cột:
    date, advances, declines, unchanged, total_stocks,
    new_highs, new_lows, up_volume, down_volume, vnindex_close,
    pct_above_ma10, pct_above_ma20, pct_above_ma50, pct_above_ma100, pct_above_ma200,
    participation_index (optional),
    daily_ad_ratio_2pct (optional),
    quarterly_breadth_up, quarterly_breadth_down (optional)
"""

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Helper: EMA
# ---------------------------------------------------------------------------
def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False, min_periods=1).mean()


def _sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=1).mean()


# ---------------------------------------------------------------------------
# Group A: A/D Based
# ---------------------------------------------------------------------------

def calc_ad_line(df: pd.DataFrame) -> pd.Series:
    """1. A/D Line — cumulative sum of (Advances - Declines)."""
    net = df["advances"] - df["declines"]
    return net.cumsum()


def calc_mcclellan_oscillator(df: pd.DataFrame) -> pd.Series:
    """2. McClellan Oscillator = EMA(19, A-D) - EMA(39, A-D)."""
    net = (df["advances"] - df["declines"]).astype(float)
    return _ema(net, 19) - _ema(net, 39)


def calc_mcclellan_summation(mcclellan_osc: pd.Series) -> pd.Series:
    """3. McClellan Summation Index = cumulative sum of McClellan Oscillator."""
    return mcclellan_osc.cumsum()


def calc_ad_ratio(df: pd.DataFrame, window: int) -> pd.Series:
    """4/5. A/D Ratio — rolling mean of Advances / (Advances + Declines)."""
    total = df["advances"] + df["declines"]
    ratio = df["advances"] / total.replace(0, np.nan)
    return ratio.rolling(window=window, min_periods=1).mean()


def calc_breadth_thrust(df: pd.DataFrame, span: int = 10) -> pd.Series:
    """6. Breadth Thrust (Zweig) = EMA(10, A / (A+D)).
    Signal: crosses from <0.40 to >0.615 within 10 days → extreme bullish thrust."""
    total = df["advances"] + df["declines"]
    ratio = df["advances"] / total.replace(0, np.nan)
    return _ema(ratio, span)


def calc_ad_oscillator(ad_line: pd.Series, fast: int = 10, slow: int = 30) -> pd.Series:
    """7. A/D Line Oscillator = SMA(fast, ADL) - SMA(slow, ADL)."""
    return _sma(ad_line, fast) - _sma(ad_line, slow)


def calc_absolute_breadth_index(df: pd.DataFrame, span: int = 21) -> pd.Series:
    """8. Absolute Breadth Index = EMA(21, |Advances - Declines|)."""
    abs_net = (df["advances"] - df["declines"]).abs().astype(float)
    return _ema(abs_net, span)


def calc_roc5_ad(ad_line: pd.Series) -> pd.Series:
    """9. ROC5 of A/D Line = (ADL - ADL.shift(5)) / |ADL.shift(5)| * 100."""
    shifted = ad_line.shift(5)
    return ((ad_line - shifted) / shifted.abs().replace(0, np.nan)) * 100


# ---------------------------------------------------------------------------
# Group B: New High / New Low
# ---------------------------------------------------------------------------

def calc_nh_nl_line(df: pd.DataFrame) -> pd.Series:
    """10. NH-NL Line = cumulative sum of (New Highs - New Lows)."""
    net = df["new_highs"] - df["new_lows"]
    return net.cumsum()


def calc_nh_nl_oscillator(df: pd.DataFrame, span: int = 10) -> pd.Series:
    """11. NH-NL Oscillator = EMA(10, NH - NL)."""
    net = (df["new_highs"] - df["new_lows"]).astype(float)
    return _ema(net, span)


def calc_nh_nl_ratio(df: pd.DataFrame, window: int = 10) -> pd.Series:
    """12. NH-NL Ratio = rolling(10, NH / (NH + NL))."""
    total = df["new_highs"] + df["new_lows"]
    ratio = df["new_highs"] / total.replace(0, np.nan)
    return ratio.rolling(window=window, min_periods=1).mean()


def calc_hindenburg_omen(df: pd.DataFrame, mcclellan_osc: pd.Series) -> pd.Series:
    """13. Hindenburg Omen — Boolean signal.
    Điều kiện: NH% > 2.2% AND NL% > 2.2% AND McClellan Osc < 0 AND VNINDEX tăng 50-day."""
    nh_pct = df["new_highs"] / df["total_stocks"].replace(0, np.nan)
    nl_pct = df["new_lows"] / df["total_stocks"].replace(0, np.nan)
    vnindex_rising = df["vnindex_close"] > df["vnindex_close"].rolling(50, min_periods=1).min()

    signal = (
        (nh_pct > 0.022) &
        (nl_pct > 0.022) &
        (mcclellan_osc < 0) &
        vnindex_rising
    )
    return signal.fillna(False)


# ---------------------------------------------------------------------------
# Group C: Volume Breadth
# ---------------------------------------------------------------------------

def calc_uv_dv_ratio(df: pd.DataFrame) -> pd.Series:
    """14. Up/Down Volume Ratio = Up Volume / Down Volume."""
    return df["up_volume"] / df["down_volume"].replace(0, np.nan)


def calc_up_volume_pct(df: pd.DataFrame) -> pd.Series:
    """15. Up Volume % = Up Volume / (Up Volume + Down Volume) * 100."""
    total = df["up_volume"] + df["down_volume"]
    return (df["up_volume"] / total.replace(0, np.nan)) * 100


def calc_net_up_volume_ema(df: pd.DataFrame, span: int = 10) -> pd.Series:
    """16. Net Up Volume EMA10 = EMA(10, Up Volume - Down Volume)."""
    net = (df["up_volume"] - df["down_volume"]).astype(float)
    return _ema(net, span)


def calc_volume_thrust_signal(up_vol_pct: pd.Series, threshold: float = 90.0, window: int = 10) -> pd.Series:
    """17. Volume Thrust Signal — True nếu Up Volume % > threshold trong cửa sổ window."""
    return up_vol_pct.rolling(window=window, min_periods=1).max() > threshold


# ---------------------------------------------------------------------------
# Group D: % Above MA — các cột này thường được load từ CSV sẵn
# (pct_above_ma10, ma20, ma50, ma100, ma200, participation_index)
# ---------------------------------------------------------------------------

def calc_disparity_index(df: pd.DataFrame, window: int = 150) -> pd.Series:
    """24. Disparity Index = (VNINDEX / MA150 - 1) * 100."""
    ma = df["vnindex_close"].rolling(window=window, min_periods=1).mean()
    return ((df["vnindex_close"] / ma) - 1) * 100


# ---------------------------------------------------------------------------
# Composite Breadth Score (0–100)
# ---------------------------------------------------------------------------

def _normalize_to_bool(series: pd.Series, bull_condition) -> pd.Series:
    """Convert indicator value to 1 (bullish) or 0 (bearish) for scoring."""
    return bull_condition.astype(float)


def calc_breadth_score(row: dict) -> float:
    """
    Tính điểm tổng hợp 0-100 từ các indicators.
    Mỗi indicator đóng góp 1 điểm nếu ở trạng thái bullish.
    """
    score_components = []

    def safe(val, default=None):
        return val if val is not None and not (isinstance(val, float) and np.isnan(val)) else default

    # A/D indicators (9 indicators)
    if (v := safe(row.get("mcclellan_osc"))) is not None:
        score_components.append(1.0 if v > 0 else 0.0)
    if (v := safe(row.get("mcclellan_sum"))) is not None:
        score_components.append(1.0 if v > 0 else 0.0)
    if (v := safe(row.get("ad_ratio_5d"))) is not None:
        score_components.append(1.0 if v > 0.5 else 0.0)
    if (v := safe(row.get("ad_ratio_10d"))) is not None:
        score_components.append(1.0 if v > 0.5 else 0.0)
    if (v := safe(row.get("breadth_thrust"))) is not None:
        score_components.append(1.0 if v > 0.5 else 0.0)
    if (v := safe(row.get("ad_oscillator"))) is not None:
        score_components.append(1.0 if v > 0 else 0.0)
    if (v := safe(row.get("roc5_ad"))) is not None:
        score_components.append(1.0 if v > 0 else 0.0)

    # NH-NL indicators
    if (v := safe(row.get("nh_nl_osc"))) is not None:
        score_components.append(1.0 if v > 0 else 0.0)
    if (v := safe(row.get("nh_nl_ratio"))) is not None:
        score_components.append(1.0 if v > 0.5 else 0.0)

    # Volume indicators
    if (v := safe(row.get("uv_dv_ratio"))) is not None:
        score_components.append(1.0 if v > 1.0 else 0.0)
    if (v := safe(row.get("up_volume_pct"))) is not None:
        score_components.append(1.0 if v > 50.0 else 0.0)

    # % Above MA (graded: bullish if > 50%)
    for col in ["pct_above_ma10", "pct_above_ma20", "pct_above_ma50", "pct_above_ma100", "pct_above_ma200"]:
        if (v := safe(row.get(col))) is not None:
            score_components.append(1.0 if v > 50.0 else 0.0)

    # Disparity
    if (v := safe(row.get("disparity_index"))) is not None:
        score_components.append(1.0 if v > 0 else 0.0)

    # Daily AD ratio 2%
    if (v := safe(row.get("daily_ad_ratio_2pct"))) is not None:
        score_components.append(1.0 if v > 1.0 else 0.0)

    if not score_components:
        return 50.0
    return round(sum(score_components) / len(score_components) * 100, 1)


def get_breadth_label(score: float) -> str:
    if score >= 75:
        return "Extremely Bullish"
    elif score >= 60:
        return "Bullish"
    elif score >= 40:
        return "Neutral"
    elif score >= 25:
        return "Bearish"
    else:
        return "Extremely Bearish"


# ---------------------------------------------------------------------------
# Master compute function — nhận DataFrame raw, trả về DataFrame đầy đủ
# ---------------------------------------------------------------------------

def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nhận DataFrame với các cột raw, trả về DataFrame có tất cả 26 indicators.
    DataFrame phải được sort theo date ascending trước khi gọi hàm này.
    """
    df = df.copy().sort_values("date").reset_index(drop=True)

    # Group A
    df["ad_line"] = calc_ad_line(df)
    df["mcclellan_osc"] = calc_mcclellan_oscillator(df)
    df["mcclellan_sum"] = calc_mcclellan_summation(df["mcclellan_osc"])
    df["ad_ratio_5d"] = calc_ad_ratio(df, 5)
    df["ad_ratio_10d"] = calc_ad_ratio(df, 10)
    df["breadth_thrust"] = calc_breadth_thrust(df)
    df["ad_oscillator"] = calc_ad_oscillator(df["ad_line"])
    df["abs_breadth_index"] = calc_absolute_breadth_index(df)
    df["roc5_ad"] = calc_roc5_ad(df["ad_line"])

    # Group B
    df["nh_nl_line"] = calc_nh_nl_line(df)
    df["nh_nl_osc"] = calc_nh_nl_oscillator(df)
    df["nh_nl_ratio"] = calc_nh_nl_ratio(df)
    df["hindenburg_omen"] = calc_hindenburg_omen(df, df["mcclellan_osc"])

    # Group C
    if "up_volume" in df.columns and "down_volume" in df.columns:
        df["uv_dv_ratio"] = calc_uv_dv_ratio(df)
        df["up_volume_pct"] = calc_up_volume_pct(df)
        df["net_up_volume_ema10"] = calc_net_up_volume_ema(df)
        df["volume_thrust_signal"] = calc_volume_thrust_signal(df["up_volume_pct"])
    else:
        for col in ["uv_dv_ratio", "up_volume_pct", "net_up_volume_ema10", "volume_thrust_signal"]:
            df[col] = np.nan

    # Group D — disparity (các % above MA load từ CSV, chỉ tính disparity)
    if "vnindex_close" in df.columns:
        df["disparity_index"] = calc_disparity_index(df)

    # Replace inf với nan
    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    return df
