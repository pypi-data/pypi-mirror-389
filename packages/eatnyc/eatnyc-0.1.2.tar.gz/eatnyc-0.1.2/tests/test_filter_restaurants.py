import pytest
from eatnyc import filter_restaurants


#Standard Sample Data
def _sample_data():
    return [
        {"name": "B", "cuisine": "X", "neighborhood": "N1", "price": "$$", "rating": 4.2, "sample_dish": "d1"},
        {"name": "A", "cuisine": "Y", "neighborhood": "N2", "price": "$$$", "rating": 4.8, "sample_dish": "d2"},
        {"name": "C", "cuisine": "Z", "neighborhood": "N3", "price": "$", "rating": 3.9, "sample_dish": "d3"},
        {"name": "D", "cuisine": "Y", "neighborhood": "N2", "price": "$$$", "rating": 4.8, "sample_dish": "d4"},
    ]

#test case for cuisine filter
def test_filter_restaurants_cuisine():
    data = _sample_data()
    result = filter_restaurants(data, cuisine="Y")
    assert [r["cuisine"] for r in result] == ["Y", "Y"]

#test case for neighborhood filter
def test_filter_restaurants_neighborhood():
    data = _sample_data()
    result = filter_restaurants(data, neighborhood="N2")
    assert [r["neighborhood"] for r in result] == ["N2", "N2"]

#test case for price filter
def test_filter_restaurants_price():
    data = _sample_data()
    result = filter_restaurants(data, price="$$$")
    assert [r["price"] for r in result] == ["$$$", "$$$"]

#test case for minimum rating filter
def test_filter_restaurants_min_rating():
    data = _sample_data()
    result = filter_restaurants(data, min_rating=4.5)
    assert [r["rating"] for r in result] == [4.8, 4.8]

#test case for sorting by name
def test_filter_restaurants_limit():
    data = _sample_data()
    result = filter_restaurants(data, limit=2)
    assert len(result) == 2
# test case for sorting by name
def test_filter_restaurants_no_matches():
    data = _sample_data()
    result = filter_restaurants(data, cuisine="Nonexistent")
    assert result == []



