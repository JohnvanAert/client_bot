from aiogram import Router, F, Bot
from aiogram.types import Message, Document
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove
from states.states import CreateOrder
from database import add_order, get_customer_by_telegram_id
import os
import re
from database import get_all_gips
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

gip_bot = Bot(
    token=os.getenv("DAED_BOT_TOKEN"),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
router = Router()

@router.message(F.text == "➕ Создать заказ")
async def start_order_creation(message: Message, state: FSMContext):
    await message.answer("Введите название проекта:")
    await state.set_state(CreateOrder.waiting_for_title)

@router.message(CreateOrder.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer("Введите описание проекта:")
    await state.set_state(CreateOrder.waiting_for_description)

@router.message(CreateOrder.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await message.answer("📎 Загрузите архив с документами (в формате .zip):")
    await state.set_state(CreateOrder.waiting_for_document)

@router.message(CreateOrder.waiting_for_document, F.document)
async def process_document(message: Message, state: FSMContext):
    file = message.document
    if not file.file_name.endswith(".zip"):
        await message.answer("❗ Пожалуйста, загрузите архив в формате .zip.")
        return

    data = await state.get_data()
    title = data.get("title", "UnnamedProject")

    # Очистим имя проекта от недопустимых символов (оставим только буквы, цифры, _, -)
    safe_title = re.sub(r'[^\w\-]', '_', title)

    # Создаём папку под проект
    project_folder = os.path.join("documents", safe_title)
    os.makedirs(project_folder, exist_ok=True)

    # Полный путь для сохранения файла
    file_path = os.path.join(project_folder, file.file_name)
    await message.bot.download(file, destination=file_path)

    customer = await get_customer_by_telegram_id(message.from_user.id)

    await add_order(
        title=title,
        description=data["description"],
        document_url=file_path,
        customer_id=customer["id"]
    )
# 🔔 Уведомление ГИПам
    gip_ids = await get_all_gips()
    for gip_id in gip_ids:
        try:
            inline_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📦 Открыть заказы", callback_data="view_orders")]
                ]
            )
            await gip_bot.send_message(
                gip_id,
                f"📬 Поступил новый заказ:\n<b>{title}</b>",
                reply_markup=inline_kb
            )
        except Exception as e:
            print(f"Не удалось отправить сообщение ГИПу {gip_id}: {e}")

    await message.answer("✅ Заказ успешно создан!", reply_markup=ReplyKeyboardRemove())
    await state.clear()