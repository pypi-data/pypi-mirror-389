import pytest
from snacktime import random_treat

class Tests:
    def test_random_treat_deterministic(self):
        assert random_treat(seed=20) == random_treat(seed=20), "Expected same result for same seed"

    def test_random_treat_is_string(self):
        t = random_treat(seed=21)
        assert isinstance(t, str) and len(t) > 0, "Expected nonempty string"

    def test_random_treat_varies_with_seed(self):
        assert random_treat(seed=22) != random_treat(seed=23), "Expected different result for different seed"
