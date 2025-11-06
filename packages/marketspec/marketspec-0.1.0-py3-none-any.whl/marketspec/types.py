from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal, Union

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
        object.__setattr__(self, "base", self.base.upper())
        object.__setattr__(self, "quote", self.quote.upper())
        if self.settle:
            object.__setattr__(self, "settle", self.settle.upper())
        if self.option:
            side = str(self.option).upper()
            if side not in {"C", "P"}:
                raise ValueError("option must be C or P")
            object.__setattr__(self, "option", side)
        if self.type in ("swap", "future") and self.settle is None:
            raise ValueError("swap/future require settle")
        if self.type == "future" and self.expiry is None:
            raise ValueError("future requires expiry")
        if self.type == "option":
            if not (self.expiry and self.strike and self.option):
                raise ValueError("option requires expiry,strike,option")
