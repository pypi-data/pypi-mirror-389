import pytest
from snacktime import recipe_salad

def test_recipe_invalid_serves_raises_valueerror():
    with pytest.raises(ValueError):
        recipe_salad(serves=0, dressing="lemon")

def test_recipe_invalid_dressing_raises_valueerror():
    with pytest.raises(ValueError):
        recipe_salad(serves=1, dressing="ranch")

#reject invalid input values