import logging
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database.models import Product, PriceHistory, User
from app.scraper.engine import scrape_product

logger = logging.getLogger(__name__)


# ── Products ──────────────────────────────────────────────

def create_product(
    db: Session,
    user_id: int,
    url: str,
    name: Optional[str] = None,
    alert_price: Optional[float] = None,
) -> dict:
    """
    Add a new product. Scrapes immediately to get initial price & name.
    Returns dict with product data and scrape status.
    """
    result = scrape_product(url)

    product_name = name or result.name or _guess_name(url)
    initial_price = result.price if result.success else None

    product = Product(
        user_id=user_id,
        name=product_name,
        url=url,
        current_price=initial_price,
        alert_price=alert_price,
        last_checked=datetime.now(timezone.utc) if result.success else None,
    )
    db.add(product)
    db.flush()  # get product.id before history insert

    if initial_price is not None:
        history = PriceHistory(product_id=product.id, price=initial_price)
        db.add(history)

    db.commit()
    db.refresh(product)

    return {
        "product": product,
        "scraped": result.success,
        "scrape_error": result.error,
        "scrape_method": result.method,
    }


def get_products(db: Session, user_id: int) -> list[Product]:
    return (
        db.query(Product)
        .filter(Product.user_id == user_id, Product.is_active == True)
        .order_by(Product.created_at.desc())
        .all()
    )


def get_product(db: Session, product_id: int, user_id: int) -> Optional[Product]:
    return (
        db.query(Product)
        .filter(Product.id == product_id, Product.user_id == user_id)
        .first()
    )


def delete_product(db: Session, product_id: int, user_id: int) -> bool:
    product = get_product(db, product_id, user_id)
    if not product:
        return False
    db.delete(product)
    db.commit()
    return True


def get_history(db: Session, product_id: int, user_id: int) -> list[PriceHistory]:
    product = get_product(db, product_id, user_id)
    if not product:
        return []
    return (
        db.query(PriceHistory)
        .filter(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.recorded_at.asc())
        .all()
    )


# ── Price refresh ─────────────────────────────────────────

def refresh_product_price(db: Session, product: Product) -> dict:
    """Scrape and update price for a single product. Returns change info."""
    result = scrape_product(product.url)

    if not result.success:
        logger.warning(f"[refresh] Failed for product {product.id}: {result.error}")
        return {"success": False, "error": result.error}

    old_price = product.current_price
    new_price = result.price
    change = None
    change_pct = None

    if old_price and new_price:
        change = new_price - old_price
        change_pct = round((change / old_price) * 100, 2)

    product.current_price = new_price
    product.last_checked = datetime.now(timezone.utc)
    if result.name and not product.name:
        product.name = result.name

    history = PriceHistory(product_id=product.id, price=new_price)
    db.add(history)
    db.commit()

    logger.info(
        f"[refresh] Product {product.id} | {old_price} → {new_price} "
        f"({change_pct:+.1f}%)" if change_pct is not None else
        f"[refresh] Product {product.id} | price set to {new_price}"
    )

    return {
        "success": True,
        "old_price": old_price,
        "new_price": new_price,
        "change": change,
        "change_pct": change_pct,
        "alert_triggered": (
            product.alert_price is not None and
            new_price is not None and
            new_price <= product.alert_price
        ),
    }


def refresh_all_products(db: Session) -> dict:
    """Called by the scheduler. Refreshes every active product."""
    products = (
        db.query(Product)
        .filter(Product.is_active == True)
        .all()
    )
    summary = {"total": len(products), "success": 0, "failed": 0, "alerts": []}

    for product in products:
        res = refresh_product_price(db, product)
        if res["success"]:
            summary["success"] += 1
            if res.get("alert_triggered"):
                summary["alerts"].append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "price": res["new_price"],
                    "alert_price": product.alert_price,
                })
        else:
            summary["failed"] += 1

    logger.info(f"[scheduler] Refresh complete: {summary}")
    return summary


# ── Stats ─────────────────────────────────────────────────

def get_product_stats(db: Session, product_id: int) -> dict:
    history = (
        db.query(PriceHistory)
        .filter(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.recorded_at.asc())
        .all()
    )
    if not history:
        return {}

    prices = [h.price for h in history]
    first = prices[0]
    last = prices[-1]
    change = last - first
    change_pct = round((change / first) * 100, 2) if first else 0

    return {
        "min_price":   min(prices),
        "max_price":   max(prices),
        "avg_price":   round(sum(prices) / len(prices), 2),
        "first_price": first,
        "last_price":  last,
        "total_change": round(change, 2),
        "total_change_pct": change_pct,
        "total_savings": round(max(prices) - last, 2),
        "data_points": len(prices),
    }


# ── Helpers ───────────────────────────────────────────────

def _guess_name(url: str) -> str:
    try:
        from urllib.parse import urlparse
        host = urlparse(url).netloc.replace("www.", "")
        domain = host.split(".")[0]
        return "Producto en " + domain.capitalize()
    except Exception:
        return "Producto sin nombre"
