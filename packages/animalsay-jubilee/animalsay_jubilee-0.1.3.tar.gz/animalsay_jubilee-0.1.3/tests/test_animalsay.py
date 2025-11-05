import pytest
import animalsay

# Parameterized tests for all animalsay

@pytest.mark.parametrize("func", [animalsay.cow, animalsay.dog, animalsay.cat, animalsay.sheep])
@pytest.mark.parametrize("mood", animalsay.moods)
def test_valid_animals_return_string(func, mood):
    """Each animal function should return a string containing the text and correct face pattern."""
    text = "Testing mood"
    result = func(text=text, mood=mood)
    assert isinstance(result, str)
    assert text in result
    # Ensure the ASCII contains at least some representation of the face mapping
    assert any(face in result for face in "oO^><@∩╥-_;")  # sanity check for mood faces


# Input type validation

@pytest.mark.parametrize("func", [animalsay.cow, animalsay.dog, animalsay.cat, animalsay.sheep])
def test_text_type_error(func):
    """Raise TypeError if text is not a string."""
    with pytest.raises(TypeError):
        func(text=123)

@pytest.mark.parametrize("func", [animalsay.cow, animalsay.dog, animalsay.cat, animalsay.sheep])
def test_mood_type_error(func):
    """Raise TypeError if mood is not a string."""
    with pytest.raises(TypeError):
        func(mood=123)


# Mood validation

@pytest.mark.parametrize("func", [animalsay.cow, animalsay.dog, animalsay.cat, animalsay.sheep])
def test_invalid_mood_value_error(func):
    """Raise ValueError for an invalid mood."""
    with pytest.raises(ValueError):
        func(mood="excited")


# Text validation

@pytest.mark.parametrize("func", [animalsay.cow, animalsay.dog, animalsay.cat, animalsay.sheep])
def test_text_length_value_error(func):
    """Raise ValueError if text exceeds 100 characters."""
    long_text = "a" * 101
    with pytest.raises(ValueError):
        func(text=long_text)

@pytest.mark.parametrize("func", [animalsay.cow, animalsay.dog, animalsay.cat, animalsay.sheep])
@pytest.mark.parametrize("text", ["", "   "])
def test_whitespace_value_error(func, text):
    """Raise ValueError for empty or whitespace-only text."""
    with pytest.raises(ValueError):
        func(text=text)


# Case insensitivity for mood

@pytest.mark.parametrize("func", [animalsay.cow, animalsay.dog, animalsay.cat, animalsay.sheep])
@pytest.mark.parametrize("mood", ["HAPPY", "Sad", "nEuTrAl", "Angry", "sUrPrIsEd"])
def test_mood_case_insensitive(func, mood):
    """Mood should be case-insensitive."""
    result = func(text="Mood test", mood=mood)
    assert "Mood test" in result


# Specific feature checks

def test_default_parameters():
    """Check that default arguments return without error."""
    for func in [animalsay.cow, animalsay.dog, animalsay.cat, animalsay.sheep]:
        output = func()
        assert isinstance(output, str)
        assert "Hello world!" in output


def test_correct_faces():
    """Check that the mood faces appear correctly."""
    assert "^^" in animalsay.cow(mood="happy")
    assert "∩" in animalsay.dog(mood="happy")
    assert "^_^" in animalsay.cat(mood="happy")
    assert "^^" in animalsay.sheep(mood="happy")
