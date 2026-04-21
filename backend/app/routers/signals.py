from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from datetime import date
from typing import Optional

from app.database import get_db
from app.models import SignalEvent, MarketBreadthDaily
from app.schemas import SignalEventSchema

router = APIRouter(prefix="/signals", tags=["signals"])

SIGNAL_TYPES = ["BREADTH_THRUST", "HINDENBURG_OMEN", "VOLUME_THRUST"]


@router.get("/active")
async def get_active_signals(db: AsyncSession = Depends(get_db)):
    """Kiểm tra các signals đang active hôm nay."""
    result = await db.execute(
        select(MarketBreadthDaily).order_by(desc(MarketBreadthDaily.date)).limit(1)
    )
    row = result.scalar_one_or_none()
    active = []
    if row:
        if row.hindenburg_omen:
            active.append({"type": "HINDENBURG_OMEN", "date": str(row.date), "description": "Hindenburg Omen signal — bearish warning"})
        if row.volume_thrust_signal:
            active.append({"type": "VOLUME_THRUST", "date": str(row.date), "description": "Volume Thrust — cực kỳ bullish"})
        if row.breadth_thrust and row.breadth_thrust > 0.615:
            active.append({"type": "BREADTH_THRUST", "date": str(row.date), "description": "Zweig Breadth Thrust — momentum cực mạnh"})
    return {"active_signals": active, "count": len(active)}


@router.get("/history", response_model=list[SignalEventSchema])
async def get_signal_history(
    signal_type: Optional[str] = Query(default=None, description="Lọc theo loại: BREADTH_THRUST, HINDENBURG_OMEN, VOLUME_THRUST"),
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Lịch sử tất cả signal events kèm forward returns."""
    query = select(SignalEvent).order_by(desc(SignalEvent.date))

    filters = []
    if signal_type and signal_type in SIGNAL_TYPES:
        filters.append(SignalEvent.signal_type == signal_type)
    if from_date:
        filters.append(SignalEvent.date >= from_date)
    if to_date:
        filters.append(SignalEvent.date <= to_date)
    if filters:
        query = query.where(and_(*filters))

    result = await db.execute(query)
    rows = result.scalars().all()
    return [SignalEventSchema.model_validate(r) for r in rows]


@router.get("/stats")
async def get_signal_stats(db: AsyncSession = Depends(get_db)):
    """Thống kê win rate và average forward returns cho từng loại signal."""
    stats = {}
    for stype in SIGNAL_TYPES:
        result = await db.execute(
            select(SignalEvent).where(SignalEvent.signal_type == stype)
        )
        rows = result.scalars().all()
        if not rows:
            stats[stype] = {"count": 0}
            continue

        def avg(vals):
            clean = [v for v in vals if v is not None]
            return round(sum(clean) / len(clean), 2) if clean else None

        def win_rate(vals):
            clean = [v for v in vals if v is not None]
            return round(sum(1 for v in clean if v > 0) / len(clean) * 100, 1) if clean else None

        fwd_1m = [r.fwd_return_1m for r in rows]
        fwd_3m = [r.fwd_return_3m for r in rows]
        fwd_6m = [r.fwd_return_6m for r in rows]
        fwd_1y = [r.fwd_return_1y for r in rows]

        stats[stype] = {
            "count": len(rows),
            "avg_fwd_1m": avg(fwd_1m),
            "avg_fwd_3m": avg(fwd_3m),
            "avg_fwd_6m": avg(fwd_6m),
            "avg_fwd_1y": avg(fwd_1y),
            "win_rate_1m": win_rate(fwd_1m),
            "win_rate_3m": win_rate(fwd_3m),
            "win_rate_6m": win_rate(fwd_6m),
            "win_rate_1y": win_rate(fwd_1y),
        }
    return stats
