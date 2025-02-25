import os
import random
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackContext, CommandHandler, CallbackQueryHandler
import asyncio
import logging

# تنظیم لاگ برای دیباگ
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# دیکشنری‌های سراسری برای ذخیره وضعیت بازی
games = {}  # بازی‌های فعال
waiting_players = {}  # بازیکنان در انتظار برای هر چت

# ساخت تخته بازی
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
    chat_id = update.message.chat_id
    username = update.message.from_user.username or f"کاربر_{user_id}"

    keyboard = [[InlineKeyboardButton("آماده هستم", callback_data=f"ready_{chat_id}_{user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"@{username}، برای شروع بازی روی دکمه کلیک کن!",
        reply_markup=reply_markup
    )

# پیدا کردن حریف و شروع بازی
async def find_player(update: Update, context: CallbackContext):
    query = update.callback_query
    logger.info(f"Callback received: {query.data}")
    await query.answer()  # پاسخ سریع به کلیک کاربر
    
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    username = query.from_user.username or f"کاربر_{user_id}"

    if not query.data.startswith("ready_"):
        logger.warning("Invalid callback data format")
        return

    try:
        _, chat_id_str, user_id_str = query.data.split("_")
        expected_chat_id = int(chat_id_str)
        ready_user_id = int(user_id_str)

        if expected_chat_id != chat_id or ready_user_id != user_id:
            await query.edit_message_text("این دکمه برای تو نیست!")
            return

        # اگر لیست انتظار برای این چت وجود نداره، بسازیم
        if chat_id not in waiting_players:
            waiting_players[chat_id] = []

        # اضافه کردن کاربر به لیست انتظار
        if user_id not in waiting_players[chat_id]:
            waiting_players[chat_id].append(user_id)
            await query.edit_message_text(f"@{username} آماده‌ست. منتظر حریف باش...")
        else:
            await query.answer("شما قبلاً آماده شده‌اید!")

        # اگر دو نفر آماده باشن، بازی رو شروع کن
        if len(waiting_players[chat_id]) >= 2:
            player1 = waiting_players[chat_id].pop(0)
            player2 = waiting_players[chat_id].pop(0)  # برداشتن نفر دوم
            if player1 == player2:  # مطمئن شو دو نفر متفاوت باشن
                await query.edit_message_text("لطفاً دوباره امتحان کن!")
                return
            
            game_id = str(uuid.uuid4())
            games[game_id] = {
                'board': ['⬜'] * 9,
                'players': [player1, player2],
                'current_turn': 0,
                'player_symbols': {player1: '❌', player2: '⭕'},
                'usernames': {
                    player1: (await context.bot.get_chat(player1)).username or f"کاربر_{player1}",
                    player2: username
                },
                'chat_id': chat_id
            }
            
            await query.edit_message_text("بازی شروع شد!")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"بازی شروع شد! نوبت @{games[game_id]['usernames'][player1]} (❌) هست.",
                reply_markup=create_board(game_id)
            )
            
    except Exception as e:
        logger.error(f"Error in find_player: {e}")
        await query.edit_message_text("یه خطا پیش اومد. دوباره امتحان کن!")
        return

# انجام حرکت در بازی
async def make_move(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    
    try:
        _, index_str, game_id = query.data.split("_")
        index = int(index_str)
        
        if game_id not in games:
            await query.edit_message_text("این بازی دیگه وجود نداره!")
            return

        game = games[game_id]
        if game['chat_id'] != chat_id:
            await query.edit_message_text("این بازی مال چت دیگه‌ست!")
            return

        current_player = game['players'][game['current_turn']]
        next_player = game['players'][(game['current_turn'] + 1) % 2]

        if user_id != current_player:
            await query.answer("نوبت تو نیست!")
            return

        if game['board'][index] != '⬜':
            await query.answer("این خونه قبلاً پر شده!")
            return

        game['board'][index] = game['player_symbols'][user_id]
        game['current_turn'] = (game['current_turn'] + 1) % 2

        result = check_winner(game['board'])
        if result:
            if result == 'مساوی':
                await query.edit_message_text("بازی مساوی شد!")
            else:
                winner = '@' + game['usernames'][user_id]
                await query.edit_message_text(f"{winner} برنده شد!")
            del games[game_id]
            return

        await query.edit_message_text(
            text=f"نوبت: @{game['usernames'][next_player]} {game['player_symbols'][next_player]}",
            reply_markup=create_board(game_id)
        )

    except Exception as e:
        logger.error(f"Error in make_move: {e}")
        await query.edit_message_text("یه خطا تو حرکت پیش اومد!")

# تابع اصلی
def main():
    try:
        token = os.getenv("TOKEN")
        if not token:
            raise ValueError("توکن در متغیرهای محیطی پیدا نشد!")
            
        app = Application.builder().token(token).build()
        # اضافه کردن اطمینان از حذف وب‌هوک در صورت وجود
        app.bot.delete_webhook(drop_pending_updates=True)
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(find_player, pattern=r"^ready_\d+_\d+$"))  # پترن دقیق‌تر
        app.add_handler(CallbackQueryHandler(make_move, pattern=r"^move_\d+_\w+$"))  # پترن دقیق‌تر
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == "__main__":
    main()
