"""
core module for joytide

we will add our function here in our own branch.
after finishing a function we will need to add tests for them in the tests folder

for now this file is empty on purpose.
"""

import random, time, os
from colorama import Fore, Style, init
from .twenty_48 import start_game
from . import ascii_art as ascii_art

init(autoreset=True)


def banner(
    text: str, border: str = "*", padding: int = 1, align: str = "center"
) -> str:
    """
    Make a simple ASCII banner.
    align: 'left' | 'center' | 'right'
    """
    if not isinstance(text, str):
        raise TypeError("text must be str")
    if not isinstance(border, str) or len(border) == 0:
        raise ValueError("border must be a non-empty string")
    if not isinstance(padding, int) or padding < 0:
        raise ValueError("padding must be >= 0")
    if align not in {"left", "center", "right"}:
        raise ValueError("align must be 'left', 'center', or 'right'")

    def _repeat_to_length(pattern: str, length: int) -> str:
        # repeat pattern to exactly length chars
        times = (length // len(pattern)) + 1
        return (pattern * times)[:length]

    inner_width = len(text) + padding * 2
    if align == "left":
        inner = text.ljust(inner_width)
    elif align == "right":
        inner = text.rjust(inner_width)
    else:
        inner = text.center(inner_width)

    middle = f"{border}|{inner}|{border}"
    line = _repeat_to_length(border, len(middle))
    return "\n".join([line, middle, line])


def confetti(width=40, height=10, duration=3, density=0.2):
    """
    Print a colorful falling confetti animation in the terminal.

    Args:
        width (int): number of characters per line.
        height (int): number of lines per frame.
        duration (float): how long to run in seconds.
        density (float): probability of a confetti appearing per cell.
    """
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be > 0")
    if not (0 < density <= 1):
        raise ValueError("density must be between 0 and 1")
    if duration <= 0:
        raise ValueError("duration must be > 0")

    chars = ["*", "✨", ".", "o", "💫", "🎉"]
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.CYAN, Fore.MAGENTA, Fore.WHITE]
    end_time = time.time() + duration

    while time.time() < end_time:
        os.system("cls" if os.name == "nt" else "clear")  # clear terminal
        frame = []
        for _ in range(height):
            row = ""
            for _ in range(width):
                if random.random() < density:
                    color = random.choice(colors)
                    char = random.choice(chars)
                    row += color + char + Style.RESET_ALL
                else:
                    row += " "
            frame.append(row)
        print("\n".join(frame))
        time.sleep(0.1)

def game_2048(size: int = 4, prob: float = 0.25, winning_tile: int = 2048):
    print(banner("Welcome to 2048!", border="*", padding=1, align="center"))
    print("\nUse WASD to move the tiles. Merge tiles of the same value to get to 2048!\n")
    print("Press Q to quit\n")
    start_game(size=size, prob=prob, winning_tile=winning_tile)

def art(theme: str = "random", size: str = "small"):
    """
    Print ASCII art based on theme and size.

    Args:
        theme (str): 'animal', 'nature', 'tech', 'random'
        size (str): 'small' or 'large'
    """
    theme = theme.lower()
    size = size.lower()

    arts = {
        "animal": {
            "small": [ascii_art.cat1, ascii_art.cat2, ascii_art.cow],
            "large": [ascii_art.bear, ascii_art.dog],
        },
        "nature": {
            "small": [ascii_art.mountains2, ascii_art.flower, ascii_art.cactus],
            "large": [ascii_art.mountains1, ascii_art.camping, ascii_art.flowers],
        },
        "tech": {
            "small": [ascii_art.calculator, ascii_art.camera, ascii_art.robot],
            "large": [ascii_art.clock, ascii_art.tv, ascii_art.phone],
        },
    }

    # if theme is random, pick random
    if theme == "random":
        theme = random.choice(list(arts.keys()))

    if theme not in arts:
        print(
            f"Invalid theme '{theme}'. Valid options are: animal, nature, tech, random."
        )
        return

    if size not in ["small", "large"]:
        print(f"Invalid size '{size}'. Valid options are: small, large.")
        return

    # pick random art with chosen theme / size
    selected_art = random.choice(arts[theme][size])
    selected_art()
