
import random

EXCUSES = {
    "deadline": [
        "My code was compiling for three days.",
        "The API rate-limited my motivation.",
        "I accidentally scheduled my task for next week."
    ],
    "meeting": [
        "Zoom refused to unmute me.",
        "I got stuck in another meeting that could have been an email.",
        "My calendar app lied about the time."
    ],
    "class": [
        "My virtual environment ate my homework.",
        "AI took credit for my assignment.",
        "My professor’s email went to spam."
    ],
    "general": [
        "The cloud was down.",
        "My laptop ran out of coffee.",
        "SyntaxError: life not defined."
    ]
}

def get_excuse(category="general"):
    """
    Return randomly chosen excuse from the selected category.

    Args: category (str): type of excuse to return (deadline, meeting, class, or general)

    Raises ValueError if the category doesn't exist
    """
    category = category.lower()
    if category not in EXCUSES:
        raise ValueError("Invalid category. Try 'deadline', 'meeting', 'class', or 'general'.")
    return random.choice(EXCUSES[category])

def get_excuses(category="general", count = None ):
    """
    Return all excuses from the selected category if no count is given. 
    Otherwise, randomly return a number of excuses equal to count. 
    If count is greater than the number of excuses in the selected category,
    repeats will be shown.

    Args: category (str): type of excuse to return (deadline, meeting, class, or general)
          count (int | None): number of excuses to return

    Raises ValueError if the category doesn't exist
    Raises TypeError if count is not an int
    Raises ValueError if count less than 0
    """
    category = category.lower()
    if category not in EXCUSES:
        raise ValueError("Invalid category. Try 'deadline', 'meeting', 'class', or 'general'.")
    if count is None:
        return list(EXCUSES[category])
    if not isinstance(count, int):
        raise TypeError("count must be an int")
    if count < 0:
        raise ValueError("count must be >= 0")
    if count == 0:
        return []
    n = len(EXCUSES[category])
    if count <= n:
        return random.sample(EXCUSES[category], k=count)
    ret = random.sample(EXCUSES[category], k=n)
    ret.extend(random.choices(EXCUSES[category], k=count - n))
    return ret

def list_excuses(category="general"):
    """
    Return all excuses from the selected category as a list.

    Args: category (str): type of excuse to return (deadline, meeting, class, or general)

    Raises ValueError if the category doesn't exist
    """
    category = category.lower()
    if category not in EXCUSES:
        raise ValueError("Invalid category. Try 'deadline', 'meeting', 'class', or 'general'.")
    return list(EXCUSES[category])

def add_excuse(category, excuse):
    """
    Add a new excuse to an existing category.

    Args:
        category (str): category name ('deadline', 'meeting', 'class', or 'general')
        excuse (str): text of the excuse to add

    Returns:
        str: the excuse that was added

    Raises:
        ValueError: if category not found or excuse invalid
    """
    #check if it is a string or not
    if not isinstance(category, str):
        raise ValueError("Category must be a string.")
    category = category.lower().strip()

    #validate category
    if category not in EXCUSES:
        raise ValueError("Invalid category. Try 'deadline', 'meeting', 'class', or 'general'.")

    #validate the new excuse
    if not isinstance(excuse, str) or not excuse.strip():
        raise ValueError("Excuse must be a non-empty string.")
    excuse = excuse.strip()

    if excuse in EXCUSES[category]:
        print("Excuse already exists; no changes made.")
        return excuse

    #add this new excuse
    EXCUSES[category].append(excuse)

    return excuse
