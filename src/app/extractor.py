import asyncio
import json
from urllib.parse import urlparse
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai import JsonCssExtractionStrategy
import os

async def get_page_source_with_crawler(url: str) -> str:
    """Fetch fully rendered HTML using crawl4ai with fallback handling."""
    print(f"Fetching page source for {url} using crawler...")
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)

        if not result.success:
            print(f"Failed to fetch page source: {result.error_message}")
            return ""

        html = ""
        if hasattr(result, "html_content") and result.html_content:
            html = result.html_content
        elif hasattr(result, "data") and result.data.get("html"):
            html = result.data["html"]
        elif isinstance(result, list) and len(result) > 0 and getattr(result[0], "html_content", None):
            html = result[0].html_content

        if not html:
            print("Crawl succeeded but no HTML was returned.")
            return ""

        return html

def save_result_to_json(base_url: str, result, url: str | None = None, file_path: str = "data/results_by_baseurl.json"):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            all_results = json.load(f)
    else:
        all_results = {}

    items = result if isinstance(result, list) else [result]

    for item in items:
        if isinstance(item, dict):
            if url is not None and "url" not in item:
                item["url"] = url
            entry = item
        else:
            entry = {"extracted": item}
            if url is not None:
                entry["url"] = url

        if base_url in all_results:
            all_results[base_url].append(entry)
        else:
            all_results[base_url] = [entry]

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

async def parse_schema(url: str, update_schema: bool = False):
    print(f"Running AI Schema parser for URL: {url}")
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "schema.json")

    prompt= """
         I need just this attributes and use exactly this names for the attributes: shop_item_id (ID or Art.Nr of the product), shop_name 
         (The name of the shop that sales the product), title, current_price (The selling price of the product), currency, description (the longest 
         description found), state (LISTED: Item has been listed, AVAILABLE: Item is available for purchase, RESERVED: 
         Item is reserved by a buyer, SOLD: Item has been sold. REMOVED: Item has been removed  and can no longer be 
         tracked) and image (image's url of the product). Do not hallucinate!
    """

    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            all_schemas = json.load(f)
    else:
        all_schemas = {}

    if base_url in all_schemas and "CSS" in all_schemas[base_url].get("schema", {}) and not update_schema:
        schema = all_schemas[base_url]["schema"]["CSS"]
        print("Schema loaded from local cache (schema.json).")
        print(schema)
    else:
        print("Generating new schema with LLM...")
        try:
            async with AsyncWebCrawler() as crawler:
                response = await crawler.arun(url=url)
                schema = JsonCssExtractionStrategy.generate_schema(
                    html=response.fit_html,
                    llm_config=LLMConfig(provider="deepseek/deepseek-chat", api_token=os.getenv("DEEPSEEK_API_KEY")),
                    query=prompt
                )
                print("Generated Schema:", json.dumps(schema, indent=2))
                all_schemas[base_url] = { "schema": { "CSS": schema } }
                with open(schema_path, "w", encoding="utf-8") as f:
                    json.dump(all_schemas, f, ensure_ascii=False, indent=2)
                print("Schema saved to schema.json")
        except Exception as e:
            print(f"Failed to generate schema: {e}")
            return None

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=extraction_strategy,
    )
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url=url, config=config)
        if not result.success:
            print(f"Crawl failed: {result.error_message}")
            return None
        extracted = json.loads(result.extracted_content)
        print("Extraction Result:", json.dumps(extracted, indent=2, ensure_ascii=False))



if __name__ == "__main__":
    asyncio.run(parse_schema(""))