from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from datetime import date, timedelta
from typing import Optional

from app.database import get_db
from app.models import MarketBreadthDaily
from app.schemas import BreadthDaySchema, OverviewResponse
from app.services.calculator import calc_breadth_score, get_breadth_label

router = APIRouter(prefix="/breadth", tags=["breadth"])


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(db: AsyncSession = Depends(get_db)):
    """Trả về snapshot mới nhất + breadth score tổng hợp."""
    result = await db.execute(
        select(MarketBreadthDaily).order_by(desc(MarketBreadthDaily.date)).limit(1)
    )
    row = result.scalar_one_or_none()
    if not row:
        return {"latest": {}, "breadth_score": 50.0, "breadth_label": "Neutral", "signals_active": []}

    row_dict = {c.name: getattr(row, c.name) for c in MarketBreadthDaily.__table__.columns}
    score = calc_breadth_score(row_dict)
    label = get_breadth_label(score)

    signals = []
    if row.hindenburg_omen:
        signals.append("HINDENBURG_OMEN")
    if row.volume_thrust_signal:
        signals.append("VOLUME_THRUST")
    # Breadth Thrust: nếu breadth_thrust > 0.615
    if row.breadth_thrust and row.breadth_thrust > 0.615:
        signals.append("BREADTH_THRUST")

    return OverviewResponse(
        latest=BreadthDaySchema.model_validate(row),
        breadth_score=score,
        breadth_label=label,
        signals_active=signals,
    )


@router.get("/historical", response_model=list[BreadthDaySchema])
async def get_historical(
    days: int = Query(default=252, ge=1, le=5000, description="Số ngày lấy về"),
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Trả về time series tất cả indicators."""
    query = select(MarketBreadthDaily).order_by(MarketBreadthDaily.date)

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
    rows = result.scalars().all()
    return [BreadthDaySchema.model_validate(r) for r in rows]


@router.get("/latest-n", response_model=list[BreadthDaySchema])
async def get_latest_n(
    n: int = Query(default=5, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Lấy n rows mới nhất."""
    result = await db.execute(
        select(MarketBreadthDaily).order_by(desc(MarketBreadthDaily.date)).limit(n)
    )
    rows = result.scalars().all()
    return [BreadthDaySchema.model_validate(r) for r in reversed(rows)]
