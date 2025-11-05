import os, random, time
from .core import banner, confetti


def race(names, width: int = 32, delay: float = 0.08):
    """
    ASCII race animation.
    Args:
        names (list[str] or tuple[str]): racer names
        width (int): track width
        delay (float): frame delay in seconds
    """
    if not names or len(names) < 2:
        print("Give me at least two racers!")
        return
    if width < 10:
        print("Width too small; try >= 10")
        return
    if delay <= 0:
        print("Delay must be > 0")
        return

    names = [str(n) for n in names]

    pos = {n: 0 for n in names}
    finish = width

    print(banner("🏁 ASCII RACE 🏁", border="=", padding=2, align="center"))
    time.sleep(0.8)

    winner = None
    while winner is None:
        os.system("cls" if os.name == "nt" else "clear")
        print(banner("🏁 ASCII RACE 🏁", border="=", padding=2, align="center"))
        print()

        for n in names:

            step = random.randint(0, 1)
            pos[n] = min(pos[n] + step, finish)

            track = "-" * finish

            car_idx = pos[n]
            if car_idx >= finish:
                car_idx = finish
            lane = track[:car_idx] + "🏎️" + track[car_idx:]
            print(f"{n:>12} |{lane}|")

            if pos[n] >= finish and winner is None:
                winner = n

        time.sleep(delay)

    print("\n")
    confetti()
    print("\n")
    print(banner(f"Winner: {winner}!", border="*", padding=1, align="center"))
