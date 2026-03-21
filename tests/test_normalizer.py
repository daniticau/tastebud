from tastebud.services.normalizer import normalize_city, normalize_name


class TestNormalizeName:
    def test_basic_lowercase(self):
        assert normalize_name("Sab E Lee") == "sab e lee"

    def test_strip_possessive(self):
        assert normalize_name("Joe's Pizza") == "joe pizza"

    def test_strip_curly_possessive(self):
        assert normalize_name("Bob\u2019s Grill") == "bob"

    def test_remove_suffix_restaurant(self):
        assert normalize_name("Thai Kitchen Restaurant") == "thai kitchen"

    def test_remove_suffix_cafe(self):
        assert normalize_name("Morning Glory Cafe") == "morning glory"

    def test_remove_multiple_suffixes(self):
        assert normalize_name("Bob's Bar Grill") == "bob"

    def test_strip_address_on_ordinal(self):
        assert normalize_name("Sab E Lee on 5th") == "sab e lee"

    def test_strip_address_at_street(self):
        assert normalize_name("Pizza Place at Main St") == "pizza place"

    def test_collapse_whitespace(self):
        assert normalize_name("  Extra   Spaces  ") == "extra spaces"

    def test_remove_punctuation(self):
        assert normalize_name("Mama's Bakery & Cafe") == "mama bakery"

    def test_preserve_hyphens(self):
        assert normalize_name("Crack-Shack") == "crack-shack"

    def test_empty_string(self):
        assert normalize_name("") == ""

    def test_all_caps(self):
        assert normalize_name("TACOS EL GORDO") == "tacos el gordo"


class TestNormalizeCity:
    def test_basic(self):
        assert normalize_city("San Diego") == "san diego"

    def test_strip_state(self):
        assert normalize_city("San Diego, CA") == "san diego"

    def test_strip_full_state(self):
        assert normalize_city("San Diego, California") == "san diego"

    def test_whitespace(self):
        assert normalize_city("  Los Angeles  ") == "los angeles"

    def test_empty(self):
        assert normalize_city("") == ""
