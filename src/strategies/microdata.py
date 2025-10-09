from typing import Optional
from .base import BaseExtractor


class MicrodataExtractor(BaseExtractor):
    name = "microdata"

    async def extract(self, data: dict, url: str) -> Optional[dict]:
        def find_products(data):
            products = []
            if isinstance(data, dict):
                if data.get("type", data.get("@type")) in [
                    "http://schema.org/Product",
                    "https://schema.org/Product"
                ]:
                    products.append(data)
                for v in data.values():
                    products.extend(find_products(v))
            elif isinstance(data, list):
                for item in data:
                    products.extend(find_products(item))
            return products

        products = find_products(data.get("microdata", []))
        if not products:
            return None

        product = products[0]
        props = product.get("properties", {})

        # Handle offers
        offers = props.get("offers", {})
        if isinstance(offers, dict) and "properties" in offers:
            offers = offers["properties"]
        elif isinstance(offers, list):
            offers = offers[0].get("properties", offers[0]) if offers else {}

        # Price extraction
        price_spec = {"currency": "EUR", "amount": 0}
        try:
            price = offers.get("price")
            currency = offers.get("priceCurrency")
            if price is not None:
                price_spec["amount"] = int(float(price) * 100)
            if currency:
                price_spec["currency"] = currency
        except (ValueError, TypeError):
            pass

        # Availability mapping
        availability = offers.get("availability", "")
        if not availability:
            state = "UNKNOWN"
        elif "InStock" in availability:
            state = "AVAILABLE"
        elif "SoldOut" in availability:
            state = "SOLD"
        elif any(k in availability for k in ["PreOrder", "Backorder", "InStoreOnly"]):
            state = "RESERVED"
        else:
            state = "OUT_OF_STOCK"

        # Images
        images = props.get("image", [])
        if not isinstance(images, list):
            images = [images] if images else []

        # Return structured product
        return {
            "shopsItemId": str(props.get("sku") or props.get("productID", "UNKNOWN")),
            "title": {"text": props.get("name", ""), "language": props.get("inLanguage", "UNKNOWN")},
            "description": {"text": (props.get("description") or "UNKNOWN").strip(), "language": props.get("inLanguage", "UNKNOWN")},
            "price": price_spec,
            "state": state,
            "url": offers.get("url", props.get("url", url)),
            "images": images,
        }
