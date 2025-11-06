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
from marketspec import venue_symbol

print(venue_symbol("binance", "BTC/USDT:USDT"))          # BTCUSDT
print(venue_symbol("bybit",   "BTC/USD:USD-20251227"))   # BTCUSD_20251227
print(venue_symbol("binance", "ETH-20251226-2500-C"))    # ETH-20251226-2500-C
```

## Grammar
- **Spot**: `BASE/QUOTE` → `BTC/USDT`
- **Swap (linear)**: `BASE/QUOTE:SETTLE` where `SETTLE == QUOTE` and is a stable → `BTC/USDT:USDT`
- **Swap (inverse)**: `BASE/QUOTE:USD` → `BTC/USD:USD`
- **Future**: append `-YYYYMMDD` to the swap form → `BTC/USDT:USDT-20251227`
- **Option**: `BASE-YYYYMMDD-STRIKE-C|P` → `ETH-20251226-2500-C`

## Supported venues
- `binance`
- `bybit`

PRs welcome for more venues.

## Development
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
pytest -q
```

## License
MIT
