from .base import BaseParser
from .mt5 import MT5Parser
from .ctrader import CTraderParser

# List of all available parsers
PARSERS = [MT5Parser(), CTraderParser()]

# Platform name mapping
PLATFORM_PARSERS = {
    'mt5': MT5Parser,
    'ctrader': CTraderParser,
}


def detect_platform(filepath: str) -> BaseParser:
    """Auto-detect platform from file structure"""
    for parser in PARSERS:
        if parser.can_parse(filepath):
            return parser
    raise ValueError(
        "Unable to detect platform. Please specify manually using --platform.\n"
        f"Supported platforms: {', '.join(PLATFORM_PARSERS.keys())}"
    )


def get_parser(platform: str) -> BaseParser:
    """Get parser by platform name"""
    platform_lower = platform.lower()
    if platform_lower not in PLATFORM_PARSERS:
        raise ValueError(
            f"Unknown platform: {platform}\n"
            f"Supported platforms: {', '.join(PLATFORM_PARSERS.keys())}"
        )
    return PLATFORM_PARSERS[platform_lower]()


def list_platforms() -> list[str]:
    """Return list of supported platform names"""
    return list(PLATFORM_PARSERS.keys())
