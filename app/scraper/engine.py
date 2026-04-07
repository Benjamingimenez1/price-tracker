import logging
from app.scraper.base import ScrapeResult
from app.scraper.requests_scraper import RequestsScraper

logger = logging.getLogger(__name__)

def scrape_product(url: str) -> ScrapeResult:
    """
    Scraper simple usando requests (sin Selenium)
    """

    result = RequestsScraper().scrape(url)

    if result.success:
        return result

    return ScrapeResult(
        success=False,
        error=f"No se pudo obtener el precio. Error: {result.error}",
        name=None,
        price=None
    )