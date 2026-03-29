import logging
import time
from app.scraper.base import BaseScraper, ScrapeResult
from app.scraper.parsers import parse_page

logger = logging.getLogger(__name__)


class SeleniumScraper(BaseScraper):
    def scrape(self, url: str) -> ScrapeResult:
        driver = None
        try:
            # Import lazily so app starts even if Chrome isn't installed
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager

            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            logger.info(f"[selenium] Loading {url}")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(url)

            # Wait for JS to render
            time.sleep(3)

            html = driver.page_source
            data = parse_page(url, html)

            if not data.get("price"):
                return ScrapeResult(
                    success=False,
                    error="No se encontró precio con Selenium",
                    method="selenium"
                )

            return ScrapeResult(
                success=True,
                price=data["price"],
                name=data.get("name"),
                method="selenium"
            )

        except ImportError:
            return ScrapeResult(
                success=False,
                error="Selenium no instalado o Chrome no disponible",
                method="selenium"
            )
        except Exception as e:
            logger.exception(f"[selenium] Error: {e}")
            return ScrapeResult(success=False, error=str(e), method="selenium")
        finally:
            if driver:
                driver.quit()
