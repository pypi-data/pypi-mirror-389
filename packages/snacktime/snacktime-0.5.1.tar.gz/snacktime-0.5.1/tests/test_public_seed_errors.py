import pytest
from snacktime import random_snack, random_vegetable, random_treat

BAD_SEEDS = [True, False, 3.14, "1", object()]

@pytest.mark.parametrize("func", [random_snack, random_vegetable, random_treat])
@pytest.mark.parametrize("bad", BAD_SEEDS)
def test_public_random_functions_reject_bad_seed(func, bad):
    with pytest.raises(TypeError):
        func(seed=bad)
        
#raise TypeError if non-int/non-None seed