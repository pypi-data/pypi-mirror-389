from chatterpy_mistral.pickuplines import pickUpLine, PICKUPLINES

def test_pickUpLine_returns_string():
    actual_no_name = pickUpLine("classic")
    actual_with_name = pickUpLine("poetic", "Aden")
    assert isinstance(actual_no_name, str), f"Expected a string, got {actual_no_name}"
    assert isinstance(actual_with_name, str), f"Expected a string, got {actual_with_name}"

def test_member_of_requested_pool_no_name():
    actual = pickUpLine("funny")
    assert actual in PICKUPLINES["funny"], f"Expected a funny pick up line, got {actual}"

def test_member_of_requested_pool_with_name():
    actual = pickUpLine("nerdy", "Sam")
    base = actual.replace("Sam, ", "")
    assert base in PICKUPLINES["nerdy"], f"Expected a nerdy pick up line, got {actual}"

def test_name_prefix_when_provided():
    actual = pickUpLine("classic", "Taylor")
    assert actual.startswith("Taylor, "), f"Expected 'Taylor, (pick up line)', got {actual}"

def test_randomness_over_multiple_calls():
    chosen = set(pickUpLine("poetic") for _ in range(50))
    assert len(chosen) > 1
