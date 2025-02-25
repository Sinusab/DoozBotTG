import random
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackContext, CommandHandler, CallbackQueryHandler

# ذخیره بازی‌ها و لیست انتظار
games = {}
waiting_players = []
TOKEN = os.getenv("TOKEN")

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
            return board[a]  # نماد برنده (❌ یا ⭕)
    if '⬜' not in board:
        return 'مساوی'
    return None

# دستور شروع بازی
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or f"کاربر_{user_id}"

    # بررسی اینکه کاربر در بازی دیگری نباشد
    for game_id, game in games.items():
        if user_id in game['players']:
            await update.message.reply_text("شما در حال حاضر در یک بازی هستید!")
            return

    # دکمه آماده شدن
    keyboard = [[InlineKeyboardButton("آماده هستم", callback_data="ready_to_play")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"@{username}، برای شروع بازی روی دکمه کلیک کنید.", reply_markup=reply_markup)

# پیدا کردن بازیکن دوم و شروع بازی
async def find_player(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    username = query.from_user.username or f"کاربر_{user_id}"

    if query.data != "ready_to_play":
        await query.answer("داده‌های ورودی اشتباه است.")
        return

    # بررسی اینکه کاربر در لیست انتظار یا بازی دیگری نباشد
    if user_id in waiting_players:
        await query.answer("شما در حال انتظار هستید!")
        return
    for game_id, game in games.items():
        if user_id in game['players']:
            await query.answer("شما در یک بازی دیگر هستید!")
            return

    if not waiting_players:  # نفر اول
        waiting_players.append(user_id)
        await query.edit_message_text(f"@{username} آماده است. منتظر بازیکن دوم باشید...")
    else:  # نفر دوم
        player1 = waiting_players.pop(0)
        game_id = str(uuid.uuid4())  # شناسه منحصربه‌فرد برای بازی
        games[game_id] = {
            'board': ['⬜'] * 9,
            'players': [player1, user_id],
            'current_turn': 0,
            'player_symbols': {player1: '❌', user_id: '⭕'},
            'usernames': {player1: (await context.bot.get_chat(player1)).username or f"کاربر_{player1}",
                          user_id: username}
        }
        # شروع بازی
        await query.edit_message_text("بازی شروع شد!")
        await context.bot.send_message(
            chat_id=player1,
            text=f"بازی شروع شد! نوبت شماست (@{games[game_id]['usernames'][player1]} ❌)",
            reply_markup=create_board(game_id)
        )
        await query.message.reply_text(
            f"بازی شروع شد! نوبت @{games[game_id]['usernames'][player1]} ❌ است.",
            reply_markup=create_board(game_id)
        )

# حرکت در بازی
async def make_move(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    game_id = query.data.split('_')[2]
    index = int(query.data.split('_')[1])

    # بررسی وجود بازی
    if game_id not in games:
        await query.answer("این بازی وجود ندارد!")
        return

    game = games[game_id]
    current_player = game['players'][game['current_turn']]
    next_player = game['players'][(game['current_turn'] + 1) % 2]

    # بررسی نوبت
    if user_id != current_player:
        await query.answer("نوبت شما نیست!")
        return

    # بررسی خالی بودن خانه
    if game['board'][index] != '⬜':
        await query.answer("این خانه قبلاً پر شده است!")
        return

    # انجام حرکت
    game['board'][index] = game['player_symbols'][user_id]
    game['current_turn'] = (game['current_turn'] + 1) % 2

    # بررسی وضعیت بازی
    result = check_winner(game['board'])
    if result:
        if result == 'مساوی':
            await query.edit_message_text("بازی مساوی شد!", reply_markup=None)
            await context.bot.send_message(
                chat_id=next_player,
                text="بازی مساوی شد!",
                reply_markup=None
            )
        else:
            winner = '@' + game['usernames'][user_id]
            await query.edit_message_text(f"{winner} برنده شد!", reply_markup=None)
            await context.bot.send_message(
                chat_id=next_player,
                text=f"{winner} برنده شد!",
                reply_markup=None
            )
        del games[game_id]  # حذف بازی پس از پایان
        return

    # به‌روزرسانی تخته و اعلام نوبت بعدی
    await query.edit_message_text(
        text=f"نوبت @{game['usernames'][next_player]} {game['player_symbols'][next_player]}",
        reply_markup=create_board(game_id)
    )
    await context.bot.send_message(
        chat_id=next_player,
        text=f"نوبت شماست (@{game['usernames'][next_player]} {game['player_symbols'][next_player]})",
        reply_markup=create_board(game_id)
    )

# تابع اصلی
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(find_player, pattern="ready_to_play"))
    app.add_handler(CallbackQueryHandler(make_move, pattern=r"move_\d+_\w+"))
    
    app.run_polling()

if __name__ == "__main__":
    main()