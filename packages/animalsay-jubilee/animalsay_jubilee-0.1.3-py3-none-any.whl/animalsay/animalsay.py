
animals = ['cow', 'dog', 'cat', 'sheep']
moods = ['happy', 'sad', 'neutral', 'angry', 'surprised']

def cow(text="Hello world!", mood="neutral"):
    """
    Make a cow say something with a specific mood.
    
    Args:
        text (str): The text for the cow to say
        mood (str): Cow's mood - 'happy', 'sad', 'neutral', 'angry', 'surprised'
    
    Returns:
        str: ASCII art of a cow speaking
    """
    # Input validation
    if not isinstance(text, str):
        raise TypeError(f"text must be a string, got {type(text).__name__}")
    
    if not isinstance(mood, str):
        raise TypeError(f"mood must be a string, got {type(mood).__name__}")
    
    # Normalize mood to lowercase
    mood_lower = mood.lower()

    # Check for value error
    if mood_lower not in moods:
        raise ValueError(f"Invalid mood '{mood}'. Available moods: {', '.join(moods)}")

    if len(text) > 100:
        raise ValueError(f"Text too long ({len(text)} characters). Maximum allowed: 100 characters")
    
    if not text.strip():
        raise ValueError("Text cannot be empty or only whitespace")
    
    # Define cow faces based on mood
    faces = {
        "happy": "^^",
        "sad": "••", 
        "neutral": "oo",
        "angry": "><",
        "surprised": "OO"
    }

    face = faces.get(mood_lower)

    # Create cow art using raw string to avoid escape sequence warnings
    cow_art = fr"""
{text}
        \   ^__^
         \  ({face})\_______
            (__)\       )\/\\
                ||----w |
                ||     ||
    """

    return cow_art


def dog(text="Hello world!", mood="neutral"):
    """
    Make a dog say something with a specific mood.
    
    Args:
        text (str): The text for the dog to say
        mood (str): Dog's mood - 'happy', 'sad', 'neutral', 'angry', 'surprised'
    
    Returns:
        str: ASCII art of a dog speaking
    """
    # Input validation
    if not isinstance(text, str):
        raise TypeError(f"text must be a string, got {type(text).__name__}")
    
    if not isinstance(mood, str):
        raise TypeError(f"mood must be a string, got {type(mood).__name__}")
    
    # Normalize mood to lowercase
    mood_lower = mood.lower()

    # Check for value error
    if mood_lower not in moods:
        raise ValueError(f"Invalid mood '{mood}'. Available moods: {', '.join(moods)}")

    if len(text) > 100:
        raise ValueError(f"Text too long ({len(text)} characters). Maximum allowed: 100 characters")
    
    if not text.strip():
        raise ValueError("Text cannot be empty or only whitespace")
    
    # Define dog faces based on mood
    faces = {
        "happy": "∩",
        "sad": "╥", 
        "neutral": "@",
        "angry": ">",
        "surprised": "O"
    }

    face = faces.get(mood_lower)


    # Create dog art using raw string to avoid escape sequence warnings
    dog_art = fr"""
{text}
      \
       \   / \__
          (    {face}\\__
          /         O
         /   (_____/
        /_____/   U
"""

    return dog_art

def cat(text="Hello world!", mood="neutral"):
    """
    Make a cat say something with a specific mood.
    
    Args:
        text (str): The text for the cat to say
        mood (str): Cat's mood - 'happy', 'sad', 'neutral', 'angry', 'surprised'
    
    Returns:
        str: ASCII art of a cat speaking
    """
    # Input validation
    if not isinstance(text, str):
        raise TypeError(f"text must be a string, got {type(text).__name__}")
    
    if not isinstance(mood, str):
        raise TypeError(f"mood must be a string, got {type(mood).__name__}")
    
    # Normalize mood to lowercase
    mood_lower = mood.lower()

    # Check for value error
    if mood_lower not in moods:
        raise ValueError(f"Invalid mood '{mood}'. Available moods: {', '.join(moods)}")

    if len(text) > 100:
        raise ValueError(f"Text too long ({len(text)} characters). Maximum allowed: 100 characters")
    
    if not text.strip():
        raise ValueError("Text cannot be empty or only whitespace")
    
    # Define cat faces based on mood
    faces = {
        "happy": "^_^",
        "sad": "-_-", 
        "neutral": "o_o",
        "angry": ">_<",
        "surprised": "O_O"
    }

    face = faces.get(mood_lower)

    # Create cat art using raw string to avoid escape sequence warnings
    cat_art = fr"""
{text}
        \    /\_/\
         \  ( {face} )
             > ^ <
    """ 

    return cat_art

def sheep(text="Hello world!", mood="neutral"):
    """
    Make a sheep say something with a specific mood.
    
    Args:
        text (str): The text for the sheep to say
        mood (str): Sheep's mood - 'happy', 'sad', 'neutral', 'angry', 'surprised'
    
    Returns:
        str: ASCII art of a sheep speaking
    """
    # Input validation
    if not isinstance(text, str):
        raise TypeError(f"text must be a string, got {type(text).__name__}")
    
    if not isinstance(mood, str):
        raise TypeError(f"mood must be a string, got {type(mood).__name__}")
    
    # Normalize mood to lowercase
    mood_lower = mood.lower()

    # Check for value error
    if mood_lower not in moods:
        raise ValueError(f"Invalid mood '{mood}'. Available moods: {', '.join(moods)}")

    if len(text) > 100:
        raise ValueError(f"Text too long ({len(text)} characters). Maximum allowed: 100 characters")
    
    if not text.strip():
        raise ValueError("Text cannot be empty or only whitespace")
    
    # Define sheep faces based on mood
    faces = {
        "happy": "^^",
        "sad": ";;", 
        "neutral": "oo",
        "angry": "><",
        "surprised": "OO"
    }

    face = faces.get(mood_lower)

    # Create sheep art using raw string to avoid escape sequence warnings
    sheep_art = fr"""
{text}
        \   www,
         \  ({face})\wwwwww
            (__)\ wwwww)\/\,
                ||wwwww |
                ||     ||
    """ 
    return sheep_art
