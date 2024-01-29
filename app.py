import sys
import argparse
import collections
from dataclasses import dataclass
from pathlib import Path
import tomllib
import curses
from time import sleep

__version__ = "1.0.0"

__all__ = ["CursesView"]


class CursesView:
    def __init__(self, pattern, gen=10, frame_rate=7, bbox=(0, 0, 40, 20)):
        self.pattern = pattern
        self.gen = gen
        self.frame_rate = frame_rate
        self.bbox = bbox

    def show(self):
        curses.wrapper(self._draw)

    def _draw(self, screen):
        current_grid = LifeGrid(self.pattern)
        curses.curs_set(0)
        screen.clear()

        try:
            screen.addstr(0, 0, current_grid.as_string(self.bbox))
        except curses.error:
            raise ValueError(
                f"Error: terminal too small for pattern '{self.pattern.name}'"
            )

        for _ in range(self.gen):
            current_grid.evolve()
            screen.addstr(0, 0, current_grid.as_string(self.bbox))
            screen.refresh()
            sleep(1 / self.frame_rate)

PATTERNS_FILE = Path(__file__).parent / "patterns.toml"


@dataclass
class Pattern:
    name: str
    alive_cells: set[tuple[int, int]]

    @classmethod
    def from_toml(cls, name, toml_data):
        return cls(
            name,
            alive_cells={tuple(cell) for cell in toml_data["alive_cells"]},
        )


def get_pattern(name, filename=PATTERNS_FILE):
    data = tomllib.loads(filename.read_text(encoding="utf-8"))
    return Pattern.from_toml(name, toml_data=data[name])


def get_all_patterns(filename=PATTERNS_FILE):
    data = tomllib.loads(filename.read_text(encoding="utf-8"))
    return [
        Pattern.from_toml(name, toml_data) for name, toml_data in data.items()
    ]

ALIVE = "#"
DEAD = " "


class LifeGrid:
    def __init__(self, pattern):
        self.pattern = pattern

    def evolve(self):
        neighbors = (
            (-1, -1),  # Above left
            (-1, 0),  # Above
            (-1, 1),  # Above right
            (0, -1),  # Left
            (0, 1),  # Right
            (1, -1),  # Below left
            (1, 0),  # Below
            (1, 1),  # Below right
        )
        num_neighbors = collections.defaultdict(int)
        for row, col in self.pattern.alive_cells:
            for drow, dcol in neighbors:
                num_neighbors[(row + drow, col + dcol)] += 1

        stay_alive = {
            cell for cell, num in num_neighbors.items() if num in {2, 3}
        } & self.pattern.alive_cells
        come_alive = {
            cell for cell, num in num_neighbors.items() if num == 3
        } - self.pattern.alive_cells

        self.pattern.alive_cells = stay_alive | come_alive

    def as_string(self, bbox):
        start_col, start_row, end_col, end_row = bbox
        display = [self.pattern.name.center(2 * (end_col - start_col))]
        for row in range(start_row, end_row):
            display_row = [
                ALIVE if (row, col) in self.pattern.alive_cells else DEAD
                for col in range(start_col, end_col)
            ]
            display.append(" ".join(display_row))
        return "\n ".join(display)

    def __str__(self):
        return (
            f"{self.pattern.name}:\n"
            f"Alive cells -> {sorted(self.pattern.alive_cells)}"
        )

def get_command_line_args():
    parser = argparse.ArgumentParser(
        prog="game",
        description="Conway's Game of Life in your terminal",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s v{__version__}"
    )
    parser.add_argument(
        "-p",
        "--pattern",
        choices=[pat.name for pat in get_all_patterns()],
        default="Pulsar",
        help="take a pattern for the Game of Life (default: %(default)s)",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="show all available patterns in a sequence",
    )
    parser.add_argument(
        "-v",
        "--view",
        choices=__all__,
        default="CursesView",
        help="display the life grid in a specific view (default: %(default)s)",
    )
    parser.add_argument(
        "-g",
        "--gen",
        metavar="NUM_GENERATIONS",
        type=int,
        default=200,
        help="number of generations (default: %(default)s)",
    )
    parser.add_argument(
        "-f",
        "--fps",
        metavar="FRAMES_PER_SECOND",
        type=int,
        default=7,
        help="frames per second (default: %(default)s)",
    )
    return parser.parse_args()

def main():
    args = get_command_line_args()
    if args.all:
        for pattern in get_all_patterns():
            _show_pattern(CursesView, pattern, args)
    else:
        _show_pattern(CursesView, get_pattern(name=args.pattern), args)


def _show_pattern(View, pattern, args):
    try:
        View(pattern=pattern, gen=args.gen, frame_rate=args.fps).show()
    except Exception as error:
        print(error, file=sys.stderr)


if __name__ == "__main__":
    main()