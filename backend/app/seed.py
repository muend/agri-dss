"""Seed: mevcut data.json'u veritabanına yükler.

Çalıştırma:
    python -m app.seed
veya Docker:
    docker compose exec api python -m app.seed

Idempotent: önce tabloları (varsa) temizler, sonra yeniden yükler.
PostGIS uzantısını ve tabloları otomatik oluşturur.
"""
from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import text

from . import models
from .config import settings
from .database import Base, SessionLocal, engine


def ensure_schema() -> None:
    """PostGIS uzantısını ve tabloları oluştur."""
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    Base.metadata.create_all(engine)


def load_data() -> dict:
    path = Path(settings.seed_file)
    if not path.exists():
        # app/ dizininden çalıştırıldıysa proje köküne çık
        path = Path(__file__).resolve().parent.parent / settings.seed_file
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def seed() -> None:
    ensure_schema()
    data = load_data()

    with SessionLocal() as db:
        # Temizle (idempotent yeniden yükleme)
        db.query(models.Neighborhood).delete()
        db.query(models.District).delete()
        db.query(models.CropSet).delete()
        db.query(models.LongTermCrop).delete()
        db.query(models.Meta).delete()
        db.commit()

        # Meta
        meta = data.get("meta", {})
        db.add(models.Meta(
            id=1,
            title=meta.get("title"),
            subtitle=meta.get("subtitle"),
            note=meta.get("note"),
            corridor=meta.get("corridor", []),
        ))

        # cropSets
        for key, crops in data.get("cropSets", {}).items():
            db.add(models.CropSet(key=key, crops=crops))

        # longTermCrops
        for key, val in data.get("longTermCrops", {}).items():
            db.add(models.LongTermCrop(key=key, name=val.get("name", key), note=val.get("note")))

        db.flush()  # referansların FK kontrolü için

        # regions -> districts -> neighborhoods
        n_districts = n_neigh = 0
        for district_name, neighborhoods in data.get("regions", {}).items():
            d = models.District(name=district_name)
            db.add(d)
            db.flush()
            n_districts += 1
            for nb_name, rec in neighborhoods.items():
                db.add(models.Neighborhood(
                    district_id=d.id,
                    name=nb_name,
                    crop_set_key=rec.get("cropSet"),
                    crops=rec.get("crops"),
                    long_term_key=rec.get("longTerm"),
                    long_term_custom=rec.get("longTermCustom"),
                    market_gap=rec.get("marketGap"),
                ))
                n_neigh += 1

        db.commit()
        print(f"Seed tamam: {n_districts} ilçe, {n_neigh} mahalle, "
              f"{len(data.get('cropSets', {}))} cropSet, "
              f"{len(data.get('longTermCrops', {}))} longTerm yüklendi.")


if __name__ == "__main__":
    seed()
