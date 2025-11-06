import math
import collections
from rich import print
from .player import Player
from ..boards.board import Board


class Computer(Player):
    def move(self, board: Board):
        print("Player " + self.piece + " is choosing...", end=" ", flush=True)
        move = self.minimax(board, 0, 6, -math.inf, math.inf)
        print("")
        return move

    def minimax(
        self,
        board: Board,
        current_depth: int,
        max_depth: int,
        alpha: float,
        beta: float,
    ):
        board_score = 0
        level = collections.deque([])
        if (
            (current_depth == max_depth)
            or (board.board_full() == True)
            or board.check_for_win(self.piece)
            or board.check_for_win(self.opponent_piece)
        ):
            board_score += board.player_score(
                self.piece, 1, 100, 100000
            )  # player evaluation (positive)
            board_score -= board.player_score(
                self.opponent_piece, 1, 100, 100000
            )  # opponent evaluation (negative)
            return board_score
        if current_depth == 0:
            for move in board.MOVES:
                if board.place_piece(self.piece, move, "simulation") != "full":
                    current_val = self.minimax(
                        board, current_depth + 1, max_depth, alpha, beta
                    )
                    level.append(current_val)
                    board.remove_piece(self.piece, move)
                    alpha = max(alpha, current_val)
                else:
                    level.append(-math.inf)
            chosen_move = board.MOVES[level.index(max(level))]
            return chosen_move
        elif current_depth % 2 == 0:
            best_val = -math.inf
            for move in board.MOVES:
                if board.place_piece(self.piece, move, "simulation") != "full":
                    current_val = self.minimax(
                        board, current_depth + 1, max_depth, alpha, beta
                    )
                    best_val = max(best_val, current_val)
                    board.remove_piece(self.piece, move)
                    alpha = max(alpha, current_val)
                    if alpha >= beta:
                        break
            return best_val
        else:
            best_val = math.inf
            for move in board.MOVES:
                if board.place_piece(self.opponent_piece, move, "simulation") != "full":
                    current_val = self.minimax(
                        board, current_depth + 1, max_depth, alpha, beta
                    )
                    best_val = min(best_val, current_val)
                    board.remove_piece(self.opponent_piece, move)
                    beta = min(beta, current_val)
                    if alpha >= beta:
                        break
            return best_val
