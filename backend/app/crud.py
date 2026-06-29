"""Veri erişim + referans çözümleme mantığı.

İki rol:
1) build_data_contract() → frontend'in beklediği data.json'un BİREBİR aynısını üretir.
2) resolve_recommendation() → tek mahalle için cropSet/longTerm referanslarını açar.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models


def build_data_contract(db: Session) -> dict:
    """Tüm veritabanını data.json sözleşmesine geri serileştirir.
    Frontend hiçbir değişiklik yapmadan bu çıktıyı tüketebilir.
    """
    meta_row = db.get(models.Meta, 1)
    meta = {
        "title": meta_row.title if meta_row else None,
        "subtitle": meta_row.subtitle if meta_row else None,
        "note": meta_row.note if meta_row else None,
        "corridor": meta_row.corridor if meta_row else [],
    }

    crop_sets = {cs.key: cs.crops for cs in db.scalars(select(models.CropSet)).all()}
    long_term = {
        lt.key: {"name": lt.name, "note": lt.note}
        for lt in db.scalars(select(models.LongTermCrop)).all()
    }

    regions: dict[str, dict] = {}
    districts = db.scalars(select(models.District)).all()
    for d in districts:
        regions[d.name] = {}
        for n in d.neighborhoods:
            record: dict = {}
            if n.crop_set_key:
                record["cropSet"] = n.crop_set_key
            elif n.crops is not None:
                record["crops"] = n.crops
            if n.long_term_key:
                record["longTerm"] = n.long_term_key
            elif n.long_term_custom is not None:
                record["longTermCustom"] = n.long_term_custom
            if n.market_gap is not None:
                record["marketGap"] = n.market_gap
            regions[d.name][n.name] = record

    return {"meta": meta, "cropSets": crop_sets, "longTermCrops": long_term, "regions": regions}


def list_districts(db: Session) -> list[str]:
    return [d.name for d in db.scalars(select(models.District).order_by(models.District.name)).all()]


def list_neighborhoods(db: Session, district_name: str) -> list[dict] | None:
    d = db.scalar(select(models.District).where(models.District.name == district_name))
    if d is None:
        return None
    return [{"name": n.name, "market_gap": n.market_gap} for n in d.neighborhoods]


def resolve_recommendation(db: Session, district_name: str, neighborhood_name: str) -> dict | None:
    """cropSet ve longTerm referanslarını açıp tam öneri döndürür."""
    d = db.scalar(select(models.District).where(models.District.name == district_name))
    if d is None:
        return None
    n = next((x for x in d.neighborhoods if x.name == neighborhood_name), None)
    if n is None:
        return None

    # Mevsimlik ürünler: referansı çöz ya da inline kullan
    if n.crops is not None:
        crops = n.crops
    elif n.crop_set_key:
        cs = db.get(models.CropSet, n.crop_set_key)
        crops = cs.crops if cs else []
    else:
        crops = []

    # Uzun vadeli: referansı çöz ya da inline kullan
    if n.long_term_custom is not None:
        long_term = n.long_term_custom
    elif n.long_term_key:
        lt = db.get(models.LongTermCrop, n.long_term_key)
        long_term = {"name": lt.name, "note": lt.note} if lt else None
    else:
        long_term = None

    return {
        "district": d.name,
        "neighborhood": n.name,
        "crops": crops,
        "long_term": long_term,
        "market_gap": n.market_gap,
    }
