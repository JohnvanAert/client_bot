from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import get_orders_by_customer_telegram
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from states.review_states import ReviewCorrectionFSM
from database import get_order_by_id, get_specialist_by_section, update_order_status
from states.review_states import ReviewCorrectionFSM
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import os
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import FSInputFile
from tempfile import NamedTemporaryFile
load_dotenv()  # Загружаем переменные окружения

# Initialize the PSD bot
psd_bot = Bot(
    token=os.getenv("DAED_BOT_TOKEN"),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
router = Router()

@router.message(F.text == "📦 Мои заказы")
async def show_my_orders(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    orders = await get_orders_by_customer_telegram(telegram_id)

    if not orders:
        await message.answer("❗ У вас пока нет заказов.")
        return

    for order in orders:
        order_id = order["id"]
        status = order["status"]
        title = order["title"]

        caption = f"📝 <b>{title}</b>\n📍 Статус: <i>{status}</i>"

        # Кнопка только если статус = Получение ИРД
        keyboard = None
        if status == "receive_ird":
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📎 Отправить ИРД", callback_data=f"send_ird:{order_id}")]
            ])

        await message.answer(caption, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("send_ird:"))
async def handle_send_ird(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split(":")[1])
    await state.set_state(ReviewCorrectionFSM.waiting_for_customer_zip)
    await state.update_data(order_id=order_id)

    await callback.message.answer("📤 Пожалуйста, прикрепите архив с ИРД (в формате ZIP)")
    await callback.answer("Ожидаю ZIP 📁")


@router.message(ReviewCorrectionFSM.waiting_for_customer_zip, F.document)
async def receive_customer_zip(message: Message, state: FSMContext):
    document = message.document

    if not document.file_name.lower().endswith(".zip"):
        await message.answer("❗ Пожалуйста, отправьте архив в формате .zip")
        return

    data = await state.get_data()
    order_id = data["order_id"]
    order = await get_order_by_id(order_id)

    # Скачиваем файл
    file = await message.bot.get_file(document.file_id)
    downloaded = await message.bot.download_file(file.file_path)

    # Временный файл
    with NamedTemporaryFile("wb+", delete=False, suffix=".zip") as tmp:
        tmp.write(downloaded.read())
        tmp.flush()

        # Инлайн-кнопки для ГИПа
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Ошибка в документах", callback_data=f"docs_error:{order_id}")],
            [InlineKeyboardButton(text="✅ Принять документы", callback_data=f"docs_accept:{order_id}")]
        ])

        file_to_send = FSInputFile(tmp.name, filename=document.file_name)

        # Отправляем ГИПу
        await psd_bot.send_document(
            chat_id=order["gip_id"],
            document=file_to_send,
            caption=f"📥 Получен ZIP-файл ИРД от заказчика по заказу: <b>{order['title']}</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        # Отправляем специалисту
        specialist = await get_specialist_by_section("эп")
        if specialist:
            await psd_bot.send_document(
                chat_id=specialist["telegram_id"],
                document=file_to_send,
                caption=f"📥 Получен ZIP-файл ИРД от заказчика по заказу: <b>{order['title']}</b>",
                parse_mode="HTML"
            )

    await message.answer("✅ Спасибо! ZIP-файл передан исполнителям.")
    await state.clear()

