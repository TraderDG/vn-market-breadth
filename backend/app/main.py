from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import create_tables
from app.config import settings
from app.routers import breadth, indicators, signals
from app.services.scheduler import create_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_tables()
    scheduler = create_scheduler()
    scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown()


app = FastAPI(
    title="VN Market Breadth API",
    description="26 Market Breadth Indicators cho thị trường chứng khoán Việt Nam (VN100 / VNINDEX)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(breadth.router, prefix=settings.API_PREFIX)
app.include_router(indicators.router, prefix=settings.API_PREFIX)
app.include_router(signals.router, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    return {
        "service": "VN Market Breadth API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "overview": f"{settings.API_PREFIX}/breadth/overview",
            "historical": f"{settings.API_PREFIX}/breadth/historical",
            "indicators_list": f"{settings.API_PREFIX}/indicators/list",
            "indicator_series": f"{settings.API_PREFIX}/indicators/{{name}}",
            "active_signals": f"{settings.API_PREFIX}/signals/active",
            "signal_history": f"{settings.API_PREFIX}/signals/history",
            "signal_stats": f"{settings.API_PREFIX}/signals/stats",
        },
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/v1/data/refresh")
async def trigger_refresh():
    """Trigger manual data refresh từ CSV files."""
    import asyncio
    from app.services.data_loader import run_full_import
    loop = asyncio.get_event_loop()
    rows, signals_count = await loop.run_in_executor(None, run_full_import)
    return {"status": "success", "rows_upserted": rows, "signals_upserted": signals_count}
