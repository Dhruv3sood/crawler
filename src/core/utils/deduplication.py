from typing import List, Dict, Any


def _field_score(value: Any) -> int:
    """
    Assign a simple score to a field's richness.
    Non-empty strings/objects get 1, lists get length-based score (capped), price with amount>0 adds 2.
    """
    if value is None:
        return 0
    if isinstance(value, dict):
        if "amount" in value:
            try:
                return 2 if int(value.get("amount") or 0) > 0 else 0
            except Exception:
                return 0
        return 1 if any(v not in (None, "", "UNKNOWN") for v in value.values()) else 0
    if isinstance(value, list):
        return min(len([v for v in value if v]), 5)
    if isinstance(value, str):
        return 1 if value.strip() and value != "UNKNOWN" else 0
    if isinstance(value, (int, float)):
        return 1 if value else 0
    return 0


def score_product(product: Dict[str, Any]) -> int:
    """
    Compute a richness score for a product dict to decide which to keep when deduplicating.
    Higher score means more complete info.
    """
    weights = {
        "title": 3,
        "description": 2,
        "price": 4,
        "images": 3,
        "state": 1,
        "url": 2,
        "shopsItemId": 2,
        "shopId": 1,
        "shopName": 1,
    }

    score = 0
    for key, weight in weights.items():
        score += weight * _field_score(product.get(key))
    # small bonus for longer descriptions and multiple images
    desc_text = (product.get("description") or {}).get("text", "")
    if isinstance(desc_text, str) and len(desc_text) > 120:
        score += 2
    images = product.get("images") or []
    if isinstance(images, list) and len(images) >= 3:
        score += 2
    return score


def product_identity(product: Dict[str, Any]) -> str:
    """
    Build a cross-domain identity for a product using normalized title or canonical URL path.
    Prefer normalized title text; fallback to URL path without domain and query.
    """
    title = (product.get("title") or {}).get("text", "").strip().lower()
    if title:
        return f"title::{title}"
    url = (product.get("url") or "").strip().lower()
    if url:
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            path = parsed.path.rstrip("/")
            return f"urlpath::{path}"
        except Exception:
            return f"url::{url}"
    # last resort
    return product.get("shopsItemId") or "unknown"


def deduplicate_products_across_domains(products_by_domain: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Given a mapping of domain -> list of product dicts (already extracted), group by identity and
    keep the most informative product (highest score). If multiple products tie, prefer one with price>0,
    then the one with most images, then first seen.
    """
    identity_to_best: Dict[str, Dict[str, Any]] = {}

    for domain, products in products_by_domain.items():
        if not products:
            continue
        for product in products:
            identity = product_identity(product)
            candidate = product
            if identity in identity_to_best:
                current_best = identity_to_best[identity]
                s_new = score_product(candidate)
                s_old = score_product(current_best)
                if s_new > s_old:
                    identity_to_best[identity] = candidate
                elif s_new == s_old:
                    # tie-breakers
                    new_price = (candidate.get("price") or {}).get("amount") or 0
                    old_price = (current_best.get("price") or {}).get("amount") or 0
                    if new_price and not old_price:
                        identity_to_best[identity] = candidate
                    elif (candidate.get("images") and len(candidate.get("images")) > len(current_best.get("images") or [])):
                        identity_to_best[identity] = candidate
            else:
                identity_to_best[identity] = candidate

    return list(identity_to_best.values())


