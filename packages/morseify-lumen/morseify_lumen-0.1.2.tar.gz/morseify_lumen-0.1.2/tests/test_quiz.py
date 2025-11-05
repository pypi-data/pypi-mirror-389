import pytest
from morseify.quiz import quiz, QUIZ_SENTENCES
from morseify.core import encode, decode


class Tests:
    """Test suite for the quiz module."""

    #
    # Fixtures - these are functions that can do any optional setup or teardown before or after a test function is run.
    #

    @pytest.fixture
    def example_fixture(self):
        """
        An example of a pytest fixture - a function that can be used for setup and teardown before and after test functions are run.
        """
        # place any setup you want to do before any test function that uses this fixture is run
        yield  # at the yield point, the test function will run and do its business
        # place with any teardown you want to do after any test function that uses this fixture has completed

    #
    # Test functions
    #

    def test_sanity_check(self, example_fixture):
        """
        Test debugging... making sure that we can run a simple test that always passes.
        Note the use of the example_fixture in the parameter list - any setup and teardown in that fixture will be run before and after this test function executes
        From the main project directory, run the `python3 -m pytest` command to run all tests.
        """
        expected = True  # the value we expect to be present
        actual = True  # the value we see in reality
        assert actual == expected, "Expected True to be equal to True!"

    def test_quiz_sentences_list_exists(self):
        """
        Verify that QUIZ_SENTENCES list is defined and not empty.
        """
        assert QUIZ_SENTENCES is not None, "QUIZ_SENTENCES should not be None"
        assert len(QUIZ_SENTENCES) > 0, "QUIZ_SENTENCES should not be empty"
        assert all(isinstance(s, str) for s in QUIZ_SENTENCES), "All sentences should be strings"

    def test_quiz_sentences_are_uppercase(self):
        """
        Verify that all quiz sentences are uppercase.
        """
        for sentence in QUIZ_SENTENCES:
            assert sentence == sentence.upper(), f"Sentence '{sentence}' should be uppercase"

    def test_quiz_sentences_content(self):
        """
        Verify that QUIZ_SENTENCES contains expected sentences.
        """
        assert len(QUIZ_SENTENCES) >= 5, f"Expected at least 5 sentences, found {len(QUIZ_SENTENCES)}"
        
        assert any("HELLO" in s or "SOS" in s or "PYTHON" in s for s in QUIZ_SENTENCES), \
            "Expected to find common words like HELLO, SOS, or PYTHON in sentences"

    def test_quiz_sentences_no_duplicates(self):
        """
        Verify that there are no duplicate sentences in QUIZ_SENTENCES.
        """
        unique_sentences = set(QUIZ_SENTENCES)
        assert len(unique_sentences) == len(QUIZ_SENTENCES), "QUIZ_SENTENCES should not contain duplicates"

    def test_quiz_sentences_valid_characters(self):
        """
        Verify that all sentences contain only valid characters for morse code.
        """
        valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,?/-()")
        
        for sentence in QUIZ_SENTENCES:
            sentence_chars = set(sentence)
            assert sentence_chars.issubset(valid_chars), \
                f"Sentence '{sentence}' contains invalid characters: {sentence_chars - valid_chars}"

    def test_quiz_sentences_can_be_encoded(self):
        """
        Verify that all quiz sentences can be successfully encoded to morse code.
        Since encode returns a morse code string, run it for all sentences and verify the output.
        """
        for sentence in QUIZ_SENTENCES:
            morse = encode(sentence)
            assert isinstance(morse, str), f"Expected encode('{sentence}') to return a string. Instead, it returned {morse}"
            assert len(morse) > 0, f"Expected encode('{sentence}') not to be empty. Instead, it returned a string with {len(morse)} characters"

    def test_quiz_sentences_roundtrip(self):
        """
        Verify that all quiz sentences can be encoded and decoded back correctly.
        Make sure that encoding then decoding returns the original text.
        """
        for sentence in QUIZ_SENTENCES:
            morse = encode(sentence)
            decoded = decode(morse)
            assert decoded == sentence, \
                f"Round trip failed for '{sentence}': encoded to '{morse}', decoded to '{decoded}'"

    def test_quiz_function_exists(self):
        """
        Verify that the quiz function exists and is callable.
        """
        assert quiz is not None, "quiz function should exist"
        assert callable(quiz), "quiz should be a callable function"

    def test_quiz_function_parameters(self):
        """
        Verify that quiz function has the expected parameters.
        """
        import inspect
        sig = inspect.signature(quiz)
        params = list(sig.parameters.keys())
        
        assert 'mode' in params, "quiz should have 'mode' parameter"
        assert 'sentence' not in params, "quiz should not have 'sentence' parameter (always random)"

    def test_quiz_integration_with_encode(self):
        """
        Verify that quiz properly integrates with encode function.
        Test that encoding works for various test sentences.
        """
        test_cases = [
            ("HELLO", ".... . .-.. .-.. ---"),
            ("SOS", "... --- ..."),
            ("TEST", "- . ... -"),
        ]
        
        for text, expected_morse in test_cases:
            actual = encode(text)
            assert actual == expected_morse, \
                f"Expected encode('{text}') to return '{expected_morse}', got '{actual}'"

    def test_quiz_sentences_length_variety(self):
        """
        Verify that quiz sentences have variety in length.
        """
        lengths = [len(s) for s in QUIZ_SENTENCES]
        
        # Check that we have both short and long sentences
        assert min(lengths) < 15, "Expected some short sentences (< 15 chars)"
        assert max(lengths) > 10, "Expected some longer sentences (> 10 chars)"

    def test_quiz_sentences_word_count(self):
        """
        Verify that quiz sentences have varying word counts.
        """
        for sentence in QUIZ_SENTENCES:
            words = sentence.split()
            assert len(words) > 0, f"Sentence '{sentence}' should have at least one word"
            assert len(words) <= 10, f"Sentence '{sentence}' should not be too long (max 10 words)"

    def test_quiz_sentences_morse_conversion(self):
        """
        Verify morse code conversion for all quiz sentences produces valid output.
        """
        valid_morse_chars = set(".- /")
        
        for sentence in QUIZ_SENTENCES:
            morse = encode(sentence)
            morse_chars = set(morse)
            assert morse_chars.issubset(valid_morse_chars), \
                f"Morse code for '{sentence}' contains invalid characters: {morse_chars - valid_morse_chars}"

    def test_quiz_random_sentence_selection(self):
        """
        Verify that we can randomly select sentences from QUIZ_SENTENCES.
        """
        import random
        
        for _ in range(100):
            selected = random.choice(QUIZ_SENTENCES)
            assert selected in QUIZ_SENTENCES, \
                f"Random selection '{selected}' not in QUIZ_SENTENCES"

    def test_quiz_specific_sentences_content(self):
        """
        Verify specific expected sentences are in the quiz list.
        """
        common_phrases = ["HELLO WORLD", "PYTHON ROCKS", "SWE IS USEFUL"]
        found_common = any(phrase in QUIZ_SENTENCES for phrase in common_phrases)
        assert found_common, f"Expected at least one common phrase from {common_phrases}"
