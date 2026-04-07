class ScrapeResult:
    def __init__(self, success: bool, price: float = None, name: str = None, error: str = None):
        self.success = success
        self.price = price
        self.name = name
        self.error = error

    def to_dict(self):
        return {
            "success": self.success,
            "price": self.price,
            "name": self.name,
            "error": self.error,
        }