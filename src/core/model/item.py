from typing import List
from pydantic import BaseModel, Field
from src.core.model.localized_text import LocalizedText
from src.core.model.price import Price


class Item(BaseModel):
    shopId: str = Field(..., description="Unique shop identifier (UUID)")
    shopsItemId: str = Field(..., description="Unique item identifier within the shop (e.g., SKU, ASIN)")
    shopName: str
    title: LocalizedText
    description: LocalizedText
    price: Price
    state: str = Field(..., description="AVAILABLE, SOLD, RESERVED, LISTED, REMOVED")
    url: str
    images: List[str]
