from morseify.mapping import LETTER_TO_MORSE
from morseify.mapping import MORSE_TO_LETTER
from morseify.normalize import normalize_text
from morseify.normalize import normalize_code

def encode(text):
    """
    Convert English text to morse code.
    
    Args:
        text: English text string to encode
        
    Returns:
        Morse code string
    """

    # Normalize the text first(delete after normalize function is implemented)
    # if text is None:
    #     return None
    # normalized = text.upper().strip() 

    normalized = normalize_text(text)
    
    # Convert each character to morse code
    result = []
    for char in normalized:
        if char == ' ':
            # Space between words becomes ' / '
            result.append('/')
        else:
            # Get morse code for character
            morse_char = LETTER_TO_MORSE.get(char, '')
            if morse_char:
                result.append(morse_char)
    
    # Join with spaces between letters
    return ' '.join(result)


def decode(morse_code):
    """
    Convert morse code to English text.
    
    Args:
        morse_code: Morse code string to decode
        
    Returns:
        English text string, or error message if morse code is invalid
    """
    # Check if the morse code is valid
    if not is_valid(morse_code):
        return "Morse code is not valid"
    
    # If valid: normalize and decode
    normalized = normalize_code(morse_code)
    
    # Split morse code by spaces to get individual morse sequences
    morse_words = normalized.split(' ')
    
    result = []
    for i in morse_words:
        if i == '':
            # Skip empty sequences (multiple spaces)
            continue
        elif i == '/':
            # Word separator
            result.append(' ')
        else:
            # Look up the morse sequence in the dictionary
            letter = MORSE_TO_LETTER.get(i, '')
            result.append(letter)
    
    return ''.join(result)  






def is_valid(morse_code):
    """
    Check if morse code is valid.
    
    Args:
        morse_code: Morse code string to check if valid
        
    Returns:
        Boolean: True if valid, False otherwise
    """

    # check if morse_code is str or empty
    try:
        morse_code = morse_code.strip()
    except AttributeError:
        return False
    
    if not morse_code:
        return False
    
    #check if valid chars or sequence
    validchars = {'.', '-', '/', ' '}
    if any(ch not in validchars for ch in morse_code):
        return False
    
    for seq in morse_code.split(' '):
        if not seq or seq == '/':
             continue
        if seq not in MORSE_TO_LETTER:
            return False        
    return True


