from typing import Optional

from .base import BaseExtractor

class JsonLDExtractor(BaseExtractor):
    name = "json-ld"

    async def extract(self, data: dict, url: str) -> Optional[dict]:
        for item in data.get("json-ld", []):
            if isinstance(item, dict) and item.get("@type") == "Product":
                product_json = item

                # --- Offers ---
                offers = product_json.get("offers")
                if isinstance(offers, list) and offers:
                    offers = offers[0]
                elif isinstance(offers, dict):
                    pass
                else:
                    offers = {}

                # --- Price ---
                price_spec = {"currency": "EUR", "amount": 0}
                price_info = offers.get("priceSpecification")
                if isinstance(price_info, list) and price_info:
                    spec = price_info[0]
                    try:
                        price_spec["amount"] = int(float(spec.get("price", 0)) * 100)
                        price_spec["currency"] = spec.get("priceCurrency", "EUR")
                    except (ValueError, TypeError):
                        pass

                return {
                    "shopsItemId": str(product_json.get("sku", "")),
                    "shopName": offers.get("seller", {}).get("name", "Unknown Shop"),
                    "title": {"text": product_json.get("name", ""), "language": product_json.get("inLanguage", "de")},
                    "description": {"text": (product_json.get("description") or "").strip(),
                                    "language": product_json.get("inLanguage", "de")},
                    "price": price_spec,
                    "state": "AVAILABLE" if "InStock" in offers.get("availability", "") else "OUT_OF_STOCK",
                    "url": product_json.get("url", url),
                    "images": product_json.get("image", []) if isinstance(product_json.get("image"), list)
                    else ([product_json.get("image")] if product_json.get("image") else []),
                }
        return None
