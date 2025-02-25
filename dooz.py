import os
import random
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackContext, CommandHandler, CallbackQueryHandler
import asyncio
import logging

# تنظیم لاگ برای دیباگ
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
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
    chat_id = update.message.chat_id
    # ساخت دکمه‌ای که برای همه کاربران در چت قابل استفاده باشه
    keyboard = [[InlineKeyboardButton("آماده هستم", callback_data=f"ready_{chat_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "برای شروع بازی روی دکمه کلیک کنید!",
        reply_markup=reply_markup
    )
    logger.info(f"Bot started in chat {chat_id}")

# پیدا کردن حریف و شروع بازی
async def find_player(update: Update, context: CallbackContext):
    query = update.callback_query
    logger.info(f"Callback received: data={query.data}, user_id={query.from_user.id}, chat_id={query.message.chat_id}")
    await query.answer()  # پاسخ سریع به کلیک کاربر
    
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    username = query.from_user.username or f"کاربر_{user_id}"

    if not query.data.startswith("ready_"):
        logger.warning(f"Invalid callback data format: {query.data}")
        await query.answer("داده نادرست است!")
        return

    try:
        # پارسیگ دقیق‌تر داده‌های callback (فقط chat_id)
        parts = query.data.split("_")
        if len(parts) != 2:
            logger.error(f"Invalid callback data structure: {query.data}")
            await query.edit_message_text("فرمت دکمه نادرست است!")
            return

        # تبدیل chat_id به عدد (حتی اگر با خط تیره شروع بشه)
        try:
            expected_chat_id = int(parts[1])
        except ValueError:
            logger.error(f"Invalid chat_id format in callback data: {parts[1]}")
            await query.edit_message_text("فرمت چت نادرست است!")
            return

        logger.info(f"Parsed data: chat_id={expected_chat_id}")

        if expected_chat_id != chat_id:
            await query.edit_message_text("این دکمه برای این چت نیست!")
            return

        # اگر لیست انتظار برای این چت وجود نداره، بسازیم
        if chat_id not in waiting_players:
            waiting_players[chat_id] = []

        # اضافه کردن کاربر به لیست انتظار
        if user_id not in waiting_players[chat_id]:
            waiting_players[chat_id].append(user_id)
            await query.edit_message_text(f"@{username} آماده است. منتظر حریف باشید...")
            logger.info(f"User {username} added to waiting list for chat {chat_id}")
        else:
            await query.answer("شما قبلاً آماده شده‌اید!")

        # اگر دو نفر آماده باشن، بازی رو شروع کن
        if len(waiting_players[chat_id]) >= 2:
            player1 = waiting_players[chat_id].pop(0)
            player2 = waiting_players[chat_id].pop(0)  # برداشتن نفر دوم
            if player1 == player2:  # مطمئن شو دو نفر متفاوت باشن
                logger.warning("Attempted to match same player")
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
                    player2: (await context.bot.get_chat(player2)).username or f"کاربر_{player2}"
                },
                'chat_id': chat_id
            }
            
            await query.edit_message_text("بازی شروع شد!")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"بازی شروع شد! نوبت @{games[game_id]['usernames'][player1]} (❌) است.",
                reply_markup=create_board(game_id)
            )
            logger.info(f"Game started between {games[game_id]['usernames'][player1]} and {games[game_id]['usernames'][player2]} in chat {chat_id}")
            
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
        # حذف وب‌هوک و پاک کردن آپدیت‌های در انتظار
        app.bot.delete_webhook(drop_pending_updates=True)
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(find_player, pattern=r"^ready_[-\d]+$"))  # پترن برای دکمه آماده هستم
        app.add_handler(CallbackQueryHandler(make_move, pattern=r"^move_\d+_\w+$"))  # پترن برای حرکت در بازی
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True, timeout=10)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == "__main__":
    main()
