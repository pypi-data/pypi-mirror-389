import csv
import random
from importlib.resources import files

_DATA_PKG = "eatnyc"
_DEFAULT_CSV = "data/nyc_restaurant_data.csv"

# columns we expect in the CSV
_REQUIRED_COLS = {"name", "cuisine", "neighborhood", "price", "rating", "sample_dish"}


# new function (NORMALIZE_ROWS)
def _normalize_row(row: dict) -> dict:
    # Clean up one CSV row: strip spaces, normalize case/types, compute helper fields.
    clean = {k.strip().lower(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}

    # rating → float (default 0.0)
    try:
        clean["rating"] = float(clean.get("rating", "") or 0.0)
    except ValueError:
        clean["rating"] = 0.0

    # cuisines list (split on / , ; | )
    raw_c = clean.get("cuisine", "")
    parts = []
    for sep in ["/", ",", ";", "|"]:
        raw_c = raw_c.replace(sep, " ")
    parts = [p for p in (w.strip().lower() for w in raw_c.split()) if p]
    clean["_cuisines"] = parts  # helper list for filtering

    # price normalize (e.g., $, $$, $$$)
    clean["price"] = (clean.get("price") or "").strip()

    return clean


# Load the NYC restaurant CSV into a list of dicts.
def load_data(path: str | None = None, validate: bool = True) -> list[dict]:

    # If `path` is None, loads the bundled file from eatnyc/data/.
    # Keys are lowercased; rating is converted to float.
    # Adds helper lists: `_cuisines`.
    if path is None:
        # use importlib.resources so this works from wheels/zip installs
        resource = files(_DATA_PKG) / _DEFAULT_CSV
        f = resource.open("r", encoding="utf-8", newline="")
    else:
        f = open(path, "r", encoding="utf-8", newline="")

    with f as fh:
        reader = csv.DictReader(fh)

        if validate:
            cols = {c.strip().lower() for c in (reader.fieldnames or [])}
            missing = _REQUIRED_COLS - cols
            if missing:
                raise ValueError(f"CSV missing required columns: {sorted(missing)}")

        return [_normalize_row(r) for r in reader]


def filter_restaurants(data, cuisine=None, neighborhood=None, price=None, min_rating=None, limit=None):

    # Error checking for empty or invalid data
    if not isinstance(data, list):
        raise TypeError("Data must be a list of dicts")

    if not data:
        return []

    results = []

    # Filtering logic
    for row in data:
        clean = _normalize_row(row)
        #Check cuisine match
        if cuisine:
            if cuisine.strip().lower() not in clean.get("_cuisines", []):
                continue
        #Check neighborhood match
        if neighborhood:
            if neighborhood.strip().lower() != row.get("neighborhood", "").lower():
                continue
        #Check price match
        if price:
            if price.strip() != clean.get("price", ""):
                continue
        if min_rating:
            try:
                min_rating_val = float(min_rating)
            except ValueError:
                raise ValueError("min_rating must be a number")
            if clean.get("rating", 0.0) < min_rating_val:
                continue

        results.append(row)
        #if its over the limit, break
        if limit:
            if len(results) >= limit:
                break
    return results


def top_n(data, n=5, sort_by="rating", descending=True):
    if not isinstance(data, list):
        raise TypeError("data must be a list of dicts")

    if not data:
        return []

    # normalize sort key to lower-case to match load_data normalization
    sort_key = (sort_by or "").strip().lower()
    if not sort_key:
        raise ValueError("sort_by must be a non-empty string")

    # validate the key exists in at least one row; otherwise error for clarity
    if all((sort_key not in row) for row in data if isinstance(row, dict)):
        raise KeyError(f"sort_by key not found in data rows: '{sort_key}'")

    def key_func(row):
        # Missing keys sort as None -> treated as smallest when descending=False, largest when descending=True
        value = row.get(sort_key)
        # Ensure consistent comparison for mixed types
        if isinstance(value, (int, float)):
            return value
        return ("" if value is None else str(value).lower())

    try:
        sorted_rows = sorted(
            (r for r in data if isinstance(r, dict)),
            key=key_func,
            reverse=bool(descending),
        )
    except TypeError:
        # Fallback: convert all keys to string for sorting if mixed incomparable types
        sorted_rows = sorted(
            (r for r in data if isinstance(r, dict)),
            key=lambda r: str(r.get(sort_key, "")),
            reverse=bool(descending),
        )

    if n is None:
        return sorted_rows
    if not isinstance(n, int) or n < 0:
        raise ValueError("n must be a non-negative integer or None")
    return sorted_rows[:n]


def sample_dish(cuisine=None, seed=None):
    '''
    Return a random restaurant with its sample dish recommendation.
    '''
    if seed is not None:
        random.seed(seed)

    # Load the restaurant data
    data = load_data()

    # Filter by cuisine if provided
    if cuisine:
        cuisine_lower = cuisine.strip().lower()
        filtered = [
            row for row in data
            if cuisine_lower in row.get("_cuisines", [])
        ]

        # Filter out entries without a sample_dish
        with_dishes = [
            row for row in filtered
            if row.get("sample_dish", "").strip()
        ]

        if not with_dishes:
            # Get all available cuisines
            all_cuisines = set()
            for row in data:
                all_cuisines.update(row.get("_cuisines", []))

            # Suggest some alternatives (random 3-5 cuisines)
            suggestions = random.sample(sorted(all_cuisines), min(5, len(all_cuisines)))

            return {
                "error": f"No restaurants found for cuisine '{cuisine}'",
                "suggestions": suggestions,
                "message": "Maybe try these instead?"
            }
    else:
        # No cuisine specified, use all restaurants
        with_dishes = [
            row for row in data
            if row.get("sample_dish", "").strip()
        ]

        if not with_dishes:
            return None

    return random.choice(with_dishes)


def format_card(row, style="ascii", width=60, show_dish=True):
    name = str(row.get("name", "") or "").strip()
    cuisine = str(row.get("cuisine", "") or "").strip()
    neighborhood = str(row.get("neighborhood", "") or "").strip()
    price = str(row.get("price", "") or "").strip()

    try:
        rating = float(row.get("rating", 0.0))
    except (TypeError, ValueError):
        rating = 0.0

    sample = str(row.get("sample_dish", "") or "").strip()

    title_line = name if name else "(unknown)"
    sub_line = f"{cuisine}, {neighborhood}".strip(", ").strip()
    meta_line = f"Rating: {rating:.1f}   Price: {price}".strip()
    dish_line = f"Dish: {sample}" if (show_dish and sample) else ""

    if style.lower() == "markdown":
        body = f"**{title_line}** — *{sub_line}*\n{meta_line}"
        if dish_line:
            body += f"\n{dish_line}"
        return body

    def _wrap_line(line: str, inner_width: int):
        if not line:
            return [""]
        words = line.split()
        out, cur = [], ""
        for w in words:
            if not cur:
                cur = w
            elif len(cur) + 1 + len(w) <= inner_width:
                cur += " " + w
            else:
                out.append(cur)
                cur = w
        if cur:
            out.append(cur)
        return out

    box_width = max(24, int(width) if isinstance(width, int) else 48)
    inner = box_width - 2

    logical_lines = [f"{title_line}  ({sub_line})" if sub_line else title_line, meta_line, dish_line]

    wrapped = []
    for ln in logical_lines:
        wrapped.extend(_wrap_line(ln, inner) if ln else [""])

    top = "+" + "-" * (box_width - 2) + "+"
    content = "\n".join("|" + (ln.ljust(inner)) + "|" for ln in wrapped if ln is not None)
    bottom = top

    return f"{top}\n{content}\n{bottom}"


def cli(argv=None):
    import argparse
    # Simple command-line entrypoint:
    #   $ eatnyc            -> prints top 5 by rating
    #   $ eatnyc -n 10      -> prints top 10
    #   $ eatnyc --sort name --asc -> sort by name ascending

    parser = argparse.ArgumentParser(prog="eatnyc", description="NYC restaurant recommender")
    parser.add_argument("-n", "--n", type=int, default=5, help="number of results")
    parser.add_argument("--sort", default="rating", help="field to sort by (rating, name, price, etc.)")
    parser.add_argument("--asc", action="store_true", help="sort ascending (default is descending)")
    args = parser.parse_args(argv)

    data = load_data()
    results = top_n(data, n=args.n, sort_by=args.sort, descending=not args.asc)
    for r in results:
        print(f"{r['name']} | {r['cuisine']} | {r['price']} | ★{r['rating']} | {r.get('sample_dish', '')}")
