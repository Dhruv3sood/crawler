import asyncio
import json
import os
import time
from typing import cast, Any
from urllib.parse import urlparse
from openai import OpenAI
import extruct
import requests
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, LLMConfig, LLMExtractionStrategy
from crawl4ai import JsonCssExtractionStrategy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from w3lib.html import get_base_url
from pydantic import BaseModel, Field

class Product(BaseModel):
    title: str
    price: str
    currency: str
    description: str
    shop_item_id: str
    shop_name: str
    state: str = Field(..., description="sold, available or reserved")
    images: list[str]

async def parse_schema(url: str, update_schema: bool = False):
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    schema_prompt = """
         I need just this attributes and use exactly this names for the attributes: shop_item_id (Art.Nr), shop_name 
         (The name of the shop that sales the product), title, current_price, currency, description (the longest 
         description found), state (LISTED: Item has been listed, AVAILABLE: Item is available for purchase, RESERVED: 
         Item is reserved by a buyer, SOLD: Item has been sold. REMOVED: Item has been removed  and can no longer be 
         tracked) and the images of the product. Do not hallucinate!
    """
    target_schema = """{
        "shopsItemId": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        "shopName": "Tech Store",
        "title": {
            "text": "Smartphone Case Premium",
            "language": "en"
        },
        "description": {
            "text": "Premium quality smartphone case with wireless charging support",
            "language": "en"
        },
        "price": {
            "currency": "EUR",
            "amount": 2999
        },
        "state": "AVAILABLE",
        "images": [
            "https://tech-store.com/images/premium-case-1.jpg",
            "https://tech-store.com/images/premium-case-2.jpg"
        ]
    }"""

    # TODO: Load existing schema from database instead of file
    if os.path.exists("schema.json"):
        with open("schema.json", "r", encoding="utf-8") as f:
            all_schemas = json.load(f)
    else:
        all_schemas = {}

    if base_url in all_schemas and "CSS" in all_schemas[base_url].get("schema", {}) and not update_schema:
        schema = all_schemas[base_url]["schema"]["CSS"]
        print("Schema aus Datei geladen.")
    else:
        response = requests.get(url)
        schema = JsonCssExtractionStrategy.generate_schema(
            query=schema_prompt,
            html=response.text,
            llm_config=LLMConfig(provider="deepseek/deepseek-chat", api_token=os.getenv("DEEPSEEK_API_KEY")),
            target_json_example= target_schema
        )
        print("Generiertes Schema:", json.dumps(schema, indent=2))
        all_schemas[base_url] = {
            "schema": {
                "CSS": schema,
            }
        }
        with open("streamlit/schema.json", "w", encoding="utf-8") as f:
            json.dump(all_schemas, f, ensure_ascii=False, indent=2)

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=extraction_strategy,
    )

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=url,
            config=config
        )

        if not result.success:
            print("Crawl failed:", result.error_message)
            return

        data = json.loads(result.extracted_content)



async def clean_up_data(data):
    input_json_str = json.dumps(data, ensure_ascii=False)

    prompt = f""""""
    client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

    response = client.chat.completions.create(
      model=cast(Any, "deepseek-chat"),
      messages=cast(Any, [
          {"role": "system", "content": prompt},
          {"role": "user", "content": input_json_str},
      ]),
      stream=cast(Any, False),
      response_format=cast(Any, {"type": "json_object"})
  )

    cleaned_data = response.choices[0].message.content
    print("Bereinigte Daten:", cleaned_data)
    # Token usage info
    if hasattr(response, "usage"):
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        print(f"Prompt tokens: {prompt_tokens}")
        print(f"Completion tokens: {completion_tokens}")
        print(f"Total tokens: {total_tokens}")
    else:
        print("No usage info returned.")

    cost_per_input = 0.14 / 1_000_000  # $ per token
    cost_per_output = 0.28 / 1_000_000  # $ per token

    cost = prompt_tokens * cost_per_input + completion_tokens * cost_per_output
    print(f"Estimated cost: ${cost:.6f}")

async def parse_json_ld(url: str):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    scripts = soup.find_all("script", type="application/ld+json")
    products = []

    for script in scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                for item in data:
                    if item.get("@type") == "Product":
                        products.append(item)
            elif data.get("@type") == "Product":
                products.append(data)
        except Exception:
            continue
    driver.quit()
    print(products)
    return products

async def parse_opengraph(url: str):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    metas = soup.select('meta[property^="og:"]')
    driver.quit()
    return metas

async def parse_twitter(url: str):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    twitter_data = []
    for tag in soup.find_all("meta"):
        name = tag.get("name") or tag.get("property")
        if name and name.startswith("twitter:"):
            twitter_data[name[8:]] = tag.get("content")
    driver.quit()
    return twitter_data

async def parse_rdfa(url: str):
    response = requests.get(url)
    html = response.text
    base_url = get_base_url(response.text, response.url)
    data = extruct.extract(html, base_url=base_url, syntaxes=['rdfa'])
    products = []
    for item in data.get("rdfa", []):
        if isinstance(item, dict) and item.get('@type') == 'Product':
            products.append(item)
    print(products)
    return products

async def parse_microdata(url: str):
    response = requests.get(url)
    html = response.text
    base_url = get_base_url(response.text, response.url)
    data = extruct.extract(html, base_url=base_url, syntaxes=['microdata'])
    return data.get("microdata", [])

async def extract(url: str):
    parsers = [
        ("json-ld", parse_json_ld),
        ("opengraph", parse_opengraph),
        ("twitter", parse_twitter),
        ("microdata", parse_microdata),
        ("rdfa", parse_rdfa),
        ("schema", parse_schema)
    ]
    for source, parser in parsers:
        try:
            data = await parser(url)
            if data and data != []:
                print(f"source: {source}, data: {data}")
                return {"source": source, "data": data}
        except Exception:
            pass
    print("Alle Extraktionsmethoden fehlgeschlagen.")
    return None

async def parse_markdown(url: str):
    llm_strategy = LLMExtractionStrategy(
        llm_config = LLMConfig(provider="deepseek/deepseek-chat", api_token=os.getenv("DEEPSEEK_API_KEY")),
        schema=Product.model_json_schema(),
        extraction_type="schema",
        instruction="""You are a highly intelligent data extraction agent. Your task is to analyze the provided markdown document and populate a JSON object based on the given schema.

        **Primary Objective & Scope:**
        Your first task is to identify the main product being described in the document. Focus *exclusively* on this single product.
        **CRUCIAL:** Ignore and do not extract any information from other sections, such as 'Related Products', 'You Might Also Like', 'Customers Also Bought', or lists of other items. All extracted data (title, price, descriptions, images, etc.) must belong solely to the primary product.

        **Field-by-Field Extraction Rules:**
        Adhere strictly to the following rules for each field. If a piece of information is not present in the text for the primary product, leave the corresponding field empty or null. Do not invent, infer, or hallucinate any data.

        *   **title:** Extract the primary product title. This is usually the most prominent heading.
        *   **price:**
            *   Find the product's price and its currency.
            *   The format MUST be a string like "AMOUNT CURRENCY" (e.g., "99.99 USD", "150 EUR").
            *   If multiple prices are listed, extract only the most current or final sale price.
        *   **short_description vs. long_description Logic:**
            *   First, identify if there are two **distinct** descriptive sections: a brief summary (often a tagline or a single paragraph under the title) AND a longer, more detailed body of text.
            *   **If YES:**
                *   **short_description:** Extract the brief, introductory summary.
                *   **long_description:** Extract the full, detailed product description that follows the summary.
            *   **If NO (there is only one block of descriptive text):**
                *   **short_description:** This field **MUST** be left empty/null.
                *   **long_description:** The *entire* block of descriptive text goes into this field.
            *   **CRUCIAL:** Do NOT copy the first few sentences of a long text block to create a `short_description`. The `short_description` must be structurally separate in the source document.
        *   **availability:**
            *   Determine the product's availability status.
            *   The value MUST be one of the following exact strings: "available", "sold", or "reserved".
            *   Infer the status from context clues (e.g., "In Stock" -> "available", "Sold Out" -> "sold").
        *   **images:**
            *   Find all URLs pointing to product images.
            *   Extract them into a list of strings, ensuring each is a complete, absolute URL.
        """,
        chunk_token_threshold=1000,
        overlap_rate=0.0,
        apply_chunking=True,
        input_format="fit_markdown",   # or "html", "fit_markdown"
        extra_args={"temperature": 0.0, "max_tokens": 800}
    )

    crawl_config = CrawlerRunConfig(
        extraction_strategy=llm_strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
            config=crawl_config
        )

        if result.success:
            data = json.loads(result.extracted_content)
            print("Extracted items:", data)

            llm_strategy.show_usage()  # prints token usage

            usage = llm_strategy.total_usage

            # Rates
            input_rate = 0.27  # $ per 1M tokens
            output_rate = 1.10  # $ per 1M tokens

            costs = (usage.prompt_tokens / 1_000_000 * input_rate) + (
                    usage.completion_tokens / 1_000_000 * output_rate)

            print(f"Total cost: ${costs:.3f}")
        else:
            print("Error:", result.error_message)

asyncio.run(parse_schema("https://www.example.com"))
