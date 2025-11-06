from snacktime.core import _SNACKS, _VEGETABLES, _TREATS
from snacktime import random_snack, random_vegetable, random_treat

def test_random_outputs_are_from_defined_sets():
    assert random_snack(seed=3) in _SNACKS
    assert random_vegetable(seed=4) in _VEGETABLES
    assert random_treat(seed=5) in _TREATS

#ensure pulled froom list created