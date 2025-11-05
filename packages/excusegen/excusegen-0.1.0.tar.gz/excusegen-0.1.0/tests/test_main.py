
import random
import pytest
from excusegen import get_excuse, get_excuses, add_excuse, list_excuses
import copy
from excusegen.main import EXCUSES


@pytest.fixture(autouse=True)
def _isolate_excuses():
    backup = copy.deepcopy(EXCUSES)
    try:
        yield
    finally:
        EXCUSES.clear()
        EXCUSES.update(backup)


def test_get_excuse_returns_valid_string():
    result = get_excuse()
    assert isinstance(result, str)
    assert len(result) > 0

def test_get_excuse_returns_random_results():
    results = {get_excuse() for _ in range(10)}
    assert len(results) > 1, "Function should return different results sometimes"

def test_get_excuse_returns_valid_excuse():
    result = get_excuse()
    all_excuses = [e for sublist in EXCUSES.values() for e in sublist]
    assert result in all_excuses, "Output should be one of the predefined excuses"

#tests for getexcuses
def test_get_excuses_returns_all_when_count_is_none():
    all_general = get_excuses("general", None)
    assert isinstance(all_general, list)
    assert all_general == list(EXCUSES["general"])

def test_get_excuses_invalid_category_raises_value_error():
    with pytest.raises(ValueError):
        get_excuses("not-a-category")

def test_get_excuses_count_type_must_be_int():
    with pytest.raises(TypeError):
        get_excuses("general","foo")

def test_get_excuses_count_must_be_nonnegative():
    with pytest.raises(ValueError):
        get_excuses("general", -1)

def test_get_excuses_count_zero_returns_empty_list():
    assert get_excuses("general", 0) == []

def test_get_excuse_count_less_than_pool_size():
    cat = random.choice(list(EXCUSES.keys()))
    n = len(EXCUSES[cat]) - 1
    res = get_excuses(cat, n)
    assert len(set(res)) == n
    assert set(res).issubset(set(EXCUSES[cat]))

def test_get_excuse_count_greater_than_pool_size():
    cat = random.choice(list(EXCUSES.keys()))
    n = len(EXCUSES[cat]) + 1
    res = get_excuses(cat, n)
    assert len(res) == n
    assert set(res).issubset(set(EXCUSES[cat]))

#tests for list_excuses
def test_list_excuses_returns_list():
    result = list_excuses()
    assert isinstance(result, list)
    assert len(result) > 0

def test_list_excuses_returns_all_excuses_from_category():
    result = list_excuses("deadline")
    assert result == list(EXCUSES["deadline"])
    assert len(result) == len(EXCUSES["deadline"])

def test_list_excuses_invalid_category_raises_value_error():
    with pytest.raises(ValueError):
        list_excuses("invalid-category")

def test_list_excuses_default_category():
    result = list_excuses()
    assert result == list(EXCUSES["general"])

def test_list_excuses_case_insensitive():
    result_lower = list_excuses("meeting")
    result_upper = list_excuses("MEETING")
    result_mixed = list_excuses("MeEtInG")
    assert result_lower == result_upper == result_mixed


#test for add excuse
def test_add_excuse_adds_new_item():
    #successfully add a new excuse to an existing category
    category = "general"
    new_excuse = "Aliens deleted my code."
    initial_len = len(EXCUSES[category])

    result = add_excuse(category, new_excuse)

    assert result == new_excuse
    assert len(EXCUSES[category]) == initial_len + 1
    assert new_excuse in EXCUSES[category]


def test_add_excuse_invalid_category_raises_error():
    #raise ValueError when category does not exist
    with pytest.raises(ValueError):
        add_excuse("nonsense", "This shouldn't work.")


def test_add_excuse_invalid_excuse_value_raises_error():
    #raise ValueError when excuse is empty, whitespace, or None
    with pytest.raises(ValueError):
        add_excuse("meeting", "")
    with pytest.raises(ValueError):
        add_excuse("meeting", "   ")
    with pytest.raises(ValueError):
        add_excuse("meeting", None)


def test_add_excuse_invalid_category_type_raises_error():
    #raise ValueError when category is not a string
    with pytest.raises(ValueError):
        add_excuse(123, "This should fail.")
    with pytest.raises(ValueError):
        add_excuse(["general"], "This should fail.")


def test_add_excuse_duplicate_not_added():
    #not increase the list length if excuse is repeated
    category = "class"
    existing_excuse = EXCUSES[category][0]
    initial_len = len(EXCUSES[category])

    result = add_excuse(category, existing_excuse)

    assert result == existing_excuse
    assert len(EXCUSES[category]) == initial_len

@pytest.mark.parametrize("bad", [123, 3.14, [], {}, None])
def test_get_excuse_invalid_category_type(bad):
    with pytest.raises((TypeError, ValueError, KeyError)):
        get_excuse(bad)

def test_add_excuse_trims_and_rejects_empty():
    with pytest.raises(ValueError):
        add_excuse("deadline", "   \t  ")

    trimmed = add_excuse("deadline", "  A real excuse  ")
    assert trimmed == "A real excuse"

def test_list_excuses_returns_deep_copy():
    data = list_excuses()
    # mutate returned structure
    some_cat = next(iter(data))
    data[some_cat].append("SHOULD NOT LEAK")
    # original should remain unchanged
    from excusegen.main import EXCUSES
    assert "SHOULD NOT LEAK" not in EXCUSES[some_cat]

def test_get_excuses_zero_returns_empty():
    assert get_excuses(count=0) == []

def test_get_excuses_negative_raises():
    with pytest.raises(ValueError):
        get_excuses(count=-1)

@pytest.mark.parametrize("k", [1, 2, 5, 10])
def test_get_excuses_count_length(k):
    res = get_excuses(count=k)
    assert isinstance(res, list)
    assert len(res) == k
    assert all(isinstance(x, str) and x.strip() for x in res)