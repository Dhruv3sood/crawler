import json
import requests
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, ExtractionStrategy, SeedingConfig, AsyncUrlSeeder
import asyncio


class JsonLdExtractionStrategy(ExtractionStrategy):
    def __init__(self):
        self.input_format = "html"

    def extract(self, response, *args, **kwargs):
        resp = requests.get(response)
        soup = BeautifulSoup(resp.text, "html.parser")

        json_ld_scripts = soup.find_all("script", {"type": "application/ld+json"})
        json_ld_data = []

        for script in json_ld_scripts:
            raw = script.string.strip() if script.string else ""
            if not raw:
                continue
            try:
                data = json.loads(raw)

                # If data is wrapped in @graph, flatten it
                if "@graph" in data:
                    json_ld_data.extend(data["@graph"])
                else:
                    json_ld_data.append(data)
            except json.JSONDecodeError:
                continue

        # Filter only Product entries
        products = [item for item in json_ld_data if isinstance(item, dict) and item.get("@type") == "Product"]

        print(f"Found {len(products)} products via JSON-LD.")
        # Normalize into a clean schema
        normalized = []
        for p in products:
            offers_list = p.get("offers", [])
            offer = {}
            if isinstance(offers_list, list) and offers_list:
                offer = offers_list[0]  # take first offer

            brand = p.get("brand", {})
            brand_name = brand.get("name") if isinstance(brand, dict) else brand

            # Handle priceSpecification as a list
            price_spec_list = offer.get("priceSpecification", [])
            price_spec = {}
            if isinstance(price_spec_list, list) and price_spec_list:
                price_spec = price_spec_list[0]

            normalized.append({
                "id": p.get("productID") or p.get("sku") or p.get("mpn"),
                "name": p.get("name"),
                "description": p.get("description"),
                "image": p.get("image"),
                "brand": brand_name,
                "price": offer.get("price") or price_spec.get("price"),
                "currency": offer.get("priceCurrency") or price_spec.get("priceCurrency"),
                "availability": offer.get("availability"),
                "url": offer.get("url"),
                "seller": (
                    offer.get("seller", {}).get("name")
                    if isinstance(offer.get("seller"), dict)
                    else offer.get("seller")
                )
            })

        return normalized


async def main(url):

    crawl_config = CrawlerRunConfig(
        extraction_strategy=JsonLdExtractionStrategy()
    )

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=url,
            config=crawl_config,
            session_id="session1"
        )

        if result.success:
            print(json.dumps(result.extracted_content, indent=2, ensure_ascii=False))
        else:
            print("Crawl failed:", result.error_message)

async def crawl(url):
    async with AsyncUrlSeeder() as seeder:
        config = SeedingConfig(
            source="sitemap+cc",
            extract_head=True
        )

        urls = await seeder.urls(url, config)

        # Filter further by price (from metadata)

        for u in urls:
            print("url: ",u)





if __name__ == "__main__":
    asyncio.run(main(""))
