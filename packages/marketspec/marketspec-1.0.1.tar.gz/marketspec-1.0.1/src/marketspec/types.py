from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal, Union

from .unified import _format_strike, _yyyymmdd

__all__ = ["Spec", "Type", "OptionSide", "Expiry"]

Type = Literal["spot", "swap", "future", "option"]
OptionSide = Literal["C", "P", None]
Expiry = Union[str, date, datetime]


@dataclass(frozen=True)
class Spec:
    base: str
    quote: str
    type: Type  # spot|swap|future|option
    linear: bool | None
    settle: str | None
    expiry: Expiry | None
    strike: float | None = None
    option: OptionSide = None
    week: str | None = None

    def __post_init__(self) -> None:
        alnum = re.compile(r"^[A-Z0-9]+$")
        object.__setattr__(self, "base", self.base.upper())
        object.__setattr__(self, "quote", self.quote.upper())
        if not alnum.fullmatch(self.base):
            raise ValueError("base/quote must be alphanumeric A-Z0-9")
        if self.type != "option" and not alnum.fullmatch(self.quote):
            raise ValueError("base/quote must be alphanumeric A-Z0-9")
        if self.settle:
            object.__setattr__(self, "settle", self.settle.upper())
            if not alnum.fullmatch(self.settle):
                raise ValueError("settle must be alphanumeric A-Z0-9")
        if self.option:
            side = str(self.option).upper()
            if side not in {"C", "P"}:
                raise ValueError("option must be C or P")
            object.__setattr__(self, "option", side)
        if self.type in ("swap", "future"):
            if self.settle is None:
                raise ValueError("swap/future require settle")
            if self.linear is None:
                raise ValueError("swap/future require linear flag")
        if self.type == "future" and self.expiry is None:
            raise ValueError("future requires expiry")
        if self.type == "option":
            if not (self.expiry and self.strike and self.option):
                raise ValueError("option requires expiry,strike,option")
            # Validate date now to fail early even before resolution.
            _ = _yyyymmdd(self.expiry)
            # Positive strike required. Also canonicalize via formatter.
            _ = _format_strike(self.strike)

    # Convenience for round-tripping in tests and logs.
    def unified(self) -> str:
        t = self.type
        b, q = self.base, self.quote
        if t == "spot":
            return f"{b}/{q}"
        if t in {"swap", "future"}:
            if self.settle is None:
                raise ValueError("swap/future require settle")
            tail = f"-{_yyyymmdd(self.expiry)}" if t == "future" else ""
            return f"{b}/{q}:{self.settle}{tail}"
        if t == "option":
            if self.expiry is None or self.strike is None or self.option is None:
                raise ValueError("option requires expiry,strike,option")
            strike = _format_strike(self.strike)
            return f"{b}-{_yyyymmdd(self.expiry)}-{strike}-{self.option}"
        raise ValueError(f"Unsupported type: {t}")
