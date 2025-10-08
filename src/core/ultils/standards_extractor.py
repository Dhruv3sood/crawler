from src.strategies.registry import EXTRACTORS

def is_valid_product(extracted) -> bool:
    """Akzeptiert ein Produkt oder eine Liste von Produkten."""
    if not extracted:
        return False
    if isinstance(extracted, list):
        return any(is_valid_product(item) for item in extracted)
    # Einzelnes Produkt
    if extracted.get("title", {}).get("text") or extracted.get("price", {}).get("amount", 0) > 0:
        return True
    return False

async def extract_standard(data: dict, url: str, preferred: list[str] | None = None) -> dict | list[dict] | None:
    """
    Gibt ein Produkt oder eine Liste von Produkten zurück.
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
            print(f"Extractor '{extractor.name}' found valid product data.")
            print(f"Row data: {data}")
            print(f"Column data: {result}")
            return result
    return None