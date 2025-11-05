import pytest
from eatnyc.core import sample_dish, load_data


def test_sample_dish_returns_restaurant():
    """Test that sample_dish returns a restaurant dict"""
    result = sample_dish(seed=42)
    assert result is not None
    assert isinstance(result, dict)
    assert "name" in result
    assert "sample_dish" in result


def test_sample_dish_with_cuisine_filter():
    """Test that sample_dish filters by cuisine correctly"""
    result = sample_dish(cuisine="Italian", seed=42)
    assert result is not None
    assert isinstance(result, dict)
    # Check that it's actually Italian cuisine
    assert "italian" in result.get("_cuisines", [])


def test_sample_dish_has_dish():
    """Test that returned restaurant has a sample_dish"""
    result = sample_dish(seed=42)
    assert result is not None
    dish = result.get("sample_dish", "").strip()
    assert dish != ""


def test_sample_dish_reproducible_with_seed():
    """Test that same seed produces same result"""
    result1 = sample_dish(cuisine="Italian", seed=123)
    result2 = sample_dish(cuisine="Italian", seed=123)

    # Both should return same restaurant
    assert result1.get("name") == result2.get("name")


def test_sample_dish_invalid_cuisine():
    """Test that invalid cuisine returns error with suggestions"""
    result = sample_dish(cuisine="InvalidCuisine123", seed=42)

    assert isinstance(result, dict)
    assert "error" in result
    assert "suggestions" in result
    assert "message" in result
    assert result["message"] == "Maybe try these instead?"
    assert isinstance(result["suggestions"], list)
    assert len(result["suggestions"]) > 0


def test_sample_dish_no_cuisine():
    """Test that no cuisine parameter returns any restaurant"""
    result = sample_dish(seed=42)
    assert result is not None
    assert isinstance(result, dict)
    assert "name" in result


def test_sample_dish_cuisine_case_insensitive():
    """Test that cuisine filter is case-insensitive"""
    result1 = sample_dish(cuisine="italian", seed=42)
    result2 = sample_dish(cuisine="ITALIAN", seed=42)
    result3 = sample_dish(cuisine="Italian", seed=42)

    # All should return the same result with same seed
    assert result1.get("name") == result2.get("name")
    assert result2.get("name") == result3.get("name")


@pytest.mark.parametrize("cuisine", ["Mexican", "French", "American", "Greek"])
def test_sample_dish_various_cuisines(cuisine):
    """Test that sample_dish works with different cuisines"""
    result = sample_dish(cuisine=cuisine, seed=42)
    assert result is not None
    assert isinstance(result, dict)
    assert cuisine.lower() in result.get("_cuisines", [])


@pytest.fixture
def sample_data():
    """Fixture to load data once for multiple tests"""
    return load_data()


def test_sample_dish_returns_from_actual_data(sample_data):
    """Test that sample_dish returns data from the loaded dataset"""
    result = sample_dish(seed=42)
    assert result is not None
    # Check that the result exists in the actual data
    names = [row.get("name") for row in sample_data]
    assert result.get("name") in names
