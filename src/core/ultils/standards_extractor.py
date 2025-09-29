from typing import Optional
from src.strategies.registry import EXTRACTORS

def is_valid_product(extracted: dict) -> bool:
    """Check if the extraction contains actual product info."""
    if not extracted:
        return False
    # Example: require at least title or price
    if extracted.get("title", {}).get("text") or extracted.get("price", {}).get("amount", 0) > 0:
        return True
    return False

async def extract_standard(data: dict, url: str, preferred: list[str] | None = None) -> dict | None:
    """
    Try structured data extractors in order until one returns results.
    :param data: extruct output dict
    :param url: page URL
    :param preferred: optional list of extractor names in desired order
    """
    extractors = EXTRACTORS
    if preferred:
        extractors = sorted(
            EXTRACTORS,
            key=lambda e: preferred.index(e.name) if e.name in preferred else len(preferred)
        )

    for extractor in extractors:
        result = await extractor.extract(data, url)
        if is_valid_product(result):
            return result
    return None
