from rich.prompt import Prompt
from .player import Player


class Human(Player):
    def move(self, board):
        unparsed_move = Prompt.ask("Player " + self.piece + " - choose a move").strip()
        move = board.parse_move(unparsed_move)
        while move is None:
            unparsed_move = Prompt.ask("Not a valid move. Choose again").strip()
            move = board.parse_move(unparsed_move)
        return move
