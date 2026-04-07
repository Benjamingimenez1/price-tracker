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
                return ScrapeResult(success=False, error=f"HTTP {response.status_code}")

            soup = BeautifulSoup(response.text, "html.parser")

            # 👇 TÍTULO
            title_element = soup.find("h1")
            title = title_element.text.strip() if title_element else "Producto"

            # 👇 PRECIO (para books.toscrape)
            price_element = soup.select_one(".price_color")

            if not price_element:
                return ScrapeResult(success=False, error="No se encontró el precio")

            price_text = price_element.text.strip().replace("£", "")
            price = float(price_text)

            # 👇 ESTE ES EL RETURN CLAVE
            return ScrapeResult(
                success=True,
                price=price,
                name=title
            )

        except Exception as e:
            return ScrapeResult(success=False, error=str(e))