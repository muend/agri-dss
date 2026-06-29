"""Bölge / mahalle / öneri uçları + birebir veri sözleşmesi."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud
from ..database import get_db

router = APIRouter(tags=["regions"])


@router.get("/data")
def get_full_data(db: Session = Depends(get_db)) -> dict:
    """Frontend'in beklediği data.json'un BİREBİR aynısı.

    Frontend'te değişiklik: fetch('data.json') -> fetch(API + '/api/v1/data')
    Başka hiçbir şey değişmez.
    """
    return crud.build_data_contract(db)


@router.get("/regions")
def get_regions(db: Session = Depends(get_db)) -> list[str]:
    """İlçe (bölge) listesi."""
    return crud.list_districts(db)


@router.get("/regions/{district}")
def get_neighborhoods(district: str, db: Session = Depends(get_db)) -> list[dict]:
    """Bir ilçedeki mahalleler."""
    result = crud.list_neighborhoods(db, district)
    if result is None:
        raise HTTPException(status_code=404, detail=f"İlçe bulunamadı: {district}")
    return result


@router.get("/regions/{district}/{neighborhood}/recommendation")
def get_recommendation(district: str, neighborhood: str, db: Session = Depends(get_db)) -> dict:
    """Tek mahalle için çözümlenmiş öneri (referanslar açılmış)."""
    result = crud.resolve_recommendation(db, district, neighborhood)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Kayıt bulunamadı: {district}/{neighborhood}")
    return result
