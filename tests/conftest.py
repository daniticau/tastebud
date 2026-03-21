import pytest


@pytest.fixture
def sample_place_names():
    """Common test cases for place name normalization."""
    return [
        ("Joe's Pizza", "joe pizza"),
        ("JOES PIZZA", "joes pizza"),
        ("Thai Kitchen Restaurant", "thai kitchen"),
        ("Sab E Lee on 5th St.", "sab e lee"),
        ("Mama's Bakery & Cafe", "mama bakery"),
        ("The Taco Stand", "the taco stand"),
        ("  Extra Spaces  ", "extra spaces"),
        ("Bob\u2019s Grill", "bob"),
        ("", ""),
    ]
