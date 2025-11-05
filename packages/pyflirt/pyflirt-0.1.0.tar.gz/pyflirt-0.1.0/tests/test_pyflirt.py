from pyflirt import line, lines, categories, search, compliment, rate_line
import pytest
import re

def test_categories_type_and_nonempty():
    cs = categories()
    assert isinstance(cs, list)
    assert all(isinstance(c, str) and c for c in cs)
    assert len(cs) >= 1

def test_categories_expected_buckets_present():
    cs = set(categories())
    for c in ["classic", "cs", "math", "nerdy", "poetic"]:
        assert c in cs

def test_categories_stable_across_calls():
    assert categories() == categories()

def test_line_seed_is_deterministic():
    a = line(category="nerdy", seed=123)
    b = line(category="nerdy", seed=123)
    assert a == b and isinstance(a, str) and a

def test_line_category_param_accepts_valid_and_filters():
    out = line(category="cs", seed=7)
    assert isinstance(out, str) and len(out) > 0

def test_line_cheese_bounds():
    with pytest.raises(ValueError):
        line(cheese=0)
    with pytest.raises(ValueError):
        line(cheese=6)

def test_lines_respects_n_and_types():
    arr = lines(n=5, name="Sam", seed=123)
    assert len(arr) == 5
    assert all(isinstance(s, str) and s for s in arr)

def test_lines_seed_is_deterministic():
    a = lines(n=3, category="nerdy", seed=42)
    b = lines(n=3, category="nerdy", seed=42)
    assert a == b

def test_lines_cheese_bounds():
    with pytest.raises(ValueError):
        lines(n=2, cheese=0)
    with pytest.raises(ValueError):
        lines(n=2, cheese=6)

def test_compliment_returns_string_and_nonempty():
    out = compliment()
    assert isinstance(out, str) and len(out) > 0

def test_compliment_includes_name_when_given():
    result = compliment(role="developer", mood="nerdy", name="Alex", seed=1)
    assert "Alex" in result

def test_compliment_emojis_count_and_suffix():
    result = compliment(role="data", emojis=3, seed=2)
    assert result.endswith("💖" * 3)

def test_compliment_determinism_with_seed():
    a = compliment(role="designer", mood="cheeky", seed=42)
    b = compliment(role="designer", mood="cheeky", seed=42)
    assert a == b

def test_stats_shape_and_totals():
    s = pyflirt.stats()
    assert isinstance(s, dict)
    assert "total" in s and "by_category" in s and "cheese_hist" in s
    assert isinstance(s["by_category"], dict)
    assert isinstance(s["cheese_hist"], dict)
    assert s["total"] == sum(s["by_category"].values())
    assert s["total"] == sum(s["cheese_hist"].values())

def test_stats_categories_match_categories_function():
    s = pyflirt.stats()
    cats = pyflirt.categories()
    assert set(s["by_category"].keys()) == set(cats)

def test_stats_cheese_hist_keys():
    s = pyflirt.stats()
    assert set(s["cheese_hist"].keys()) == {1, 2, 3, 4, 5}

def test_search_basic_limit_and_seed_stability():
    sample = pyflirt.line(seed=12345)
    token = None
    for t in re.findall(r"[A-Za-z]+", sample):
        if len(t) >= 3:
            token = t
            break
    token = token or "love"

    r1 = pyflirt.search(token, limit=3, seed=7)
    r2 = pyflirt.search(token, limit=3, seed=7)
    r3 = pyflirt.search(token, limit=3, seed=8)

    assert len(r1) <= 3
    assert r1 == r2
    if len(r1) > 1 and len(r3) > 1:
        assert r1 != r3 or r1[0] != r3[0]

def test_search_category_filter_and_case_insensitivity():
    token = "code"
    a = pyflirt.search(token, category="cs", limit=5, seed=11)
    b = pyflirt.search(token.upper(), category="cs", limit=5, seed=11)
    assert isinstance(a, list) and all(isinstance(x, str) for x in a)
    assert a == b

def test_search_invalid_inputs_raise():
    with pytest.raises(ValueError):
        pyflirt.search("x", category="__nope__", limit=1)
    with pytest.raises(ValueError):
        pyflirt.search("", limit=1)

def test_stylize_uppercase_and_width_wrap():
    s = pyflirt.stylize("hello world", uppercase=True, width=5, color="none")
    lines = s.splitlines()
    assert all(line.isupper() for line in lines)
    assert len(lines) >= 2

def test_stylize_force_color_magenta_codes_present():
    out = pyflirt.stylize("x", color="magenta")
    assert "\x1b[95m" in out and out.endswith("\x1b[0m")

def test_stylize_color_none_returns_plain():
    out = pyflirt.stylize("abc", color="none")
    assert out == "abc"

def test_say_prints_and_returns_same(capsys):
    res = pyflirt.say(category="nerdy", seed=1, color="none")
    captured = capsys.readouterr().out.strip()
    assert isinstance(res, str) and res
    assert res.strip() == captured

def test_say_emojis_suffix_and_uppercase(capsys):
    res = pyflirt.say(category="nerdy", seed=2, emojis=2, uppercase=True, color="none")
    assert res.endswith("💘💘")
    assert res.split("💘")[0].strip().isupper()

def test_say_width_wrap_occurs(capsys):
    res = pyflirt.say(category="nerdy", seed=3, width=4, color="none")
    assert "\n" in res

def test_rate_line_length_metric():
    txt = "x" * 10
    v = pyflirt.rate_line(txt, metric="length")
    assert v == float(max(0, 100 - len(txt)))

def test_rate_line_cheese_level_counts_keywords():
    txt = "You are so sweet and cute, my heart melts"
    v = pyflirt.rate_line(txt, metric="cheese_level")
    assert v >= 3.0

def test_rate_line_random_seeded_deterministic():
    a = pyflirt.rate_line("hi", metric="random", seed=123)
    b = pyflirt.rate_line("hi", metric="random", seed=123)
    c = pyflirt.rate_line("hi", metric="random", seed=124)
    assert 0.0 <= a <= 10.0 and 0.0 <= c <= 10.0
    assert a == b and a != c

def test_rate_line_invalid_metric_raises():
    with pytest.raises(ValueError):
        pyflirt.rate_line("x", metric="nope")

def test__check_cat_none_ok_and_invalid_raises():
    fn = getattr(pyflirt, "_check_cat")
    assert fn(None) is None
    with pytest.raises(ValueError):
        fn("__not_a_cat__")

def test__with_name_inserts_or_defaults():
    fn = getattr(pyflirt, "_with_name")
    assert fn("hi {name}", "Sam") == "hi Sam"
    assert fn("hi {name}", None) == "hi you"
    assert fn("hi there", "Sam") == "hi there"

def test__pool_filters_by_cheese_and_fallback():
    fn = getattr(pyflirt, "_pool")
    cat = pyflirt.categories()[0]
    p = fn(cat, 1)
    assert isinstance(p, list) and p
    p2 = fn(cat, 1)
    assert p2
