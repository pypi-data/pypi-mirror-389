# 🥗 snacktime 

**Build & Tests**  
Python 3.09  ![Python 3.09](https://github.com/swe-students-fall2025/3-python-package-team_solace/actions/workflows/pr_test.yaml/badge.svg?branch=pipfile-experiment&label=Python%203.09)  
Python 3.10  ![Python 3.10](https://github.com/swe-students-fall2025/3-python-package-team_solace/actions/workflows/pr_test.yaml/badge.svg?branch=pipfile-experiment&label=Python%203.10)  
Python 3.11  ![Python 3.11](https://github.com/swe-students-fall2025/3-python-package-team_solace/actions/workflows/pr_test.yaml/badge.svg?branch=pipfile-experiment&label=Python%203.11)  



A lightweight and fun Python package that helps you pick a **random snack**, **vegetable**, **sweet treat**, or even generate a **simple salad recipe**.  
Originally created as part of the Software Engineering Fall 2025 team project — this package demonstrates Python packaging, publishing, and CI automation.

---

## 📦 PyPI Project

🔗 **Link:** [https://pypi.org/project/snacktime/](https://pypi.org/project/snacktime/)  

---

## 🚀 Installation

You can install directly from PyPI using pip:

```bash
pip install snacktime
```

---

## 🧩 Usage

Once installed, simply import and call any of the available functions:

```python
import snacktime

print(snacktime.random_snack())
print(snacktime.random_vegetable())
print(snacktime.random_treat())
print(snacktime.recipe_salad(serves=2, dressing="balsamic"))
```

---

## 🧾 Example Output

```
granola bar
spinach
cupcake

Simple Green Salad
Serves: 2

Ingredients
-----------
- 4 cups mixed greens
- 2 cups chopped vegetables (e.g., cucumber, tomato, carrot)
- 4 tbsp nuts or seeds (optional)
- Salt & pepper to taste
- Dressing: 4 tbsp olive oil, 2 tbsp balsamic vinegar, pinch of salt

Steps
-----
1) Toss greens and chopped veggies in a bowl.
2) Whisk dressing separately, then drizzle over salad.
3) Sprinkle nuts/seeds. Season with salt & pepper. Toss and serve.
```

---

## ✨ Features

- 🍎 **`random_snack()`** — pick a random healthy or quick snack  
- 🥦 **`random_vegetable()`** — choose a random vegetable  
- 🍩 **`random_treat()`** — get a random dessert idea  
- 🥗 **`recipe_salad()`** — generate a simple, customizable salad recipe  

---

## 👥 Team Solace

- **Member**: [funfigwat](https://github.com/funfig16), [qiexian-mf](https://github.com/qiexian-mf), [ems9856-lgtm](https://github.com/ems9856-lgtm), [hanqigui](https://github.com/hanqigui), [jawarbx](https://github.com/jawarbx)

---

## 🧠 Notes

- Tested with **Python 3.9+** on macOS and Linux.  
- All random functions can be made deterministic with a `seed` argument.  
  ```python
  snacktime.random_snack(seed=42)
  ```
- Supports CLI and programmatic use.

---

## 🧑‍💻 Project Details

| Field | Description |
|-------|-------------|
| **Package Name** | `snacktime` |
| **Author** | Team Solace |
| **License** | GPL 3.0 |
| **Language** | Python 3.9+ |
| **PyPI Page** | [https://pypi.org/project/snacktime/](https://pypi.org/project/snacktime/)  

---

## 🥳 Credits

Developed by **Team Solace** for *Software Engineering (Fall 2025)*  
as part of the Python Package exercise.  
This project demonstrates collaboration, testing, automation, and packaging best practices.

---

**Enjoy your snacks and code responsibly，thank you! 🍪🥗🍫**
