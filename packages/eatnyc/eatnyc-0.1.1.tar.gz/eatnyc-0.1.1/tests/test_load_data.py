import pytest
from eatnyc import load_data

def test_load_data_returns_list_and_dicts():
    #load_data should return a nonempty list of dicts with expected keys
    data = load_data()
    assert isinstance(data, list)
    assert data, "Dataset should not be empty"
    first = data[0]
    assert isinstance(first, dict)
    for key in ["name", "cuisine", "neighborhood", "price", "rating", "sample_dish"]:
        assert key in first

def test_load_data_missing_file_raises():
    #specifying a nonexistent path should raise FileNotFoundError.
    with pytest.raises(FileNotFoundError):
        load_data(path="does_not_exist.csv")

def test_load_data_missing_required_columns(tmp_path):
    #if a CSV lacks required columns, load_data(validate=True) raises ValueError.
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("name,rating\nExample,4.5\n", encoding="utf-8")

    with pytest.raises(ValueError) as e:
        load_data(path=str(bad_csv), validate=True)

    #must mention at least one of the other required columns
    assert any(k in str(e.value) for k in ["cuisine","neighborhood","price","sample_dish"])

def test_load_data_normalizes_fields(tmp_path):
    #normalization: rating -> float, cuisines tokenized, price trimmed.
    csv_text = (
        "name,cuisine,neighborhood,price,rating,sample_dish\n"
        "Foo,\"Italian/ Pizza ; Pasta\",SoHo, $$ ,4.7,Margherita\n"
    )
    good_csv = tmp_path / "good.csv"
    good_csv.write_text(csv_text, encoding="utf-8")

    data = load_data(path=str(good_csv), validate=True)
    row = data[0]

    #rating parsed to float
    assert isinstance(row["rating"], float) and row["rating"] == 4.7

    #cuisines split & lowercased
    assert all(c in row["_cuisines"] for c in ["italian", "pizza", "pasta"])

    #price trimmed (e.g., "$$")
    assert row["price"] == "$$"