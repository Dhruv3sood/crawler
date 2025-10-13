from typing import Optional
from .base import BaseExtractor
from ..core.ultils.availability_normalizer import map_availability_to_state

class JsonLDExtractor(BaseExtractor):
    name = "json-ld"

    async def extract(self, data: dict, url: str) -> Optional[dict]:
        products = []

        for entry in data.get("json-ld", []):
            if not isinstance(entry, dict):
                continue

            # Direct product
            if entry.get("@type") == "Product":
                products.append(entry)

            # Product(s) nested in @graph
            graph = entry.get("@graph")
            if isinstance(graph, list):
                products.extend(
                    item for item in graph
                    if isinstance(item, dict) and item.get("@type") == "Product"
                )
        if not products:
            return None

        product_json = products[0]
        offers = product_json.get("offers")
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        elif not isinstance(offers, dict):
            offers = {}

        # --- Price ---
        price_spec = {"currency": "EUR", "amount": 0}

        try:
            price = offers.get("price")
            currency = offers.get("priceCurrency")
            if price is not None and currency:
                price_spec["amount"] = int(round(float(price) * 100))
                price_spec["currency"] = currency

        except (ValueError, TypeError):
            pass

        price_info = offers.get("priceSpecification")
        if price_spec["amount"] == 0 and isinstance(price_info, list) and price_info:
            spec = price_info[0]
            try:
                price_spec["amount"] = int(float(spec.get("price", "0")) * 100)
                price_spec["currency"] = spec.get("priceCurrency", "UKNOWN")
            except (ValueError, TypeError):
                pass

        state = map_availability_to_state(offers.get("availability"))

        # --- Images ---
        images = product_json.get("image", [])
        if not isinstance(images, list):
            images = [images] if images else []

        return {
            # Use sku from the ProductGroup, or productGroupID, or a variant's sku if needed
            "shopsItemId": str(product_json.get("sku") or product_json.get("productGroupID", url)),
            "title": {"text": product_json.get("name", ""),
                      "language": product_json.get("inLanguage", "UNKNOWN")},
            "description": {"text": (product_json.get("description") or "UNKNOWN").strip(),
                            "language": product_json.get("inLanguage", "UNKNOWN")},
            "price": price_spec,
            "state": state,
            "url": product_json.get("url", offers.get("url", url)),
            "images": images,
        }