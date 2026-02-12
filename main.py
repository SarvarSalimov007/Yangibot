import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F  # type: ignore
from aiogram.filters import Command  # type: ignore
from aiogram.fsm.context import FSMContext  # type: ignore
from aiogram.fsm.state import State, StatesGroup  # type: ignore
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile  # type: ignore
from game import BoxingGame  # type: ignore
from video_downloader import VideoDownloader  # type: ignore
from math_quiz import MathQuiz  # type: ignore
from dotenv import load_dotenv  # type: ignore
from typing import List, Any, Optional, cast

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
def get_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📹 Video Yuklash"), KeyboardButton(text="🎮 O'yin O'ynash")],
            [KeyboardButton(text="🧮 Matematika"), KeyboardButton(text="ℹ️ Ma'lumot")],
            [KeyboardButton(text="📞 Bog'lanish")]
        ],
        resize_keyboard=True
    )

def get_back_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Orqaga")]],
        resize_keyboard=True
    )

def get_phone_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamingizni yuboring", request_contact=True)],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_location_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Manzilni yuboring", request_location=True)],
            [KeyboardButton(text="⬅️ Orqaga")]
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
            ],
            [
                InlineKeyboardButton(text="⬅️ Asosiy Menuga", callback_data="back_to_main")
            ]
        ]
    )

# Initialize Logic Components
game = BoxingGame()
downloader = VideoDownloader()
math_quiz = MathQuiz()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "<b>👋 Assalomu alaykum!</b>\n\n"
        "🤖 <i>Yangibot</i> tizimiga xush kelibsiz.\n"
        "🚀 <i>Biz bilan o'yindan zavqlaning va xizmatlardan foydalaning!</i>\n\n"
        "🔽 <b>Kerakli bo'limni tanlang:</b>",
        reply_markup=get_main_kb(),
        parse_mode="HTML"
    )

@dp.message(F.text == "⬅️ Orqaga")
@dp.message(Command("cancel"))
async def cmd_back(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Bosh sahifa", reply_markup=get_main_kb())

@dp.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("Asosiy menu", reply_markup=get_main_kb())

@dp.message(F.text == "📹 Video Yuklash")
@dp.message(Command("video"))
async def cmd_video(message: types.Message, state: FSMContext):
    await state.set_state(UserStates.video_url)
    await message.answer(
        "📹 <b>Video yuklash bo'limi</b>\n\n"
        "Iltimos, video havolasini (link) yuboring.\n"
        "<i>Men YouTube, Instagram, TikTok va hokazolardan yuklay olaman.</i>\n\n"
        "Sifatni tanlash imkoniyati mavjud! ✅",
        parse_mode="HTML",
        reply_markup=get_back_kb()
    )

@dp.message(F.text == "🎮 O'yin O'ynash")
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

@dp.message(F.text == "ℹ️ Ma'lumot")
async def cmd_info(message: types.Message):
    await message.answer(
        "🤖 <b>Yangibot Haqida</b>\n\n"
        "Ushbu bot orqali siz:\n"
        "1. Ijtimoiy tarmoqlardan video yuklashingiz (4K gacha).\n"
        "2. Interaktiv mini o'yinlar o'ynashingiz mumkin.\n\n"
        "Bot aiogram 3.x kutubxonasida yaratilgan.",
        parse_mode="HTML"
    )

@dp.message(F.text == "📞 Bog'lanish")
async def cmd_contact(message: types.Message, state: FSMContext):
    await state.set_state(UserStates.phone)
    await message.answer(
        "☎️ <b>Biz bilan bog'lanish</b>\n\n"
        "Iltimos, telefon raqamingizni yuboring, operatorlarimiz siz bilan bog'lanishadi.",
        reply_markup=get_phone_kb(),
        parse_mode="HTML"
    )

@dp.message(F.text == "🧮 Matematika")
@dp.message(Command("math"))
async def cmd_math(message: types.Message, state: FSMContext):
    question, options, correct_label = math_quiz.generate_question()
    
    # Store correct answer in state
    await state.update_data(math_correct=correct_label)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"A: {options['A']}", callback_data="math_A")],
        [InlineKeyboardButton(text=f"B: {options['B']}", callback_data="math_B")],
        [InlineKeyboardButton(text=f"C: {options['C']}", callback_data="math_C")],
        [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="back_to_main")]
    ])
    
    await message.answer(
        f"<b>🧮 Matematika Savoli</b>\n\n"
        f"Savol: <code>{question}</code>\n\n"
        f"To'g'ri javobni tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("math_"))
async def process_math_answer(callback: CallbackQuery, state: FSMContext):
    if callback.data == "math_next":
        question, options, correct_label = math_quiz.generate_question()
        await state.update_data(math_correct=correct_label)
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"A: {options['A']}", callback_data="math_A")],
            [InlineKeyboardButton(text=f"B: {options['B']}", callback_data="math_B")],
            [InlineKeyboardButton(text=f"C: {options['C']}", callback_data="math_C")],
            [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="back_to_main")]
        ])
        
        await callback.message.edit_text(
            f"<b>🧮 Matematika Savoli</b>\n\n"
            f"Savol: <code>{question}</code>\n\n"
            f"To'g'ri javobni tanlang:",
            reply_markup=kb,
            parse_mode="HTML"
        )
        return

    user_answer = callback.data.split("_")[1]
    data = await state.get_data()
    correct_label = data.get("math_correct")
    
    if not correct_label:
        await callback.answer("⚠️ Savol muddati o'tgan yoki xatolik yuz berdi.", show_alert=True)
        return

    if user_answer == correct_label:
        text = "✅ <b>To'g'ri!</b>\nBarakalla, siz matematikani yaxshi bilasiz! 🚀"
    else:
        text = f"❌ <b>Noto'g'ri!</b>\nTo'g'ri javob: <b>{correct_label}</b> edi. 😔"
    
    await callback.message.edit_text(
        f"{text}\n\n🔄 <b>Yana bir urinib ko'rasizmi?</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yana bir savol", callback_data="math_next")],
            [InlineKeyboardButton(text="⬅️ Asosiy Menuga", callback_data="back_to_main")]
        ]),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("move_"))
async def process_game_move(callback: CallbackQuery):
    user_move = callback.data.split("_")[1]
    bot_move = game.get_bot_move()
    result = game.get_result(user_move, bot_move)
    
    result_text = game.format_result_message(user_move, bot_move, result)
    
    await callback.message.edit_text("⏳ <i>Raqib zarba bermoqda...</i>", parse_mode="HTML")
    await asyncio.sleep(0.5)
    
    await callback.message.edit_text(
        f"{result_text}\n\n🔄 <b>Yana o'ynaysizmi?</b>",
        reply_markup=get_game_kb(),
        parse_mode="HTML"
    )

@dp.message(UserStates.phone, F.contact)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(UserStates.location)
    await message.answer(
        "✅ Rahmat! Endi manzilingizni yuboring 📍",
        reply_markup=get_location_kb()
    )

@dp.message(UserStates.location, F.location)
async def process_location(message: types.Message, state: FSMContext):
    data = await state.get_data()
    phone = data.get("phone")
    lat = message.location.latitude
    lon = message.location.longitude
    
    await message.answer(
        f"✅ <b>Ma'lumotlar yuborildi!</b>\n\n"
        f"📞 Telefon: {phone}\n"
        f"📍 Manzil: <a href='https://www.google.com/maps?q={lat},{lon}'>Google Maps</a>",
        reply_markup=get_main_kb(),
        parse_mode="HTML"
    )
    await state.clear()

# Video Downloader Logic
@dp.message(UserStates.video_url, F.text.regexp(r'^https?://'))
async def process_video_link(message: types.Message, state: FSMContext):
    url = message.text.strip()
    status_msg = await message.answer("🔍 <b>Video tahlil qilinmoqda...</b>", parse_mode="HTML", reply_markup=types.ReplyKeyboardRemove())
    
    qualities, title = await downloader.extract_info(url)
    
    # Cast qualities to a list explicitly for the linter with proper typing
    qualities_raw: Any = qualities
    qualities_list: List[str] = list(qualities_raw) if qualities_raw else []
    
    if title == "TIMEOUT":
        await status_msg.edit_text("⏳ <b>Tahlil juda uzoq davom etdi.</b>\nIltimos, qaytadan urinib ko'ring.", reply_markup=get_back_kb())
        return
    elif title == "SIGN_IN":
        await status_msg.edit_text("🔞 <b>Bu video yoshga doir cheklovga ega yoki login talab qiladi.</b>", reply_markup=get_back_kb())
        return
    elif title == "PRIVATE":
        await status_msg.edit_text("🔒 <b>Bu video shaxsiy (private) yoki o'chirilgan.</b>", reply_markup=get_back_kb())
        return
    elif title == "ERROR" or not qualities_list:
        await status_msg.edit_text("❌ <b>Videoni tahlil qilib bo'lmadi.</b>\nLink to'g'riligini tekshiring.", reply_markup=get_back_kb())
        return

    rows: List[List[InlineKeyboardButton]] = []
    # Build keyboard rows without slicing to appease all linters
    for i in range(0, len(qualities_list), 2):
        row: List[InlineKeyboardButton] = []
        # First button
        q1 = str(qualities_list[i])
        row.append(InlineKeyboardButton(text=f"📥 {q1.upper()}", callback_data=f"dl_{q1}"))
        # Second button (optional)
        if i + 1 < len(qualities_list):
            q2 = str(qualities_list[i+1])
            row.append(InlineKeyboardButton(text=f"📥 {q2.upper()}", callback_data=f"dl_{q2}"))
        rows.append(row)
    
    rows.append([InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="cancel_dl")])
        
    await state.update_data(video_url=url)
        
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    
    text = (
        f"🎬 <b>Video:</b> {title}\n\n"
        f"✅ <b>Tavsiya etilgan formatlar:</b>\n"
        f"Marhamat, yuklab olish uchun sifatni tanlang:"
    )
    
    if not downloader.ffmpeg_available:
        text += "\n\n⚠️ <i>Eslatma: Ba'zi yuqori sifatlar ovozsiz bo'lishi mumkin.</i>"

    await status_msg.edit_text(text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data == "cancel_dl")
async def cancel_dl_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("Video yuklash bekor qilindi.", reply_markup=get_main_kb())

@dp.callback_query(F.data.startswith("dl_"))
async def process_download_callback(callback: CallbackQuery, state: FSMContext):
    quality = callback.data.split("_")[1]
    data = await state.get_data()
    url = data.get("video_url")
    
    if not url:
        await callback.answer("❌ Seans muddati tugagan.", show_alert=True)
        return
    await callback.message.edit_text(f"🚀 <b>Yuklash boshlandi...</b>\n🎬 Sifat: <b>{quality.upper()}</b>\n\n<i>Iltimos, kuting...</i>", parse_mode="HTML")
    
    filepath: Optional[str] = None
    try:
        download_result: Any = await downloader.download_video(url, quality)
        filepath = cast(Optional[str], download_result)
        
        if filepath and os.path.exists(filepath):
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            
            if size_mb > 50:
                 await callback.message.edit_text(
                    f"⚠️ <b>Hajmi juda katta:</b> {size_mb:.1f} MB\n\n"
                    f"Telegram botlar 50 MB gacha fayl yubora oladi.\n"
                    f"<i>Maslahat: 720p yoki 480p tanlang.</i>",
                    reply_markup=get_back_kb(),
                    parse_mode="HTML"
                )
            else:
                await callback.message.edit_text("📤 <b>Video yuborilmoqda...</b>", parse_mode="HTML")
                video = FSInputFile(filepath)
                await callback.message.answer_video(
                    video, 
                    caption=f"🎥 <b>Sifat:</b> {quality.upper()}\n⚖️ <b>Hajmi:</b> {size_mb:.1f} MB\n🤖 @Yangibot", 
                    parse_mode="HTML"
                )
                await callback.message.delete()
                await callback.message.answer("Yana biror nima yuklaymizmi? 😊", reply_markup=get_main_kb())
        else:
            await callback.message.edit_text("❌ <b>Yuklashda xatolik!</b>\nBu sifat yoki video bilan muammo bo'ldi.", reply_markup=get_back_kb())
            
    except Exception as e:
        await callback.message.answer(f"❌ Xatolik: {str(e)}", reply_markup=get_main_kb())
    finally:
        if filepath is not None and os.path.exists(str(filepath)):
            try: 
                os.remove(str(filepath))
            except: 
                pass

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
