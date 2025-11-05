# Python Package Exercise

An exercise to create a Python package, build it, test it, distribute it, and use it. See [instructions](./instructions.md) for details.

# Animal Say
Animal Say is a Python package that lets animals "speak" in ASCII art with different moods! You can have a cow, dog, cat, or sheep say anything you want, in a happy, sad, neutral, angry, or surprised mood.

USAGE:

```python
import animalsay

# Make a happy dog say "Hello! I'm a happy dog!"
print(animalsay.dog("Hello! I'm a happy dog!", mood="happy"))
```

EXAMPLE OUTPUT:

```
Hello! I'm a happy dog!
      \
       \   / \__
          (    ∩\\__
          /         O
         /   (_____/
        /_____/   U
```

# Available Animals
- cow
- dog
- cat
- sheep

# Available Moods
- happy
- sad
- neutral
- angry
- surprised

# Functions

All animals use the same function signature:

animal(test: str, mood: str = "neutral") -> str
- text: The string message the animal will "say".
- mood: One of the available moods (happy, sad, neutral, angry, surprised). Defaults to "neutral".
- Returns: A string containing the ASCII art of the animal speaking the message with the selected mood.

# Example:

import animalsay

ascii_art = animalsay.sheep("Baa! I'm surprised!", mood="surprised")
print(ascii_art)

# Contributions
To set up the project locally: 
1. First, clone the repository into a workspace.
```Bash
git clone https://github.com/user/repository-name.git
cd repository-name
```

2. Change this line in Pipfile into your current Python version.

```
[requires]
python_version = "3.10"
```

3. Then, use pipenv to install all dependencies.
```Bash
pip install pipenv

pipenv install --dev
```

4. To build, run tests, or upload through twine, use pipenv to run our scripts.

```Bash
pipenv run test # run tests
pipenv run build # build the package
pipenv run upload # upload to PyPI
```
# Installation

1. Option A — Install from TestPyPI

   If the package has been uploaded to **TestPyPI**, install it using:

```bash
pip install -i https://test.pypi.org/simple/ animalsay-jubilee-yl9778
```
#### Tip: Add --upgrade if you already installed an older version.
```bash
pip install -i https://test.pypi.org/simple/ animalsay-jubilee-yl9778 --upgrade
```

2. Option B — Install from Source

   If you have cloned the repository manually:
```bash
git clone https://github.com/swe-students-fall2025/3-python-package-team_jubilee.git
cd 3-python-package-team_jubilee
pip install .
```

# Team Members
- [Jasmine Zhu](https://github.com/jasminezjr)
- [Grace He](https://github.com/gracehe04)
- [Vaishnavi Suresh](https://github.com/vaishnavi-suresh)
- [Chengqi Li](https://github.com/lichengqi617)
- [Krystal Lin](https://github.com/krystalll-0)

Have fun making animals talk! 🐶🐱🐮🐑
