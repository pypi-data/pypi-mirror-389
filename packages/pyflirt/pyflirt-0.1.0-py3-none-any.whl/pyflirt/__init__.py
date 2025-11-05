# src/pyflirt/__init__.py
"""
pyflirt 💘
Public API:
- categories()
- line(category, name, cheese, seed)
- lines(n, category, name, cheese, seed)
- compliment(role, mood, name, emojis, seed)
- search(query, category=None, name=None, cheese=5, limit=10, seed=None)
- stats()
- stylize(text, width=None, uppercase=False, color="auto")
- say(category="nerdy", name=None, cheese=2, seed=None, width=None, uppercase=False, color="auto", emojis=0)
- rate_line(text, metric="length", seed=None)
"""

from .api import (
    line,
    lines,
    categories,
    compliment,
    search,
    stats,
    rate_line,
    stylize,
    say,
    _check_cat,
    _with_name,
    _pool,
)

__all__ = [
    "categories",
    "line",
    "lines",
    "compliment",
    "search",
    "stats",
    "rate_line",
    "stylize",
    "say",
]
__version__ = "0.1.0"


try:
    import sys
    import builtins
    builtins.pyflirt = sys.modules[__name__]
except Exception:
    pass
