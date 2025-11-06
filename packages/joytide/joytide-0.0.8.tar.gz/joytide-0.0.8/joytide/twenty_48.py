import random
import sys
import readchar


class GameOverError(Exception):
    """Custom exception for when the game is over"""

    pass


class GameWonError(Exception):
    """Custom exception for when the game is won"""

    pass


class BoardTooSmallError(Exception):
    """Custom exception for when the board is too small (less than 2x2)"""

    pass


class Board:
    """
    Represents the 2048 game board
    args:
    size (int): The size of the board (default 4)
    prob (float): The probability of a tile being filled with a 4 (default 0.25)
    """

    def __init__(
        self, size: int = 4, prob: float = 0.25, winning_tile: int = 2048
    ) -> None:
        if size < 2:
            raise BoardTooSmallError("Error: Board must be at least 2x2")
        self.size = size
        self.prob = prob
        self.winning_tile = winning_tile
        # create empty board
        self.board = [[0 for _ in range(size)] for _ in range(size)]
        self.occupied_tiles = 0
        # add two random tiles to prep the board for the game
        self.add_random_tile()
        self.add_random_tile()

    def __str__(self) -> str:
        # Calculate the width needed based on the largest possible number
        # The winning tile is 4 characters, so we use that as minimum
        max_value = max(max(row) for row in self.board)
        cell_width = max(4, len(str(max_value)))

        # Total width = cells + spaces between them + 2 for borders + 2 for padding
        total_width = self.size * cell_width + (self.size - 1) + 2
        # Create top border
        border = "+" + "-" * (total_width) + "+"

        # Create rows with side borders
        rows = []
        for row in self.board:
            # Right-align numbers in their cells, but show 0 as empty
            formatted_cells = [
                f"{cell:>{cell_width}}" if cell != 0 else " " * cell_width
                for cell in row
            ]
            row_str = " ".join(formatted_cells)
            rows.append(f"| {row_str} |")
        return border + "\n" + "\n".join(rows) + "\n" + border

    def add_random_tile(self) -> None:
        if self.occupied_tiles >= self.size * self.size:
            # board is full, game over
            raise GameOverError("Game Over!: Board is full")
        while True:
            # randomly select a cell to add a tile to
            row = random.randint(0, self.size - 1)
            col = random.randint(0, self.size - 1)
            # if the cell is empty, add a tile to it
            if self.board[row][col] == 0:
                self.board[row][col] = 4 if random.random() < self.prob else 2
                self.occupied_tiles += 1
                break

    def move_left(self) -> None:
        for j in range(self.size):
            current_row = self.board[j]
            updated_row = []
            for i in range(self.size):
                if current_row[i] != 0:
                    if updated_row and updated_row[-1] == current_row[i]:
                        updated_row[-1] *= 2
                        self.occupied_tiles -= 1
                        if updated_row[-1] == self.winning_tile:
                            raise GameWonError("You won!")
                    else:
                        updated_row.append(current_row[i])
            # fill the remaining cells with zeros
            updated_row.extend([0] * (self.size - len(updated_row)))
            self.board[j] = updated_row
        self.add_random_tile()

    def move_right(self) -> None:
        for j in range(self.size):
            current_row = self.board[j]
            updated_row = []
            for i in range(self.size - 1, -1, -1):
                if current_row[i] != 0:
                    if updated_row and updated_row[-1] == current_row[i]:
                        updated_row[-1] *= 2
                        self.occupied_tiles -= 1
                        if updated_row[-1] == self.winning_tile:
                            raise GameWonError("You won!")
                    else:
                        updated_row.append(current_row[i])
            # fill the remaining cells with zeros
            updated_row.extend([0] * (self.size - len(updated_row)))
            self.board[j] = updated_row[::-1]
        self.add_random_tile()

    def move_up(self) -> None:
        for i in range(self.size):
            current_col = [self.board[j][i] for j in range(self.size)]
            updated_col = []
            for j in range(self.size):
                if current_col[j] != 0:
                    if updated_col and updated_col[-1] == current_col[j]:
                        updated_col[-1] *= 2
                        self.occupied_tiles -= 1
                        if updated_col[-1] == self.winning_tile:
                            raise GameWonError("You won!")
                    else:
                        updated_col.append(current_col[j])
            # fill the remaining cells with zeros
            updated_col.extend([0] * (self.size - len(updated_col)))
            for j in range(self.size):
                self.board[j][i] = updated_col[j]
        self.add_random_tile()

    def move_down(self) -> None:
        for i in range(self.size):
            current_col = [self.board[j][i] for j in range(self.size)]
            updated_col = []
            for j in range(self.size - 1, -1, -1):
                if current_col[j] != 0:
                    if updated_col and updated_col[-1] == current_col[j]:
                        updated_col[-1] *= 2
                        self.occupied_tiles -= 1
                        if updated_col[-1] == self.winning_tile:
                            raise GameWonError("You won!")
                    else:
                        updated_col.append(current_col[j])
            # fill the remaining cells with zeros
            updated_col.extend([0] * (self.size - len(updated_col)))
            updated_col = updated_col[::-1]
            for j in range(self.size):
                self.board[j][i] = updated_col[j]
        self.add_random_tile()


def get_key() -> str:
    """
    Captures a single keyboard input from terminal.
    Returns the character pressed in lowercase.
    """
    char = readchar.readkey()

    # Handle Ctrl+C
    if char == "\x03":
        return "q"  # Treat Ctrl+C as quit

    return char.lower()


def start_game(size: int = 4, prob: float = 0.25, winning_tile: int = 2048) -> None:
    try:
        board = Board(size=size, prob=prob, winning_tile=winning_tile)
    except BoardTooSmallError as e:
        print(e)
        sys.exit(1)

    try:
        while True:
            try:
                print(board)
                key = get_key()

                # Handle the key press
                if key == "q":
                    print("Thanks for playing!\n")
                    break
                elif key == "w":
                    board.move_up()
                elif key == "s":
                    board.move_down()
                elif key == "a":
                    board.move_left()
                elif key == "d":
                    board.move_right()

            except GameWonError as e:
                print(e)
                break
            except GameOverError as e:
                print(e)
                break
    finally:
        # Flush stdout to ensure all output is displayed
        sys.stdout.flush()
