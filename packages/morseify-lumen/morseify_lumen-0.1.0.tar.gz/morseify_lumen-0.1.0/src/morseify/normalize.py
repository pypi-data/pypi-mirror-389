import re
import string

def normalize_text(text):
    """
    Clean and standardize English text before encoding to Morse.

    Args:
        text (str): Input text string

    Returns:
        str: Normalized text ready for encoding
    """
    if not isinstance(text, str):
        return ""
    # convert to uppercase
    text = text.upper()

    # keep only supporting text
    morse_punct = ".,?/-()"
    allowed_chars = string.ascii_uppercase + string.digits + ' ' + morse_punct
    cleaned = ''.join(ch for ch in text if ch in allowed_chars)

    # clean multiple or leading/trailing spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.strip()

    return cleaned


def normalize_code(morse_code):
    """
    Clean and standardize Morse code text before decoding.

    Args:
        morse_code (str): Raw Morse code string

    Returns:
        str: Normalized Morse code ready for decoding
    """
    if not isinstance(morse_code, str):
        return ""

    # replace any tabs with a space
    morse_code = morse_code.replace('\t', ' ')

    # clean multiple spaces
    morse_code = re.sub(r'\s+', ' ', morse_code)

    # clean multiple slashes
    morse_code = re.sub(r'/+', '/', morse_code)

    # clean any leading/trailing space or slashes
    morse_code = morse_code.strip(' /')

    return morse_code
