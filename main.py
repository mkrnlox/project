import json
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from config import API_TOKEN, ADMIN_IDS

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

def load_items():
    with open("data/items.json", "r") as file:
        return json.load(file)

def save_items(data):
    with open("data/items.json", "w") as file:
        json.dump(data, file, indent=4)

async def set_commands():
    commands = [
        BotCommand(command="/start", description="перезапустить бота"),
        BotCommand(command="Категории", description="показать категории товаров"),
    ]
    await bot.set_my_commands(commands)

def main_menu(user_id):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="Категории")]
    ])

    if is_admin(user_id):
        keyboard.keyboard.append([KeyboardButton(text="Админ панель")])

    return keyboard

def category_items_menu(categories_list):
    inline_keyboard = []
    for category in categories_list:
        inline_keyboard.append([InlineKeyboardButton(text=category, callback_data=category)])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def product_items_menu(items_list):
    inline_keyboard = []
    for item in items_list:
        inline_keyboard.append([InlineKeyboardButton(text=item, callback_data=item)])
    inline_keyboard.append([InlineKeyboardButton(text="🔙 Вернуться к категориям", callback_data="back_to_categories")])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

async def delete_message_after_delay(message: types.Message, delay: int):
    await asyncio.sleep(delay)
    await message.delete()

def is_admin(user_id):
    return user_id in ADMIN_IDS

@dp.message(lambda message: message.text == "/start")
async def start_handler(message: types.Message):
    await message.delete()
    await message.answer("Добро пожаловать! Главное меню:", reply_markup=main_menu(message.from_user.id))

@dp.callback_query(lambda c: c.data == "back_to_main_menu")
async def back_to_main_menu(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await callback_query.message.answer("Добро пожаловать! Главное меню:", reply_markup=main_menu(callback_query.from_user.id))
    await callback_query.answer()

@dp.message(lambda message: message.text == "Категории")
async def view_categories_handler(message: types.Message):
    items = load_items()
    categories_list = items["categories"].keys()
    
    await message.delete()
    response_message = await message.answer("Выберите категорию:", reply_markup=category_items_menu(categories_list))

    asyncio.create_task(delete_message_after_delay(response_message, 300))

@dp.callback_query(lambda c: c.data in load_items()["categories"].keys())
async def category_handler(callback_query: types.CallbackQuery):
    category_name = callback_query.data
    items = load_items()
    items_list = items["categories"].get(category_name, [])

    await callback_query.message.delete()
    await callback_query.message.answer(f"Вы выбрали категорию '{category_name}'.", reply_markup=product_items_menu(items_list))
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "back_to_categories")
async def back_to_categories(callback_query: types.CallbackQuery):
    items = load_items()
    categories_list = items["categories"].keys()
    await callback_query.message.delete()
    await callback_query.message.answer("Выберите категорию:", reply_markup=category_items_menu(categories_list))
    await callback_query.answer()

@dp.callback_query(lambda c: c.data not in ["back_to_categories", "back_to_main_menu"])
async def item_handler(callback_query: types.CallbackQuery):
    item_name = callback_query.data
    await callback_query.answer(f"Вы выбрали товар: {item_name}")

@dp.message()
async def unknown_command_handler(message: types.Message):
    await message.reply("Команда не найдена. Пожалуйста, используйте доступные команды.")

if __name__ == "__main__":
    dp.run_polling(bot)
