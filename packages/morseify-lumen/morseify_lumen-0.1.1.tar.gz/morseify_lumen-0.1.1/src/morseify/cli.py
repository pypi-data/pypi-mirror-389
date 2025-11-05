"""
Command-line interface for morseify.
"""

import sys
from morseify.core import encode, decode, is_valid
from morseify.explain import explain
from morseify.quiz import quiz


def cli():
    """
    Command-line interface for morseify.
    Auto-detects whether input is text (encode) or morse code (decode).
    Supports --explain flag for step-by-step breakdown.
    Supports --quiz flag for interactive quiz.
    Supports --validate flag to check if morse code is valid.
    
    Usage:
        morseify "HELLO"           # Encodes text to morse code
        morseify ".... . .-.. .-.. ---"  # Decodes morse code to text
        morseify --explain ".... . .-.. .-.. ---"  # Explains morse code
        morseify -e ".... . .-.. .-.. ---"  # Short form for explain
        morseify --validate ".... . .-.. .-.. ---"  # Check if morse code is valid
        morseify -v ".... . .-.. .-.. ---"  # Short form for validate
        morseify --quiz             # Start interactive quiz (mode selection) -- prompts user to select mode
        morseify --quiz-reading     # Start quiz in reading mode
        morseify --quiz-writing     # Start quiz in writing mode
        morseify -q                 # Short form for quiz
    """


    
    if len(sys.argv) < 2:
        print("Usage: morseify [OPTIONS] <text or morse code>")
        print("\nOptions:")
        print("  --explain, -e        Explain morse code step-by-step")
        print("  --validate, -v       Check if morse code is valid")
        print("  --quiz, -q           Start interactive quiz (mode selection)")
        print("  --quiz-reading       Start quiz in reading mode (decode)")
        print("  --quiz-writing       Start quiz in writing mode (encode)")
        print("\nExamples:")
        print('  morseify "HELLO"')
        print('  morseify ".... . .-.. .-.. ---"')
        print('  morseify --explain ".... . .-.. .-.. ---"')
        print('  morseify -e ".... . .-.. .-.. ---"')
        print('  morseify --validate ".... . .-.. .-.. ---"')
        print('  morseify -v ".... . .-.. .-.. ---"')
        print('  morseify --quiz')
        print('  morseify --quiz-reading')
        print('  morseify --quiz-writing')
        sys.exit(1)
    
    # Check for flags
    args = sys.argv[1:]
    first_arg = args[0]
    
    # Handle quiz flags
    if first_arg in ['--quiz', '-q']:
        quiz()  # Interactive mode selection
        return
    
    if first_arg == '--quiz-reading':
        quiz('reading')
        return
    
    if first_arg == '--quiz-writing':
        quiz('writing')
        return
    
    # Handle explain flag
    if first_arg in ['--explain', '-e']:
        args = args[1:]  # Remove the flag
        
        if not args:
            print("Error: No input provided after flag.")
            print("Usage: morseify --explain <morse code>")
            sys.exit(1)
        
        input_text = ' '.join(args)
        result = explain(input_text)
        print(result)
        return
    
    # Handle validate flag
    if first_arg in ['--validate', '-v']:
        args = args[1:]  # Remove the flag
        
        if not args:
            print("Error: No input provided after flag.")
            print("Usage: morseify --validate <morse code>")
            sys.exit(1)
        
        input_text = ' '.join(args)
        is_morse_valid = is_valid(input_text)
        
        if is_morse_valid:
            print(f"✓ Valid morse code: '{input_text}'")
            print("The morse code you entered means: ", decode(input_text))
        else:
            print(f"✗ Invalid morse code: '{input_text}'")
            
        return
    
    # Join all arguments in case user passes multiple words
    input_text = ' '.join(args)
    
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

