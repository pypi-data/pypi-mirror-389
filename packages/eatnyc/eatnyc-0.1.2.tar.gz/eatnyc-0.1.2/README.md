# Python Package Exercise

An exercise to create a Python package, build it, test it, distribute it, and use it. See [instructions](./instructions.md) for details.

# eatnyc - NYC Restaurant Recommender
![Build and Test](https://github.com/swe-students-fall2025/3-python-package-team_avalon/actions/workflows/build.yaml/badge.svg)

**eatnyc** is a lightweight Python package that recommends top-rated NYC restaurants based on cuisine, neighborhood, price, and rating.  
It’s designed to help users explore the city’s dining scene and discover great places through data-driven recommendations — directly from the command line or in Python.

---

## How to install and use this package
### Option 1: Try it from **TestPyPI** (current test version)
You can try out the latest build of eatnyc from the [TestPyPI](https://test.pypi.org/project/eatnyc/) repository. 

1. **Create and Activate a virtual environment**
```bash
pipenv --python 3.11
pipenv shell
```
2. **Install from TestPyPI**
Replace 0.1.1 with your latest version number (see pyproject.toml)
```bash
pipenv install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple eatnyc==0.1.1
```
For now: The --extra-index-url flag ensures dependencies are installed from the real PyPI, while your package is pulled from TestPyPI

3. **Run the package**
You can use eatnyc either as a CLI app or a Python module.

#### Command line:
```bash
eatnyc -n 5 --sort rating
```
#### Python module:
```bash
python -m eatnyc
```
---
### Example Program
```python
from eatnyc import load_data, filter_restaurants, top_n, sample_dish, format_card

data = load_data()

# Filter restaurants by cuisine and neighborhood
italian_manhattan = filter_restaurants(
    data,
    cuisine="Italian",
    neighborhood="Manhattan",
    min_rating=4.0
)

# Get top 5 restaurants by rating
best = top_n(data, n=5, sort_by="rating")

# Show a sample dish recommendation
print(sample_dish(cuisine="Japanese"))

# Print formatted cards
for r in best:
    print(format_card(r, style="ascii", width=48))
```
Run the example:
```bash
pipenv run python examples/demo.py
```

## Function Documentation

### `load_data(path=None, validate=True)`
Loads NYC restaurant data from CSV file.

**Parameters:**
- `path` (str, optional): Path to CSV file. If `None`, loads bundled data file.
- `validate` (bool, default=True): Whether to validate required columns.

**Returns:**
- `list[dict]`: List of restaurant dictionaries with normalized fields (lowercase keys, float ratings).

**Example:**
```python
data = load_data()  # Load bundled data
data = load_data("custom.csv")  # Load custom file
```

### `filter_restaurants(data, cuisine=None, neighborhood=None, price=None, min_rating=None, limit=None)`
Filters restaurants based on multiple criteria.

**Parameters:**
- `data` (list): List of restaurant dictionaries (from `load_data()`).
- `cuisine` (str, optional): Filter by cuisine type.
- `neighborhood` (str, optional): Filter by neighborhood.
- `price` (str, optional): Filter by price range (e.g., "$", "$$", "$$$").
- `min_rating` (float, optional): Minimum rating threshold.
- `limit` (int, optional): Maximum number of results to return.

**Returns:**
- `list[dict]`: Filtered list of restaurant dictionaries.

**Example:**
```python
italian = filter_restaurants(data, cuisine="Italian", min_rating=4.5, limit=10)
```

### `top_n(data, n=5, sort_by="rating", descending=True)`
Returns top N restaurants sorted by a specified field.

**Parameters:**
- `data` (list): List of restaurant dictionaries.
- `n` (int, default=5): Number of results to return. Use `None` for all results.
- `sort_by` (str, default="rating"): Field to sort by (e.g., "rating", "name", "price").
- `descending` (bool, default=True): Whether to sort in descending order.

**Returns:**
- `list[dict]`: Top N restaurants sorted by the specified field.

**Example:**
```python
top_5 = top_n(data, n=5, sort_by="rating", descending=True)
top_10_by_price = top_n(data, n=10, sort_by="price", descending=False)
```

### `sample_dish(cuisine=None, seed=None)`
Returns a random restaurant with a sample dish recommendation.

**Parameters:**
- `cuisine` (str, optional): Filter by cuisine type. If `None`, returns any restaurant.
- `seed` (int, optional): Random seed for reproducible results.

**Returns:**
- `dict` or `None`: Restaurant dictionary with sample dish, or `None` if no matches.
- If cuisine not found, returns dict with `error`, `suggestions`, and `message` keys.

**Example:**
```python
random_dish = sample_dish()  # Any restaurant
italian_dish = sample_dish(cuisine="Italian", seed=42)  # Reproducible
```

### `format_card(row, style="ascii", width=60, show_dish=True)`
Formats a restaurant dictionary as a display card.

**Parameters:**
- `row` (dict): Restaurant dictionary (from `load_data()` or filter functions).
- `style` (str, default="ascii"): Display style - "ascii" for box format, "markdown" for markdown.
- `width` (int, default=60): Card width in characters (minimum 24).
- `show_dish` (bool, default=True): Whether to include sample dish in output.

**Returns:**
- `str`: Formatted card string.

**Example:**
```python
card = format_card(restaurant, style="ascii", width=48)
print(card)
```

**See the complete example program:** [examples/demo.py](examples/demo.py) - demonstrates all functions working together.

## How to Run Unit Tests
Simple unit tests are included in the 'tests' directory. To run them:
1. **Install 'pytest' inside your virtual environment:**
```bash
pipenv install pytest
```
2. **Run the tests from project root:**
```bash
python3 -m pytest
```
3. All tests should pass. Any failed test indicates that the package code is behaving differently from the expected results.

### Option 2: Install from PyPI (for users)
```bash
pip install eatnyc
```
### Install locally (for developers)
```bash
pipenv install -e .
```
If that set up fails for you, use:
```bash
python3 -m pipenv install -e .
```

## Developer Mode Switch (using Makefile)

```bash
make dev-on      # install editable
make dev-off     # restore TestPyPI version
make verify      # confirm path
```

# Developer Workflow (Building & Publishing)
If you modify the code and want to publish a new version to TestPyPI, follow these steps:
```bash
#1. CLEAN old build artifacts
rm -rf dist build src/*.egg-info
pipenv install build

#2. BUMP version number in pyproject.toml (e.g., 0.1.0 → 0.1.1)

#3. BUILD the package
pipenv run python -m build

#4. UPLOAD new version to TestPyPI
pipenv install twine
pipenv run twine upload -r testpypi dist/*
```
5. REINSTALL to test it:
```bash
pipenv run pip uninstall -y eatnyc
pipenv install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple eatnyc==0.1.1
```
6. Once final, UPLOAD to real PyPI (final version) with:
```bash
pipenv run twine upload dist/*
```
--- 
## Project Links
- **PyPI:** [https://pypi.org/project/eatnyc](https://pypi.org/project/eatnyc)
- **TestPyPI:** [https://test.pypi.org/project/eatnyc](https://test.pypi.org/project/eatnyc)
- **Github Repo:** [https://github.com/swe-students-fall2025/3-python-package-team_avalon.git](https://github.com/swe-students-fall2025/3-python-package-team_avalon.git)

# Contributors
- [amiraadum](https://github.com/amiraadum)
- [Ivan-Wang-tech](https://github.com/Ivan-Wang-tech)
- [hyunkyuu](https://github.com/hyunkyuu)
- [jmo7728](https://github.com/jmo7728)
- [lilyluo7412](https://github.com/lilyluo7412)
