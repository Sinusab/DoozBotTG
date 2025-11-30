# src/handlers.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from .game import TicTacToeGame, GAMES, WAITING
from .utils import build_board

import logging
logger = logging.getLogger(__name__)


async def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id

    await update.message.reply_text(
        "برای شروع بازی روی دکمه زیر کلیک کنید:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("آماده‌ام 🎮", callback_data=f"ready_{chat_id}")]
        ])
    )


async def on_ready(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    chat_id = query.message.chat_id

    # ساخت waiting list برای چت
    WAITING.setdefault(chat_id, set())

    # اضافه کردن بازیکن
    WAITING[chat_id].add(user.id)
    await query.edit_message_text(f"@{user.username} آماده است. منتظر حریف...")

    # اگر دو نفر آماده بودند → بازی را شروع کن
    if len(WAITING[chat_id]) >= 2:
        p1, p2 = list(WAITING[chat_id])[:2]
        WAITING[chat_id].remove(p1)
        WAITING[chat_id].remove(p2)

        game = TicTacToeGame(p1, p2, chat_id)
        GAMES[game.id] = game

        # ذخیره username
        game.usernames[p1] = (await context.bot.get_chat(p1)).username
        game.usernames[p2] = (await context.bot.get_chat(p2)).username

        # اعلان شروع بازی
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🎮 بازی شروع شد!\nنوبت @{game.usernames[p1]} {game.symbols[p1]} است.",
            reply_markup=build_board(game)
        )


async def make_move(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    try:
        _, index, game_id = query.data.split("_")
        index = int(index)
    except:
        return

    if game_id not in GAMES:
        await query.edit_message_text("بازی تمام شده.")
        return

    game = GAMES[game_id]

    if query.message.chat_id != game.chat_id:
        await query.edit_message_text("این بازی متعلق به چت دیگری است.")
        return

    user_id = query.from_user.id
    if user_id != game.get_current_player():
        await query.answer("نوبت شما نیست!")
        return

    ok = game.make_move(index)
    if not ok:
        await query.answer("این خانه پر است!")
        return

    # بررسی نتیجه
    winner = TicTacToeGame.check_winner(game.board)

    if winner:
        if winner == "draw":
            await query.edit_message_text("🤝 بازی مساوی شد!")
        else:
            player = game.get_next_player()  
            await query.edit_message_text(f"🏆 @{game.usernames[player]} برنده شد!")
        del GAMES[game_id]
        return

    # ادامه بازی
    next_player = game.get_current_player()
    await query.edit_message_text(
        text=f"نوبت @{game.usernames[next_player]} {game.symbols[next_player]}.",
        reply_markup=build_board(game)
    )
