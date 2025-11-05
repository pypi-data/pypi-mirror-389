import pytest
from morseify.core import is_valid

def test_valid_single():
    assert is_valid("....") is True  
    assert is_valid(".") is True
    assert is_valid("-.--") is True
    
    assert is_valid("-...") is True
    assert is_valid(".-.") is True
    assert is_valid("---") is True

def test_valid_multiple():
    hey = ".... . -.--"
    bro = "-... .-. ---"
    i = '..'
    want = ".-- .- -. -"
    a = ".-"
    cat = "-.-. .- -"
    assert is_valid(hey) is True
    assert is_valid(bro) is True
    assert is_valid(i) is True
    assert is_valid(want) is True
    assert is_valid(a) is True
    assert is_valid(cat) is True

def test_valid_separator():
    morse1 = ".... . -.-- / -... .-. ---"           
    morse2 = ".. / .-- .- -. - / .- / -.-. .- -"   
    assert is_valid(morse1) is True
    assert is_valid(morse2) is True

def test_invalid_morse_char():
    assert is_valid("x") is False
    assert is_valid(".... x ...") is False
    assert is_valid(".... & ...") is False

def test_emptywhite_space():
    assert is_valid("") is False
    assert is_valid("   ") is False
    assert is_valid(None) is False

def test_valid_morse_extraspace():
    morse = ".... . .-.. .-.. ---   /  .-- --- .-. .-.. -.."
    assert is_valid(morse) is True

def test_invalid_morse_seq():
    assert is_valid("...---...-") is False

def test_slashspace_only():
    assert is_valid("/") is True
    assert is_valid(" / ") is True

def test_mix_validinvalid_seq():
    assert is_valid(".- / x") is False
    assert is_valid(".- / .--.-") is False

def test_multiple_separators():
    assert is_valid(".... / ....") is True
    assert is_valid("....   ....") is True
    assert is_valid(".... // ....") is False