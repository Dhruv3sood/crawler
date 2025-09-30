from .base import BaseExtractor

class MicrodataExtractor(BaseExtractor):
    name = "microdata"

    async def extract(self, data: dict, url: str) -> dict | None:
        """
        Extract product information from Microdata structured data.
        :param data: Extracted structured data dictionary.
        :param url: The URL of the webpage.
        :return: A dictionary with standardized product information or None.
        """
        products = [
            item for item in data.get("microdata", [])
            if isinstance(item, dict) and item.get("@type") == "http://schema.org/Product"
        ]
        if len(products) != 1:
            return None

        product_json = products[0]
        print(product_json)

        offers = product_json.get("offers")
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        elif not isinstance(offers, dict):
            return None

        product_item = products[0]
        props = product_item.get("properties", {})


        # --- Offers ---
        offers = {}
        if "offers" in props and props["offers"]:
         offer = props["offers"]
         if isinstance(offer, list):
             offer = offer[0]
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
