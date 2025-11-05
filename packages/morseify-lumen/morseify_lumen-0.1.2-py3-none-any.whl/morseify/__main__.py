from .core import encode, decode, is_valid
from .explain import explain
from .quiz import quiz
from .normalize import normalize_text, normalize_code


def main():
    print("MORSE CODE PACKAGE - DEMO")
    
    # Encode/Decode Test Section

    

    print("ENCODE/DECODE TEST")

     # Showcase encode and decode
    print("\nEncode Examples:")
    encode_examples = ["HELLO", "SOS", "PYTHON"]
    for text in encode_examples:
        encoded = encode(text)
        print(f"  '{text}' → '{encoded}'")
    
    print("\nDecode Examples:")
    decode_examples = [".... . .-.. .-.. ---", "... --- ...", ".--. -.-- - .... --- -."]
    for morse in decode_examples:
        decoded = decode(morse)
        print(f"  '{morse}' → '{decoded}'")
    

    test_cases = [
        "HELLO WORLD",
        "PYTHON",
        "123",
    ]
    
    for text in test_cases:
        encoded = encode(text)
        decoded = decode(encoded)
        
        print(f"\nOriginal: '{text}'")
        print(f"Encoded : '{encoded}'")
        print(f"Decoded : '{decoded}'")
        
        # Check if round-trip works
        if decoded == text:
            print("✓ Round-trip successful!")
        else:
            print(f"✗ Round-trip failed! Expected: '{text}'")

    print("\n" + "=" * 60)
    print("IS_VALID FUNCTION DEMO")
    
    valid_examples = [
        ".... . .-.. .-.. ---",
        "... --- ...",
        ".- / -...",
        ".... . .-.. .-.. --- / .-- --- .-. .-.. -.."
    ]
    
    invalid_examples = [
        ".... x .-.. .-.. ---",  # Invalid character 'x'
        ".... . .-.. .-.. ------",  # Invalid sequence
        "abc",  # Not morse code
        "123",  # Not morse code
        ""  # Empty string
    ]
    
    print("\nValid morse code examples:")
    for morse in valid_examples:
        result = is_valid(morse)
        status = "✓ Valid" if result else "✗ Invalid"
        print(f"  '{morse}' → {status}")
    
    print("\nInvalid morse code examples:")
    for morse in invalid_examples:
        result = is_valid(morse)
        status = "✓ Valid" if result else "✗ Invalid"
        print(f"  '{morse}' → {status}")
    
    print("\n" + "=" * 60)
    print("NORMALIZE FUNCTIONS DEMO")
    
    print("\nnormalize_text() examples:")
    text_examples = [
        "  hello world  ",
        "Hello World",
        "HELLO   WORLD",
        "hello!!!world",
        "Hello, World!",
        "123  ABC"
    ]
    
    for text in text_examples:
        normalized = normalize_text(text)
        print(f"  Input:    '{text}'")
        print(f"  Output:   '{normalized}'")
        print()
    
    print("normalize_code() examples:")
    code_examples = [
        "  .... . .-.. .-.. ---  ",
        "....   .   .-..   .-..   ---",
        ".... . .-.. .-.. ---//.-- --- .-. .-.. -..",
        "... --- ...   ",
        "\t.... . .-.. .-.. ---\t"
    ]
    
    for code in code_examples:
        normalized = normalize_code(code)
        print(f"  Input:    '{code}'")
        print(f"  Output:   '{normalized}'")
        print()

    print("\n" + "=" * 60)
    print("EXPLAIN FEATURE DEMO")
    
    explain_examples = [
        ".... . .-.. .-.. ---",
        ".... . .-.. .-.. --- / .-- --- .-. .-.. -..",
        "... --- ...",
        ".--. -.-- - .... --- -."
    ]
    
    for i, morse_code in enumerate(explain_examples, 1):
        print(f"\nExample {i}:")
        explanation = explain(morse_code)
        print(explanation)
    
    print("\n" + "=" * 60)
    print("QUIZ FEATURE DEMO")
    print("\nThe quiz feature is interactive and allows you to practice:")
    print("  - Reading mode: Decode morse code → text")
    print("  - Writing mode: Encode text → morse code")
    print("\nStarting interactive quiz...")
    
    # Start the quiz (it will handle all user interaction)
    quiz()


if __name__ == "__main__":
    main()