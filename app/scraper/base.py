class ScrapeResult:
    def __init__(self, success: bool, price: str = None, title: str = None, error: str = None):
        self.success = success
        self.price = price
        self.title = title
        self.error = error

    def to_dict(self):
        return {
            "success": self.success,
            "price": self.price,
            "title": self.title,
            "error": self.error,
        }