import asyncio
import json
from crawl4ai import BrowserConfig, CrawlerRunConfig, CacheMode, MemoryAdaptiveDispatcher, AsyncWebCrawler
from extruct import extract as extruct_extract
from w3lib.html import get_base_url
from src.core.ultils.sitemap_extractor import sitemap_extractor
from src.core.ultils.standards_extractor import extract_standard


async def crawl_batch(url: str) -> None:
    urls = await sitemap_extractor(url)

    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        stream=False,
        check_robots_txt=True,
    )

    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=100.0,
        check_interval=1.0,
        max_session_permit=100,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(urls=urls, config=run_config, dispatcher=dispatcher)
        list_data = []
        for result in results:
            if result.success:
                base_url = get_base_url(result.html, result.url)
                structured = extruct_extract(
                    result.html,
                    base_url=base_url,
                    syntaxes=["json-ld", "microformat", "microdata", "rdfa", "opengraph"],
                )

                # auto-dispatch extractors
                extracted_data = await extract_standard(structured, result.url)
                if extracted_data:
                    list_data.append(extracted_data)
                else:
                    print(f"No structured data found for {result.url}")
            else:
                print(f"Failed to crawl {result.url}: {result.error_message}")

        with open("../../data/crawled_data.json", "w") as f:
            json.dump(list_data, f, indent=4)

if __name__ == "__main__":
    asyncio.run(crawl_batch(""))