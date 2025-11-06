class Player:
    def __init__(self, piece, opponent_piece):
        self.piece = piece
        self.opponent_piece = opponent_piece

    def move(self, board):
        raise NotImplementedError
