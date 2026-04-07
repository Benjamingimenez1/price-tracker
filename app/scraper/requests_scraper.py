import requests
from bs4 import BeautifulSoup
from app.scraper.base import ScrapeResult

class RequestsScraper:
    def scrape(self, url: str) -> ScrapeResult:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0"
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                return ScrapeResult(
                    success=False,
                    error=f"Error HTTP {response.status_code}"
                )

            soup = BeautifulSoup(response.text, "html.parser")

            # 📌 PRECIO (books.toscrape)
            price_element = soup.select_one(".price_color")

            if not price_element:
                return ScrapeResult(
                    success=False,
                    error="No se encontró precio en la página"
                )

            price = price_element.text.strip()

            # 📌 TÍTULO
            title_element = soup.select_one("h1")
            title = title_element.text.strip() if title_element else "Sin título"

            return ScrapeResult(
                success=True,
                price=price,
                title=title
            )

        except Exception as e:
            return ScrapeResult(
                success=False,
                error=str(e)
            )