import os
import random
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackContext, CommandHandler, CallbackQueryHandler

# ذخیره بازی‌ها و لیست انتظار برای هر چت
games = {}  # بازی‌های فعال
waiting_players = {}  # لیست انتظار برای هر چت (chat_id -> [user_ids])

# ایجاد تخته بازی
def create_board(game_id):
    board = games[game_id]['board']
    buttons = []
    for i in range(0, 9, 3):
        row = [
            InlineKeyboardButton(board[i], callback_data=f"move_{i}_{game_id}"),
            InlineKeyboardButton(board[i + 1], callback_data=f"move_{i + 1}_{game_id}"),
            InlineKeyboardButton(board[i + 2], callback_data=f"move_{i + 2}_{game_id}")
        ]
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

# بررسی برنده یا مساوی
def check_winner(board):
    winning_combinations = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),  # ردیف‌ها
        (0, 3, 6), (1, 4, 7), (2, 5, 8),  # ستون‌ها
        (0, 4, 8), (2, 4, 6)             # قطری‌ها
    ]
    for a, b, c in winning_combinations:
        if board[a] == board[b] == board[c] != '⬜':
            return board[a]
    if '⬜' not in board:
        return 'مساوی'
    return None

# دستور شروع بازی
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id  # شناسه چت (گروه یا خصوصی)
    username = update.message.from_user.username or f"کاربر_{user_id}"

    # حذف کاربر از بازی‌های قبلی توی این چت
    for game_id in list(games.keys()):
        if user_id in games[game_id]['players'] and games[game_id]['chat_id'] == chat_id:
            del games[game_id]
            other_player = [p for p in games[game_id]['players'] if p != user_id]
            if other_player:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="حریف شما بازی را ترک کرد و بازی لغو شد."
                )

    # حذف کاربر از لیست انتظار توی این چت
    if chat_id in waiting_players and user_id in waiting_players[chat_id]:
        waiting_players[chat_id].remove(user_id)

    # دکمه آماده شدن
    keyboard = [[InlineKeyboardButton("آماده هستم", callback_data=f"ready_{chat_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"@{username}، برای شروع بازی روی دکمه کلیک کنید.", reply_markup=reply_markup)

# پیدا کردن بازیکن دوم و شروع بازی
async def find_player(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    username = query.from_user.username or f"کاربر_{user_id}"

    if not query.data.startswith("ready_"):
        await query.answer("داده‌های ورودی اشتباه است.")
        return

    expected_chat_id = int(query.data.split("_")[1])
    if expected_chat_id != chat_id:
        await query.answer("این دکمه برای چت دیگری است!")
        return

    # اگه این چت لیست انتظار نداره، بسازیم
    if chat_id not in waiting_players:
        waiting_players[chat_id] = []

    if user_id in waiting_players[chat_id]:
        await query.answer("شما در حال انتظار هستید!")
        return
    for game_id, game in games.items():
        if user_id in game['players'] and game['chat_id'] == chat_id:
            await query.answer("شما در یک بازی دیگر هستید!")
            return

    if not waiting_players[chat_id]:
        waiting_players[chat_id].append(user_id)
        await query.edit_message_text(f"@{username} آماده است. منتظر بازیکن دوم باشید...")
    else:
        player1 = waiting_players[chat_id].pop(0)
        game_id = str(uuid.uuid4())
        games[game_id] = {
            'board': ['⬜'] * 9,
            'players': [player1, user_id],
            'current_turn': 0,
            'player_symbols': {player1: '❌', user_id: '⭕'},
            'usernames': {player1: (await context.bot.get_chat(player1)).username or f"کاربر_{player1}",
                          user_id: username},
            'chat_id': chat_id  # اضافه کردن chat_id به بازی
        }
        await query.edit_message_text("بازی شروع شد!")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"بازی شروع شد! نوبت @{games[game_id]['usernames'][player1]} ❌ است.",
            reply_markup=create_board(game_id)
        )

# حرکت در بازی
async def make_move(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    game_id = query.data.split('_')[2]
    index = int(query.data.split('_')[1])

    if game_id not in games:
        await query.answer("این بازی وجود ندارد!")
        return

    game = games[game_id]
    if game['chat_id'] != chat_id:
        await query.answer("این بازی مربوط به چت دیگری است!")
        return

    current_player = game['players'][game['current_turn']]
    next_player = game['players'][(game['current_turn'] + 1) % 2]

    if user_id != current_player:
        await query.answer("نوبت شما نیست!")
        return

    if game['board'][index] != '⬜':
        await query.answer("این خانه قبلاً پر شده است!")
        return

    game['board'][index] = game['player_symbols'][user_id]
    game['current_turn'] = (game['current_turn'] + 1) % 2

    result = check_winner(game['board'])
    if result:
        if result == 'مساوی':
            await query.edit_message_text("بازی مساوی شد!", reply_markup=None)
            await context.bot.send_message(chat_id=chat_id, text="بازی مساوی شد!", reply_markup=None)
        else:
            winner = '@' + game['usernames'][user_id]
            await query.edit_message_text(f"{winner} برنده شد!", reply_markup=None)
            await context.bot.send_message(chat_id=chat_id, text=f"{winner} برنده شد!", reply_markup=None)
        del games[game_id]
        return

    await query.edit_message_text(
        text=f"نوبت @{game['usernames'][next_player]} {game['player_symbols'][next_player]}",
        reply_markup=create_board(game_id)
    )
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"نوبت @{game['usernames'][next_player]} {game['player_symbols'][next_player]}",
        reply_markup=create_board(game_id)
    )

# تابع اصلی
def main():
    try:
        app = Application.builder().token(os.getenv("TOKEN")).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(find_player, pattern=r"ready_\d+"))
        app.add_handler(CallbackQueryHandler(make_move, pattern=r"move_\d+_\w+"))
        app.run_polling()
    except Exception as e:
        print(f"خطا در اجرا: {e}")

if __name__ == "__main__":
    main()
