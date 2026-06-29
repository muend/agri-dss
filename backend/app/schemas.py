"""Pydantic şemaları — API giriş/çıkış sözleşmesi (data.json ile uyumlu)."""
from __future__ import annotations

from pydantic import BaseModel


class Crop(BaseModel):
    name: str
    yield_: str | None = None
    profit: str | None = None
    note: str | None = None

    # data.json'da alan adı "yield" (Python'da rezerve kelime) — alias ile eşle.
    model_config = {"populate_by_name": True}

    def model_dump_contract(self) -> dict:
        return {"name": self.name, "yield": self.yield_, "profit": self.profit, "note": self.note}


class LongTermCropOut(BaseModel):
    name: str
    note: str | None = None


class MetaOut(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    note: str | None = None
    corridor: list[str] = []


class RecommendationOut(BaseModel):
    """Tek bir mahalle için ÇÖZÜMLENMİŞ öneri (referanslar açılmış)."""
    district: str
    neighborhood: str
    crops: list[dict]                 # mevsimlik ürünler (set çözülmüş)
    long_term: dict | None = None     # {name, note}
    market_gap: str | None = None


class NeighborhoodSummary(BaseModel):
    name: str
    market_gap: str | None = None
