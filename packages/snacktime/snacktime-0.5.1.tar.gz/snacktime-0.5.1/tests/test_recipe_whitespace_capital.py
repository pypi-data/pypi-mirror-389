import pytest
from snacktime import recipe_salad

@pytest.mark.parametrize("txt,expected", [
    ("LEMON", "lemon"),
    ("  Lemon  ", "lemon"),
    ("bAlSaMiC", "balsamic"),
    ("  olive", "olive"),
])
def test_dressing_accepts_case_and_whitespace(txt, expected):
    out = recipe_salad(serves=2, dressing=txt)
    assert expected in out.lower()

#case insensitive