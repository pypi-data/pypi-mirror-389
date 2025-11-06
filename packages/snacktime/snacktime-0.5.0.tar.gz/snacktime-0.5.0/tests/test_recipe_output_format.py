from snacktime import recipe_salad

def test_recipe_has_sections_and_trailing_newline():
    out = recipe_salad(serves=1, dressing="lemon")
    assert "Simple Green Salad" in out
    assert "Ingredients" in out and "Steps" in out
    assert out.endswith("\n"), "Expect trailing newline for nice CLI printing"
    for n in ("1)", "2)", "3)"):
        assert n in out


#ensure formatted & readable recipe