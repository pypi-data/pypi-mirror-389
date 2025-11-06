import re
import snacktime

def test_version_semver_like():
    assert isinstance(snacktime.__version__, str)
    assert re.match(r"^\d+\.\d+\.\d+$", snacktime.__version__)

def test_all_exports():
    for name in ["random_snack", "random_vegetable", "random_treat", "recipe_salad"]:
        assert name in snacktime.__all__

#semantic version expected