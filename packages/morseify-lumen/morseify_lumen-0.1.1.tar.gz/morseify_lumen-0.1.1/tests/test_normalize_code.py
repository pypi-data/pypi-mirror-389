from morseify.normalize import normalize_code
def test_normalize_code_basic():
    assert normalize_code(".- -... / -.-.") == ".- -... / -.-."

def test_normalize_code_tabs_and_spaces():
    assert normalize_code(".-\t-...") == ".- -..."  # replaces tab with space
    assert normalize_code(".-   -...") == ".- -..."  # multiple spaces to single

def test_normalize_code_slashes():
    assert normalize_code(".-//-...///-.-.") == ".-/-.../-.-."  # multiple slashes to single

def test_normalize_code_strip_edges():
    assert normalize_code(" / .- -... / ") == ".- -..."
    assert normalize_code("  .- -...  ") == ".- -..."

def test_normalize_code_non_string_input():
    assert normalize_code(123) == ""
    assert normalize_code(None) == ""
