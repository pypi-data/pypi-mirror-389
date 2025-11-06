# excusegen 
**excusegen** is a python package that generates random excuses for various situations, for those of us who are less creative. Read about the project on PyPI [here](https://pypi.org/project/excusegen/0.1.0/ "link to PyPI page")!

[![CI / CD](https://github.com/swe-students-fall2025/3-python-package-team_ember/actions/workflows/build.yaml/badge.svg)](https://github.com/swe-students-fall2025/3-python-package-team_ember/actions/workflows/build.yaml)

## Team Members

[Jeffrey Chen](https://github.com/jzc719 "Jeffrey's GitHub profile")<br>
[Sophia Fu](https://github.com/Sophiaaa430 "Sophia's GitHub profile")<br>
[Avi Herman](https://github.com/avih7531 "Avi's GitHub profile")<br>
[Alissa Hsu](https://github.com/alissahsu22 "Alissa's GitHub profile")<br>
[Jacob Ng](https://github.com/jng20 "Jacob's GitHub profile") <br>

## Installation and Testing (for Developers)

If you want to install this project on your own machine (for testing or further development purposes), first clone the repository and install dependencies using Pipenv:

    git clone https://github.com/swe-students-fall2025/3-python-package-team_ember.git
    cd excusegen
    pipenv install --dev

Next install the package itself in editable mode:

    pipenv run pip install -e .

If you don't have Pipenv installed, install it first:

    pip install pipenv

To enter the virutal environment, run:

    pipenv shell

To perform tests, run:

    pipenv run pytest -q

## Importing and Usage (for Users) 

First, install the package from PyPI with pip:

    pip install excusegen

Alternatively, install the package directly from this GitHub repo:

    git clone https://github.com/swe-students-fall2025/3-python-package-team_ember.git
    cd excusegen
    pipenv install .

If you don't have Pipenv installed, install it first:

    pip install pipenv

Then, run the package from the command line:

    python3 -m excusegen

Or use it in Python code:

    from excusegen import get_excuse, get_excuses, add_excuse, list_excuses

    print(get_excuse())                # returns a general excuse
    print(get_excuse("deadline"))      # returns a deadline-related excuse
    print(get_excuses("meeting", count=2))   # returns two excuses from the meeting category
    add_excuse("general", "My keyboard took a break.")   # adds a new excuse
    print(list_excuses("general"))     # lists all general excuses

Available categories:
- general
- deadline
- meeting
- class

Example python code with all functions: 
[example.py](https://github.com/swe-students-fall2025/3-python-package-team_ember/blob/pipfile-experiment/example.py)

Run the example python code from the command line:

    python3 example.py

## Functions and Features

| Function |  Purpose | Parameters | Raises |
|---|---|---|---|
| get_excuse() | randomly returns an excuse from the specified category | category (str) - type of excuse to return (deadline, meeting, class, or general) | ValueError if the category doesn't exist |
| get_excuses() | randomly returns a number of excuses equal to count from the specified category, returns all excuses if count is not specified | 1. category (str) - type of excuse to return (deadline, meeting, class, or general)<br> 2. count (int or None) - number of excuses to return | ValueError if the category doesn't exist<br> TypeError if count is not an int<br> ValueError if count less than 0 |
| list_excuses() | returns all excuses from the selected category as a list | category (str) - type of excuse to return (deadline, meeting, class, or general) | ValueError if the category doesn't exist |
| add_excuse() | adds a new excuse to an existing category | 1. category (str) - category name ('deadline', 'meeting', 'class', or 'general')<br> 2. excuse (str) - text of the excuse to add | ValueError if category not found or excuse invalid |