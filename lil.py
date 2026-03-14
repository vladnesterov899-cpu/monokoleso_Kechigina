import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = '7963812689:AAGH_wl5Kw9X3dtu1xdXRR7UxOJy9i-s6Ck'
logging.basicConfig(level=logging.INFO)


games = {}

EMPTY = "⬜"
CROSS = "❌"
NOUGHT = "⭕"

bot = Bot(token=TOKEN)
dp = Dispatcher()


def create_board():
    return [EMPTY] * 9

def check_winner(board):
    wins = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6)
    ]
    for a, b, c in wins:
        if board[a] == board[b] == board[c] and board[a] != EMPTY:
            return board[a]
    if EMPTY not in board:
        return "Draw"
    return None

def get_available_moves(board):
    return [i for i, cell in enumerate(board) if cell == EMPTY]

def minimax(board, depth, is_maximizing):
    result = check_winner(board)
    if result == NOUGHT: return 10 - depth
    if result == CROSS: return depth - 10
    if result == "Draw": return 0
    
    if is_maximizing:
        best_score = -float('inf')
        for move in get_available_moves(board):
            board[move] = NOUGHT
            score = minimax(board, depth + 1, False)
            board[move] = EMPTY
            best_score = max(score, best_score)
        return best_score
    else:
        best_score = float('inf')
        for move in get_available_moves(board):
            board[move] = CROSS
            score = minimax(board, depth + 1, True)
            board[move] = EMPTY
            best_score = min(score, best_score)
        return best_score

def get_ai_move(board, difficulty):
    available = get_available_moves(board)
    if not available:
        return None
    
    if difficulty == "easy":
        return random.choice(available)
    
    best_score = -float('inf')
    best_move = None
    
    for move in available:
        board[move] = NOUGHT
        score = minimax(board, 0, False)
        board[move] = EMPTY
        
        if score > best_score:
            best_score = score
            best_move = move
            
    return best_move if best_move is not None else random.choice(available)

def get_keyboard(board):
    """Генерирует обычную клавиатуру 3x3"""
    kb = []
    for i in range(0, 9, 3):
        row = []
        for j in range(3):
            cell = board[i + j]
            btn_text = str(i + j + 1) if cell == EMPTY else cell
            row.append(KeyboardButton(text=btn_text))
        kb.append(row)
    
    
    kb.append([KeyboardButton(text="🔄 Заново"), KeyboardButton(text="📊 Меню")])
    
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_menu_keyboard():
    kb = [
        [KeyboardButton(text="🟢 Легко"), KeyboardButton(text="🔴 Сложно")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_main_menu_keyboard():
    kb = [
        [KeyboardButton(text="🎮 Новая игра")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

async def update_game_message(chat_id):
    game = games.get(chat_id)
    if not game or not game.get('active'):
        return

    board = game['board']
    winner = check_winner(board)

    if winner:
        game['active'] = False
        if winner == "Draw":
            text = "🤝 Ничья!"
        elif winner == CROSS:
            text = "🎉 Вы победили!"
        else:
            text = "🤖 Бот победил!"
        
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=get_main_menu_keyboard()
        )
    else:
        text = "🤔 Ваш ход..."
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=get_keyboard(board)
        )

async def make_ai_move(chat_id):
    game = games.get(chat_id)
    if not game or not game.get('active'):
        return

    await asyncio.sleep(0.5)
    
    board = game['board']
    difficulty = game.get('difficulty', 'hard')
    
    move = get_ai_move(board, difficulty)
    if move is not None:
        board[move] = NOUGHT
        
        winner = check_winner(board)
        if winner:
            game['active'] = False
            if winner == "Draw":
                text = "🤝 Ничья!"
            elif winner == CROSS:
                text = "🎉 Вы победили!"
            else:
                text = "🤖 Бот победил!"
            
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await update_game_message(chat_id)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот Крестики-Нолики.\n\n"
        "Выберите сложность:",
        reply_markup=get_menu_keyboard()
    )

@dp.message(F.text == "📊 Меню")
async def cmd_menu(message: types.Message):
    await message.answer(
        "🎮 Главное меню\n\nВыберите сложность:",
        reply_markup=get_menu_keyboard()
    )

@dp.message(F.text.in_(["🟢 Легко", "🔴 Сложно"]))
async def start_game(message: types.Message):
    chat_id = message.chat.id
    difficulty = "easy" if message.text == "🟢 Легко" else "hard"
    
    games[chat_id] = {
        'board': create_board(),
        'active': True,
        'difficulty': difficulty
    }
    
    await message.answer(
        text="🤔 Ваш ход...",
        reply_markup=get_keyboard(games[chat_id]['board'])
    )

@dp.message(F.text == "🎮 Новая игра")
async def new_game(message: types.Message):
    await message.answer(
        "🎮 Выберите сложность:",
        reply_markup=get_menu_keyboard()
    )

@dp.message(F.text == "🔄 Заново")
async def handle_restart(message: types.Message):
    chat_id = message.chat.id
    
    if chat_id not in games:
        await message.answer("Сначала начните игру!", reply_markup=get_main_menu_keyboard())
        return

    difficulty = games[chat_id].get('difficulty', 'hard')
    
    games[chat_id] = {
        'board': create_board(),
        'active': True,
        'difficulty': difficulty
    }
    
    await message.answer(
        text="🤔 Ваш ход...",
        reply_markup=get_keyboard(games[chat_id]['board'])
    )

@dp.message(F.text.in_(["1", "2", "3", "4", "5", "6", "7", "8", "9"]))
async def handle_move(message: types.Message):
    chat_id = message.chat.id
    
    if chat_id not in games or not games[chat_id].get('active'):
        await message.answer("⚠️ Начните новую игру!", reply_markup=get_main_menu_keyboard())
        return

    game = games[chat_id]
    cell_index = int(message.text) - 1
    board = game['board']
    
    if board[cell_index] != EMPTY:
        await message.answer("⛔ Клетка занята! Выберите другую.", reply_markup=get_keyboard(board))
        return

    board[cell_index] = CROSS
    
    winner = check_winner(board)
    if winner:
        game['active'] = False
        if winner == "Draw":
            text = "🤝 Ничья!"
        elif winner == CROSS:
            text = "🎉 Вы победили!"
        else:
            text = "🤖 Бот победил!"
        
        await message.answer(text=text, reply_markup=get_main_menu_keyboard())
        return
    
    await update_game_message(chat_id)
    await make_ai_move(chat_id)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())