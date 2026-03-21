import re


_SUFFIXES = {
    "restaurant", "cafe", "café", "bar", "grill",
    "eatery", "bistro", "pizzeria", "diner", "pub", "tavern",
    "shack", "spot",
}

_ADDRESS_PATTERN = re.compile(
    r"\b(on|at|off|near)\s+\w+\s+(st|street|ave|avenue|blvd|boulevard|rd|road|dr|drive|way|ln|lane|ct|court)\b",
    re.IGNORECASE,
)

_ORDINAL_PATTERN = re.compile(
    r"\b(on|at)\s+\d+(st|nd|rd|th)\b",
    re.IGNORECASE,
)


def normalize_name(name: str) -> str:
    """Normalize a restaurant name for deduplication.

    Pipeline: lowercase → strip possessives → remove punctuation →
    collapse whitespace → remove common suffixes → strip address fragments.
    """
    if not name:
        return ""

    s = name.lower()

    # Strip possessives
    s = s.replace("'s", "").replace("\u2019s", "")

    # Remove punctuation except hyphens
    s = re.sub(r"[^\w\s-]", "", s)

    # Strip address fragments ("on 5th", "at main st")
    s = _ORDINAL_PATTERN.sub("", s)
    s = _ADDRESS_PATTERN.sub("", s)

    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()

    # Remove common suffixes (only if they're the last word)
    words = s.split()
    while words and words[-1] in _SUFFIXES:
        words.pop()

    return " ".join(words) if words else s


def normalize_city(city: str) -> str:
    """Normalize a city name: lowercase, strip state suffixes."""
    if not city:
        return ""

    s = city.lower().strip()

    # Strip state suffixes like ", CA" or ", California"
    s = re.sub(r",\s*\w{2,}$", "", s)

    return s.strip()
