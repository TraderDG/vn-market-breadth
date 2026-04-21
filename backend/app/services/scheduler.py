"""
scheduler.py
APScheduler job chạy hàng ngày để cập nhật data mới nhất.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)


def run_daily_update():
    """Job chạy hàng ngày lúc 18:30 (sau khi thị trường đóng cửa)."""
    logger.info("Chạy daily update job...")
    try:
        from app.services.data_loader import run_full_import
        rows, signals = run_full_import()
        logger.info(f"Daily update xong: {rows} rows, {signals} signals")
    except Exception as e:
        logger.error(f"Daily update lỗi: {e}", exc_info=True)


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_daily_update,
        trigger=CronTrigger(hour=18, minute=30, timezone="Asia/Ho_Chi_Minh"),
        id="daily_update",
        name="VN Market Breadth Daily Update",
        replace_existing=True,
    )
    return scheduler
