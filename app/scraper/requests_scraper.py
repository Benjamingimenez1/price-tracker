# 👇 TÍTULO
title_element = soup.find("h1")
title = title_element.text.strip() if title_element else "Producto"

# 👇 PRECIO
price_element = soup.select_one(".price_color")

if not price_element:
    return ScrapeResult(success=False, error="No se encontró el precio")

price_text = price_element.text.strip().replace("£", "")
price = float(price_text)

# 👇 RETURN CORRECTO
return ScrapeResult(
    success=True,
    price=price,
    name=title
)