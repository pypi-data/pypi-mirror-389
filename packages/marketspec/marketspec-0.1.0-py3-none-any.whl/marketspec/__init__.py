from __future__ import annotations

from typing import Optional, cast

from . import exchanges as _exchanges  # auto-register resolvers on import
from .registry import resolve_venue_symbol
from .types import Expiry, OptionSide, Spec, Type
from .unified import parse_unified_symbol, set_stables

__all__ = [
    "venue_symbol",
    "parse_unified_symbol",
    "resolve_venue_symbol",
    "Spec",
    "set_stables",
    "_exchanges",
]


def _spec_from_dict(d: dict[str, object | None]) -> Spec:
    return Spec(
        base=cast(str, d["base"]),
        quote=cast(str, d["quote"]),
        type=cast(Type, d["type"]),
        linear=cast(Optional[bool], d["linear"]),
        settle=cast(Optional[str], d["settle"]),
        expiry=cast(Expiry, d["expiry"]),
        strike=cast(Optional[float], d.get("strike")),
        option=cast(OptionSide, d.get("option")),
        week=cast(Optional[str], d.get("week")),
    )


def venue_symbol(exchange: str, unified: str) -> str:
    """
    One-call API. Parse a unified symbol string and return the venue-native symbol.

    Examples:
        venue_symbol("binance", "BTC/USDT:USDT")          -> "BTCUSDT"
        venue_symbol("bybit",   "BTC/USD:USD-20251227")   -> "BTCUSD_20251227"
        venue_symbol("binance", "ETH-20251226-2500-C")    -> "ETH-20251226-2500-C"
    """
    spec = _spec_from_dict(parse_unified_symbol(unified))
    return resolve_venue_symbol(exchange=exchange, spec=spec)
