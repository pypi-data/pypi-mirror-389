from morseify.core import decode


def test_decode_single_letter():
    """Test decoding a single letter."""
    assert decode(".-") == "A"
    assert decode("-...") == "B"
    assert decode("-.-.") == "C"
    assert decode("-..") == "D"
    assert decode(".") == "E"
    assert decode("..-.") == "F"
    assert decode("--.") == "G"
    assert decode("....") == "H"
    assert decode("..") == "I"
    assert decode(".---") == "J"
    assert decode("-.-") == "K"
    assert decode(".-..") == "L"
    assert decode("--") == "M"
    assert decode("-.") == "N"
    assert decode("---") == "O"
    assert decode(".--.") == "P"
    assert decode("--.-") == "Q"
    assert decode(".-.") == "R"
    assert decode("...") == "S"
    assert decode("-") == "T"
    assert decode("..-") == "U"
    assert decode("...-") == "V"
    assert decode(".--") == "W"
    assert decode("-..-") == "X"
    assert decode("-.--") == "Y"
    assert decode("--..") == "Z"


def test_decode_word():
    """Test decoding a word."""
    assert decode(".... . .-.. .-.. ---") == "HELLO"
    assert decode("... --- ...") == "SOS"


def test_decode_multiple_words():
    """Test decoding multiple words with separator."""
    assert decode(".... . .-.. .-.. --- / .-- --- .-. .-.. -..") == "HELLO WORLD"
    assert decode("... --- ... / .... . .-.. .--.") == "SOS HELP"


def test_decode_numbers():
    """Test decoding numbers."""
    assert decode(".---- ..--- ...--") == "123"
    assert decode("-----") == "0"

def test_decode_extra_spaces():
    """Test decoding morse code with extra spaces."""
    assert decode("   ...   ---   ...   ") == "SOS"

def test_decode_invalid_morse_code():
    """Test decoding invalid morse code returns error message."""
    assert decode("---.") == "Morse code is not valid"  # Invalid sequence not in mapping
    assert decode("ABC") == "Morse code is not valid"  # Contains invalid characters
    assert decode("....X") == "Morse code is not valid"  # Contains invalid character
    assert decode("") == "Morse code is not valid"  # Empty string
    assert decode("   ") == "Morse code is not valid"  # Only spaces


def test_decode_mixed_valid_invalid():
    """Test decoding morse code with invalid sequences."""
    assert decode(".... . .-.. .-.. --- ---.") == "Morse code is not valid"  # Has invalid sequence


def test_decode_with_punctuation():
    """Test decoding morse code with punctuation."""
    assert decode(".... . .-.. .-.. --- .-.-.-") == "HELLO."
    assert decode("-- ..- .-.. - .. .--. .-.. .") == "MULTIPLE"


def test_decode_normalized_input():
    """Test decoding already normalized morse code."""
    # decode should handle normalization internally
    assert decode("  .... . .-.. .-.. ---  ") == "HELLO"  # Extra spaces



def test_decode_punctuation_only():
    """Test decoding morse code with only punctuation."""
    assert decode(".-.-.-") == "."  # period
    assert decode("--..--") == ","  # comma
    assert decode("..--..") == "?"  # question mark
    assert decode("-..-.") == "/"   # slash
    assert decode("-....-") == "-"  # hyphen


def test_decode_with_parentheses():
    """Test decoding morse code with parentheses."""
    assert decode("-.--. -.--.-") == "()"
    assert decode(".... . .-.. .-.. --- -.--.") == "HELLO("
    assert decode("-.--.- .-- --- .-. .-.. -..") == ")WORLD"

