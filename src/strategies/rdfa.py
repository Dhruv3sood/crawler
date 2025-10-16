from .base import BaseExtractor
from ..core.utils.availability_normalizer import map_availability_to_state


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
            if any(t.get("@value", "").lower() in ("product") for t in types):
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

        title = get_first_value("http://ogp.me/ns#title", "UNKNOWN")
        description = get_first_value("http://ogp.me/ns#description", "UNKNOWN")
        product_url = get_first_value("http://ogp.me/ns#url", url)
        images = get_all_values("http://ogp.me/ns#image")
        language_value = get_first_value("http://ogp.me/ns#locale", "")
        language = language_value[0:2] if language_value else "UNKNOWN"

        # Price handling
        raw_price = get_first_value("product:price:amount") or get_first_value(
            "product:price", "UNKNOWN"
        )

        # Handle European decimal format and remove spaces
        if raw_price != "UNKNOWN":
            raw_price = raw_price.replace(" ", "").replace(",", ".")

        currency = get_first_value("product:price:currency", "UNKNOWN")
        try:
            price_spec = {
                "currency": currency,
                "amount": int(round(float(raw_price) * 100)),
            }
        except ValueError:
            price_spec = {"currency": currency, "amount": 0}

        availability = get_first_value("product:availability", "")

        state = map_availability_to_state(availability)

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
