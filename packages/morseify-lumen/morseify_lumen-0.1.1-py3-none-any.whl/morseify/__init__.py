"""
Morse Code Package
A Python package for encoding and decoding Morse code with additional utilities.
"""

from morseify.core import (
    encode,
    decode,
    is_valid
)
from morseify.normalize import (
    normalize_text,
    normalize_code
)
from morseify.explain import explain
from morseify.quiz import quiz

__all__ = [
    'encode',
    'decode',
    'is_valid',
    'normalize_text',
    'normalize_code',
    'explain',
    'quiz'
]

