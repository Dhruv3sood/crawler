import httpx
import os
import sys
from dotenv import load_dotenv


async def send_items(items):
    async with httpx.AsyncClient() as client:
        load_dotenv()
        api_url = os.getenv("AWS_API_URL")
        if not api_url:
            print("ERROR: AWS_API_URL environment variable is not set.")
            sys.exit(1)

        response = await client.put(
            api_url, json={"items": items}, headers={"Content-Type": "application/json"}
        )
        print(f"Response: {response}")
