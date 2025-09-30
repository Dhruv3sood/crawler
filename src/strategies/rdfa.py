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

        # Find the product node
        for item in data.get("rdfa", []):
            if not isinstance(item, dict):
                continue
            types = item.get("type", [])
            if any("Product" in t for t in types):
                product_item = item
                break

        if not product_item:
            return None

        props = product_item.get("properties", {})

        # --- Offers ---
        offers = {}
        if "offers" in props and props["offers"]:
            offer = props["offers"][0]
            if isinstance(offer, dict):
                offers = offer.get("properties", {})

        # --- Price ---
        price = offers.get("price", [0])[0]
        currency = offers.get("priceCurrency", ["EUR"])[0]
        price_spec = {
            "currency": currency,
            "amount": int(float(price) * 100) if price else 0
        }

        # --- Shop name ---
        shop_name = "Unknown Shop"
        if "seller" in offers and offers["seller"]:
            seller = offers["seller"][0]
            if isinstance(seller, dict):
                shop_name = seller.get("properties", {}).get("name", ["Unknown Shop"])[0]

        # --- Images ---
        images = props.get("image", [])
        if not isinstance(images, list):
            images = [images] if images else []

        return {
            "shopsItemId": str(props.get("sku", [""])[0]),
            "shopName": shop_name,
            "title": {
                "text": props.get("name", [""])[0],
                "language": props.get("inLanguage", ["de"])[0]
            },
            "description": {
                "text": (props.get("description", [""])[0] or "").strip(),
                "language": props.get("inLanguage", ["de"])[0]
            },
            "price": price_spec,
            "state": "AVAILABLE" if "InStock" in (offers.get("availability", [""])[0]) else "OUT_OF_STOCK",
            "url": props.get("url", [url])[0],
            "images": images,
        }