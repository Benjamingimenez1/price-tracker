import logging
import time
import random
import requests
from app.scraper.base import BaseScraper, ScrapeResult
from app.scraper.headers import get_headers
from app.scraper.parsers import parse_page

logger = logging.getLogger(__name__)

TIMEOUT = 15
MAX_RETRIES = 3


class RequestsScraper(BaseScraper):
    def scrape(self, url: str) -> ScrapeResult:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"[requests] Attempt {attempt} → {url}")
                session = requests.Session()
                session.headers.update(get_headers(url))

                # Small random delay to be polite
                time.sleep(random.uniform(0.5, 1.5))

                resp = session.get(url, timeout=TIMEOUT, allow_redirects=True)
                resp.raise_for_status()

                data = parse_page(url, resp.text)

                if not data.get("price"):
                    logger.warning(f"[requests] No price found on attempt {attempt}")
                    if attempt < MAX_RETRIES:
                        time.sleep(2 ** attempt)
                        continue
                    return ScrapeResult(
                        success=False,
                        error="No se encontró precio en la página",
                        method="requests"
                    )

                return ScrapeResult(
                    success=True,
                    price=data["price"],
                    name=data.get("name"),
                    method="requests"
                )

            except requests.exceptions.HTTPError as e:
                logger.error(f"[requests] HTTP error: {e}")
                return ScrapeResult(success=False, error=f"HTTP {e.response.status_code}", method="requests")

            except requests.exceptions.ConnectionError as e:
                logger.error(f"[requests] Connection error: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(2 ** attempt)
                    continue
                return ScrapeResult(success=False, error="Error de conexión", method="requests")

            except requests.exceptions.Timeout:
                logger.error(f"[requests] Timeout on attempt {attempt}")
                if attempt < MAX_RETRIES:
                    continue
                return ScrapeResult(success=False, error="Timeout al cargar la página", method="requests")

            except Exception as e:
                logger.exception(f"[requests] Unexpected error: {e}")
                return ScrapeResult(success=False, error=str(e), method="requests")

        return ScrapeResult(success=False, error="Máximo de reintentos alcanzado", method="requests")
