from pydantic import BaseModel


class Price(BaseModel):
    currency: str
    amount: int