import re
import logging
from typing import Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def clean_price(raw: str) -> Optional[float]:
    """Convert price string like '$1.299,99' or '1299.99' to float."""
    if not raw:
        return None
    # Remove currency symbols and whitespace
    cleaned = re.sub(r"[^\d.,]", "", raw.strip())
    if not cleaned:
        return None
    # Handle formats: 1.299,99 (ES) or 1,299.99 (EN)
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            # ES format: 1.299,99
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            # EN format: 1,299.99
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        # Could be 1299,99 or 1,299
        parts = cleaned.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_mercadolibre(soup: BeautifulSoup) -> dict:
    result = {}
    # Price
    price_el = (
        soup.select_one(".andes-money-amount__fraction") or
        soup.select_one("span.price-tag-fraction") or
        soup.select_one("meta[itemprop='price']")
    )
    if price_el:
        raw = price_el.get("content") or price_el.get_text()
        result["price"] = clean_price(raw)

    # Name
    name_el = (
        soup.select_one("h1.ui-pdp-title") or
        soup.select_one("h1.item-title__primary") or
        soup.select_one("h1")
    )
    if name_el:
        result["name"] = name_el.get_text(strip=True)[:200]

    return result


def parse_amazon(soup: BeautifulSoup) -> dict:
    result = {}
    price_el = (
        soup.select_one("span.a-price-whole") or
        soup.select_one("#priceblock_ourprice") or
        soup.select_one("#priceblock_dealprice") or
        soup.select_one("span[data-a-color='price'] .a-offscreen")
    )
    if price_el:
        result["price"] = clean_price(price_el.get_text())

    name_el = soup.select_one("#productTitle")
    if name_el:
        result["name"] = name_el.get_text(strip=True)[:200]

    return result


def parse_falabella(soup: BeautifulSoup) -> dict:
    result = {}
    price_el = (
        soup.select_one("[data-internet-price]") or
        soup.select_one(".jsx-1369949851.price") or
        soup.select_one("span.price")
    )
    if price_el:
        raw = price_el.get("data-internet-price") or price_el.get_text()
        result["price"] = clean_price(raw)

    name_el = soup.select_one("h1.product-name") or soup.select_one("h1")
    if name_el:
        result["name"] = name_el.get_text(strip=True)[:200]

    return result


# Generic fallback: tries common CSS patterns
GENERIC_PRICE_SELECTORS = [
    "[itemprop='price']",
    ".price",
    ".product-price",
    ".sale-price",
    ".offer-price",
    "#price",
    ".precio",
    "[class*='price']",
    "[class*='precio']",
    "[data-price]",
]

GENERIC_NAME_SELECTORS = [
    "h1[itemprop='name']",
    ".product-title",
    ".product-name",
    "h1.title",
    "h1",
]


def parse_generic(soup: BeautifulSoup) -> dict:
    result = {}

    # Try meta tags first (most reliable)
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        result["name"] = og_title["content"].strip()[:200]

    price_meta = soup.find("meta", property="product:price:amount")
    if price_meta and price_meta.get("content"):
        result["price"] = clean_price(price_meta["content"])

    if "price" not in result:
        for sel in GENERIC_PRICE_SELECTORS:
            els = soup.select(sel)
            for el in els:
                raw = el.get("content") or el.get("data-price") or el.get_text()
                p = clean_price(raw)
                if p and p > 0:
                    result["price"] = p
                    break
            if "price" in result:
                break

    if "name" not in result:
        for sel in GENERIC_NAME_SELECTORS:
            el = soup.select_one(sel)
            if el:
                result["name"] = el.get_text(strip=True)[:200]
                break

    return result


DOMAIN_PARSERS = {
    "mercadolibre": parse_mercadolibre,
    "amazon":       parse_amazon,
    "falabella":    parse_falabella,
}


def parse_page(url: str, html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    domain = urlparse(url).netloc.lower()

    for key, parser_fn in DOMAIN_PARSERS.items():
        if key in domain:
            logger.debug(f"Using {key} parser for {domain}")
            result = parser_fn(soup)
            if result.get("price"):
                return result
            logger.debug(f"{key} parser failed, falling back to generic")

    return parse_generic(soup)
