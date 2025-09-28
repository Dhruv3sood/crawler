import json
from crawl4ai import SeedingConfig, AsyncUrlSeeder
import asyncio
from src.core.ultils.standards_extractor import extract_standards


async def extract(url: str):
    global product_json
    data = await extract_standards(url)

    # Loop over all extracted JSON-LD blocks
    for item in data["json-ld"]:
        if isinstance(item, dict):
            # Case 1: direct Product
            if item.get("@type") == "Product":
                product_json = item
                break
            # Case 2: inside @graph
            if "@graph" in item:
                for node in item["@graph"]:
                    if node.get("@type") == "Product":
                        product_json = node
                        break

    if not product_json:
        raise ValueError("No Product found!")

    # Extract offer
    offers = product_json.get("offers", [])
    if isinstance(offers, list):
        offers = offers[0]

    price_spec = {}
    if offers and "priceSpecification" in offers:
        spec = offers["priceSpecification"][0]
        price_spec = {
            "currency": spec.get("priceCurrency", "EUR"),
            "amount": int(float(spec.get("price", 0)) * 100)  # convert to cents
        }

    # Map into your structure
    result = {
        "shopsItemId": str(product_json.get("sku", "")),
        "shopName": offers.get("seller", {}).get("name", "Unknown Shop"),
        "title": {
            "text": product_json.get("name", ""),
            "language": product_json.get("inLanguage", "de")
        },
        "description": {
            "text": product_json.get("description", "").strip(),
            "language": product_json.get("inLanguage", "de")
        },
        "price": price_spec,
        "state": "AVAILABLE" if offers.get("availability", "").endswith("InStock") else "OUT_OF_STOCK",
        "url": product_json.get("url", url),
        "images": product_json.get("image", []) if isinstance(product_json.get("image"), list) else [
            product_json.get("image")]
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))




async def main():
    await extract("")



async def crawl(url):
    async with AsyncUrlSeeder() as seeder:
        config = SeedingConfig(
            source="sitemap+cc",
            extract_head=True
        )

        urls = await seeder.urls(url, config)


if __name__ == "__main__":

    asyncio.run(main())