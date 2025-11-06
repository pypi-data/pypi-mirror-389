![CI / CD](https://github.com/swe-students-fall2025/3-python-package-team_mistral/actions/workflows/build.yaml/badge.svg)


# ChatterPy

ChatterPy is a lighthearted Python package that helps spark **fun conversations** by giving you a random **fun fact**, **small talk question**, **compliment**, or even a **pickup line** for when things get quiet.  

## Group Members

[Mahabub Alif](https://github.com/Alif-4)

[Sydney Nadeau](https://github.com/sen5217)

[Susan Wang](https://github.com/sw5556)

[Aden Juda](https://github.com/yungsemitone)

[Serena Wang](https://github.com/serena0615)

## PyPi
[View our package's page here.](https://test.pypi.org/project/chatterpy-mistral/0.0.2/)

## Installation

### For Users: Install via pip
```bash
pip install chatterpy_mistral
```

### For Contributors: Set Up Development Environment

If you want to contribute to ChatterPy, follow these steps:

1. **Clone the repository:**
```bash
   git clone https://github.com/swe-students-fall2025/3-python-package-team_mistral.git
   cd 3-python-package-team_mistral
```

2. **Install pipenv** (if you don't have it):
```bash
   pip install pipenv
```

3. **Install dependencies:**
```bash
   pipenv install --dev
```

4. **Activate the virtual environment:**
```bash
   pipenv shell
```

5. **Build the package:**
```bash
   pipenv run python -m build
```

---

## How to run tests

Unit tests are included within the `tests` directory. Inorder to run these tests:

1. Install `pytest` into the virtual environment by running `pipenv install pytest`
2. Run the tests from the main project directory: `pipenv run python -m pytest`. So it works on any shell or if you are already in `pipenv shell` you can run `pytest -q`
3. If no changes were made and the system works as intended 34 tests should pass.

## Usage

### Importing ChatterPy in Your Code

After installing with `pip install chatterpy_mistral`, you can import and use any function:
```python
from chatterpy_mistral import fun_fact, smallTalk, pickUpLine, compliment, banter

# Get a random fun fact
print(fun_fact())

# Get a fun fact from a specific category
print(fun_fact(category="science", rarity="rare"))

# Get small talk - question
print(smallTalk(question=True))

# Get small talk - comment
print(smallTalk(question=False))

# Get a pickup line
print(pickUpLine(kind="poetic", name="Alex"))

# Get a compliment
print(compliment(name="Jordan", intensity=2, style="classic", category="personality"))

# Get playful banter
print(banter(intensity="mild", name="Sam"))
```

**See [example.py](src/example.py) for a complete interactive demonstration.**

To run the example program:
```bash
python src/example.py
```

## Command-Line Interface

### Using the CLI After Installation

Once installed via pip, you can use ChatterPy from the command line, for example:

```bash
chatterpy_mistral --smalltalk --comment
```

## Example Output

When you run these commands, you'll get different outputs:

### Small Talk (Comment)

```bash
python -m chatterpy_mistral --smalltalk --comment
```

You might see something like this:

```

Avocado toast is overrated, but I’d still eat it.

```

### Small Talk (Question)

```bash
python -m chatterpy_mistral --smalltalk --question
```
You might get:

```

I’ve been meaning to start reading/watching something new — any recommendations?

```

### Pickup Line (No Name)

```bash
python -m chatterpy_mistral --pickup --kind poetic
```

You could see:

```

your presence feels like morning sunshine.

```

### Pickup Line (With Name)

```bash
python -m chatterpy_mistral --pickup --kind nerdy --name Susan
```

The output might be:

```

Susan, you’re a clean solution in a messy codebase.

```

### Compliment (With Name)

```bash
python -m chatterpy_mistral --compliment --name Sydney --intensity medium
```
This might return:

```

Sydney, You always add something unique to your look.

```

### Fun Facts (No parameters)

```bash
python -m chatterpy_mistral --fact
```

Could get you:

```

Bananas are berries, but strawberries aren’t.

```

### Fun Facts (With parameters)

```bash
python -m chatterpy_mistral --fact --category history --rarity rare
```

Might spit out:

```

Ancient Roman concrete can 'self-heal'.


```

### Banter (No name)

```bash
python -m chatterpy_mistral --banter --intensity medium
```

Will say:

```

you look like something I drew with my left hand.

```

### Banter (With name)

```bash
python -m chatterpy_mistral --banter --intensity mild --name Aden
```

Will return:

```
Aden, you're like a software update: nobody asked for you.


```



---

## Features

| Function | Description |
| ----------------------------- | -------------------------------------------------------------- |
| `fun_fact(category: str = "general", rarity: str = "common")` | Returns a random fun fact from one of four categories: `general`, `science`, `history`, or `animals`, with varying rarity|
| `smallTalk(question: bool)` | Returns either a fun question (`True`) or a random comment (`False`). |
| `pickUpLine(kind: str, name: str = "")` | Returns a pickup line of a certain type (`classic`, `poetic`, `funny`, `nerdy`). Optionally includes a name at the start. |
| `compliment(name: str, intensity: str)` | Returns a compliment of a specific intesity(`mild`, `medium`, `intense`). Includes a name at the start. |
| `banter(intensity: str, name: str = "")` | Returns a playful roast or joke depending on the chosen intensity (`mild`, `medium`, `intense`). Optionally includes a name to personalize it. |



## Project Structure

```
3-python-package-team_mistral/
├──src/
│   ├───chatterpy_mistral/
│       ├── __init__.py
│       ├── __main__.py
│       ├── funfacts.py
│       ├── smalltalk.py
│       ├── pickuplines.py
│       └── banter.py
│       └── compliments.py
│   ├─── example.py
├──tests/
│   ├── test_funfacts.py
│   ├── test_smalltalk.py
│   ├── test_pickuplines.py
│   └── test_compliments.py
│   └── test_banter.py
├── Pipfile
├── pyproject.toml
└── README.md
```

## example.py

[Link to example.py](src/example.py)

example.py is a standalone Python script that demonstrates the functionality of the chatterpy_mistral package. It calls each of the package’s functions: fun facts, small talk, banter, pickup lines, and compliments.  

This script is separate from the CLI interface in that it can be run directly with Python, and is intended for demonstration or testing purposes, rather than as a command-line tool for user input.
