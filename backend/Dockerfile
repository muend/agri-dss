FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Sistem bağımlılıkları (psycopg2 / GeoAlchemy2 için)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# entrypoint: DB'yi bekle -> seed -> uvicorn
RUN chmod +x ./entrypoint.sh
CMD ["./entrypoint.sh"]
