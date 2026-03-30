from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu_kb(plan: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👤 Один", callback_data="mode:solo"),
        InlineKeyboardButton(text="⚔️ Битва", callback_data="mode:battle"),
    )
    if plan in ("max",):
        builder.row(InlineKeyboardButton(text="🔥 Роастинг", callback_data="mode:roast"))
    else:
        builder.row(InlineKeyboardButton(text="🔥 Роастинг 🔒 MAX", callback_data="roast_locked"))
    builder.row(InlineKeyboardButton(text="💳 Подписки", callback_data="subscriptions"))
    builder.row(InlineKeyboardButton(text="📊 Мой профиль", callback_data="profile"))
    return builder.as_markup()

def battle_opponent_kb(plan: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # Free/Pro — only GPT. Ultra/Max — all
    builder.row(InlineKeyboardButton(text="🤖 ChatGPT", callback_data="opponent:gpt"))
    if plan in ("ultra", "max"):
        builder.row(
            InlineKeyboardButton(text="🧠 Claude", callback_data="opponent:claude"),
            InlineKeyboardButton(text="🐉 DeepSeek", callback_data="opponent:deepseek"),
        )
    else:
        builder.row(InlineKeyboardButton(text="🧠 Claude 🔒 ULTRA", callback_data="opp_locked"))
        builder.row(InlineKeyboardButton(text="🐉 DeepSeek 🔒 ULTRA", callback_data="opp_locked"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_menu"))
    return builder.as_markup()

def subscriptions_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🆓 FREE — бесплатно", callback_data="sub_info:free"))
    builder.row(InlineKeyboardButton(text="💎 PRO — 150 ⭐", callback_data="sub_info:pro"))
    builder.row(InlineKeyboardButton(text="⚡ ULTRA — 220 ⭐", callback_data="sub_info:ultra"))
    builder.row(InlineKeyboardButton(text="🔥 MAX — 300 ⭐", callback_data="sub_info:max"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_menu"))
    return builder.as_markup()

def buy_plan_kb(plan: str, stars: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=f"⭐ Купить за {stars} звёзд",
        callback_data=f"buy:{plan}"
    ))
    builder.row(InlineKeyboardButton(text="◀️ Назад к подпискам", callback_data="subscriptions"))
    return builder.as_markup()

def back_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ В главное меню", callback_data="back_menu"))
    return builder.as_markup()

def cancel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🛑 Стоп / Меню", callback_data="back_menu"))
    return builder.as_markup()

def roast_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎯 Новая жертва", callback_data="mode:roast"))
    builder.row(InlineKeyboardButton(text="◀️ Меню", callback_data="back_menu"))
    return builder.as_markup()
