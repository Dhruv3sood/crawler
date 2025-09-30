from typing import Optional

from .base import BaseExtractor

class MicroformatExtractor(BaseExtractor):
    name = "microformat"

    async def extract(self, data: dict, url: str) -> Optional[dict]:
        for item in data.get("microformat", []):
            types = item.get("type", [])
            if "h-product" not in types:
                continue

            props = item.get("properties", {})

            # Helper to safely get first value from list
            def get_first(key, default=""):
                val = props.get(key, [default])
                if isinstance(val, list) and val:
                    return val[0]
                elif isinstance(val, str):
                    return val
                return default

            # Price
            price_str = get_first("price", "0")
            try:
                price_amount = int(float(price_str) * 100)
            except (ValueError, TypeError):
                price_amount = 0
            currency = get_first("currency", "EUR")

            # Availability
            availability = get_first("availability", "").lower()
            state = "AVAILABLE" if "in stock" in availability else "OUT_OF_STOCK"

            # Images
            images = props.get("photo", [])
            if isinstance(images, str):
                images = [images]
            elif not isinstance(images, list):
                images = []

            return {
                "shopsItemId": str(get_first("identifier", "")),
                "shopName": get_first("brand", "Unknown Shop"),
                "title": {"text": get_first("name", ""), "language": "und"},
                "description": {"text": get_first("description", ""), "language": "und"},
                "price": {"currency": currency, "amount": price_amount},
                "state": state,
                "url": get_first("url", url),
                "images": images,
            }
        return None
