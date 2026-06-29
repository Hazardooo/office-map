from src.printers.parsers.kyocera import KyoceraParser
from src.printers.parsers.canon import CanonParser
from src.printers.parsers.hp import HPParser

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