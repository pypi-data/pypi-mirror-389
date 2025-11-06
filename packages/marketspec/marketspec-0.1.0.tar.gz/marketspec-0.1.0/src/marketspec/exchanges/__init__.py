from __future__ import annotations

from importlib import import_module
from pkgutil import iter_modules

__all__ = []  # resolvers self-register on import

# Auto-register all exchange modules in this package.
_pkg = __name__
for m in iter_modules([__path__[0]]):
    import_module(f"{_pkg}.{m.name}")
