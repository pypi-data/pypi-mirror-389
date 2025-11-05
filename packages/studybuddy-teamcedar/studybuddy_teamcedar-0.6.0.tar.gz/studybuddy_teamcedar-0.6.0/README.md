# StudyBuddy — Your (Unhelpfully) Helpful Study Companion

[![log github events](https://github.com/swe-students-fall2025/3-python-package-team_cedar/actions/workflows/event-logger.yml/badge.svg)](https://github.com/swe-students-fall2025/3-python-package-team_cedar/actions/workflows/event-logger.yml)

---

**StudyBuddy** is a lighthearted Python package that adds sarcasm, pep talks, and playful structure to your study routine. It gives you randomized study tips, motivational messages, funny excuses, and silly study plans to make your academic life a bit more entertaining.

- **PyPI:** https://pypi.org/project/studybuddy/
- **Example app:** [`example.py`](./example.py)

---

## Installation

From PyPI (recommended):
```bash
pip install studybuddy
```

From source:
```bash
git clone https://github.com/swe-students-fall2025/3-python-package-team_cedar.git
cd 3-python-package-team_cedar
pip install -e .
```

---

## Quick Start (Import & Use)
```python
from studybuddy import study_tip, motivate, excuse, study_plan

# Get a humorous study tip
print(study_tip("physics", "chaotic"))

# Get some motivation (sarcastic or genuine)
print(motivate("sarcastic"))

# Get a funny excuse
print(excuse("homework"))

# Generate a study plan
for step in study_plan(3, "high", seed=4):
    print(step)
```

---

## API Reference (All Functions)

All functions accept an optional `seed` parameter for reproducible randomness.

### `study_tip(topic="math", mood="chaotic", seed=None) -> str`
Returns a humorous study tip for the given topic.

**Parameters:**
- `topic` (str): The subject area. Options: `"math"`, `"physics"`, `"history"`. Unknown topics default to `"math"`.
- `mood` (str): Currently unused, reserved for future expansion. Default: `"chaotic"`.
- `seed` (int | None): Optional seed for reproducible results.

**Returns:** A string containing a humorous study tip.

**Example:**
```python
from studybuddy import study_tip

print(study_tip("physics", "chaotic"))
# Output: "If it moves, it's probably physics. If not, hit it again."

print(study_tip("math", seed=42))
# Output: "If it's too complex, assume x = 0. Problem solved."
```

---

### `motivate(style="sarcastic", seed=None) -> str`
Returns a motivational or sarcastic message to keep you going.

**Parameters:**
- `style` (str): The tone of motivation. Options: `"sarcastic"`, `"genuine"`. Unknown styles default to `"sarcastic"`.
- `seed` (int | None): Optional seed for reproducible results.

**Returns:** A string containing a motivational message.

**Example:**
```python
from studybuddy import motivate

print(motivate("sarcastic"))
# Output: "Remember: diamonds are made under pressure. So start panicking."

print(motivate("genuine"))
# Output: "One page at a time — just keep going."
```

---

### `excuse(reason="homework", seed=None) -> str`
Returns a funny excuse for various academic mishaps.

**Parameters:**
- `reason` (str): The situation needing an excuse. Options: `"homework"`, `"late"`, `"exam"`. Unknown reasons default to `"homework"`.
- `seed` (int | None): Optional seed for reproducible results.

**Returns:** A string containing a humorous excuse.

**Example:**
```python
from studybuddy import excuse

print(excuse("homework"))
# Output: "My cat deleted my assignment. She's learning cybersecurity."

print(excuse("exam"))
# Output: "I didn't fail. I just found 99 ways that didn't work."

print(excuse("late"))
# Output: "My Wi-Fi connected to another dimension."
```

---

### `study_plan(hours=3, caffeine_level="high", seed=None) -> list[str]`
Generates a humorous study plan with steps.

**Parameters:**
- `hours` (int): Number of hours to plan for. Range: 1–5 (values above 5 are clamped to 5). Default: 3.
- `caffeine_level` (str): Caffeine consumption level. Options: `"low"`, `"high"`. When `"high"`, adds coffee-related steps. Default: `"high"`.
- `seed` (int | None): Optional seed for reproducible results.

**Returns:** A list of strings, each representing a study step.

**Example:**
```python
from studybuddy import study_plan

plan = study_plan(3, "high", seed=4)
for step in plan:
    print(step)
# Output:
# Step 1: Drink more coffee. Make coffee.
# Step 2: Drink more coffee. Open your notes.
# Step 3: Panic productively for 90 minutes.

# With low caffeine
plan = study_plan(2, "low", seed=10)
for step in plan:
    print(step)
# Output:
# Step 1: Reward yourself with a snack break.
# Step 2: Google half the material.
```

---

## Example Program

See the complete working example at [`example.py`](./example.py):
```python
from studybuddy import study_tip, motivate, excuse, study_plan

def main():
    print("=== StudyBuddy Demo ===")
    print("\nStudy Tip:", study_tip("physics", "chaotic"))
    print("\nMotivation:", motivate("sarcastic"))
    print("\nExcuse:", excuse("homework"))
    print("\nStudy Plan:")
    for step in study_plan(3, "high", seed=4):
        print(" -", step)

if __name__ == "__main__":
    main()
```

**Run it:**
```bash
python example.py
```

**Sample output:**
```
=== StudyBuddy Demo ===

Study Tip: If it moves, it's probably physics. If not, hit it again.

Motivation: Remember: diamonds are made under pressure. So start panicking.

Excuse: My cat deleted my assignment. She's learning cybersecurity.

Study Plan:
 - Step 1: Drink more coffee. Make coffee.
 - Step 2: Drink more coffee. Open your notes.
 - Step 3: Panic productively for 90 minutes.
```

---

## Contributing

We welcome contributions! Follow this workflow to contribute to the project.

### Set up your development environment

Clone the repository:
```bash
git clone https://github.com/swe-students-fall2025/3-python-package-team_cedar.git
cd 3-python-package-team_cedar
```

Create a virtual environment:
```bash
# Option 1: venv (recommended)
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Option 2: Pipenv
pip install pipenv
pipenv install --dev
pipenv shell
```

Install dependencies:
```bash
pip install -U pip
pip install -e . pytest build twine
```

### Run tests
```bash
pytest -q
```

All tests should pass before submitting a pull request.

### Build the package
```bash
python -m build
```

This creates distribution files in the `./dist` directory.

### Publish to PyPI (maintainer only)
```bash
twine upload dist/*
```

### Git workflow for new features

1. **Create a feature branch:**
```bash
git switch -c feat/your-feature-name
```

2. **Make changes and add tests** for any new functionality

3. **Commit your changes:**
```bash
git add -A
git commit -m "feat(core): add your feature description"
```

4. **Push to GitHub:**
```bash
git push -u origin feat/your-feature-name
```

5. **Open a Pull Request** on GitHub
6. **Request a teammate review**
7. **After approval, merge** into `main`
8. **Delete your feature branch**


## Continuous Integration

Every pull request triggers automated testing via GitHub Actions on **Python 3.10** and **3.11**.

The CI badge at the top of this README shows the current build status.

**Workflow file:** [`.github/workflows/event-logger.yml`](.github/workflows/event-logger.yml)

---

## Team Cedar

| Name | GitHub |
|------|--------|
| Nicole Zhang | [@chzzznn](https://github.com/chzzznn) |
| Kylie | [@kylin1209](https://github.com/kylin1209) |
| Sean Tang | [@plant445](https://github.com/plant445) |

---

## PyPI Package 

**https://pypi.org/project/studybuddy-teamcedar/0.5.0/**

---

## License

MIT — do cool things responsibly (and sarcastically). 