import pytest
from snacktime import random_snack

class Tests:
    def test_random_snack_deterministic(self):
        assert random_snack(seed=1) == random_snack(seed=1)

    def test_random_snack_membership(self):
        s = random_snack(seed=2)
        assert isinstance(s, str) and len(s) > 0

    def test_random_snack_varies_with_seed(self):
        # Over multiple seeds we should see at least 2 distinct results
        results = {random_snack(seed=i) for i in range(10)}
        assert len(results) >= 2
