import random
from typing import List, Optional
from .data import BANK, COMPLIMENT_TEMPLATES, categories as _categories
from typing import cast, Dict
import os, textwrap
from typing import Literal


__all__ = ["line", "lines", "categories", "compliment", "search", "stats"]

def categories() -> List[str]:
    """Return a sorted list of all available pickup line categories."""
    return _categories()

def _check_cat(cat: Optional[str]) -> Optional[str]:
    if cat is None:
        return None
    if cat not in BANK:
        valid = ", ".join(_categories())
        raise ValueError(f"Unknown category {cat!r}. Choose from {valid}.")
    return cat

def _pool(cat: Optional[str], cheese: int) -> List[dict]:
    """Return candidate lines filtered by category and cheese.
    If filtering wipes everything out, fall back to the unfiltered pool.
    """
    def ok(e: dict) -> bool:
        return e.get("cheese", 3) <= cheese

    if cat is None:
        picks = [e for items in BANK.values() for e in items if ok(e)]
    else:
        picks = [e for e in BANK[cat] if ok(e)]

    if not picks:
        picks = BANK[cat] if cat else [e for items in BANK.values() for e in items]
    return picks

def _with_name(text: str, name: Optional[str]) -> str:
    if "{name}" in text:
        return text.replace("{name}", name or "you")
    return text

def line(
    category: Optional[str] = "nerdy",
    name: Optional[str] = None,
    cheese: int = 2,
    seed: Optional[int] = None,
) -> str:
    """Return one random pickup line for the given category, name, and cheese level."""
    if not 1 <= int(cheese) <= 5:
        raise ValueError("cheese must be in 1..5")
    category = _check_cat(category)
    rng = random.Random(seed)
    choice = rng.choice(_pool(category, cheese))
    return _with_name(choice["text"], name)

def lines(
    n: int = 5,
    category: Optional[str] = None,
    name: Optional[str] = None,
    cheese: int = 2,
    seed: Optional[int] = None,
) -> List[str]:
    """Return a list of n pickup lines matching the given category and cheese level."""
    if n <= 0:
        return []
    if not 1 <= int(cheese) <= 5:
        raise ValueError("cheese must be in 1..5")
    category = _check_cat(category)
    rng = random.Random(seed)
    pool = _pool(category, cheese)

    out: List[str] = []
    if len(pool) >= n:
        for e in rng.sample(pool, n):
            out.append(_with_name(e["text"], name)) # type: ignore[index]
        return out

    for _ in range(n):
        e = rng.choice(pool)
        out.append(_with_name(e["text"], name))
    return out

def compliment(role="developer", mood="sweet", name=None, emojis=0, seed=None):
    """Return a list of n pickup lines matching the given category and cheese level."""
    rng = random.Random(seed) if seed is not None else random

    role = role.lower()
    mood = mood.lower()
    if role not in COMPLIMENT_TEMPLATES:
        raise ValueError(f"Unknown role '{role}'. Choose from {list(COMPLIMENT_TEMPLATES.keys())}.")
    if mood not in COMPLIMENT_TEMPLATES[role]:
        raise ValueError(f"Unknown mood '{mood}'. Choose from {list(COMPLIMENT_TEMPLATES[role].keys())}.")

    template = rng.choice(COMPLIMENT_TEMPLATES[role][mood])
    name_bit = f", {name}" if name else ""
    text = template.format(name_bit=name_bit)

    if emojis > 0:
        text += " " + "💖" * emojis
    return text

def stylize(
    text: str,
    *,
    width: Optional[int] = None,
    uppercase: bool = False,
    color: Literal["auto", "none", "magenta", "cyan", "green"] = "auto",
) -> str:
    """
    Post-process a string with wrapping, casing, and ANSI color.
      - width: wrap to N columns (None = no wrap)
      - uppercase: True to SHOUT
      - color: 'auto' enables color only on TTY; or force 'magenta'/'cyan'/'green'/'none'
    """
    s = text.upper() if uppercase else text
    if width:
        s = "\n".join(textwrap.wrap(s, width=width))

    palette = {"magenta": "\033[95m", "cyan": "\033[96m", "green": "\033[92m"}
    reset = "\033[0m"

    if color == "none":
        return s
    if color == "auto":
        color = "magenta" if os.getenv("TERM") else "none"
    if color in palette:
        return f"{palette[color]}{s}{reset}"
    return s

def say(
    *,
    category: Optional[str] = "nerdy",
    name: Optional[str] = None,
    cheese: int = 2,
    seed: Optional[int] = None,
    width: Optional[int] = None,
    uppercase: bool = False,
    color: Literal["auto", "none", "magenta", "cyan", "green"] = "auto",
    emojis: int = 0,
) -> str:
    """
    Generate a line, optionally decorate it (wrap/case/color), print it, and return it.
    """
    txt = line(category=category, name=name, cheese=cheese, seed=seed)
    if emojis > 0:
        txt += " " + "💘" * emojis
    pretty = stylize(txt, width=width, uppercase=uppercase, color=color)
    print(pretty)
    return pretty

def rate_line(text: str, metric: str = "length", seed: Optional[int] = None) -> float:
    """
    Rate a pickup line by various heuristics.
    Args:
        text: pickup line string.
        metric: rating metric ('length', 'cheese_level', 'random').
        seed: random seed for repeatability.
    Returns:
        A float rating score.
    Raises:
        ValueError if metric unknown.
    """
    if metric not in ("length", "cheese_level", "random"):
        raise ValueError(f"Unknown metric {metric!r}")

    if metric == "length":
        length = len(text)
        return float(max(0, 100 - length))

    if metric == "cheese_level":
        cheesy_words = ["love", "heart", "cute", "sweet", "charm", "kiss"]
        count = sum(word in text.lower() for word in cheesy_words)
        return float(count)

    rng = random.Random(seed)
    return rng.uniform(0, 10)

def search(
    query: str,
    category: Optional[str] = None,
    name: Optional[str] = None,
    cheese: int = 5,
    limit: int = 10,
    seed: Optional[int] = None,
) -> List[str]:
    """Return up to `limit` lines containing `query` (case-insensitive)."""
    if not query:
        raise ValueError("query must be non-empty")
    if not 1 <= int(cheese) <= 5:
        raise ValueError("cheese must be in 1..5")
    if limit <= 0:
        return []

    category = _check_cat(category)
    q = query.lower()

    def ok(e: dict) -> bool:
        return e.get("cheese", 3) <= cheese and q in str(e.get("text", "")).lower()

    if category is None:
        pool = [e for items in BANK.values() for e in items if ok(e)]
    else:
        pool = [e for e in BANK[category] if ok(e)]

    rng = random.Random(seed) if seed is not None else random
    rng.shuffle(pool)

    out: List[str] = []
    for e in pool[:limit]:
        out.append(_with_name(e.get("text", ""), name))
    return out


def stats() -> dict:
    """Return counts: total, by_category, and cheese_hist (1..5)."""
    cats = _categories()
    by_category = {c: len(BANK.get(c, [])) for c in cats}
    cheese_hist = {i: 0 for i in range(1, 6)}
    for c in cats:
        for e in BANK.get(c, []):
            ch = int(e.get("cheese", 3))
            if 1 <= ch <= 5:
                cheese_hist[ch] += 1
    total = sum(by_category.values())
    return {"total": total, "by_category": by_category, "cheese_hist": cheese_hist}
  
