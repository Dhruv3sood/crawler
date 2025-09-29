from typing import Optional

class BaseExtractor:
    name: str = "base"

    async def extract(self, data: dict, url: str) -> Optional[dict]:
        """Extract structured product data from extruct output."""
        raise NotImplementedError
