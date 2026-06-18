from .kyocera import KyoceraParser
from .canon import CanonParser
from .hp import HPParser

PARSERS = {
    "kyocera": KyoceraParser,
    "canon": CanonParser,
    "hp": HPParser,
}

def get_parser(vendor: str, ip: str):
    parser_class = PARSERS.get(vendor.lower())
    if not parser_class:
        raise ValueError(f"Неизвестный производитель: {vendor}")
    return parser_class(ip)