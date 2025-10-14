from pydantic import BaseModel


def something():
    print("hello")


class LocalizedText(BaseModel):
    text: str
    language: str
