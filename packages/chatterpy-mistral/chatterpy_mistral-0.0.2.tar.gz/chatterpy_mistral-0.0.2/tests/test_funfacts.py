from chatterpy_mistral.funfacts import fun_fact, FACTS

def test_returns_string_nonempty():
    s = fun_fact()
    assert isinstance(s, str) and s.strip()

def test_fallback_on_unknown_inputs():
    s = fun_fact(category="???", rarity="???")
    assert isinstance(s, str) and s.strip()

def test_member_of_requested_pool():
    s = fun_fact("science", "rare")
    assert s in FACTS["science"]["rare"]
