def scrape_product(url: str) -> ScrapeResult:
    """
    Scraper simple usando requests
    """

    result = RequestsScraper().scrape(url)

    if result.success:
        return result

    return ScrapeResult(
        success=False,
        error=f"No se pudo obtener el precio. Error: {result.error}",
    )