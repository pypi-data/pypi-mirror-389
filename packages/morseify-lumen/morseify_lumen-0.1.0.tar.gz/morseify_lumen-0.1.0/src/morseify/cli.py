"""
Command-line interface for morseify.
"""

import sys
from morseify.core import encode, decode, is_valid


def cli():
    """
    Command-line interface for morseify.
    Auto-detects whether input is text (encode) or morse code (decode).
    
    Usage:
        morseify "HELLO"           # Encodes text to morse code
        morseify ".... . .-.. .-.. ---"  # Decodes morse code to text
    """
    if len(sys.argv) < 2:
        print("Usage: morseify <text or morse code>")
        print("Examples:")
        print('  morseify "HELLO"')
        print('  morseify ".... . .-.. .-.. ---"')
        sys.exit(1)
    
    # Join all arguments in case user passes multiple words
    input_text = ' '.join(sys.argv[1:])
    
    # Auto-detect: if input contains only morse characters (., -, /, space), decode it
    # Otherwise, encode it
    valid_morse_chars = {'.', '-', '/', ' '}
    is_morse = all(char in valid_morse_chars for char in input_text) and input_text.strip()
    
    if is_morse and is_valid(input_text):
        # It's valid morse code, decode it
        result = decode(input_text)
        print(result)
    else:
        # It's text, encode it
        result = encode(input_text)
        print(result)

