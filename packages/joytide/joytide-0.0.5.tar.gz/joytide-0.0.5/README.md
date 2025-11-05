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
python -m pip install joytide
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
python -m joytide banner TEXT --border "#" --padding 2 --align right
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

### Art
Print ASCII art with a chosen theme and size.

**Usage**
```bash
joytide art [--theme animal|nature|tech|random] [--size small|large]
# if console script isn't on PATH:
python -m joytide art --theme animal --size large
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
python -m joytide 2048 --size 5 --prob 0.3 --winning-tile 4096
py -m joytide 2048   # windows**Options:**
- `--size`: Board size (default: 4, must be > 1)
- `--prob`: Probability of spawning a 4 tile (default: 0.25, range: 0-1)  
- `--winning-tile`: Target tile value to win (default: 2048)
```

**examples**
```bash
joytide 2048
joytide 2048 --size 5
joytide 2048 --size 3 --prob 0.5 --winning-tile 512
```

### Put each of your functions here with examples

## example program for all functions

a short demo that calls each function is in `examples/demo.py`.

```bash
python demo.py
py demo.py
```



## how to contribute

we use pipenv for development.

```bash
python -m pip install --user pipenv
pipenv install --dev
pipenv install -e .
pipenv run python -m pytest -v
```

build the package manually if needed:
```bash
pipenv run python -m build .
```

format code with Black:
```bash
pipenv run black .
```

## testing

each function should have tests for a normal case, an edge case, and an invalid input case.

```bash
pipenv run python -m pytest -v
```

## CI / CD

- code is formatted with **Black** for consistent style
- pull requests run tests on python 3.11 and 3.12 
- merges to `main` build the package and publish to **PyPI** using twine via GitHub Actions (`pypa/gh-action-pypi-publish`)

## configuration

no environment variables or secret config files are required. no database or starter data is needed. works on mac, windows, and linux.
