import pytest
from eatnyc import top_n


def _sample_data():
    return [
        {"name": "B", "cuisine": "X", "neighborhood": "N1", "price": "$$", "rating": 4.2, "sample_dish": "d1"},
        {"name": "A", "cuisine": "Y", "neighborhood": "N2", "price": "$$$", "rating": 4.8, "sample_dish": "d2"},
        {"name": "C", "cuisine": "Z", "neighborhood": "N3", "price": "$", "rating": 3.9, "sample_dish": "d3"},
        {"name": "D", "cuisine": "Y", "neighborhood": "N2", "price": "$$$", "rating": 4.8, "sample_dish": "d4"},
    ]


def test_top_n_default_rating_desc():
    data = _sample_data()
    result = top_n(data, n=2)
    assert len(result) == 2
    # default: sort_by="rating", descending=True
    assert [r["name"] for r in result] == ["A", "D"]


def test_top_n_sort_by_name_ascending_all():
    data = _sample_data()
    result = top_n(data, n=None, sort_by="name", descending=False)
    assert [r["name"] for r in result] == ["A", "B", "C", "D"]


def test_top_n_n_zero_returns_empty():
    data = _sample_data()
    result = top_n(data, n=0)
    assert result == []


def test_top_n_invalid_params_raise():
    data = _sample_data()
    # invalid n
    try:
        top_n(data, n=-1)
        assert False, "expected ValueError"
    except ValueError:
        pass

    # missing key
    try:
        top_n(data, sort_by="does_not_exist")
        assert False, "expected KeyError"
    except KeyError:
        pass


