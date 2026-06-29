#!/usr/bin/env bash
set -e

echo "PostgreSQL bekleniyor..."
python - <<'PY'
import time, sqlalchemy
from app.config import settings
for i in range(30):
    try:
        e = sqlalchemy.create_engine(settings.database_url)
        with e.connect() as c:
            c.execute(sqlalchemy.text("SELECT 1"))
        print("DB hazır.")
        break
    except Exception as ex:
        print(f"  beklemede ({i+1}/30): {ex}")
        time.sleep(2)
else:
    raise SystemExit("DB'ye bağlanılamadı.")
PY

echo "Seed çalıştırılıyor..."
python -m app.seed || echo "Seed atlandı/başarısız (devam ediliyor)."

echo "API başlatılıyor..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
