from morseify.mapping import MORSE_TO_LETTER, LETTER_TO_MORSE
from morseify.core import is_valid
from morseify.normalize import normalize_code

def explain(morse_message):
  
    """
    WantToDo in explain.py
    Provide a step-by-step breakdown of a morse code input.

    Args:
        morse_message: Morse code string need to be explained
        
    Returns:
        String containing the step-by-step breakdown
    """
    #input validation
    if not is_valid(morse_message):
        return "Error: Invalid Morse code message. Please check the format."
    
    #morse code normalization
    normalized = normalize_code(morse_message)

    #explainaion building
    explanation = []
    explanation.append("=" * 50)
    explanation.append("MORSE CODE BREAKDOWN")
    explanation.append("=" * 50)
    explanation.append(f"Input: {morse_message}")
    
    if normalized != morse_message.strip():
        explanation.append(f"Normalized: {normalized}")
    
    explanation.append("\nStep-by-step translation:")
    explanation.append("-" * 30)
    
    #Process each morse sequence
    sequences = normalized.split(' ')
    result_chars = []
    
    for seq in sequences:
        if seq == '':
            continue
        elif seq == '/':
            explanation.append("  /        → [SPACE]")
            result_chars.append(' ')
        else:
            letter = MORSE_TO_LETTER.get(seq, '?')
            explanation.append(f"  {seq:<8} → {letter}")
            result_chars.append(letter)

    #show the final result
    explanation.append("-" * 30)
    explanation.append(f"\nFinal message: {(''.join(result_chars))}")
    explanation.append("=" * 50)
    
    return '\n'.join(explanation)
    
    #pass