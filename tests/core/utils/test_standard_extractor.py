import pytest
from src.core.utils.standards_extractor import extract_standard, is_valid_product


@pytest.mark.asyncio
async def test_extract_standard_with_generic_data(monkeypatch):
    """Test extract_standard using anonymized, slightly modified structured data."""

    # --- Anonymized mock data ---
    data = {
        "microdata": [
            {
                "type": "https://schema.org/Product",
                "properties": {
                    "name": "Collectible Medal Set 1940s",
                    "image": [
                        "https://example-store.test/shop/_3780602.JPG?ts=1759398792",
                        "https://example-store.test/shop/_3780601.JPG?ts=1759398792",
                    ],
                    "releaseDate": "2025-10-07",
                    "offers": {
                        "type": "https://schema.org/Offer",
                        "properties": {
                            "url": "https://example-store.test/shop/collectible-medal-set-1940s/",
                            "priceCurrency": "EUR",
                            "price": "130",
                        },
                    },
                    "sku": "M78123",
                },
            }
        ],
        "json-ld": [
            {
                "@context": "https://schema.org",
                "@graph": [
                    {
                        "@type": "WebSite",
                        "@id": "https://example-store.test/#/schema/WebSite",
                        "url": "https://example-store.test/",
                        "name": "Example Collectibles",
                        "description": "Shop for vintage collectibles.",
                        "inLanguage": "de",
                    },
                    {
                        "@type": "WebPage",
                        "@id": "https://example-store.test/shop/collectible-medal-set-1940s/",
                        "url": "https://example-store.test/shop/collectible-medal-set-1940s/",
                        "name": "Collectible Medal Set 1940s - Example Collectibles",
                        "description": "Well-preserved set, lightly used.",
                        "inLanguage": "de",
                        "datePublished": "2025-10-01T11:26:56+00:00",
                    },
                    {
                        "@type": "Product",
                        "@id": "https://example-store.test/shop/collectible-medal-set-1940s/#product",
                        "name": "Collectible Medal Set 1940s",
                        "url": "https://example-store.test/shop/collectible-medal-set-1940s/",
                        "description": "Well-preserved set, original case included.",
                        "image": "https://example-store.test/media/medal-set.jpg",
                        "sku": "A1023",
                        "offers": [
                            {
                                "@type": "Offer",
                                "priceSpecification": [
                                    {
                                        "@type": "UnitPriceSpecification",
                                        "price": "275.00",
                                        "priceCurrency": "EUR",
                                        "valueAddedTaxIncluded": True,
                                        "validThrough": "2026-12-31",
                                    }
                                ],
                                "priceValidUntil": "2026-12-31",
                                "availability": "http://schema.org/InStock",
                            }
                        ],
                    },
                ],
            }
        ],
        "opengraph": [
            {
                "namespace": {
                    "og": "http://ogp.me/ns#",
                    "article": "http://ogp.me/ns/article#",
                },
                "properties": [
                    ("og:type", "product"),
                    ("og:site_name", "Example Collectibles"),
                    ("og:title", "Collectible Medal Set 1940s"),
                    ("og:description", "Well-preserved set, original case included."),
                    (
                        "og:url",
                        "https://example-store.test/shop/collectible-medal-set-1940s/",
                    ),
                    ("og:image", "https://example-store.test/media/medal-set.jpg"),
                    ("article:published_time", "2025-10-01T11:26:56+00:00"),
                ],
            }
        ],
        "rdfa": [
            {
                "@id": "https://example-store.test/shop/collectible-medal-set-1940s/",
                "http://ogp.me/ns#type": [{"@value": "product"}],
                "http://www.w3.org/1999/xhtml/vocab#role": [
                    {"@id": "http://www.w3.org/1999/xhtml/vocab#none"}
                ],
                "http://ogp.me/ns#description": [
                    {"@value": "Well-preserved set, original case included."}
                ],
                "http://ogp.me/ns#locale": [{"@value": "de_DE"}],
                "http://ogp.me/ns#image": [
                    {"@value": "https://example-store.test/media/medal-set.jpg"}
                ],
                "product:price": [{"@value": "275.00"}],  # <-- add
                "product:price:currency": [{"@value": "EUR"}],  # <-- add
            }
        ],
    }

    # --- Execute the function under test ---
    result = await extract_standard(
        data,
        "https://example-store.test/shop/collectible-medal-set-1940s/",
        preferred=["json-ld", "microdata", "opengraph", "rdfa"],
    )

    # --- Assertions ---
    assert isinstance(result, dict)
    assert is_valid_product(result)

    # Shops item ID assertion
    assert result["shopsItemId"] == "A1023"

    # Title assertions
    assert result["title"]["text"] == "Collectible Medal Set 1940s"
    assert "language" in result["title"]
    assert result["title"]["language"] == "de"

    # Description assertions
    assert "description" in result
    assert "well-preserved" in result["description"]["text"].lower()
    assert result["description"]["language"] == "de"

    # Price assertions
    assert result["price"]["amount"] == 27500
    assert result["price"]["currency"] == "EUR"

    # Image assertions
    assert result["images"] == [
        "https://example-store.test/media/medal-set.jpg",
        "https://example-store.test/shop/_3780602.JPG?ts=1759398792",
        "https://example-store.test/shop/_3780601.JPG?ts=1759398792",
    ]

    # Product state and URL assertions
    assert result["state"] == "AVAILABLE"
    assert (
        result["url"] == "https://example-store.test/shop/collectible-medal-set-1940s/"
    )
