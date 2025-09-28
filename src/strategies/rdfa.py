import asyncio
from src.core.ultils.standards_extractor import extract_standards


async def extract(url: str) -> None:
    data = await extract_standards(url, standard="rdfa")
    print(data)

if __name__ == "__main__":
    asyncio.run(extract(""))
