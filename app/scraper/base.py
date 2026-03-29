from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ScrapeResult:
    success: bool
    price: Optional[float] = None
    name: Optional[str] = None
    currency: str = "ARS"
    error: Optional[str] = None
    method: str = "requests"  # "requests" | "selenium"


class BaseScraper(ABC):
    @abstractmethod
    def scrape(self, url: str) -> ScrapeResult:
        pass
