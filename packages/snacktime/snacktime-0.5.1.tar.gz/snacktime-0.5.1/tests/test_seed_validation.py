import pytest
from snacktime.core import _normalize_seed
from snacktime import recipe_salad

def test_seed_accepts_int_and_none():
    assert _normalize_seed(42) == 42
    assert _normalize_seed(None) is None

@pytest.mark.parametrize("bad", [True, False, 3.14, "7", object()])
def test_seed_rejects_others(bad):
    with pytest.raises(TypeError):
        _normalize_seed(bad)

@pytest.mark.parametrize("n", [1, 2, 4])
def test_recipe_quantities_scale(n):
    out = recipe_salad(serves=n, dressing="lemon")
    assert f"Serves: {n}" in out
    assert f"- {2*n} cups mixed greens" in out
    assert f"- {n} cup chopped vegetables" in out
    assert f"- {2*n} tbsp nuts or seeds" in out

#ormalize_seed should accept int/None & other types raise typeError; recpite quantiity follows serve argument