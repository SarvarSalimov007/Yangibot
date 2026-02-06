import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
from game import BoxingGame
from video_downloader import VideoDownloader
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Define FSM States
class UserStates(StatesGroup):
    phone = State()
    location = State()
    video_url = State()

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
downloader = VideoDownloader()

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

@dp.message(Command("video"))
async def cmd_video(message: types.Message, state: FSMContext):
    await state.set_state(UserStates.video_url)
    await message.answer(
        "📹 <b>Video yuklash tartibi:</b>\n\n"
        "Iltimos, video havolasini (link) yuboring.\n"
        "<i>Men YouTube, Instagram, TikTok va boshqa ko'plab saytlarni qo'llab-quvvatlayman.</i>",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="❌ Bekor qilish")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
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

# Video Downloader Logic
@dp.message(UserStates.video_url, lambda msg: msg.text and (msg.text.startswith("http") or "youtube.com" in msg.text or "youtu.be" in msg.text))
async def process_video_link(message: types.Message, state: FSMContext):
    url = message.text.strip()
    status_msg = await message.reply("🔍 <i>Video qidirilmoqda...</i>", parse_mode="HTML")
    
    qualities, title = await downloader.extract_info(url)
    
    if not qualities:
        await status_msg.edit_text("❌ <b>Video topilmadi yoki yuklab bo'lmaydi.</b>\nLink to'g'riligini tekshiring.", parse_mode="HTML")
        return

    # Create keyboard with quality options
    rows = []
    chunk_size = 2
    for i in range(0, len(qualities), chunk_size):
        chunk = qualities[i:i + chunk_size]
        row = [InlineKeyboardButton(text=f"📥 {q}", callback_data=f"download_{q}") for q in chunk]
        rows.append(row)
        
    # Store URL in memory (simplest way for now, better to use state or temporary storage)
    # Using a simple trick: append URL hash or ID to callback, but URL might be long.
    # For now, we'll store it in a simple dict mapping user_id -> url
    # Note: Global variable is not ideal for production but works for simple bot
    if not hasattr(bot, 'user_urls'):
        bot.user_urls = {}
    bot.user_urls[message.from_user.id] = url
        
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    
    ffmpeg_warning = ""
    if not downloader.ffmpeg_available:
        ffmpeg_warning = "\n\n⚠️ <i>Diqqat: Tizimda FFmpeg mavjud emas. Yuqori sifatli (1080p, 4K) videolar ovozsiz bo'lishi yoki sifati pasayishi mumkin.</i>"

    await status_msg.edit_text(
        f"📹 <b>Video:</b> {title}\n"
        f"✅ <i>Sifatni tanlang:</i>{ffmpeg_warning}",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await state.clear()

@dp.callback_query(F.data.startswith("download_"))
async def process_download_callback(callback: CallbackQuery):
    quality = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    if not hasattr(bot, 'user_urls') or user_id not in bot.user_urls:
        await callback.answer("❌ Eskirgan so'rov. Linkni qayta yuboring.", show_alert=True)
        return

    url = bot.user_urls[user_id]
    await callback.message.edit_text(f"⏳ <i>Yuklanmoqda ({quality})...\nBiroz kuting.</i>", parse_mode="HTML")
    
    filepath = await downloader.download_video(url, quality)
    
    if filepath and os.path.exists(filepath):
        filesize_mb = os.path.getsize(filepath) / (1024 * 1024)
        
        if filesize_mb > 50:
            await callback.message.edit_text(
                f"❌ <b>Xatolik:</b> Video hajmi juda katta ({filesize_mb:.1f} MB).\n"
                f"Telegram botlar orqali faqat 50 MB gacha bo'lgan fayllarni yuborish mumkin.\n"
                f"<i>Iltimos, pastroq sifatni tanlang.</i>",
                parse_mode="HTML"
            )
            # Cleanup
            try: os.remove(filepath)
            except: pass
            return

        try:
            await callback.message.edit_text("📤 <i>Video yuborilmoqda...</i>", parse_mode="HTML")
            video_file = FSInputFile(filepath)
            await callback.message.answer_video(
                video_file, 
                caption=f"🎥 <b>Sifat:</b> {quality}\n⚖️ <b>Hajmi:</b> {filesize_mb:.1f} MB\n🤖 @Yangibot", 
                parse_mode="HTML"
            )
            await callback.message.delete()
        except Exception as e:
            await callback.message.edit_text(f"❌ Yuborishda xatolik: {e}")
        finally:
            try: os.remove(filepath)
            except: pass
    else:
        await callback.message.edit_text("❌ Yuklashda xatolik yuz berdi. Linkni yoki sifatni tekshiring.")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
