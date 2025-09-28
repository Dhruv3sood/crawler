import extruct
from crawl4ai import AsyncWebCrawler

async def extract_standards(url: str, standard: str = "json-ld") -> dict:
    """
    Extracts structured data from a webpage using the specified standard.

    Args:
        url (str): The URL of the webpage to extract data from.
        standard (str, optional): The standard to use ('json-ld', 'microdata', 'opengraph', 'microformat', 'rdfa', 'dublincore'). Default is 'json-ld'.

    Returns:
        dict: The extracted structured data as a dictionary.
    """
    async with AsyncWebCrawler() as crawler:
        response = await crawler.arun(url=url)
        data = extruct.extract(response.html, syntaxes=[standard], uniform=True)

        #save results in json file in data in the root directory
        return data