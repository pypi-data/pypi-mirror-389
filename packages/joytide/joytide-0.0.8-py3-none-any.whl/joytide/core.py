"""
core module for joytide
"""

import random, time, os
from colorama import Fore, Style, init
from .twenty_48 import start_game
from . import ascii_art

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


import random, time, sys, shutil
from colorama import Fore, Style, init

init(autoreset=True)


def confetti(
    width=40, height=12, n_particles=120, spawn_time=2.0, gravity=0.03, wind=0.01
):
    """
    Confetti animation with:
    - Limited spawn time
    - Piling up at the bottom
    - Vertical centering in terminal
    - Natural stop when all confetti land
    """

    # check for invalid parameters
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be > 0")
    if spawn_time <= 0:
        raise ValueError("spawn_time must be > 0")
    if gravity < 0 or wind < 0:
        raise ValueError("gravity and wind must be non-negative")

    # detect terminal size and warn if too small
    cols, rows = shutil.get_terminal_size((80, 24))
    if cols < width or rows < height:
        print("\n !!! Terminal too small!")
        print(f"   Requested: {width}×{height}")
        print(f"   Current:   {cols}×{rows}")
        print("Please enlarge your terminal window, then press Enter to continue...")
        input()

    # check again after user resizes
    cols, rows = shutil.get_terminal_size((80, 24))

    # adjust to fit new dimensions if still smaller
    width = min(width, cols - 2)
    height = min(height, rows - 2)

    print(f"\n Using adjusted size: {width}×{height}\n")
    time.sleep(1)

    padding_top = max(0, (rows - height) // 2)

    chars = ["*", "✨", ".", "o", "💫", "🎉"]
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.CYAN, Fore.MAGENTA, Fore.WHITE]

    particles = []
    start_time = time.time()
    ground = [height - 1 for _ in range(width)]

    while True:
        current_time = time.time()
        elapsed = current_time - start_time

        # spawn new confetti
        if elapsed < spawn_time:
            for _ in range(random.randint(2, 10)):
                particles.append(
                    {
                        "x": random.uniform(0, width - 1),
                        "y": 0,
                        "vx": random.uniform(-0.3, 0.3),
                        "vy": random.uniform(0.0, 0.4),
                        "ax": random.uniform(-wind, wind),
                        "ay": random.uniform(gravity * 0.5, gravity * 1.5),
                        "char": random.choice(chars),
                        "color": random.choice(colors),
                        "landed": False,
                    }
                )

        # frame redraw
        sys.stdout.write("\033[H\033[J")  # Move cursor home + clear
        sys.stdout.write("\n" * padding_top)

        frame = [[" " for _ in range(width)] for _ in range(height)]

        # Update particle positions
        for p in particles:
            if not p["landed"]:
                p["vx"] += p["ax"]
                p["vy"] += p["ay"]
                p["vx"] = max(-0.4, min(0.4, p["vx"]))
                p["x"] += p["vx"]
                p["y"] += p["vy"]

                if p["x"] < 0:
                    p["x"] = 0
                    p["vx"] *= -0.3
                elif p["x"] >= width - 1:
                    p["x"] = width - 1
                    p["vx"] *= -0.3

                xi = int(p["x"])
                floor_y = ground[xi]

                if p["y"] >= floor_y:
                    p["y"] = floor_y
                    p["landed"] = True
                    ground[xi] -= 1

            xi, yi = int(p["x"]), int(p["y"])
            if 0 <= yi < height:
                frame[yi][xi] = p["color"] + p["char"] + Style.RESET_ALL

        if min(ground) < height - 1:
            floor_line = height - 1
            frame[floor_line] = ["·" for _ in range(width)]

        sys.stdout.write("\n".join("".join(row) for row in frame))
        sys.stdout.flush()
        time.sleep(0.08)

        # Stop after spawn wundow and when all confetti have landed
        if elapsed > spawn_time and all(p["landed"] for p in particles):
            break


def game_2048(size: int = 4, prob: float = 0.25, winning_tile: int = 2048):
    print(banner("Welcome to 2048!", border="*", padding=1, align="center"))
    print(
        "\nUse WASD to move the tiles. Merge tiles of the same value to get to 2048!\n"
    )
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
