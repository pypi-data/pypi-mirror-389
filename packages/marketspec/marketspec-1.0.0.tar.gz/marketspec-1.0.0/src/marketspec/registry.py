from __future__ import annotations

import re
import warnings
from typing import Callable

from .types import Spec

__all__ = ["register", "resolve", "Resolver", "ResolveError"]


class ResolveError(ValueError):
    """Resolution failed for a venue symbol."""


Resolver = Callable[[Spec], str]
_REGISTRY: dict[str, Resolver] = {}
# Venue symbol validation (non-option). Hyphen remains disallowed by design.
_SYM_SIMPLE = re.compile(r"^[A-Z0-9_]+$")
_SYM_OPTION = re.compile(r"^[A-Z0-9]+-\d{8}-[0-9]+(?:\.[0-9]+)?-[CP]$")


def register(exchange: str) -> Callable[[Resolver], Resolver]:
    """Decorator to register a resolver for an exchange key."""
    key = exchange.lower()

    def deco(fn: Resolver) -> Resolver:
        if key in _REGISTRY and _REGISTRY[key] is not fn:
            raise RuntimeError(f"Resolver already registered for {exchange}")
        _REGISTRY[key] = fn
        return fn

    return deco


def resolve(exchange: str, spec: Spec) -> str:
    try:
        fn = _REGISTRY[exchange.lower()]
    except KeyError as e:
        raise ResolveError(f"No symbol resolver for exchange={exchange}") from e
    sym = fn(spec).strip()
    if not sym:
        raise ResolveError(f"Empty symbol for exchange={exchange} with spec={spec}")
    if not (_SYM_SIMPLE.fullmatch(sym) or _SYM_OPTION.fullmatch(sym)):
        raise ResolveError(f"Illegal characters in symbol: {sym!r}")
    return sym

