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

        def get_val(key, default=""):
            val = og.get(key, default)
            if isinstance(val, list) and val:
                return val[0]
            return val

        og_type = get_val("og:type", "").lower()
        if "product" not in og_type:
            return None

        # Extract price safely, normalize European decimal commas
        price_str = (
                get_val("product:price:amount", None)
                or get_val("og:price:amount", "0")
        ).replace(",", ".").replace(" ", "")

        try:
            price_amount = int(float(price_str) * 100)
        except (ValueError, TypeError):
            price_amount = "UNKNOWN"

        currency = get_val("product:price:currency", "UNKNOWN")

        availability = get_val("product:availability") or get_val("og:availability") or ""

        locale = get_val("og:locale", "")
        language = locale.split("_")[0] if locale else "UNKNOWN"

        if not availability:
            state = "UNKNOWN"
        elif any(k in availability.lower() for k in ["instock", "in stock", "available"]):
            state = "AVAILABLE"
        elif any(k in availability.lower() for k in ["soldout", "sold out", "unavailable"]):
            state = "SOLD"
        elif any(k in availability.lower() for k in
                 ["preorder", "pre-order", "backorder", "back-order", "in_store_only", "in store only"]):
            state = "RESERVED"
        else:
            state = "OUT_OF_STOCK"

        # Build result
        return {
            "shopsItemId": url,
            "title": {"text": get_val("og:title", ""), "language": language},
            "description": {"text": get_val("og:description", ""), "language": language},
            "price": {"currency": currency, "amount": price_amount},
            "state": state,
            "url": get_val("og:url", url),
            "images": [get_val("og:image")] if get_val("og:image") else "UNKNOWN",
        }