from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database.session import get_db
from app.database.models import User
from app.routes.deps import get_current_user
from app.services import product_service

router = APIRouter(prefix="/products", tags=["products"])


# ── Schemas ──────────────────────────────────────────────

class ProductCreate(BaseModel):
    url: str
    name: Optional[str] = None
    alert_price: Optional[float] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    url: str
    current_price: Optional[float]
    alert_price: Optional[float]
    last_checked: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class HistoryPoint(BaseModel):
    price: float
    recorded_at: str


# ── Endpoints ─────────────────────────────────────────────

@router.post("")
def add_product(
    body: ProductCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not body.url.startswith("http"):
        raise HTTPException(status_code=400, detail="URL inválida")

    result = product_service.create_product(
        db=db,
        user_id=current_user.id,
        url=body.url,
        name=body.name,
        alert_price=body.alert_price,
    )
    p = result["product"]
    return {
        "id":            p.id,
        "name":          p.name,
        "url":           p.url,
        "current_price": p.current_price,
        "alert_price":   p.alert_price,
        "last_checked":  p.last_checked.isoformat() if p.last_checked else None,
        "created_at":    p.created_at.isoformat(),
        "scraped":       result["scraped"],
        "scrape_error":  result["scrape_error"],
        "scrape_method": result["scrape_method"],
    }


@router.get("")
def list_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    products = product_service.get_products(db, current_user.id)
    return [
        {
            "id":            p.id,
            "name":          p.name,
            "url":           p.url,
            "current_price": p.current_price,
            "alert_price":   p.alert_price,
            "last_checked":  p.last_checked.isoformat() if p.last_checked else None,
            "created_at":    p.created_at.isoformat(),
            "stats":         product_service.get_product_stats(db, p.id),
        }
        for p in products
    ]


@router.get("/{product_id}/history")
def get_history(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    history = product_service.get_history(db, product_id, current_user.id)
    if history is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return [
        {"price": h.price, "recorded_at": h.recorded_at.isoformat()}
        for h in history
    ]


@router.post("/{product_id}/refresh")
def refresh_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = product_service.get_product(db, product_id, current_user.id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    result = product_service.refresh_product_price(db, product)
    return result


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = product_service.delete_product(db, product_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"success": True}
