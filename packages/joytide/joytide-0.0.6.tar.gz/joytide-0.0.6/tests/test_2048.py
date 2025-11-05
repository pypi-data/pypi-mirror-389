import pytest
import random
from joytide.twenty_48 import Board, GameOverError, GameWonError, BoardTooSmallError


# Helper function for tests


def create_empty_board(size=4, prob=0.25, winning_tile=2048):
    # Set random seed for deterministic initialization
    random.seed(42)
    board = Board(size=size, prob=prob, winning_tile=winning_tile)
    # Clear the board for manual setup
    board.board = [[0 for _ in range(size)] for _ in range(size)]
    board.occupied_tiles = 0
    return board


# Test board initialization


## test board initialization with default parameters
def test_board_default_initialization():
    random.seed(123)
    board = Board()
    # Check default parameters
    assert board.size == 4
    assert board.prob == 0.25
    assert board.winning_tile == 2048
    # Check board is 4x4
    assert len(board.board) == 4
    assert all(len(row) == 4 for row in board.board)
    # Check that 2 tiles were added
    assert board.occupied_tiles == 2


## test board initialization with custom size
def test_board_custom_size():
    random.seed(123)
    board = Board(size=3)
    assert board.size == 3
    assert len(board.board) == 3
    assert all(len(row) == 3 for row in board.board)
    assert board.occupied_tiles == 2


## test board initialization with custom probability
def test_board_custom_prob():
    random.seed(123)
    board = Board(prob=0.5)
    assert board.prob == 0.5


## test board initialization with custom winning tile
def test_board_custom_winning_tile():
    random.seed(123)
    board = Board(winning_tile=128)
    assert board.winning_tile == 128


## test board initialization with exactly 2 tiles
def test_board_initial_two_tiles():
    random.seed(123)
    board = Board()
    # Count non-zero tiles
    tile_count = sum(1 for row in board.board for cell in row if cell != 0)
    assert tile_count == 2
    assert board.occupied_tiles == 2


## test board initialization with small size (2x2)
def test_board_small_size():
    random.seed(123)
    board = Board(size=2)
    assert board.size == 2
    assert len(board.board) == 2
    assert board.occupied_tiles == 2


## test board initialization with impossibly small size (1x1)
def test_board_impossibly_small_size():
    with pytest.raises(BoardTooSmallError):
        board = Board(size=1)


# test movement


## test left movement (no merge)
def test_move_left_simple():
    # create an arbitrary board
    board = create_empty_board()
    board.board = [[0, 0, 2, 0], [0, 4, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    board.occupied_tiles = 2

    random.seed(42)
    board.move_left()

    # make sure the board is updated correctly
    assert board.board[0][0] == 2
    assert board.board[1][0] == 4


## test left movement (with merge)
def test_move_left_with_merge():
    # create an arbitrary board
    board = create_empty_board()
    board.board = [[2, 2, 0, 0], [4, 4, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    board.occupied_tiles = 4

    random.seed(42)
    board.move_left()

    # make sure the board is updated correctly
    assert board.board[0][0] == 4
    assert board.board[0][1] == 0
    assert board.board[1][0] == 8
    assert board.board[1][1] == 0


## test right movement (no merge)
def test_move_right_simple():
    # create an arbitrary board
    board = create_empty_board()
    board.board = [[2, 0, 0, 0], [4, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    board.occupied_tiles = 2

    random.seed(42)
    board.move_right()

    # make sure the board is updated correctly
    assert board.board[0][3] == 2
    assert board.board[1][3] == 4


## test right movement (with merge)
def test_move_right_with_merge():
    # create an arbitrary board
    board = create_empty_board()
    board.board = [[0, 0, 2, 2], [0, 0, 4, 4], [0, 0, 0, 0], [0, 0, 0, 0]]
    board.occupied_tiles = 4

    random.seed(42)
    board.move_right()

    # make sure the board is updated correctly
    assert board.board[0][3] == 4
    assert board.board[0][2] == 0
    assert board.board[1][3] == 8
    assert board.board[1][2] == 0


## test up movement (no merge)
def test_move_up_simple():
    # create an arbitrary board
    board = create_empty_board()
    board.board = [[0, 0, 0, 0], [0, 0, 0, 0], [2, 0, 0, 0], [0, 4, 0, 0]]
    board.occupied_tiles = 2

    random.seed(42)
    board.move_up()

    # make sure the board is updated correctly
    assert board.board[0][0] == 2
    assert board.board[0][1] == 4


## test up movement (with merge)
def test_move_up_with_merge():
    # create an arbitrary board
    board = create_empty_board()
    board.board = [[2, 4, 0, 0], [2, 4, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    board.occupied_tiles = 4

    random.seed(42)
    board.move_up()

    # make sure the board is updated correctly
    assert board.board[0][0] == 4
    assert board.board[1][0] == 0
    assert board.board[0][1] == 8
    assert board.board[1][1] == 0


## test down movement (no merge)
def test_move_down_simple():
    # create an arbitrary board
    board = create_empty_board()
    board.board = [[2, 0, 0, 0], [0, 4, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    board.occupied_tiles = 2

    random.seed(42)
    board.move_down()

    # make sure the board is updated correctly
    assert board.board[3][0] == 2
    assert board.board[3][1] == 4


## test down movement (with merge)
def test_move_down_with_merge():
    # create an arbitrary board
    board = create_empty_board()
    board.board = [[0, 0, 0, 0], [0, 0, 0, 0], [2, 4, 0, 0], [2, 4, 0, 0]]
    board.occupied_tiles = 4

    random.seed(42)
    board.move_down()

    # make sure the board is updated correctly
    assert board.board[3][0] == 4
    assert board.board[2][0] == 0
    assert board.board[3][1] == 8
    assert board.board[2][1] == 0


## test that each move adds a new random tile
def test_move_adds_new_tile():
    # create an arbitrary board
    board = create_empty_board()
    board.board = [[2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    board.occupied_tiles = 1

    random.seed(42)
    initial_occupied = board.occupied_tiles
    board.move_left()

    # make sure the board is updated correctly
    assert board.occupied_tiles == initial_occupied + 1


## test that merging tiles decrements occupied_tiles count
def test_merge_decrements_occupied_tiles():
    # create an arbitrary board
    board = create_empty_board()
    board.board = [[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    board.occupied_tiles = 2

    random.seed(42)
    board.move_left()

    # same count as before the move (-1 for the merge, +1 for the new tile)
    assert board.occupied_tiles == 2


# test winning conditions


## test that GameWonError is raised when reaching 2048 via left move
def test_win_on_reaching_2048_left():
    # create an arbitrary board
    board = create_empty_board()
    board.board = [[1024, 1024, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    board.occupied_tiles = 2

    with pytest.raises(GameWonError):
        board.move_left()


## test that GameWonError is raised when reaching 2048 via right move
def test_win_on_reaching_2048_right():
    # create an arbitrary board
    board = create_empty_board()
    board.board = [[0, 0, 1024, 1024], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    board.occupied_tiles = 2

    with pytest.raises(GameWonError):
        board.move_right()


## test that GameWonError is raised when reaching 2048 via up move
def test_win_on_reaching_2048_up():
    # create an arbitrary board

    board = create_empty_board()
    board.board = [[1024, 0, 0, 0], [1024, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    board.occupied_tiles = 2

    with pytest.raises(GameWonError):
        board.move_up()


## test that GameWonError is raised when reaching 2048 via down move
def test_win_on_reaching_2048_down():
    # create an arbitrary board
    board = create_empty_board()
    board.board = [[0, 0, 0, 0], [0, 0, 0, 0], [1024, 0, 0, 0], [1024, 0, 0, 0]]
    board.occupied_tiles = 2

    with pytest.raises(GameWonError):
        board.move_down()


## test custom winning tile
def test_custom_winning_tile():
    # create an arbitrary board
    board = create_empty_board(winning_tile=128)
    board.board = [[64, 64, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    board.occupied_tiles = 2

    with pytest.raises(GameWonError):
        board.move_left()


# test that game doesn't end before reaching winning tile
def test_no_win_before_target():
    # create an arbitrary board
    board = create_empty_board()
    board.board = [[512, 512, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    board.occupied_tiles = 2

    random.seed(42)
    # Should not raise GameWonError (creates 1024, not 2048)
    board.move_left()
    assert board.board[0][0] == 1024


# test game over conditions


## test that add_random_tile raises GameOverError on full board
def test_add_random_tile_on_full_board():
    # create an arbitrary board
    board = create_empty_board()
    # Fill the board completely
    board.board = [
        [2, 4, 8, 16],
        [32, 64, 128, 256],
        [512, 1024, 2, 4],
        [8, 16, 32, 64],
    ]
    board.occupied_tiles = 16

    with pytest.raises(GameOverError):
        board.add_random_tile()


## test that no movement is possible when tiles are already against the edge
def test_no_movement_possible():
    # create an arbitrary board
    board = create_empty_board()
    board.board = [[2, 0, 0, 0], [4, 0, 0, 0], [8, 0, 0, 0], [0, 0, 0, 0]]
    board.occupied_tiles = 3

    random.seed(42)
    # Tiles already at left edge, but move still adds a new tile
    board.move_left()

    # Position of existing tiles shouldn't change (except new tile added)
    assert board.board[0][0] == 2
    assert board.board[1][0] == 4
    assert board.board[2][0] == 8
