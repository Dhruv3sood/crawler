from typing import Optional
from .base import BaseExtractor

class OpenGraphExtractor(BaseExtractor):
    name = "opengraph"

    async def extract(self, data: dict, url: str) -> Optional[dict]:
        og_data = data.get("opengraph", {})

        # Convert Extruct "properties" list to dict if needed
        if isinstance(og_data, dict) and "properties" in og_data:
            og = dict(og_data["properties"])
        elif isinstance(og_data, list) and og_data:
            first = og_data[0]
            og = dict(first.get("properties", [])) if "properties" in first else first
        else:
            return None

        # Helper to safely get value
        def get_val(key, default=""):
            val = og.get(key, default)
            if isinstance(val, list) and val:
                return val[0]
            return val

        # Skip non-product pages
        og_type = get_val("og:type", "").lower()
        if "product" not in og_type:
            return None

        # Extract price safely, normalize European decimal commas
        price_str = get_val("og:price:amount", "0").replace(",", ".").replace(" ", "")
        try:
            price_amount = int(float(price_str) * 100)
        except (ValueError, TypeError):
            price_amount = "UNKNOWN"

        currency = get_val("og:price:currency", "UNKNOWN")

        # Determine availability
        availability = get_val("product:availability") or get_val("og:availability") or "UNKNOWN"
        if availability:
            state = "AVAILABLE" if "in stock" in availability.lower() else "OUT_OF_STOCK"
        else:
            # Fallback: if price exists, assume AVAILABLE
            state = "AVAILABLE" if price_amount > 0 else "OUT_OF_STOCK"

        # Build result
        return {
            "shopsItemId": "",
            "shopName": get_val("og:site_name", "UNKNOWN"),
            "title": {"text": get_val("og:title", ""), "language": "UNKNOWN"},
            "description": {"text": get_val("og:description", ""), "language": "UNKNOWN"},
            "price": {"currency": currency, "amount": price_amount},
            "state": state,
            "url": get_val("og:url", url),
            "images": [get_val("og:image")] if get_val("og:image") else "UNKNOWN",
        }