# marketspec

Unified instrument spec parser and venue symbol resolver for crypto markets.

- Parse `BTC/USDT:USDT`, `BTC/USD:USD-20251227`, `ETH-20251226-2500-C`.
- Resolve symbols for Binance and Bybit.
- No runtime dependencies. Typed. MIT.

## Install
```bash
pip install marketspec
```

## Quick start
```python
from marketspec import venue_symbol, parse, resolve_symbol

print(venue_symbol("binance", "BTC/USDT:USDT"))          # BTCUSDT
print(venue_symbol("bybit",   "BTC/USD:USD-20251227"))   # BTCUSD_20251227

s = parse("ETH-20251226-2500-C")   # -> Spec
print(resolve_symbol("binance", s))  # ETH-20251226-2500-C
print(s.unified())                   # round-trip -> "ETH-20251226-2500-C"
```

## Grammar
- **Spot**: `BASE/QUOTE` → `BTC/USDT`
- **Swap (linear)**: `BASE/QUOTE:SETTLE` where `SETTLE == QUOTE` and is a stable → `BTC/USDT:USDT`
- **Swap (inverse)**: `BASE/QUOTE:USD` → `BTC/USD:USD`
- **Future**: append `-YYYYMMDD` to the swap form → `BTC/USDT:USDT-20251227`
- **Option**: `BASE-YYYYMMDD-STRIKE-C|P` → `ETH-20251226-2500-C`

Dates accept `YYYYMMDD`, `YYYY-MM-DD`, `YYMMDD` (assumes 20YY), or `date/datetime`.

## API
```python
from marketspec import parse, resolve_symbol, venue_symbol, set_stables
from marketspec.unified import override_stables  # optional scoped override
from marketspec.types import Spec

# One-call convenience
venue_symbol("binance", "BTC/USDT:USDT")  # -> "BTCUSDT"

# Stable parser + resolver
s: Spec = parse("BTC/USD:USD-20251227")
resolve_symbol("bybit", s)                # -> "BTCUSD_20251227"

# Round-trip for logs/tests
s.unified()                               # -> "BTC/USD:USD-20251227"

# Configure stables (global)
set_stables({"USDT", "USDC", "FDUSD"})

# Scoped override for tests or multi-tenant code
from marketspec.unified import override_stables
with override_stables({"USDT", "USDC"}):
    resolve_symbol("binance", parse("BTC/USDT:USDT"))
```

### Exceptions
- Parsing errors raise `ValueError`.
- Resolution errors raise `marketspec.registry.ResolveError` (subclasses `ValueError`).

## Deprecations
- `parse_unified_symbol()` is deprecated. Use `parse() -> Spec`. Still exported and functional, emits `DeprecationWarning`.
- `resolve_venue_symbol()` is deprecated. Use `resolve_symbol()`.

## Supported venues
- `binance`
- `bybit`

PRs welcome for more venues.

## Development
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scriptsctivate
pip install -e . pytest ruff mypy
pytest -q
ruff check .
mypy src
```

## License
MIT
