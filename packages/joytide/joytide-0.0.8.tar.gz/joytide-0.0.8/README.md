[![CI / CD](https://github.com/swe-students-fall2025/3-python-package-team_riptide/actions/workflows/build.yaml/badge.svg)](https://github.com/swe-students-fall2025/3-python-package-team_riptide/actions/workflows/build.yaml)  
PyPI: https://pypi.org/project/joytide/

# joytide

Joytide is a small Python package with fun terminal helpers to de-stress after hours of serious coding. Each function is customizable via arguments. You can use Joytide via the **CLI** or by **importing it in Python**.

**Team members**

- [Saud Alsheddy](https://github.com/Saud-Al5)
- [Omer Hortig](https://github.com/ohortig)
- [Amy Liu](https://github.com/Amyliu2003)
- [Alfardil Alam](https://github.com/alfardil)
- [Lucy Hartigan](https://github.com/lucyhartigan)

## Installation

Requires **python 3.10 or higher**

```bash
pip install joytide
# if pip is not on PATH:
python3 -m pip install joytide
# Windows:
py -m pip install joytide
```

## Use as a Library

Install first (once per environment):

```bash
pip install joytide
```

Import in your code:

```python
from joytide import banner, confetti, art, game_2048, race
```

Quick check:

```bash
python -c "from joytide import banner; print(banner('OK'))"
```

Examples:

```python
# Banner returns a string
print(banner("Team Riptide", border="<>", padding=2, align="center"))

# Render ASCII art and confetti in the terminal
art(theme="nature", size="large")
confetti(width=60, height=15, n_particles=200, spawn_time=3.0)

# Games/animations in the terminal
game_2048(size=4, prob=0.25, winning_tile=2048)
race(["Mario", "Peach", "Yoshi"], width=50, delay=0.12)
```


## CLI

### Banner

Print an ASCII banner.

**Usage**

```bash
joytide banner TEXT [--border "*" ] [--padding 1] [--align left|center|right]
# if console script isn't on PATH:
python3 -m joytide banner TEXT --border "#" --padding 2 --align right
py -m joytide banner "team_riptide"   # Windows
```

**Examples**

```bash
joytide banner "hello"
joytide banner "team_riptide" --border "##"
joytide banner "left"  --padding 2 --align left
joytide banner "right" --border "<>" --align right
```

---

### Confetti

Create a colorful **confetti animation** right in your terminal — great for celebrating test passes, merges, or just taking a break.

**Usage**

```bash
joytide confetti [--width WIDTH] [--height HEIGHT] [--n-particles N]
                 [--spawn-time SECONDS] [--gravity VALUE] [--wind VALUE]

# If console script isn't on PATH:
python -m joytide confetti --width 60 --height 15 --spawn-time 3.0
py -m joytide confetti --n-particles 200 --gravity 0.02  # Windows
```

**Options**

| Flag            | Description                                            | Default |
| --------------- | ------------------------------------------------------ | ------- |
| `--width`       | number of columns in the frame                         | `40`    |
| `--height`      | number of rows                                         | `12`    |
| `--n-particles` | **maximum total number** of confetti pieces that can appear                       | `120`   |
| `--spawn-time`  | seconds to keep spawning new confetti before they stop | `2.0`   |
| `--gravity`     | downward acceleration                                  | `0.03`  |
| `--wind`        | horizontal drift per frame                             | `0.01`  |

**Examples**

```bash
joytide confetti
joytide confetti --width 80 --height 20 --n-particles 200 --spawn-time 3.5
joytide confetti --gravity 0.015 --wind 0.005  # slower, smoother motion
joytide confetti --width 30 --height 10 --n-particles 40  # mini version
```

---


### Art

Print ASCII art with a chosen theme and size.

**Usage**

```bash
joytide art [--theme animal|nature|tech|random] [--size small|large]
# if console script isn't on PATH:
python3 -m joytide art --theme animal --size large
py -m joytide art --theme tech  # Windows
```

**Examples**

```bash
joytide art
joytide art --theme animal
joytide art --theme nature --size large
joytide art --theme tech --size small
joytide art --theme random --size large
```

---

### 2048

Play the game 2048 in your terminal

**Usage**

```bash
joytide 2048 [--size SIZE] [--prob PROB] [--winning-tile TILE]
# if console script isn't on PATH:
python3 -m joytide 2048 --size 5 --prob 0.3 --winning-tile 4096
py -m joytide 2048   # Windows
```
**Options**

- `--size`: Board size (default: 4, must be > 1)
- `--prob`: Probability of spawning a 4 tile (default: 0.25, range: 0-1)
- `--winning-tile`: Target tile value to win (default: 2048)


**Examples**

```bash
joytide 2048
joytide 2048 --size 5
joytide 2048 --size 3 --prob 0.5 --winning-tile 512
```

---

### Race

Race 2 or more players!

**Usage**
```bash
# You can add as many names as you like; for names with spaces, use quotes.
joytide race NAME [NAME ...] [--width WIDTH] [--delay SECONDS]
# if console script isn't on PATH:
python3 -m joytide race NAME [NAME ...]
py -m joytide race NAME [NAME ...] # Windows
```

**Examples**

```bash
joytide race Mario Peach Yoshi
joytide race "Fast Car" "Zoomies" --delay 0.15 # to make the race slower
joytide race Me You --width 50 # change track width
```

## Example program for all functions

- A short demo that calls each function is in [`demo.py`](./demo.py).
- [demo.py (permalink for PyPI)](https://github.com/swe-students-fall2025/3-python-package-team_riptide/blob/main/demo.py)

To run it:

```bash
python3 demo.py
# Windows:
py demo.py
# if you're using pipenv:
pipenv run python3 demo.py
```

## How to Contribute

We use **Pipenv** and a simple **branch → PR** workflow.

1) **Clone the repo**
```bash
git clone https://github.com/swe-students-fall2025/3-python-package-team_riptide.git
cd 3-python-package-team_riptide
```

2) **Create a feature branch**
```bash
git checkout -b feature/<short-name>
```

3) **Set up the dev environment**
```bash
python3 -m pip install --user pipenv
pipenv install --dev
pipenv install -e .
```

4) **Run tests and format**
```bash
pipenv run pytest -v
pipenv run black .
```

5) **Commit using a clear one sentence line**
```bash
git add -A
git commit -m "added delay flag and examples"
```

6) **Push your branch**
```bash
git push -u origin feature/<short-name>
```

7) **Open a Pull Request**
- Go to the repository on GitHub and create the pull request.
- Fill in what changed and why; link issues if relevant.
- CI will run on the PR (format + tests on Python 3.11/3.12).

8) **After approval**
- We will merge the PR. Merges to `main` will build and publish to PyPI via GitHub Actions.

### Testing

Each function should have tests for a normal case, an edge case, and an invalid input case.

```bash
pipenv run python3 -m pytest -v
```

## CI / CD

- code is formatted with **Black** for consistent style
- pull requests run tests on python 3.11 and 3.12
- merges to `main` build the package and publish to **PyPI** using twine via GitHub Actions (`pypa/gh-action-pypi-publish`)

## Configuration

No environment variables or secret config files are required. Nno database or starter data is needed. Works on mac, Windows, and linux.
