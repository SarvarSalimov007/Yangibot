import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from game import BoxingGame
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Define FSM States
class UserStates(StatesGroup):
    phone = State()
    location = State()

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Keyboards
def get_phone_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamingizni yuboring", request_contact=True)],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_location_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Manzilni yuboring", request_location=True)],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_game_kb():
    """Modern 'Neon' style buttons using emojis"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🥊 Jab (Tez)", callback_data="move_jab"),
                InlineKeyboardButton(text="💥 Cross (Kuchli)", callback_data="move_cross")
            ],
            [
                InlineKeyboardButton(text="🛡 Blok", callback_data="move_block")
            ]
        ]
    )

# Initialize Game
game = BoxingGame()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.set_state(UserStates.phone)
    await message.answer(
        "<b>👋 Assalomu alaykum!</b>\n\n"
        "🤖 <i>Yangibot</i> tizimiga xush kelibsiz.\n"
        "🚀 <i>Biz bilan o'yindan zavqlaning va xizmatlardan foydalaning!</i>\n\n"
        "🔽 <b>Davom etish uchun telefon raqamingizni yuboring:</b>",
        reply_markup=get_phone_kb(),
        parse_mode="HTML"
    )

@dp.message(Command("game"))
async def cmd_game(message: types.Message):
    await message.answer(
        "🥊 <b>BOKS ARENASI</b> 🥊\n\n"
        "<i>Raqibingiz tayyor...</i>\n"
        "Quyidagi usullardan birini tanlang:\n\n"
        "• 🥊 <b>Jab</b> - Cross'ni yengadi, Blokga yutqazadi\n"
        "• 💥 <b>Cross</b> - Blokni yengadi, Jabga yutqazadi\n"
        "• 🛡 <b>Blok</b> - Jabni qaytaradi, Crossga yutqazadi",
        reply_markup=get_game_kb(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("move_"))
async def process_game_move(callback: CallbackQuery):
    user_move = callback.data.split("_")[1]
    bot_move = game.get_bot_move()
    result = game.get_result(user_move, bot_move)
    
    result_text = game.format_result_message(user_move, bot_move, result)
    
    # Animatsiya effekti uchun avval "O'ylamoqda..." deb o'zgartiramiz
    await callback.message.edit_text("⏳ <i>Raqib zarba bermoqda...</i>", parse_mode="HTML")
    await asyncio.sleep(0.5) # Qisqa pauza
    
    await callback.message.edit_text(
        f"{result_text}\n\n🔄 <b>Yana o'ynaysizmi?</b>",
        reply_markup=get_game_kb(),
        parse_mode="HTML"
    )

@dp.message(F.text == "❌ Bekor qilish")
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Amallar bekor qilindi. Boshlash uchun /start ni bosing.",
        reply_markup=types.ReplyKeyboardRemove()
    )

@dp.message(UserStates.phone, F.contact)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(UserStates.location)
    await message.answer(
        "Rahmat! Endi manzilingizni yuboring.",
        reply_markup=get_location_kb()
    )

@dp.message(UserStates.location, F.location)
async def process_location(message: types.Message, state: FSMContext):
    data = await state.get_data()
    phone = data.get("phone")
    latitude = message.location.latitude
    longitude = message.location.longitude
    
    await message.answer(
        f"✅ Ma'lumotlar qabul qilindi!\n\n📞 Telefon: {phone}\n📍 Manzil: https://www.google.com/maps?q={latitude},{longitude}",
        reply_markup=types.ReplyKeyboardRemove()
    )
    # Clear state after finishing
    await state.clear()

@dp.message(UserStates.phone)
async def phone_invalid(message: types.Message):
    await message.reply("Iltimos, telefon raqamingizni pastdagi tugma orqali yuboring. 📱")

@dp.message(UserStates.location)
async def location_invalid(message: types.Message):
    await message.reply("Iltimos, manzilni pastdagi tugma orqali yuboring. 📍")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
