from rich.console import Console
from rich.table import Table
from .board import Board


console = Console()


class Tictactoe(Board):
    NUM_ROWS = 3
    NUM_COLUMNS = 3
    MOVES = [
        (0, 0),
        (0, 1),
        (0, 2),
        (1, 0),
        (1, 1),
        (1, 2),
        (2, 0),
        (2, 1),
        (2, 2),
    ]
    PIECE_1 = "[bold red]X[/bold red]"
    PIECE_2 = "[bold cyan]O[/bold cyan]"
    __slots__ = "b"

    def __init__(self):
        self.b = [[" " for _ in range(self.NUM_ROWS)] for _ in range(self.NUM_COLUMNS)]

    def print_board(self):
        table = Table(show_lines=True, show_header=False, show_footer=True)

        table.add_column(footer="")
        for i in range(self.NUM_COLUMNS):
            table.add_column(footer=f"[dim]{str(i)}[/dim]")

        for j in range(self.NUM_ROWS - 1, -1, -1):
            table.add_row(
                f"[dim]{str(j)}[/dim]",
                *(str(self.b[i][j]) for i in range(self.NUM_COLUMNS)),
            )

        console.print(table)

    def parse_move(self, unparsed_move):
        try:
            if unparsed_move.strip()[0] != "(" or unparsed_move.strip()[-1] != ")":
                return None
            player_move = tuple(
                [int(val.strip()) for val in unparsed_move.strip()[1:-1].split(",")]
            )
            for move in self.MOVES:
                if player_move == move:
                    return player_move
            return None
        except ValueError:
            return None

    def board_full(self):
        for i in range(0, self.NUM_COLUMNS):
            for j in range(0, self.NUM_ROWS):
                if self.b[i][j] == " ":
                    return False
        return True

    def reset_board(self):
        for i in range(0, self.NUM_COLUMNS):
            for j in range(0, self.NUM_ROWS):
                self.b[i][j] = " "

    def place_piece(self, piece, position, situation):
        pos_x, pos_y = position
        if self.b[pos_x][pos_y] == " ":
            self.b[pos_x][pos_y] = piece
            return
        if situation == "game":
            unparsed_move = input(
                "This position is taken. Please choose a different one: "
            ).strip()
            move = self.parse_move(unparsed_move)
            while move is None:
                unparsed_move = input("Not a valid move. Choose again: ").strip()
                move = self.parse_move(unparsed_move)
            self.place_piece(piece, move, "game")
        else:
            return "full"

    def remove_piece(self, piece, position):
        pos_x, pos_y = position
        if self.b[pos_x][pos_y] == piece:
            self.b[pos_x][pos_y] = " "
            return

    def state_scanner(self, piece1, piece2, piece3):
        score = 0
        # east scan
        for j in range(0, self.NUM_ROWS):
            if (
                (self.b[0][j] == piece1)
                and (self.b[1][j] == piece2)
                and (self.b[2][j] == piece3)
            ):
                score += 1
        # north scan
        for i in range(0, self.NUM_COLUMNS):
            if (
                (self.b[i][0] == piece1)
                and (self.b[i][1] == piece2)
                and (self.b[i][2] == piece3)
            ):
                score += 1
        # north east scan
        if (
            (self.b[0][0] == piece1)
            and (self.b[1][1] == piece2)
            and (self.b[2][2] == piece3)
        ):
            score += 1
        # north east reverse scan
        if (
            (self.b[0][2] == piece1)
            and (self.b[1][1] == piece2)
            and (self.b[2][0] == piece3)
        ):
            score += 1
        return score

    def player_score(self, piece, one_score, two_score, three_score):
        score = 0
        score += one_score * self.state_scanner(piece, " ", " ")
        score += one_score * self.state_scanner(" ", piece, " ")
        score += one_score * self.state_scanner(" ", " ", piece)
        score += two_score * self.state_scanner(piece, piece, " ")
        score += two_score * self.state_scanner(piece, " ", piece)
        score += two_score * self.state_scanner(" ", piece, piece)
        score += three_score * self.state_scanner(piece, piece, piece)
        return score

    def check_for_win(self, player_piece):
        if self.state_scanner(player_piece, player_piece, player_piece) > 0:
            return True
        else:
            return False
