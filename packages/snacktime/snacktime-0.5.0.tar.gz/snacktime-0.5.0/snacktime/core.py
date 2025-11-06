from typing import Optional, Sequence
import random
import textwrap

def _normalize_seed(seed: Optional[int]) -> Optional[int]:
    """Accept only int or None; raise on other types."""
    if seed is None:
        return None
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an int or None")
    return seed

_SNACKS: Sequence[str] = (
    "pretzels", "popcorn", "granola bar", "apple slices", "yogurt cup",
    "cheese & crackers", "trail mix", "rice cakes", "hummus & pita"
)

_VEGETABLES: Sequence[str] = (
    "carrot", "cucumber", "spinach", "kale", "broccoli",
    "bell pepper", "tomato", "celery", "edamame"
)

_TREATS: Sequence[str] = (
    "chocolate chip cookie", "brownie bite", "gummy bears",
    "ice cream scoop", "cupcake", "churro", "donut hole"
)

def random_snack(seed: Optional[int] = None) -> str:
    seed = _normalize_seed(seed)
    rng = random.Random(seed) if seed is not None else random.Random()
    return rng.choice(_SNACKS)

def random_vegetable(seed: Optional[int] = None) -> str:
    seed = _normalize_seed(seed)
    rng = random.Random(seed) if seed is not None else random.Random()
    return rng.choice(_VEGETABLES)

def random_treat(seed: Optional[int] = None) -> str:
    seed = _normalize_seed(seed)
    rng = random.Random(seed) if seed is not None else random.Random()
    return rng.choice(_TREATS)

def recipe_salad(serves: int = 1, dressing: str = "lemon") -> str:
    """
    Return a simple salad recipe as a formatted string.
    Args:
        serves: number of servings (must be >= 1)
        dressing: 'lemon' | 'balsamic' | 'olive'
    """
    if serves < 1:
        raise ValueError("serves must be >= 1")
    dressing = dressing.lower().strip()
    if dressing not in {"lemon", "balsamic", "olive"}:
        raise ValueError("dressing must be 'lemon', 'balsamic', or 'olive'")

    base = textwrap.dedent(f"""
    Simple Green Salad
    Serves: {serves}

    Ingredients
    ----------
    - {2*serves} cups mixed greens
    - {serves} cup chopped vegetables (e.g., cucumber, tomato, carrot)
    - {serves*2} tbsp nuts or seeds (optional)
    - Salt & pepper to taste
    """).strip()

    if dressing == "lemon":
        d = f"- Dressing: {serves*2} tbsp olive oil, {serves} tbsp lemon juice, pinch of salt"
    elif dressing == "balsamic":
        d = f"- Dressing: {serves*2} tbsp olive oil, {serves} tbsp balsamic vinegar, pinch of salt"
    else:  # olive
        d = f"- Dressing: {serves*2} tbsp olive oil, {serves} tsp red wine vinegar (optional), pinch of salt"

    steps = textwrap.dedent("""
    Steps
    -----
    1) Toss greens and chopped veggies in a bowl.
    2) Whisk dressing separately, then drizzle over salad.
    3) Sprinkle nuts/seeds. Season with salt & pepper. Toss and serve.
    """).strip()

    return f"{base}\n{d}\n\n{steps}\n"
