from rich.console import Console
from rich.table import Table
from .board import Board

console = Console()


class Connect4(Board):
    NUM_ROWS = 6
    NUM_COLUMNS = 7
    MOVES = [0, 1, 2, 3, 4, 5, 6]
    PIECE_1 = "[bold red]X[/bold red]"
    PIECE_2 = "[bold cyan]O[/bold cyan]"
    __slots__ = "b"

    def __init__(self):
        self.b = [[" " for _ in range(self.NUM_ROWS)] for _ in range(self.NUM_COLUMNS)]

    def print_board(self):
        table = Table(show_lines=True, show_header=False, show_footer=True)
        for i in range(self.NUM_COLUMNS):
            table.add_column(footer=f"[dim]{str(i)}[/dim]")

        for j in range(self.NUM_ROWS - 1, -1, -1):
            table.add_row(*(str(self.b[i][j]) for i in range(self.NUM_COLUMNS)))

        console.print(table)

    def parse_move(self, unparsed_move):
        try:
            player_move = int(unparsed_move.strip())
            for move in self.MOVES:
                if player_move == move:
                    return player_move
            return None
        except ValueError:
            return None

    def board_full(self):
        for i in range(0, self.NUM_COLUMNS):
            if self.b[i][len(self.b[0]) - 1] == " ":
                return False
        return True

    def reset_board(self):
        for i in range(0, self.NUM_COLUMNS):
            for j in range(0, self.NUM_ROWS):
                self.b[i][j] = " "

    def place_piece(self, piece, position, situation):
        for i in range(0, self.NUM_ROWS):
            if self.b[position][i] == " ":
                self.b[position][i] = piece
                return
        if situation == "game":
            unparsed_move = input(
                "This column is full. Please choose a different one: "
            ).strip()
            move = self.parse_move(unparsed_move)
            while move is None:
                unparsed_move = input("Not a valid move. Choose again: ").strip()
                move = self.parse_move(unparsed_move)
            self.place_piece(piece, move, "game")
        else:
            return "full"

    def remove_piece(self, piece, position):
        # loops backwards from top of column down to bottom
        for i in range(self.NUM_ROWS - 1, -1, -1):
            if self.b[position][i] == piece:
                self.b[position][i] = " "
                return

    def state_scanner(self, piece1, piece2, piece3, piece4):
        score = 0
        # east scan
        for i in range(0, self.NUM_COLUMNS - 3):  # [0 - 3]
            for j in range(0, self.NUM_ROWS):  # [0 - 5]
                if (
                    (self.b[i][j] == piece1)
                    and (self.b[i + 1][j] == piece2)
                    and (self.b[i + 2][j] == piece3)
                    and (self.b[i + 3][j] == piece4)
                ):
                    score += 1
        # north scan
        for i in range(0, self.NUM_COLUMNS):
            for j in range(0, self.NUM_ROWS - 3):
                if (
                    (self.b[i][j] == piece1)
                    and (self.b[i][j + 1] == piece2)
                    and (self.b[i][j + 2] == piece3)
                    and (self.b[i][j + 3] == piece4)
                ):
                    score += 1
        # north east scan
        for i in range(0, self.NUM_COLUMNS - 3):
            for j in range(0, self.NUM_ROWS - 3):
                if (
                    (self.b[i][j] == piece1)
                    and (self.b[i + 1][j + 1] == piece2)
                    and (self.b[i + 2][j + 2] == piece3)
                    and (self.b[i + 3][j + 3] == piece4)
                ):
                    score += 1
        # north east reverse scan
        for i in range(0, self.NUM_COLUMNS - 3):
            for j in range(0, self.NUM_ROWS - 3):
                if (
                    (self.b[i + 3][j] == piece1)
                    and (self.b[i + 2][j + 1] == piece2)
                    and (self.b[i + 1][j + 2] == piece3)
                    and (self.b[i][j + 3] == piece4)
                ):
                    score += 1
        return score

    def player_score(self, piece, two_score, three_score, four_score):
        score = 0
        score += self.state_scanner(piece, " ", " ", " ")
        score += self.state_scanner(" ", piece, " ", " ")
        score += self.state_scanner(" ", " ", piece, " ")
        score += self.state_scanner(" ", " ", " ", piece)
        score += two_score * self.state_scanner(piece, piece, " ", " ")
        score += two_score * self.state_scanner(piece, " ", piece, " ")
        score += two_score * self.state_scanner(piece, " ", " ", piece)
        score += two_score * self.state_scanner(" ", piece, " ", piece)
        score += two_score * self.state_scanner(" ", " ", piece, piece)
        score += two_score * self.state_scanner(" ", piece, piece, " ")
        score += three_score * self.state_scanner(piece, piece, piece, " ")
        score += three_score * self.state_scanner(piece, piece, " ", piece)
        score += three_score * self.state_scanner(piece, " ", piece, piece)
        score += three_score * self.state_scanner(" ", piece, piece, piece)
        score += four_score * self.state_scanner(piece, piece, piece, piece)
        return score

    def check_for_win(self, player_piece: str):
        if (
            self.state_scanner(player_piece, player_piece, player_piece, player_piece)
            > 0
        ):
            return True
        else:
            return False
