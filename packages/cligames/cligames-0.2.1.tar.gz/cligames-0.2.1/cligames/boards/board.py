from abc import ABC, abstractmethod
from typing import Any


class Board(ABC):
    NUM_ROWS: int
    NUM_COLUMNS: int
    MOVES: list[Any]
    PIECE_1: str
    PIECE_2: str

    @abstractmethod
    def print_board(self) -> None:
        """
        Prints the board.
        """
        pass

    @abstractmethod
    def parse_move(self, unparsed_move: str) -> Any:
        """
        Parses the given move.
        """
        pass

    @abstractmethod
    def board_full(self) -> bool:
        """
        Checks if the board is full.
        """
        pass

    @abstractmethod
    def reset_board(self) -> None:
        """
        Resets the board to its original state.
        """
        pass

    @abstractmethod
    def place_piece(self, piece: str, position: Any, situation: str) -> None:
        """
        Places the given piece in the given position.
        """
        pass

    @abstractmethod
    def remove_piece(self, piece: str, position: Any) -> None:
        """
        Removes the given piece from the given position.
        """
        pass

    @abstractmethod
    def state_scanner(self, *pieces: str) -> int:
        """
        Scans the board for the given match of pieces.
        """
        pass

    @abstractmethod
    def player_score(self, player_piece: str, *pieces: int) -> int:
        """
        Returns the score of the given player.
        """
        pass

    @abstractmethod
    def check_for_win(self, player_piece: str) -> bool:
        """
        Checks if the player has won the game.
        """
        pass
