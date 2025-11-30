# src/game.py

import uuid

class TicTacToeGame:
    def __init__(self, player1, player2, chat_id):
        self.id = str(uuid.uuid4())
        self.chat_id = chat_id
        
        self.players = [player1, player2]
        self.symbols = {player1: "❌", player2: "⭕"}
        self.usernames = {}
        
        self.board = ["⬜"] * 9
        self.turn = 0   # index of players list

    def get_current_player(self):
        return self.players[self.turn]

    def get_next_player(self):
        return self.players[(self.turn + 1) % 2]

    def make_move(self, index):
        if self.board[index] != "⬜":
            return False  # invalid move
        
        player = self.get_current_player()
        self.board[index] = self.symbols[player]
        self.turn = (self.turn + 1) % 2
        return True

    @staticmethod
    def check_winner(board):
        combos = [
            (0,1,2),(3,4,5),(6,7,8),
            (0,3,6),(1,4,7),(2,5,8),
            (0,4,8),(2,4,6)
        ]
        for a,b,c in combos:
            if board[a] == board[b] == board[c] != "⬜":
                return board[a]
        
        if "⬜" not in board:
            return "draw"
        
        return None

# global state
GAMES = {}
WAITING = {}
