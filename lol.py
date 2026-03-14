import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ================= КОНФИГУРАЦИЯ =================
TOKEN = '7963812689:AAGH_wl5Kw9X3dtu1xdXRR7UxOJy9i-s6Ck'  # Вставьте сюда токен
logging.basicConfig(level=logging.INFO)

# ================= ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ =================
games = {}  # Хранилище всех игр

# Константы для крестиков-ноликов
EMPTY = "⬜"
CROSS = "❌"
NOUGHT = "⭕"

# ================= ИНИЦИАЛИЗАЦИЯ =================
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================= КЛАВИАТУРЫ =================

def get_main_menu():
    """Главное меню с выбором игр"""
    kb = [
        [KeyboardButton(text="🎮 Крестики-Нолики")],
        [KeyboardButton(text="🔢 Угадай Число")],
        [KeyboardButton(text="ℹ️ Помощь")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_tic_tac_toe_menu():
    """Меню сложности для крестиков-ноликов"""
    kb = [
        [KeyboardButton(text="🟢 Легко"), KeyboardButton(text="🔴 Сложно")],
        [KeyboardButton(text="🔙 Назад")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_number_game_menu():
    """Меню для угадай число"""
    kb = [
        [KeyboardButton(text="🎲 1-50"), KeyboardButton(text="🎲 1-100")],
        [KeyboardButton(text="🔙 Назад")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_tic_tac_toe_keyboard(board):
    """Клавиатура для крестиков-ноликов"""
    kb = []
    for i in range(0, 9, 3):
        row = []
        for j in range(3):
            cell = board[i + j]
            btn_text = str(i + j + 1) if cell == EMPTY else cell
            row.append(KeyboardButton(text=btn_text))
        kb.append(row)
    kb.append([KeyboardButton(text="🔄 Заново"), KeyboardButton(text="🔙 В меню")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_guess_number_keyboard():
    """Клавиатура для угадай число"""
    kb = [
        [KeyboardButton(text="🔢 Ввести число")],
        [KeyboardButton(text="🔄 Заново"), KeyboardButton(text="🔙 В меню")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# ================= ЛОГИКА КРЕСТИКИ-НОЛИКИ =================

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

# ================= ЛОГИКА УГАДАЙ ЧИСЛО =================

def start_number_game(chat_id, max_number):
    """Запускает игру угадай число"""
    number = random.randint(1, max_number)
    games[chat_id] = {
        'type': 'number',
        'number': number,
        'max_number': max_number,
        'attempts': 0,
        'active': True
    }
    return number

# ================= ОБРАБОТЧИКИ =================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я игровой бот.\n\n"
        "Выберите игру:",
        reply_markup=get_main_menu()
    )

@dp.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: types.Message):
    await message.answer(
        "ℹ️ Помощь\n\n"
        "🎮 Крестики-Нолики - классическая игра против бота\n"
        "🔢 Угадай Число - угадайте число от 1 до 50 или 100\n\n"
        "Выберите игру в меню:",
        reply_markup=get_main_menu()
    )

@dp.message(F.text == "🎮 Крестики-Нолики")
async def tic_tac_toe_menu(message: types.Message):
    await message.answer(
        "🎮 Крестики-Нолики\n\n"
        "Выберите сложность:",
        reply_markup=get_tic_tac_toe_menu()
    )

@dp.message(F.text == "🔢 Угадай Число")
async def number_game_menu(message: types.Message):
    await message.answer(
        "🔢 Угадай Число\n\n"
        "Выберите диапазон:",
        reply_markup=get_number_game_menu()
    )

@dp.message(F.text == "🔙 Назад")
async def go_back(message: types.Message):
    await message.answer(
        "🏠 Главное меню",
        reply_markup=get_main_menu()
    )

@dp.message(F.text == "🔙 В меню")
async def go_to_menu(message: types.Message):
    await message.answer(
        "🏠 Главное меню",
        reply_markup=get_main_menu()
    )

# ================= КРЕСТИКИ-НОЛИКИ =================

@dp.message(F.text.in_(["🟢 Легко", "🔴 Сложно"]))
async def start_tic_tac_toe(message: types.Message):
    chat_id = message.chat.id
    difficulty = "easy" if message.text == "🟢 Легко" else "hard"
    
    games[chat_id] = {
        'type': 'tictactoe',
        'board': create_board(),
        'active': True,
        'difficulty': difficulty
    }
    
    await message.answer(
        text="🤔 Ваш ход (1-9)...",
        reply_markup=get_tic_tac_toe_keyboard(games[chat_id]['board'])
    )

@dp.message(F.text == "🔄 Заново")
async def restart_game(message: types.Message):
    chat_id = message.chat.id
    
    if chat_id not in games:
        await message.answer("Сначала начните игру!", reply_markup=get_main_menu())
        return
    
    game_type = games[chat_id].get('type')
    
    if game_type == 'tictactoe':
        difficulty = games[chat_id].get('difficulty', 'hard')
        games[chat_id] = {
            'type': 'tictactoe',
            'board': create_board(),
            'active': True,
            'difficulty': difficulty
        }
        await message.answer(
            text="🤔 Ваш ход (1-9)...",
            reply_markup=get_tic_tac_toe_keyboard(games[chat_id]['board'])
        )
    
    elif game_type == 'number':
        max_num = games[chat_id].get('max_number', 100)
        start_number_game(chat_id, max_num)
        await message.answer(
            text=f"🔢 Я загадал число от 1 до {max_num}!\n"
                 f"Попробуйте угадать (введите число):",
            reply_markup=get_guess_number_keyboard()
        )

@dp.message(F.text.in_(["1", "2", "3", "4", "5", "6", "7", "8", "9"]))
async def handle_tic_tac_toe_move(message: types.Message):
    chat_id = message.chat.id
    
    if chat_id not in games or games[chat_id].get('type') != 'tictactoe':
        await message.answer("⚠️ Начните игру в Крестики-Нолики!", reply_markup=get_main_menu())
        return
    
    if not games[chat_id].get('active'):
        await message.answer("⚠️ Игра завершена! Нажмите 🔄 Заново", reply_markup=get_tic_tac_toe_keyboard(games[chat_id]['board']))
        return
    
    game = games[chat_id]
    cell_index = int(message.text) - 1
    board = game['board']
    
    if board[cell_index] != EMPTY:
        await message.answer("⛔ Клетка занята! Выберите другую.", reply_markup=get_tic_tac_toe_keyboard(board))
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
        
        await message.answer(text=text, reply_markup=get_tic_tac_toe_keyboard(board))
        return
    
    # Ход бота
    await message.answer("🤖 Бот думает...", reply_markup=get_tic_tac_toe_keyboard(board))
    await asyncio.sleep(0.5)
    
    move = get_ai_move(board, game['difficulty'])
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
            
            await message.answer(text=text, reply_markup=get_tic_tac_toe_keyboard(board))
        else:
            await message.answer(
                text="🤔 Ваш ход (1-9)...",
                reply_markup=get_tic_tac_toe_keyboard(board)
            )

# ================= УГАДАЙ ЧИСЛО =================

@dp.message(F.text.in_(["🎲 1-50", "🎲 1-100"]))
async def start_number_game_cmd(message: types.Message):
    chat_id = message.chat.id
    max_number = 50 if message.text == "🎲 1-50" else 100
    
    number = start_number_game(chat_id, max_number)
    logging.info(f"Загадано число {number} для чата {chat_id}")  # Для тестов
    
    await message.answer(
        text=f"🔢 Я загадал число от 1 до {max_number}!\n"
             f"У вас есть неограниченное количество попыток.\n"
             f"Введите число для guesses:",
        reply_markup=get_guess_number_keyboard()
    )

@dp.message(F.text == "🔢 Ввести число")
async def ask_number(message: types.Message):
    await message.answer(
        "✏️ Введите число:\n(просто напишите цифру в чат)"
    )

@dp.message(F.text.isdigit())
async def handle_number_guess(message: types.Message):
    chat_id = message.chat.id
    
    if chat_id not in games or games[chat_id].get('type') != 'number':
        return  # Игнорируем цифры если не игра в угадай число
    
    if not games[chat_id].get('active'):
        await message.answer("⚠️ Игра завершена! Нажмите 🔄 Заново", reply_markup=get_guess_number_keyboard())
        return
    
    game = games[chat_id]
    guess = int(message.text)
    game['attempts'] += 1
    
    if guess < 1 or guess > game['max_number']:
        await message.answer(
            f"⚠️ Число должно быть от 1 до {game['max_number']}!\n"
            f"Попробуйте ещё раз:",
            reply_markup=get_guess_number_keyboard()
        )
        return
    
    if guess == game['number']:
        game['active'] = False
        await message.answer(
            f"🎉 Поздравляю! Вы угадали!\n"
            f"Загаданное число: {game['number']}\n"
            f"Количество попыток: {game['attempts']}\n"
            f"{'🏆 Отличный результат!' if game['attempts'] <= 5 else '😅 Можно было лучше!'}",
            reply_markup=get_guess_number_keyboard()
        )
    elif guess < game['number']:
        await message.answer(
            f"📈 Больше!\n"
            f"Попытка №{game['attempts']}\n"
            f"Введите следующее число:",
            reply_markup=get_guess_number_keyboard()
        )
    else:
        await message.answer(
            f"📉 Меньше!\n"
            f"Попытка №{game['attempts']}\n"
            f"Введите следующее число:",
            reply_markup=get_guess_number_keyboard()
        )

# ================= ЗАПУСК =================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())