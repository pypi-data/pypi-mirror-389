from __future__ import annotations

import re
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, localcontext
from typing import Union

__all__ = [
    "_yyyymmdd",
    "_deribit_date",
    "set_stables",
    "override_stables",
    "_format_strike",
]

Dateish = Union[str, date, datetime]
_STABLES: set[str] = {"USDT", "USDC", "DAI", "FDUSD", "TUSD"}


def set_stables(stables: set[str]) -> None:
    """Override the stable-coin set used for linear detection. Global."""
    _STABLES.clear()
    _STABLES.update(x.upper() for x in stables)


@contextmanager
def override_stables(stables: set[str]) -> Iterator[None]:
    """
    Temporarily override the stable-coin set in a controlled scope.

    Example:
        with override_stables({"USDT", "USDC"}):
            ...
    """
    prev = set(_STABLES)
    try:
        set_stables(stables)
        yield
    finally:
        set_stables(prev)


def _parse_to_dict(s: str) -> dict[str, object | None]:
    """
    Grammar:
      spot   BASE/QUOTE
      swap   BASE/QUOTE:SETTLE
      future BASE/QUOTE:SETTLE-YYYYMMDD
      option BASE-YYYYMMDD-STRIKE-C|P
    Returns a dict used by marketspec.parse() to build Spec.
    """

    s = s.strip().upper()

    # Option: BASE-YYYYMMDD-STRIKE-C|P (strike supports 1e-3 and scientific notation)
    m = re.fullmatch(
        r"([A-Z0-9]+)-(\d{8})-([0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)\-([CP])",
        s,
        re.I,
    )
    if m:
        base, ymd, strike, cp = m.groups()
        # calendar-check expiry
        _ = _yyyymmdd(ymd)
        return {
            "base": base,
            "quote": "",
            "type": "option",
            "linear": None,
            "settle": "USD",
            "expiry": ymd,
            "strike": float(strike),
            "option": cp.upper(),
            "week": None,
        }

    # Spot / Swap / Future
    m = re.fullmatch(r"([A-Z0-9]+)/([A-Z0-9]+)(?::([A-Z0-9]+))?(?:-(\d{8}))?$", s, re.I)
    if not m:
        raise ValueError(f"Unrecognized unified symbol: {s}")
    base, quote, settle, ymd = m.groups()
    settle = settle or None
    mtype = "future" if ymd else ("swap" if settle else "spot")

    if ymd:
        # calendar-check expiry
        _ = _yyyymmdd(ymd)

    linear: bool | None = None
    if mtype in {"swap", "future"}:
        if settle == "USD":
            linear = False
        elif settle and settle == quote and settle in _STABLES:
            linear = True
        else:
            # Mismatched or non-stable settle for a supposed linear contract
            raise ValueError(
                f"Inconsistent settle/quote for swap/future: {base}/{quote}:{settle}"
            )

    return {
        "base": base,
        "quote": quote,
        "type": mtype,
        "linear": linear,
        "settle": settle,
        "expiry": ymd,
        "strike": None,
        "option": None,
        "week": None,
    }


def _yyyymmdd(expiry: Dateish | None) -> str:
    if expiry is None:
        raise ValueError("Missing expiry")
    if isinstance(expiry, (date, datetime)):
        ymd = expiry.strftime("%Y%m%d")
    else:
        s = str(expiry).strip().replace("-", "").replace("/", "")
        if len(s) == 6 and s.isdigit():
            s = "20" + s
        if not (len(s) == 8 and s.isdigit()):
            raise ValueError(f"Bad expiry: {expiry}")
        ymd = s
    # validate calendar date
    try:
        datetime.strptime(ymd, "%Y%m%d")
    except ValueError as e:
        raise ValueError(f"Invalid calendar date: {expiry}") from e
    return ymd


def _deribit_date(expiry: Dateish) -> str:
    ymd = _yyyymmdd(expiry)
    y, m, d = ymd[:4], ymd[4:6], ymd[6:]
    month = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    mm = month[int(m) - 1]
    return f"{int(d):02d}{mm}{y[2:]}"


def _format_strike(x: object) -> str:
    """
    Format strikes robustly. Accepts float|int|str|Decimal.
    Removes trailing zeros. Avoids scientific notation.
    """
    try:
        with localcontext() as ctx:
            ctx.prec = 28
            d = Decimal(str(x)).normalize()
            if d <= 0:
                raise ValueError("strike must be > 0")
            s = format(d, "f")
            # Only trim zeros after the decimal point.
            if "." in s:
                s = s.rstrip("0").rstrip(".")
            return s or "0"
    except (InvalidOperation, ValueError, TypeError) as err:
        raise ValueError(f"Bad strike: {x!r}") from err
