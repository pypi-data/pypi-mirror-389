# joytide/__main__.py
import argparse

from .core import banner, game_2048, art, confetti
from .race import race


def _run_banner(args) -> int:
    print(banner(args.text, border=args.border, padding=args.padding, align=args.align))
    return 0


def _run_game_2048(args) -> int:
    game_2048(size=args.size, prob=args.prob, winning_tile=args.winning_tile)
    return 0


def _run_art(args):
    art(theme=args.theme, size=args.size)
    return 0


def _run_race(args) -> int:
    race(args.names, width=args.width, delay=args.delay)
    return 0


def _run_confetti(args):
    confetti(
        width=args.width,
        height=args.height,
        n_particles=args.n_particles,
        spawn_time=args.spawn_time,
        gravity=args.gravity,
        wind=args.wind,
    )
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="joytide", description="joytide CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # banner function
    p_banner = sub.add_parser("banner", help="print an ASCII banner")
    p_banner.add_argument("text")
    p_banner.add_argument("--border", default="*", help="border characters")
    p_banner.add_argument("--padding", type=int, default=1, help="spaces around text")
    p_banner.add_argument(
        "--align", choices=["left", "center", "right"], default="center"
    )
    p_banner.set_defaults(func=_run_banner)

    # 2048 function
    p_2048 = sub.add_parser("2048", help="play 2048 in your terminal")
    p_2048.add_argument("--size", type=int, default=4, help="board size (default: 4)")
    p_2048.add_argument(
        "--prob",
        type=float,
        default=0.25,
        help="probability of a 4 tile appearing (default: 0.25)",
    )
    p_2048.add_argument(
        "--winning-tile",
        type=int,
        default=2048,
        help="winning tile value (default: 2048)",
    )
    p_2048.set_defaults(func=_run_game_2048)

    # art function
    p_art = sub.add_parser("art", help="print ASCII art")
    p_art.add_argument(
        "--theme",
        choices=["animal", "nature", "tech", "random"],
        default="random",
        help="theme of the art",
    )
    p_art.add_argument(
        "--size", choices=["small", "large"], default="small", help="size of the art"
    )
    p_art.set_defaults(func=_run_art)

    # race function
    p_race = sub.add_parser("race", help="run an ASCII race")
    p_race.add_argument("names", nargs="+", help="racer names (2+)")
    p_race.add_argument(
        "--width", type=int, default=32, help="track width (default: 32)"
    )
    p_race.add_argument(
        "--delay", type=float, default=0.04, help="frame delay seconds (default: 0.04)"
    )
    p_race.set_defaults(func=_run_race)

    #  confetti function
    p_confetti = sub.add_parser("confetti", help="run confetti animation in terminal")
    p_confetti.add_argument("--width", type=int, default=40, help="number of columns")
    p_confetti.add_argument("--height", type=int, default=12, help="number of rows")
    p_confetti.add_argument(
        "--n-particles", type=int, default=120, help="max number of confetti"
    )
    p_confetti.add_argument(
        "--spawn-time",
        type=float,
        default=2.0,
        help="how long to spawn new confetti (seconds)",
    )
    p_confetti.add_argument(
        "--gravity", type=float, default=0.03, help="gravity strength"
    )
    p_confetti.add_argument("--wind", type=float, default=0.01, help="wind strength")

    p_confetti.set_defaults(func=_run_confetti)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
