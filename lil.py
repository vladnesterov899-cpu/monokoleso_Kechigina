import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional, Dict

# --- КОНФИГУРАЦИЯ ---
TOKEN = "ВАШ_ТОКЕН_ОТ_BOTFATHER"

# --- ЛОГИКА ИГРЫ ---

class GameState:
    def init(self):
        # Явно инициализируем поле 3x3
        self.board = [""] * 9
        self.player_turn = True  # True = ход игрока (X)
        self.game_active = True

# Глобальное хранилище состояний {user_id: GameState}
games = {}

WIN_COMBINATIONS = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8],
    [0, 3, 6], [1, 4, 7], [2, 5, 8],
    [0, 4, 8], [2, 4, 6]
]

def check_winner(board: List[str]) -> Optional[str]:
    """Проверяет победителя. Возвращает 'X', 'O', 'Draw' или None."""
    for combo in WIN_COMBINATIONS:
        a, b, c = combo
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    if "" not in board:
        return "Draw"
    return None

def get_bot_move(board: List[str]) -> Optional[int]:
    """Возвращает индекс хода бота."""
    # 1. Попытка выиграть
    for i in range(9):
        if board[i] == "":
            board[i] = "O"
            if check_winner(board) == "O":
                board[i] = ""
                return i
            board[i] = ""    
    # 2. Блокировка игрока
    for i in range(9):
        if board[i] == "":
            board[i] = "X"
            if check_winner(board) == "X":
                board[i] = ""
                return i
            board[i] = ""
            
    # 3. Занять центр
    if board[4] == "":
        return 4
        
    # 4. Случайный ход
    available = [i for i, x in enumerate(board) if x == ""]
    return random.choice(available) if available else None

def create_keyboard(board: List[str], active: bool) -> InlineKeyboardMarkup:
    """Создает клавиатуру игрового поля."""
    builder = InlineKeyboardBuilder()
    emojis = {"X": "❌", "O": "⭕", "": "➖"}
    
    for i in range(9):
        symbol = emojis.get(board[i], "➖")
        # Кнопка активна только если игра идет и клетка пуста
        is_clickable = active and board[i] == ""
        callback = f"move_{i}" if is_clickable else "ignore"
        
        builder.button(text=symbol, callback_data=callback)
    
    builder.adjust(3, 3, 3)
    
    if not active:
        builder.button(text="🔄 Новая игра", callback_data="restart")
        builder.adjust(3, 3, 3, 1)
        
    return builder.as_markup()

# --- ХЕНДЛЕРЫ ---

dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    games[user_id] = GameState()
    await message.answer(
        "Привет! Я бот для игры в Крестики-Нолики.\n"
        "Ты играешь за ❌, я за ⭕.\n"        "Нажми /game, чтобы начать новую партию."
    )

@dp.message(Command("game"))
async def cmd_game(message: types.Message):
    user_id = message.from_user.id
    # Пересоздаем состояние для пользователя
    state = GameState()
    games[user_id] = state
    
    await message.answer("Новая игра! Твой ход.", reply_markup=create_keyboard(state.board, True))

@dp.callback_query(F.data.startswith("move_"))
async def process_move(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    
    # 1. Проверка: есть ли игра у этого пользователя
    if user_id not in games:
        await callback.answer("Игра не найдена. Начните заново /game", show_alert=True)
        return

    game = games[user_id]
    
    # 2. Проверка: существует ли атрибут board (защита от ошибок)
    if not hasattr(game, 'board'):
        await callback.answer("Ошибка состояния. Начните /game", show_alert=True)
        return

    # 3. Проверка: активна ли игра
    if not game.game_active:
        await callback.answer("Игра закончена. Нажмите кнопку рестарта.", show_alert=True)
        return
    # 4. Проверка: чей сейчас ход
    if not game.player_turn:
        await callback.answer("Сейчас мой ход, подождите!", show_alert=True)
        return

    # Получаем индекс клетки
    try:
        move_idx = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer("Некорректный ход.", show_alert=True)
        return

    # Проверка: не занята ли клетка
    if game.board[move_idx] != "":
        await callback.answer("Клетка занята!", show_alert=True)
        return
    # --- ХОД ИГРОКА ---
    game.board[move_idx] = "X"
    game.player_turn = False
    
    # Проверка победы игрока
    winner = check_winner(game.board)
    if winner:
        game.game_active = False
        msg = "🎉 Ты победил!" if winner == "X" else ("🤝 Ничья!" if winner == "Draw" else "🤖 Я победил!")
        await callback.message.edit_text(f"Игра окончена!\n{msg}", reply_markup=create_keyboard(game.board, False))
        return

    # Визуально обновляем поле перед ходом бота
    await callback.message.edit_text("Я думаю...", reply_markup=create_keyboard(game.board, False))
    await asyncio.sleep(0.6)

    # --- ХОД БОТА ---
    bot_move = get_bot_move(game.board)
    if bot_move is not None:
        game.board[bot_move] = "O"
        
        winner = check_winner(game.board)
        if winner:
            game.game_active = False
            msg = "🎉 Ты победил!" if winner == "X" else ("🤝 Ничья!" if winner == "Draw" else "🤖 Я победил!")
            await callback.message.edit_text(f"Игра окончена!\n{msg}", reply_markup=create_keyboard(game.board, False))
            return

    game.player_turn = True
    await callback.message.edit_text("Твой ход (❌)", reply_markup=create_keyboard(game.board, True))

@dp.callback_query(F.data == "restart")
async def process_restart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    games[user_id] = GameState()
    await callback.message.edit_text("Новая игра началась! Твой ход.", reply_markup=create_keyboard(games[user_id].board, True))

# --- ЗАПУСК ---

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)

if __name__ == "main__":
    asyncio.run(main())