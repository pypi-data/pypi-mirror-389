import pytest
from morseify import explain


def test_explain_simple_message():
    """Test explaining a simple SOS message."""
    result = explain("... --- ...")
    assert "SOS" in result
    assert "..." in result
    assert "---" in result
    

def test_explain_single_letter():
    """Test explaining a single letter."""
    result = explain(".-")  #letter -- A
    assert "A" in result
    assert ".-" in result


def test_explain_word():
    """Test explaining a word."""
    result = explain(".... . .-.. .-.. ---")  #answer is HELLO
    assert "HELLO" in result
    

def test_explain_with_word_separator():
    """Test explaining message with word separator."""
    result = explain(".... .. / - .... . .-. .")  #answer is HI THERE
    assert "HI THERE" in result
    assert "[SPACE]" in result or "/" in result


def test_explain_invalid_morse():
    """Test explaining invalid morse code."""
    result = explain("ABC123")  #Invalid - contains letters
    assert "Invalid" in result or "invalid" in result


def test_explain_empty_string():
    """Test explaining empty string."""
    result = explain("")
    assert "Invalid" in result or "invalid" in result


def test_explain_with_numbers():
    """Test explaining morse code with numbers."""
    result = explain(".---- ..--- ...--")  # 123
    assert "123" in result


def test_explain_shows_input():
    """Test that explanation shows the input."""
    morse_input = "... --- ..."
    result = explain(morse_input)
    assert morse_input in result or "Input" in result


def test_explain_shows_result():
    """Test that explanation shows the final result."""
    result = explain("... --- ...")
    assert "Result" in result or "SOS" in result


def test_explain_with_extra_spaces():
    """Test explaining morse code with extra spaces."""
    result = explain("  ... --- ...  ")
    # Should still decode to SOS
    assert "SOS" in result