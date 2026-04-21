from sqlalchemy import Column, Date, Float, Integer, Boolean, String, UniqueConstraint
from app.database import Base


class MarketBreadthDaily(Base):
    """One row per trading day — stores raw inputs + all 26 computed indicators."""
    __tablename__ = "market_breadth_daily"
    __table_args__ = (UniqueConstraint("date", name="uq_breadth_date"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)

    # --- Raw inputs ---
    vnindex_close = Column(Float)
    advances = Column(Integer)        # số CP tăng
    declines = Column(Integer)        # số CP giảm
    unchanged = Column(Integer)       # số CP đứng
    total_stocks = Column(Integer)    # tổng CP
    new_highs = Column(Integer)       # 52-week highs
    new_lows = Column(Integer)        # 52-week lows
    up_volume = Column(Float)         # khối lượng tăng
    down_volume = Column(Float)       # khối lượng giảm

    # --- Group A: A/D Based ---
    ad_line = Column(Float)                  # 1. A/D Line (cumulative)
    mcclellan_osc = Column(Float)            # 2. McClellan Oscillator
    mcclellan_sum = Column(Float)            # 3. McClellan Summation Index
    ad_ratio_5d = Column(Float)              # 4. A/D Ratio 5-day
    ad_ratio_10d = Column(Float)             # 5. A/D Ratio 10-day
    breadth_thrust = Column(Float)           # 6. Breadth Thrust (Zweig 10d EMA)
    ad_oscillator = Column(Float)            # 7. A/D Line Oscillator (MA10-MA30)
    abs_breadth_index = Column(Float)        # 8. Absolute Breadth Index (21d EMA)
    roc5_ad = Column(Float)                  # 9. ROC5 of A/D Line

    # --- Group B: New High / New Low ---
    nh_nl_line = Column(Float)               # 10. NH-NL cumulative line
    nh_nl_osc = Column(Float)                # 11. NH-NL Oscillator (10d EMA)
    nh_nl_ratio = Column(Float)              # 12. NH/(NH+NL) 10d smooth
    hindenburg_omen = Column(Boolean, default=False)  # 13. Hindenburg Omen signal

    # --- Group C: Volume Breadth ---
    uv_dv_ratio = Column(Float)              # 14. Up/Down Volume Ratio
    up_volume_pct = Column(Float)            # 15. Up Volume % of total
    net_up_volume_ema10 = Column(Float)      # 16. Net Up Volume (10d EMA)
    volume_thrust_signal = Column(Boolean, default=False)  # 17. Volume Thrust event

    # --- Group D: % Above MA ---
    pct_above_ma10 = Column(Float)           # 18
    pct_above_ma20 = Column(Float)           # 19
    pct_above_ma50 = Column(Float)           # 20
    pct_above_ma100 = Column(Float)          # 21
    pct_above_ma200 = Column(Float)          # 22
    participation_index = Column(Float)      # 23. VMT custom
    disparity_index = Column(Float)          # 24. (VNINDEX/MA150 - 1)*100

    # --- Group E: Return-Based ---
    daily_ad_ratio_2pct = Column(Float)      # 25. stocks ≥+2% / stocks ≤-2%
    quarterly_breadth_up = Column(Float)     # 26a. % stocks up ≥10% quarterly
    quarterly_breadth_down = Column(Float)   # 26b. % stocks down ≤-10% quarterly


class SignalEvent(Base):
    """Lưu lịch sử các tín hiệu đặc biệt (Breadth Thrust, Hindenburg Omen, Volume Thrust)."""
    __tablename__ = "signal_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    signal_type = Column(String(50), nullable=False)  # "BREADTH_THRUST", "HINDENBURG_OMEN", "VOLUME_THRUST"
    vnindex_at_signal = Column(Float)

    # Forward returns tính sau khi tín hiệu xuất hiện
    fwd_return_1m = Column(Float)
    fwd_return_3m = Column(Float)
    fwd_return_6m = Column(Float)
    fwd_return_1y = Column(Float)
