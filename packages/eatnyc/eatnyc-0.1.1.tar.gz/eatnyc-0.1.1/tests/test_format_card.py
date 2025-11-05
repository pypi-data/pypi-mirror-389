import pytest
from eatnyc import format_card

# Reusable sample restaurant row
@pytest.fixture
def row():
    return {
        "name": "Joe's Pizza",
        "cuisine": "italian",
        "neighborhood": "Manhattan",
        "price": "$",
        "rating": 4.5,
        "sample_dish": "Classic cheese slice",
    }

# Test ASCII rendering at multiple widths, including min-width clamp
@pytest.mark.parametrize(
    "width, expected_width",
    [
        (60, 60),  # normal width
        (40, 40),  # medium width
        (10, 24),  # smaller than minimum -> should clamp to 24
    ],
)
def test_ascii_box_width(row, width, expected_width):
    output = format_card(row, width=width)
    top_line = output.splitlines()[0]
    bottom_line = output.splitlines()[-1]

    assert len(top_line) == expected_width
    assert top_line == bottom_line  # top and bottom frame match

    # Each inner line must be within the width and framed by | |
    for line in output.splitlines()[1:-1]:
        assert line.startswith("|") and line.endswith("|")
        assert len(line) <= expected_width

# Test markdown format and dish toggle
@pytest.mark.parametrize("show_dish, expected_contains", [(True, True), (False, False)])
def test_markdown_format(row, show_dish, expected_contains):
    md = format_card(row, style="markdown", show_dish=show_dish)

    assert "**Joe's Pizza**" in md       # bold title
    assert "*italian, Manhattan*" in md  # italic subtitle
    assert "Rating: 4.5" in md
    assert "Price: $" in md

    assert ("Dish:" in md) is expected_contains

# Test error on invalid input type
def test_invalid_input_type_error():
    # format_card expects a dict; passing wrong type should raise
    with pytest.raises(AttributeError):
        format_card(None)

    with pytest.raises(AttributeError):
        format_card(["not", "a", "dict"])
