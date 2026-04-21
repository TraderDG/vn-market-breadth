"""
Import CSV data into PostgreSQL. Idempotent — safe to re-run (upsert).
Usage: python import_data.py
"""
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)

from app.services.data_loader import run_full_import

if __name__ == "__main__":
    rows, signals = run_full_import()
    print(f"\n✅ Import done: {rows} breadth rows, {signals} signal events")
