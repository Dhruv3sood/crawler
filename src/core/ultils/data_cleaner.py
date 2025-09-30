import os
import json
from typing import Iterable, Union, Any, Coroutine

from openai import OpenAI
from openai.types.chat import ChatCompletionUserMessageParam, ChatCompletionSystemMessageParam
from openai.types.shared_params import ResponseFormatJSONSchema
from openai.types.shared_params.response_format_json_schema import JSONSchema

from src.core.model.item import Item
from src.core.model.price import Price


async def refine_data(scraped_data: dict) -> Item:
    """
    Refine only the price and state by sending minimal data to DeepSeek.
    Other fields remain unchanged.
    """

    client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

    # Only pass minimal fields to DeepSeek
    minimal_data = {
        "current_price": scraped_data.get("current_price"),
        "currency": scraped_data.get("currency"),
        "state": scraped_data.get("state"),
    }

    input_json = json.dumps(minimal_data, ensure_ascii=False)

    prompt = """
        You are a product data normalization agent.
        Normalize this JSON with only price, currency, and state:
        
        - Price must be an object: { "currency": "<CURRENCY>", "amount": <integer in cents> }
        - State must be one of: LISTED, AVAILABLE, RESERVED, SOLD, REMOVED
        - Return the final JSON object with only the normalized fields
        - Do not invent or hallucinate any other data
        """

    messages: Iterable[Union[ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam]] = [
        ChatCompletionSystemMessageParam(content=prompt, role="system"),
        ChatCompletionUserMessageParam(content=input_json, role="user"),
    ]
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        response_format= ResponseFormatJSONSchema(type="json_object",json_schema=JSONSchema(name="normalized_response", schema={
            "type": "object",
            "properties": {
                "price": {
                    "type": "object",
                    "properties": {
                        "currency": {"type": "string"},
                        "amount": {"type": "integer", "minimum": 0}
                    },
                    "required": ["currency", "amount"]
                },
                "state": {
                    "type": "string",
                    "enum": ["LISTED", "AVAILABLE", "RESERVED", "SOLD", "REMOVED"]
                }
            },
            "required": ["price", "state"]
        }))
    )

    normalized_str = response.choices[0].message.content

    normalized: dict = json.loads(normalized_str)  # convert JSON string → dict

    item = Item(
        shopId=scraped_data.get("shop_item_id"),
        shopsItemId=scraped_data.get("shop_item_id"),
        shopName=scraped_data.get("shopName", ""),
        url=scraped_data.get("url"),
        images=[scraped_data.get("image")] if scraped_data.get("image") else [],
        price=Price(**normalized["price"]),
        state=normalized["state"],
        title={"text": scraped_data.get("title", ""), "language": "en"},
        description={"text": scraped_data.get("description", ""), "language": "en"}
    )

    return item
