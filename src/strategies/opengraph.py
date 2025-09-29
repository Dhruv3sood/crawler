from typing import Optional

from .base import BaseExtractor

class OpenGraphExtractor(BaseExtractor):
    name = "opengraph"

    async def extract(self, data: dict, url: str) -> Optional[dict]:
        og_data = data.get("opengraph", {})

        if isinstance(og_data, list):
            if not og_data:
                return None
            og = og_data[0]
        elif isinstance(og_data, dict):
            og = og_data
        else:
            return None

        # Helper to safely get value
        def get_val(key, default=""):
            val = og.get(key, default)
            if isinstance(val, list) and val:
                return val[0]
            return val

        # Extract fields safely
        try:
            price_amount = int(float(get_val("product:price:amount", 0)) * 100)
        except (ValueError, TypeError):
            price_amount = 0

        currency = get_val("product:price:currency", "EUR")
        availability = get_val("product:availability", "").lower()
        state = "AVAILABLE" if "in stock" in availability else "OUT_OF_STOCK"

        return {
            "shopsItemId": "",
            "shopName": get_val("og:site_name", "Unknown Shop"),
            "title": {"text": get_val("og:title", ""), "language": "und"},
            "description": {"text": get_val("og:description", ""), "language": "und"},
            "price": {"currency": currency, "amount": price_amount},
            "state": state,
            "url": get_val("og:url", url),
            "images": [get_val("og:image")] if get_val("og:image") else [],
        }
