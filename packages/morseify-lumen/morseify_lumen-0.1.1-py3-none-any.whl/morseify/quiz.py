import random
import sys
from pathlib import Path


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from morseify.core import encode, decode
except ModuleNotFoundError:
    from .core import encode, decode

QUIZ_SENTENCES = [
    "HELLO WORLD",
    "LET US TRY",
    "MORSE CODE IS FUN",
    "PYTHON ROCKS",
    "LEARNING TAKES TIME",
    "FORZA ROMA",
    "SWE IS USEFUL",
    "RUNNING OUT OF IDEAS",
    "THIS SHOULD BE ENOUGH",
    "I AM NOT VERY CREATIVE"
]


def quiz(mode=None):
    """
    Interactive morse code quiz.
    
    Args:
        mode: Optional - 'reading' or 'writing', or None to ask
    """
    # Always use a random sentence
    selected_sentence = random.choice(QUIZ_SENTENCES)
    


    if mode is None:
        print("\nMORSE CODE QUIZ")
        print("Choose your mode:")
        print("'reading'  - Decode morse code → text")
        print("'writing'  - Encode text → morse code")
        print()
        mode = input("Enter the mode ('reading' or 'writing'): ").strip().lower()
        
        while mode not in ['reading', 'writing']:
            print("\nInvalid mode!")
            print("Please enter 'reading' or 'writing'")
            mode = input("\nEnter the mode: ").strip().lower()
    
    print()
    if mode == 'reading':
        print("READING MODE: Decode morse code → text")
        morse_to_decode = encode(selected_sentence)
        print(f"\nMorse code: {morse_to_decode}")
        print()
        
        while True:
            answer = input("Your answer: ").upper().strip()
            
            if answer == selected_sentence:
                print("\nCorrect! Well done!")
                break
            else:
                print("\nIncorrect!\n")
                retry = input("Try again? (yes/no): ").strip().lower()
                
                # Validate yes/no input
                while retry not in ['yes', 'no']:
                    print("Please enter 'yes' or 'no'")
                    retry = input("Try again? (yes/no): ").strip().lower()
                
                if retry == 'yes':

                    print(f"\nMorse code: {morse_to_decode}")
                    print()
                    continue  # Try again
                else: 
                    print("\nANSWER REVEALED")
                    print(f"Your answer:    {answer}")
                    print(f"Correct answer: {selected_sentence}")
                    print(f"\nThe morse code '{morse_to_decode}' translates to '{selected_sentence}'")
                    break
    
    else:  
        print("")
        print("WRITING MODE: Encode text → morse code")
        print(f"\nText to encode: {selected_sentence}")
        print()
        correct_morse = encode(selected_sentence)
        
        
        while True:
            answer = input("Your answer: ").strip()
            
            # Check if answer contains only valid morse characters
            valid_chars = set(".- /")
            while not all(char in valid_chars for char in answer) or not answer:
                print("\nInvalid morse code format!")
                print("Please use only dots (.), dashes (-), spaces, and slashes (/)")
                print("Example: ... --- ... (for SOS)")
                answer = input("\nYour answer: ").strip()
        
            # Now check if the answer is correct (don't validate if it's real morse)
            if answer == correct_morse:
                print("\nCorrect! Well done!")
                break
            else:
                print("\nIncorrect!\n")
                retry = input("Try again? (yes/no): ").strip().lower()
                
                # Validate yes/no input
                while retry not in ['yes', 'no']:
                    print("Please enter 'yes' or 'no'")
                    retry = input("Try again? (yes/no): ").strip().lower()
                
                if retry == 'yes':
                    print(f"\nText to encode: {selected_sentence}")
                    print()
                    continue  
                else:  
                    print("\nANSWER REVEALED")
                    print(f"Your answer:    {answer}")
                    print(f"Correct answer: {correct_morse}")
                    print(f"\n'{selected_sentence}' in morse code is: {correct_morse}")
                    break
    
    # print("=" * 60)


if __name__ == "__main__":
    quiz()