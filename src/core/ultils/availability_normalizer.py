def normalize_availability(value) -> str:
    if value is None:
        return ""
    s = str(value)
    # handle URIs like https://schema.org/InStock or schema:InStock
    for sep in ("/", "#", ":"):
        if sep in s:
            s = s.split(sep)[-1]
    return s.strip().upper()


AVAILABILITY_MAP = {
    "INSTOCK": "AVAILABLE",
    "INSTOREONLY": "AVAILABLE",
    "ONLINEONLY": "AVAILABLE",
    "LIMITEDAVAILABILITY": "AVAILABLE",
    "MADETOORDER": "AVAILABLE",
    "BACKORDER": "LISTED",
    "PREORDER": "LISTED",
    "PRESALE": "LISTED",
    "RESERVED": "RESERVED",
    "SOLDOUT": "SOLD",
    "DISCONTINUED": "REMOVED",
    "OUTOFSTOCK": "SOLD",
}

def map_availability_to_state(availability_raw: str) -> str:
    # Listen oder Einzelwerte unterstützen
    if isinstance(availability_raw, list) and availability_raw:
        key = normalize_availability(availability_raw[0])
    else:
        key = normalize_availability(availability_raw)
    return AVAILABILITY_MAP.get(key, "UNKNOWN")