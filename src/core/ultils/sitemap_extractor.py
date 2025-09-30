from typing import List
from crawl4ai import AsyncUrlSeeder, SeedingConfig


async def sitemap_extractor(url: str) -> List[str]:
    """Seed URLs using sitemap + Common Crawl."""
    async with AsyncUrlSeeder() as seeder:
        config = SeedingConfig(source="sitemap+cc",
                               live_check=True,
                               verbose=True,
                               filter_nonsense_urls=True,
                               max_urls=100,
                               )
        urls = await seeder.urls(url, config)
        valid_urls = [item["url"] for item in urls]

        return valid_urls