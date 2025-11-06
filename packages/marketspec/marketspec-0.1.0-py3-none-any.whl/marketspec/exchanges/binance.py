from __future__ import annotations

from ..registry import register
from ..types import Spec
from ..unified import _format_strike, _yyyymmdd  # UPDATED

__all__ = ["_binance"]


@register("binance")
def _binance(s: Spec) -> str:
    b, q, t = s.base, s.quote, s.type

    if t == "spot":
        return f"{b}{q}"

    if t in {"swap", "future"}:
        if s.settle is None or s.linear is None:
            raise ValueError("swap/future require settle and linear")
        # Binance linear: settle==quote in stables. Inverse: settle==USD.
        if s.linear and s.settle != q:
            raise ValueError(f"linear contract must settle in quote: {b}/{q}:{s.settle}")
        if not s.linear and s.settle != "USD":
            raise ValueError(f"inverse contract must settle in USD: {b}/{q}:{s.settle}")

        if s.linear is False:
            root = f"{b}USD"
            return f"{root}_{_yyyymmdd(s.expiry)}" if t == "future" else f"{root}_PERP"

        root = f"{b}{q}"
        return f"{root}_{_yyyymmdd(s.expiry)}" if t == "future" else root

    if t == "option":
        if s.strike is None or s.expiry is None or s.option is None:
            raise ValueError("option requires expiry,strike,option")
        strike = _format_strike(s.strike)
        return f"{b}-{_yyyymmdd(s.expiry)}-{strike}-{s.option}"

    raise ValueError(f"Unsupported type for binance: {t}")
