from .core import encode, decode, is_valid
from .explain import explain
from .quiz import quiz


def main():
    print("Morse Code Encode/Decode Test")
    # Test cases
    test_cases = [
        "HELLO",
        "HELLO WORLD",
        "SOS",
        "PYTHON",
        "123",
        "A1B2C3"
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
    
    # Example of explain feature with user input
    print("Explain Feature")
    user_morse = input("Enter morse code to explain: ").strip()
    if user_morse:
        explanation = explain(user_morse)
        print(explanation)
    else:
        print("No input provided. Using example:")
        example_morse = ".... . .-.. .-.. --- / .-- --- .-. .-.. -.."
        explanation = explain(example_morse)
        print(explanation)


if __name__ == "__main__":
    main()