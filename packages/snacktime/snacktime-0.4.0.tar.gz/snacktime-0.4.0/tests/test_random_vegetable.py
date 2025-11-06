import pytest
from snacktime import random_vegetable

class Tests:
    def test_random_vegetable_deterministic(self):
        assert random_vegetable(seed=10) == random_vegetable(seed=10)

    def test_random_vegetable_is_string(self):
        v = random_vegetable(seed=11)
        assert isinstance(v, str) and len(v) > 0

    def test_random_vegetable_varies_with_seed(self):
        assert random_vegetable(seed=12) != random_vegetable(seed=13)
