from .base import BaseExtractor

class RdfaExtractor(BaseExtractor):
    name = "rdfa"

    async def extract(self, data: dict, url: str) -> dict | None:
        """
        Extract product information from RDFa structured data.
        :param data: Extracted structured data dictionary.
        :param url: Fallback URL if product JSON doesn't include one.
        :return: A dictionary with standardized product information or None.
        """
        product_item = None
        for item in data.get("rdfa", []):
            types = item.get("http://ogp.me/ns#type", [])
            if any(t.get("@value", "").lower() == "product" for t in types):
                product_item = item
                break

        if not product_item:
            return None

        def get_first_value(key: str, default=""):
            items = product_item.get(key, [])
            if items and isinstance(items, list):
                return items[0].get("@value", default)
            return default

        def get_all_values(key: str):
            items = product_item.get(key, [])
            if not isinstance(items, list):
                return []
            return [i["@value"] for i in items if "@value" in i]

        title = get_first_value("http://ogp.me/ns#title")
        description = get_first_value("http://ogp.me/ns#description")
        product_url = get_first_value("http://ogp.me/ns#url", url)
        images = get_all_values("http://ogp.me/ns#image")
        language = get_first_value("http://ogp.me/ns#locale", "de")[0:2]

        # Price handling
        raw_price = get_first_value("product:price:amount") or get_first_value("product:price", "UNKNOWN")

        # Handle European decimal format
        if raw_price != "UNKNOWN":
            raw_price = raw_price.replace(",", ".")

        currency = get_first_value("product:price:currency", "UNKNOWN")
        try:
            price_spec = {"currency": currency, "amount": int(float(raw_price) * 100)}
        except ValueError:
            price_spec = {"currency": currency, "amount": "UNKNOWN"}

        availability = get_first_value("product:availability", "")
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

        shops_item_id = product_url if product_url else "UNKNOWN"

        return {
            "shopsItemId": shops_item_id,
            "title": {"text": title, "language": language},
            "description": {"text": description, "language": language},
            "price": price_spec,
            "state": state,
            "url": product_url,
            "images": images,
        }
