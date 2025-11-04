from morseify.core import encode, decode


def test_encode_single_letter():
    """Test encoding a single letter."""
    assert encode("A") == ".-"
    assert encode("B") == "-..."
    assert encode("C") == "-.-."
    assert encode("D") == "-.."
    assert encode("E") == "."
    assert encode("F") == "..-."
    assert encode("G") == "--."
    assert encode("H") == "...."
    assert encode("I") == ".."
    assert encode("J") == ".---"
    assert encode("K") == "-.-"
    assert encode("L") == ".-.."
    assert encode("M") == "--"
    assert encode("N") == "-."
    assert encode("O") == "---"
    assert encode("P") == ".--."
    assert encode("Q") == "--.-"
    assert encode("R") == ".-."
    assert encode("S") == "..."
    assert encode("T") == "-"
    assert encode("U") == "..-"
    assert encode("V") == "...-"
    assert encode("W") == ".--"
    assert encode("X") == "-..-"
    assert encode("Y") == "-.--"
    assert encode("Z") == "--.."


def test_encode_lowercase():
    """Test encoding lowercase letters (should convert to uppercase first)."""
    assert encode("a") == ".-"
    assert encode("hello") == ".... . .-.. .-.. ---"
    assert encode("sos") == "... --- ..."


def test_encode_word():
    """Test encoding an uppercase word."""
    assert encode("HELLO") == ".... . .-.. .-.. ---"
    assert encode("SOS") == "... --- ..."

def test_encode_mixed_case():
    """Test encoding text with mixed case."""
    assert encode("Hello") == ".... . .-.. .-.. ---"
    assert encode("World") == ".-- --- .-. .-.. -.."
    assert encode("SoS") == "... --- ..."


def test_encode_multiple_words():
    """Test encoding multiple words with separator."""
    assert encode("HELLO WORLD") == ".... . .-.. .-.. --- / .-- --- .-. .-.. -.."
    assert encode("SOS HELP") == "... --- ... / .... . .-.. .--."


def test_encode_numbers():
    """Test encoding numbers."""
    assert encode("123") == ".---- ..--- ...--"
    assert encode("0") == "-----"
    assert encode("0123456789") == "----- .---- ..--- ...-- ....- ..... -.... --... ---.. ----."


def test_encode_with_punctuation():
    """Test encoding text with punctuation."""
    assert encode("HELLO.") == ".... . .-.. .-.. --- .-.-.-"
    assert encode("SOS?") == "... --- ... ..--.."
    assert encode("A,B") == ".- --..-- -..."


def test_encode_with_parentheses():
    """Test encoding text with parentheses."""
    assert encode("()") == "-.--. -.--.-"
    assert encode("HELLO(WORLD)") == ".... . .-.. .-.. --- -.--. .-- --- .-. .-.. -.. -.--.-"
    assert encode("(A)") == "-.--. .- -.--.-"


def test_encode_with_extra_spaces():
    """Test encoding text with extra spaces."""
    assert encode("  HELLO  ") == ".... . .-.. .-.. ---"
    assert encode("A  B") == ".- / -..."
    assert encode("   SOS   ") == "... --- ..."


def test_encode_only_spaces():
    """Test encoding only spaces."""
    assert encode(" ") == ""
    assert encode("  ") == ""
    assert encode("   ") == ""


def test_encode_empty_string():
    """Test encoding empty string."""
    assert encode("") == ""


def test_encode_decode_roundtrip():
    """Test that encoding then decoding returns the original text."""
    texts = [
        "A",
        "HELLO",
        "HELLO WORLD",
        "123",
        "SOS",
        "HELLO.",
        "SOS?",
        "()",
        "HELLO(WORLD)",
        "0123456789"
    ]
    
    for text in texts:
        encoded = encode(text)
        decoded = decode(encoded)
        assert decoded == text, f"Round trip failed for '{text}': {encoded} -> {decoded}"


def test_decode_encode_roundtrip():
    """Test that decoding then encoding returns the original morse code."""
    morse_codes = [
        ".-",
        "-",
        "...",
        ".... . .-.. .-.. ---",
        "... --- ...",
        ".... . .-.. .-.. --- / .-- --- .-. .-.. -..",
        ".---- ..--- ...--",
        "-----",
        ".... . .-.. .-.. --- .-.-.-",
        "... --- ... ..--..",
        "-.--. -.--.-",
        ".- .-.-.- -..."
    ]
    
    for morse_code in morse_codes:
        decoded = decode(morse_code)
        encoded = encode(decoded)
        assert encoded == morse_code, f"Round trip failed for '{morse_code}': {decoded} -> {encoded}"
        