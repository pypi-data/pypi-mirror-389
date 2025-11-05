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
Replace 0.1.0 with your latest version number (see pyproject.toml)
```bash
pipenv install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple eatnyc==0.1.0
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
