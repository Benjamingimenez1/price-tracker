import logging
from app.scraper.base import ScrapeResult
from app.scraper.requests_scraper import RequestsScraper

logger = logging.getLogger(__name__)


def needs_selenium(url: str) -> bool:
    return False


def scrape_product(url: str) -> ScrapeResult:
    """
    Main scraping entry point.
    Uses requests only (Selenium disabled on this server).
    """
    result = RequestsScraper().scrape(url)
    if result.success:
        return result

    return ScrapeResult(
        success=False,
        error=f"No se pudo obtener el precio. Error: {result.error}",
    )
```

Abrí el bloc de notas con:
```
notepad app\scraper\engine.py
```

Borrá todo, pegá el código de arriba, guardá con **Ctrl+S** y cerrá. Después:
```
git add app\scraper\engine.py
git commit -m "fix engine remove selenium"
git push
