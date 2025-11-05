[![CI / CD](https://github.com/swe-students-fall2025/3-python-package-team_lumen/actions/workflows/build.yml/badge.svg)](https://github.com/swe-students-fall2025/3-python-package-team_lumen/actions/workflows/build.yml)

# morseify 
morseify is a lightweight Python package that brings the world of Morse code to anyone curious about how digital communication began. It offers intuitive encode and decode functionality to translate between English text and Morse code, along with built-in tools for text normalization and message validation.

For a more interactive experience, morseify also includes a quiz mode that generates random Morse code challenges for users to decode, making it both an educational and entertaining way to explore the fundamentals of encoded communication.

## Features
- Encode English text to Morse code  
- Decode Morse code to English text  
- Normalize text and Morse sequences  
- Validate Morse message formats  
- Explain Morse code with detailed breakdowns
- Quiz mode to test Morse knowledge 

## Team Members
- [Coco Liu](https://github.com/yiminliu2004)  
- [Angela Gao](https://github.com/Xuan4781)  
- [Phoebe Huang](https://github.com/phoebelh)  
- [Galal Bichara](https://github.com/gkbichara)
- [Leo Qian](https://github.com/Leo-codingMaster)  

## Installation / Setup

Install from PyPI:
```bash
pip install morseify-lumen
```
Or install from source:
```bash
git clone https://github.com/swe-students-fall2025/3-python-package-team_lumen.git
cd 3-python-package-team_lumen
pipenv install --dev
```
Activate the environment:
```bash
pipenv shell
```
## Using morseify in Your Code
You can import and use morseify. Here's documentation for all available functions:

### Core Functions

```python
from morseify import encode, decode, is_valid

text = "HELLO WORLD"
morse = encode(text)
print(morse)

decoded = decode(morse)
print(decoded)

print(is_valid(morse))
```
### Normalization Functions
```python
from morseify.normalize import normalize_text, normalize_code

# Clean up raw text before encoding
text = "  Hello,  World!! "
cleaned = normalize_text(text)
print(cleaned)  # "HELLO, WORLD"

# Normalize Morse code before decoding
code = "....   . / /   .-.."
normalized = normalize_code(code)
print(normalized)  # ".... . / .-.."
```
### Explain Function 
```python
from morseify.explain import explain

morse_message = ".... . .-.. .-.. ---"
output = explain(morse_message)
print(output)

```
Example output:
```sql
MORSE CODE BREAKDOWN
Input: .... . .-.. .-.. ---
Normalized: .... . .-.. .-.. ---

Step-by-step translation:
  ....     → H
  .        → E
  .-..     → L
  .-..     → L
  ---      → O

Final Message: HELLO
```
### Quiz Function
```python
from morseify.quiz import quiz

# Option 1: Let user choose mode interactively
quiz()

# Option 2: Specify the mode directly
quiz("reading")   # Decode morse → text
quiz("writing")   # Encode text → morse

```
Example terminal session:
```bash
MORSE CODE QUIZ
Choose your mode:
'reading'  - Decode morse code → text
'writing'  - Encode text → morse code

Enter the mode ('reading' or 'writing'): reading

READING MODE: Decode morse code → text

Morse code: .... . .-.. .-.. --- / .-- --- .-. .-.. -..

Your answer: HELLO WORLD

Correct! Well done!
```

### Example Program

See our complete example program that demonstrates all functions: 

```python
from morseify.core import encode, decode, is_valid
from morseify.normalize import normalize_text, normalize_code
from morseify.explain import explain
from morseify.quiz import quiz


def main():
    print("=== MORSEIFY DEMO ===\n")

    # 1. Normalize text
    text = "  Hello,  World!! "
    normalized_text = normalize_text(text)
    print("Normalized text:", normalized_text)
    # Output: HELLO, WORLD

    # 2. Encode text to Morse code
    encoded = encode(normalized_text)
    print("\nEncoded Morse code:", encoded)
    # Output: .... . .-.. .-.. --- --..-- / .-- --- .-. .-.. -..

    # 3. Decode Morse code back to text
    decoded = decode(encoded)
    print("\nDecoded text:", decoded)
    # Output: HELLO, WORLD

    # 4. Validate a Morse code string
    print("\nIs valid Morse code?", is_valid(encoded))
    # Output: True

    # 5. Explain Morse code step-by-step
    print("\nMorse code breakdown:\n")
    explanation = explain(encoded)
    print(explanation)

    # 6. Start an interactive quiz session
    print("\n=== STARTING QUIZ ===")
    print("You can practice encoding or decoding Morse messages.\n")
    quiz()  # Interactive: user selects 'reading' or 'writing'


if __name__ == "__main__":
    main()
```

## Project Structure
```sql
morseify/                 
    ├── __init__.py           # Package initializer
    ├── __main__.py           # Entry point for CLI
    ├── cli.py                # Command-line interface logic
    ├── core.py               # Encode, decode, and validation functions
    ├── explain.py            # Step-by-step morse code explanation logic
    ├── mapping.py            # Dictionary mapping letters ↔ morse code
    ├── normalize.py          # Text and morse normalization utilities
    └── quiz.py               # Interactive quiz feature
tests/                        # Unit tests for all functions above
    ├── test_decode.py
    ├── test_encode.py
    ├── test_explain.py
    ├── test_is_valid.py
    ├── test_normalize_code.py
    ├── test_normalize_text.py
    └── test_quiz.py

```

## Contributing to Morseify
We welcome contributions that improve functionality, testing, or documentation.
Before contributing, make sure your environment is set up correctly and that all tests pass.

### Development Workflow
Create a new branch for your feature:
```bash
git checkout -b feature/<feature-name>
git add .
git commit -m "Add <feature-description>"
git push origin feature/<feature-name>
```
Then open a Pull Request on GitHub to the piefile-experiment branch.

### Running Tests
Follow Installation / Setup instructions first, then run the following commands:
```bash
# Run all tests
pipenv run pytest -v

# Run tests with coverage report
pytest tests/ --cov=morseify --cov-report=term-missing

# Run a specific test file
pytest tests/test_explain.py -v
```
All pull requests are automatically tested using GitHub Actions. Make sure tests pass locally before submitting your PR.

## PyPI Package

This package is available on PyPI: [morseify-lumen](https://pypi.org/project/morseify-lumen/).
