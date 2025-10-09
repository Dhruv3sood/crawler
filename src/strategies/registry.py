from src.strategies.json_ld import JsonLDExtractor
from src.strategies.microdata import MicrodataExtractor
from src.strategies.opengraph import OpenGraphExtractor
from src.strategies.rdfa import RdfaExtractor

EXTRACTORS = [
    JsonLDExtractor(),
    MicrodataExtractor(),
    RdfaExtractor(),
    OpenGraphExtractor(),
]
