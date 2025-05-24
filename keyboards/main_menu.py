from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def customer_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Создать заказ")],
            # Можно позже добавить просмотр заказов
        ],
        resize_keyboard=True
    )
