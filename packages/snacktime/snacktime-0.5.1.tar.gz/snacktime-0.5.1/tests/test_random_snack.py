import pytest
from snacktime import random_snack

class Tests:
    def test_random_snack_deterministic(self):
        assert random_snack(seed=1) == random_snack(seed=1)

    def test_random_snack_membership(self):
        s = random_snack(seed=2)
        assert isinstance(s, str) and len(s) > 0

    def test_random_snack_varies_with_seed(self):
        seeds = range(10, 30)
        values = [random_snack(seed=s) for s in seeds]
        assert len(set(values)) > 1
