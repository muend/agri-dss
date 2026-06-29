"""ORM modelleri — data.json sözleşmesini veritabanına eşler.

Mekansal sütunlar (geom) bugünden TANIMLI ama NULLABLE. Yani gerçek sınır/koordinat
verisi gelmeden sistem çalışır; veri gelince aynı şemaya doldurulur (kod değişmez).
"""
from __future__ import annotations

from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Meta(Base):
    """Tekil site meta verisi (başlık, alt başlık, koridor listesi)."""
    __tablename__ = "meta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    title: Mapped[str | None] = mapped_column(String(255))
    subtitle: Mapped[str | None] = mapped_column(String(255))
    note: Mapped[str | None] = mapped_column(Text)
    corridor: Mapped[list | None] = mapped_column(JSONB)  # ["Demre", "Finike", ...]


class CropSet(Base):
    """Yeniden kullanılabilir mevsimlik ürün seti (ör. seraDomatesBiberSalatalik)."""
    __tablename__ = "crop_sets"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    # [{name, yield, profit, note}, ...]
    crops: Mapped[list] = mapped_column(JSONB, nullable=False)


class LongTermCrop(Base):
    """Uzun vadeli yatırım ürünü sözlüğü (ör. avokado, zeytin)."""
    __tablename__ = "long_term_crops"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)


class District(Base):
    """İlçe. geom: ilçe sınırı (MULTIPOLYGON) — şimdilik NULL, sonra doldurulur."""
    __tablename__ = "districts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    geom: Mapped[object | None] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, nullable=True)
    )

    neighborhoods: Mapped[list[Neighborhood]] = relationship(
        back_populates="district", cascade="all, delete-orphan"
    )


class Neighborhood(Base):
    """Mahalle kaydı. Her kayıt ya cropSet referansı YA inline crops taşır;
    ya longTerm referansı YA inline longTermCustom taşır.
    geom: mahalle sınırı/noktası — şimdilik NULL, sonra doldurulur.
    """
    __tablename__ = "neighborhoods"
    __table_args__ = (UniqueConstraint("district_id", "name", name="uq_district_neighborhood"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    district_id: Mapped[int] = mapped_column(ForeignKey("districts.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)

    # Mevsimlik ürün: referans (crop_set_key) VEYA inline (crops)
    crop_set_key: Mapped[str | None] = mapped_column(ForeignKey("crop_sets.key"))
    crops: Mapped[list | None] = mapped_column(JSONB)

    # Uzun vadeli: referans (long_term_key) VEYA inline (long_term_custom)
    long_term_key: Mapped[str | None] = mapped_column(ForeignKey("long_term_crops.key"))
    long_term_custom: Mapped[dict | None] = mapped_column(JSONB)

    market_gap: Mapped[str | None] = mapped_column(Text)

    geom: Mapped[object | None] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, nullable=True)
    )

    district: Mapped[District] = relationship(back_populates="neighborhoods")
