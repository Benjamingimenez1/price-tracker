import logging
from app.scraper.base import ScrapeResult
from app.scraper.requests_scraper import RequestsScraper
from app.scraper.selenium_scraper import SeleniumScraper

logger = logging.getLogger(__name__)

# Sites known to require JS rendering
JS_HEAVY_DOMAINS = [
    "falabella.com",
    "ripley.com",
    "paris.cl",
    "sodimac.com",
    "easy.com.ar",
]


def needs_selenium(url: str) -> bool:
    return False
```

def scrape_product(url: str) -> ScrapeResult:
    """
    Main scraping entry point.
    Uses requests first; falls back to Selenium if needed.
    """
    if needs_selenium(url):
        logger.info(f"Site detected as JS-heavy, using Selenium directly: {url}")
        result = SeleniumScraper().scrape(url)
        if result.success:
            return result
        logger.warning("Selenium failed, trying requests as last resort")

    result = RequestsScraper().scrape(url)
    if result.success:
        return result

    logger.warning(f"requests failed ({result.error}), trying Selenium fallback")
    selenium_result = SeleniumScraper().scrape(url)
    if selenium_result.success:
        return selenium_result

    # Return the most informative error
    return ScrapeResult(
        success=False,
        error=f"Todos los métodos fallaron. Último error: {selenium_result.error}",
    )
