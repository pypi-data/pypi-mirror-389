[![CI / CD](https://github.com/swe-students-fall2025/3-python-package-team_riptide/actions/workflows/build.yaml/badge.svg)](https://github.com/swe-students-fall2025/3-python-package-team_riptide/actions/workflows/build.yaml)  
PyPI: https://pypi.org/project/joytide/

# joytide

joytide is a small python package with random fun helpers to help de-stress after hours of serious coding. each function can be visually changed with different inputs. the main way to use it is the **CLI**.

**team members**

- [Saud Alsheddy](https://github.com/Saud-Al5)
- [Omer Hortig](https://github.com/ohortig)
- [Amy Liu](https://github.com/Amyliu2003)
- [Alfardil Alam](https://github.com/alfardil)
- [Lucy Hartigan](https://github.com/lucyhartigan)

## install

requires **python 3.10 or higher**

```bash
pip install joytide
# if pip is not on PATH:
python3 -m pip install joytide
# windows:
py -m pip install joytide
```

## CLI

### Banner

print an ASCII banner.

**usage**

```bash
joytide banner TEXT [--border "*" ] [--padding 1] [--align left|center|right]
# if console script isn't on PATH:
python3 -m joytide banner TEXT --border "#" --padding 2 --align right
py -m joytide banner "team_riptide"   # windows
```

**examples**

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
py -m joytide art --theme tech  #windows
```

**examples**

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
py -m joytide 2048   # windows
```
**Options**

- `--size`: Board size (default: 4, must be > 1)
- `--prob`: Probability of spawning a 4 tile (default: 0.25, range: 0-1)
- `--winning-tile`: Target tile value to win (default: 2048)


**examples**

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
joytide race Mario Peach Yoshi
joytide race "Fast Car" "Zoomies" --delay 0.15 # to make the race slower
joytide race Me You --width 50 # change track width
```

## example program for all functions

- a short demo that calls each function is in [`demo.py`](./demo.py).
- [demo.py (permalink for PyPI)](https://github.com/swe-students-fall2025/3-python-package-team_riptide/blob/main/demo.py)

to run it:

```bash
python3 demo.py
# windows:
py demo.py
# if you're using pipenv:
pipenv run python3 demo.py
```

## how to contribute

we use pipenv for development.

```bash
python3 -m pip install --user pipenv
pipenv install --dev
pipenv install -e .
pipenv run python3 -m pytest -v
```

build the package manually if needed:

```bash
pipenv run python3 -m build .
```

format code with Black:

```bash
pipenv run black .
```

## testing

each function should have tests for a normal case, an edge case, and an invalid input case.

```bash
pipenv run python3 -m pytest -v
```

## CI / CD

- code is formatted with **Black** for consistent style
- pull requests run tests on python 3.11 and 3.12
- merges to `main` build the package and publish to **PyPI** using twine via GitHub Actions (`pypa/gh-action-pypi-publish`)

## configuration

no environment variables or secret config files are required. no database or starter data is needed. works on mac, windows, and linux.
