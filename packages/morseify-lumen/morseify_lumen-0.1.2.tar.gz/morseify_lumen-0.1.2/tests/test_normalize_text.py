from morseify.normalize import normalize_text

def test_normalize_text_basic():
    assert normalize_text("Hello World!") == "HELLO WORLD"
    assert normalize_text("sos?") == "SOS?"

def test_normalize_text_remove_invalid_chars():
    assert normalize_text("hi@123") == "HI123"  # removes @
    assert normalize_text("...,,!!") == ".,"

def test_normalize_text_spacing():
    assert normalize_text("  hello   world  ") == "HELLO WORLD"
    assert normalize_text("A   B   C") == "A B C"

def test_normalize_text_non_string_input():
    assert normalize_text(None) == ""
    assert normalize_text(12345) == ""

def test_normalize_text_allowed_punct():
    text = "HELLO, WORLD?"
    assert normalize_text(text) == "HELLO, WORLD?"