#!/bin/bash
set -e

echo "=== VN Market Breadth Backend Starting ==="

# Wait for PostgreSQL
echo "Waiting for database..."
until python -c "
import psycopg2, os
url = os.environ.get('SYNC_DATABASE_URL', '')
# Parse URL: postgresql+psycopg2://user:pass@host:port/db
url = url.replace('postgresql+psycopg2://', '')
parts = url.split('@')
user_pass = parts[0].split(':')
host_db = parts[1].split('/')
host_port = host_db[0].split(':')
conn = psycopg2.connect(
    host=host_port[0], port=int(host_port[1]) if len(host_port)>1 else 5432,
    user=user_pass[0], password=user_pass[1],
    database=host_db[1]
)
conn.close()
print('DB ready')
" 2>/dev/null; do
  echo "  DB not ready, retrying in 2s..."
  sleep 2
done

# Import CSV data into DB (idempotent — upsert, safe to re-run)
echo "Importing CSV data..."
python import_data.py

# Start API server
echo "Starting FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
