# src/utils.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def build_board(game):
    board = game.board
    gid = game.id

    buttons = []
    for i in range(0, 9, 3):
        row = [
            InlineKeyboardButton(board[i], callback_data=f"move_{i}_{gid}"),
            InlineKeyboardButton(board[i+1], callback_data=f"move_{i+1}_{gid}"),
            InlineKeyboardButton(board[i+2], callback_data=f"move_{i+2}_{gid}")
        ]
        buttons.append(row)

    return InlineKeyboardMarkup(buttons)
