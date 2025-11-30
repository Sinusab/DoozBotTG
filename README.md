# 🎮 DoozBotTG  
A modern, fully asynchronous Telegram Tic-Tac-Toe bot built with **Python** and **python-telegram-bot v20+**, featuring clean architecture, modular game logic, and an interactive inline keyboard interface.

---

## 🚀 Features

- Fully asynchronous PTB v20+ implementation  
- Two-player matchmaking inside group chats  
- Real-time Tic-Tac-Toe board using Inline Keyboards  
- Turn-based gameplay with move validation  
- Win, lose, and draw detection  
- Clean modular architecture (`main`, `handlers`, `game`, `utils`)  
- Lightweight — no database required  
- Safe environment variable handling via `.env`

---

## 🧠 Tech Stack

- Python 3.10+  
- python-telegram-bot 20.7  
- python-dotenv  
- OOP-based game engine  

---

## 📁 Project Structure

```
DoozBotTG/
│
├── src/
│   ├── main.py            # Entry point of the bot
│   ├── handlers.py        # Telegram command & callback handlers
│   ├── game.py            # Core TicTacToe game logic
│   ├── utils.py           # Helper utilities (board builder, etc.)
│   ├── config.py          # Token & environment loader
│   └── __init__.py
│
├── requirements.txt
└── README.md
```

---

## 🔧 Installation

Clone the repository:

```bash
git clone https://github.com/Sinusab/DoozBotTG.git
cd DoozBotTG
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

Create a `.env` file in the project root:

```
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
```

Do not commit this file.

---

## ▶️ Running the Bot

Run from the project root:

```bash
python -m src.main
```

---

## 🎮 How It Works

1. User sends `/start`
2. Bot shows a "Ready" button
3. Two players click "Ready"
4. Bot matches both players
5. Game board appears (inline keyboard)
6. Players take turns selecting cells
7. Bot detects:
   - X wins  
   - O wins  
   - Draw  
8. Game ends automatically

---

## 🤝 Contributing

Pull requests are welcome.  
Feel free to open issues for bugs or enhancements.

---

## 📝 License

This project is licensed under the MIT License.
