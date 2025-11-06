import enum
import typer
from rich import print
from timeit import default_timer as timer
from typing import Optional
from . import boards, players
from .version import __version__


app = typer.Typer(
    pretty_exceptions_show_locals=False,
    add_completion=False,
)


class GameType(enum.Enum):
    CONNECT4 = "connect4"
    TICTACTOE = "tictactoe"


class PlayerType(enum.Enum):
    HUMAN = "human"
    COMPUTER = "computer"


class Game:
    def __init__(
        self,
        board: boards.Board,
        player_1: players.Player,
        player_2: players.Player,
    ) -> None:
        """
        Initialise a new game.

        Args:
            board: The game board.
            player_1: The first player.
            player_2: The second player.
        """

        self.board = board
        self.player_1 = player_1
        self.player_2 = player_2

    def play(self):
        """
        Enter a loop to play the game.
        """

        print("A new game has started.")
        self.board.print_board()
        current_player = self.player_1
        winner = ""

        while not winner:
            # Get the current player's move, and record the time taken
            start = timer()
            current_player_move = current_player.move(self.board)
            end = timer()

            # Apply the move to the board, and print the board, move and decision time
            self.board.place_piece(current_player.piece, current_player_move, "game")
            self.board.print_board()
            print(f"Player {current_player.piece} chose move {current_player_move}.")
            print(f"Decision time: {round(end - start, 3)} seconds")

            if self.board.check_for_win(current_player.piece):
                # If the board is in a winning state, the current player wins
                winner = current_player.piece
            elif self.board.board_full():
                # Otherwise, if the board is full, the game is a draw
                winner = "draw"
            else:
                # If the game is still ongoing, switch to the other player
                if current_player == self.player_1:
                    current_player = self.player_2
                else:
                    current_player = self.player_1

        if winner == "draw":
            print("Game ended in a draw.")
        else:
            print(f"Player {winner} wins! Game Over.")


def version_callback(value: bool):
    if value:
        print(__version__)
        raise typer.Exit()


@app.command(no_args_is_help=True, help="Welcome to CLI Games.")
def run(
    game: GameType,
    player1: Optional[PlayerType] = typer.Option(
        PlayerType.HUMAN.value,
        "-p1",
        "--player1",
        help="Choose the type of player for player 1.",
    ),
    player2: Optional[PlayerType] = typer.Option(
        PlayerType.COMPUTER.value,
        "-p2",
        "--player2",
        help="Choose the type of player for player 2.",
    ),
    version: Optional[bool] = typer.Option(
        None,
        "-v",
        "--version",
        callback=version_callback,
        help="Show the program version number and exit.",
    ),
):
    """
    CLI entry point for the game.
    """

    # Assign the board based on the game type
    if game == GameType.CONNECT4:
        board = boards.Connect4()
    else:
        board = boards.Tictactoe()

    # Assign player1 based on the player type
    if player1 == PlayerType.HUMAN:
        p1 = players.Human(board.PIECE_1, board.PIECE_2)
    else:
        p1 = players.Computer(board.PIECE_1, board.PIECE_2)

    # Assign player2 based on the player type
    if player2 == PlayerType.HUMAN:
        p2 = players.Human(board.PIECE_2, board.PIECE_1)
    else:
        p2 = players.Computer(board.PIECE_2, board.PIECE_1)

    # Start the game
    g = Game(board, p1, p2)
    g.play()


def main():
    app()
