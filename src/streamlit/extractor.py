import json
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai import JsonCssExtractionStrategy
import os
import requests
import extruct
from w3lib.html import get_base_url

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

async def parse_schema(url: str, prompt:str, update_schema: bool = False):
    print(f"Running AI Schema parser for URL: {url}")
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    schema_file = "schema.json"

    if os.path.exists(schema_file):
        with open(schema_file, "r", encoding="utf-8") as f:
            all_schemas = json.load(f)
    else:
        all_schemas = {}

    if base_url in all_schemas and "CSS" in all_schemas[base_url].get("schema", {}) and not update_schema:
        schema = all_schemas[base_url]["schema"]["CSS"]
        print("Schema loaded from local cache (schema.json).")
    else:
        print("Generating new schema with LLM...")
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            schema = JsonCssExtractionStrategy.generate_schema(
                html=response.text,
                llm_config=LLMConfig(provider="deepseek/deepseek-chat", api_token=os.getenv("DEEPSEEK_API_KEY")),
                query=prompt
            )
            print("Generated Schema:", json.dumps(schema, indent=2))
            all_schemas[base_url] = { "schema": { "CSS": schema } }
            with open(schema_file, "w", encoding="utf-8") as f:
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
        return json.loads(result.extracted_content)


async def parse_json_ld(url: str):
    print(f"Running JSON-LD parser for URL: {url}")
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    response.raise_for_status()
    html = response.text

    soup = BeautifulSoup(html, "html.parser")
    scripts = soup.find_all("script", type="application/ld+json")

    products = []
    for script in scripts:
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                products.extend([item for item in data if isinstance(item, dict) and item.get("@type") == "Product"])
            elif isinstance(data, dict) and data.get("@type") == "Product":
                products.append(data)
        except json.JSONDecodeError:
            continue

    print(f"Found {len(products)} products via JSON-LD.")
    return products

async def parse_opengraph(url: str):
    print(f"Running OpenGraph parser for URL: {url}")
    html = await get_page_source_with_crawler(url)
    if not html: return {}

    soup = BeautifulSoup(html, "html.parser")
    og_data = {}
    metas = soup.select('meta[property^="og:"]')
    for meta in metas:
        prop = meta.get('property')[3:]
        content = meta.get('content')
        if prop and content:
            og_data[prop] = content
    print(f"Found {len(og_data)} OpenGraph properties.")
    return og_data

async def parse_twitter(url: str):
    print(f"Running Twitter Card parser for URL: {url}")
    html = await get_page_source_with_crawler(url)
    if not html: return {}

    soup = BeautifulSoup(html, "html.parser")
    twitter_data = {}
    for tag in soup.find_all("meta"):
        name = tag.get("name") or tag.get("property")
        if name and name.startswith("twitter:"):
            twitter_data[name[8:]] = tag.get("content")
    print(f"Found {len(twitter_data)} Twitter Card properties.")
    return twitter_data

async def parse_microdata(url: str):
    print(f"Running Microdata parser for URL: {url}")
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    response.raise_for_status()
    base_url_val = get_base_url(response.text, response.url)
    data = extruct.extract(response.text, base_url=base_url_val, syntaxes=['microdata'])
    print(f"Found {len(data.get('microdata', []))} items via Microdata.")
    return data.get("microdata", [])

async def parse_rdfa(url: str):
    print(f"Running RDFA parser for URL: {url}")
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    response.raise_for_status()
    base_url_val = get_base_url(response.text, response.url)
    data = extruct.extract(response.text, base_url=base_url_val, syntaxes=['rdfa'])
    print(f"Found {len(data.get('rdfa', []))} items via RDFA.")
    return data.get("rdfa", [])