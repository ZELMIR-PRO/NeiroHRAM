import time
from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery, LabeledPrice,
    PreCheckoutQuery, FSInputFile
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import PLANS, BANNED_WORDS, DANIIL_PATTERNS, DANIIL_RESPONSE, PERSONAS
from database import get_user, can_send_message, increment_messages, upgrade_plan
from keyboards import (
    main_menu_kb, battle_opponent_kb, subscriptions_kb,
    buy_plan_kb, back_menu_kb, cancel_kb, roast_kb
)
from ai import call_ai

router = Router()

# ── FSM States ──────────────────────────────────────────────
class UserState(StatesGroup):
    idle = State()
    solo_chat = State()
    battle_choose_opponent = State()
    battle_chat = State()
    roast_waiting_target = State()
    roast_chat = State()

# ── Helpers ──────────────────────────────────────────────────
def is_banned(text: str) -> bool:
    t = text.lower()
    return any(w in t for w in BANNED_WORDS)

def is_daniil(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in DANIIL_PATTERNS)

def plan_info_text(plan: str) -> str:
    info = {
        "free": (
            "🆓 <b>FREE</b> — Бесплатный план\n\n"
            "• 20 сообщений в месяц\n"
            "• Режим «Один» ✅\n"
            "• Режим «Битва» — только с ChatGPT ✅\n"
            "• Выбор нейросети в битве ❌\n"
            "• Режим «Роастинг» ❌\n\n"
            "<i>Это твой текущий план. Обновись для большего!</i>"
        ),
        "pro": (
            "💎 <b>PRO</b> — 150 ⭐ в месяц\n\n"
            "• 90 сообщений в месяц\n"
            "• Режим «Один» ✅\n"
            "• Режим «Битва» — только с ChatGPT ✅\n"
            "• Выбор нейросети в битве ❌\n"
            "• Режим «Роастинг» ❌"
        ),
        "ultra": (
            "⚡ <b>ULTRA</b> — 220 ⭐ в месяц\n\n"
            "• 180 сообщений в месяц\n"
            "• Режим «Один» ✅\n"
            "• Режим «Битва» ✅\n"
            "• Выбор нейросети: ChatGPT, Claude, DeepSeek ✅\n"
            "• Режим «Роастинг» ❌"
        ),
        "max": (
            "🔥 <b>MAX</b> — 300 ⭐ в месяц\n\n"
            "• 270 сообщений в месяц\n"
            "• Режим «Один» ✅\n"
            "• Режим «Битва» ✅\n"
            "• Выбор нейросети: ChatGPT, Claude, DeepSeek ✅\n"
            "• Режим «Роастинг» 🔥 ОТКРЫТ ✅"
        ),
    }
    return info.get(plan, "")

PLAN_IMAGES = {
    "free":  "FREE.png",
    "pro":   "PRO.png",
    "ultra": "ULTRA.png",
    "max":   "MAX.png",
}

async def send_main_menu(message: Message, state: FSMContext):
    await state.clear()
    user = await get_user(message.chat.id)
    plan = user["plan"]
    used = user["messages_used"]
    limit = user["messages_limit"]
    await state.set_state(UserState.idle)
    await message.answer(
        f"🔥 <b>НЕЙРОХРАМ</b> — самая грубая нейросеть рунета\n\n"
        f"📊 Твой план: <b>{plan.upper()}</b>\n"
        f"💬 Использовано: <b>{used}/{limit}</b> сообщений\n\n"
        f"Выбери режим:",
        reply_markup=main_menu_kb(plan),
        parse_mode="HTML"
    )

# ── /start ────────────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await get_user(message.from_user.id)
    await send_main_menu(message, state)

# ── /subscriptions ────────────────────────────────────────────
@router.message(Command("subscriptions"))
async def cmd_subscriptions(message: Message, state: FSMContext):
    await state.set_state(UserState.idle)
    await message.answer(
        "💳 <b>Подписки НЕЙРОХРАМ</b>\n\nВыбери план для подробностей:",
        reply_markup=subscriptions_kb(),
        parse_mode="HTML"
    )

# ── /profile ──────────────────────────────────────────────────
@router.message(Command("profile"))
async def cmd_profile(message: Message):
    user = await get_user(message.from_user.id)
    plan = user["plan"]
    used = user["messages_used"]
    limit = user["messages_limit"]
    expires = user["plan_expires"]
    exp_str = ""
    if expires:
        days_left = max(0, (expires - int(time.time())) // 86400)
        exp_str = f"\n⏳ До конца периода: <b>{days_left} дн.</b>"
    await message.answer(
        f"👤 <b>Твой профиль</b>\n\n"
        f"📦 План: <b>{plan.upper()}</b>\n"
        f"💬 Сообщений: <b>{used}/{limit}</b>{exp_str}",
        parse_mode="HTML",
        reply_markup=back_menu_kb()
    )

# ── Callbacks: menu navigation ────────────────────────────────
@router.callback_query(F.data == "back_menu")
async def cb_back_menu(cb: CallbackQuery, state: FSMContext):
    await cb.message.delete()
    await send_main_menu(cb.message, state)
    await cb.answer()

@router.callback_query(F.data == "profile")
async def cb_profile(cb: CallbackQuery):
    user = await get_user(cb.from_user.id)
    plan = user["plan"]
    used = user["messages_used"]
    limit = user["messages_limit"]
    expires = user["plan_expires"]
    exp_str = ""
    if expires:
        days_left = max(0, (expires - int(time.time())) // 86400)
        exp_str = f"\n⏳ До конца периода: <b>{days_left} дн.</b>"
    await cb.message.edit_text(
        f"👤 <b>Твой профиль</b>\n\n"
        f"📦 План: <b>{plan.upper()}</b>\n"
        f"💬 Сообщений: <b>{used}/{limit}</b>{exp_str}",
        parse_mode="HTML",
        reply_markup=back_menu_kb()
    )
    await cb.answer()

@router.callback_query(F.data == "subscriptions")
async def cb_subscriptions(cb: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.idle)
    await cb.message.edit_text(
        "💳 <b>Подписки НЕЙРОХРАМ</b>\n\nВыбери план для подробностей:",
        reply_markup=subscriptions_kb(),
        parse_mode="HTML"
    )
    await cb.answer()

@router.callback_query(F.data.startswith("sub_info:"))
async def cb_sub_info(cb: CallbackQuery, bot: Bot):
    plan = cb.data.split(":")[1]
    text = plan_info_text(plan)
    image_path = PLAN_IMAGES.get(plan)
    kb = buy_plan_kb(plan, PLANS[plan]["stars"]) if PLANS[plan]["stars"] > 0 else back_menu_kb()

    try:
        await cb.message.delete()
    except Exception:
        pass

    if image_path:
        try:
            photo = FSInputFile(image_path)
            await bot.send_photo(
                cb.from_user.id,
                photo=photo,
                caption=text,
                parse_mode="HTML",
                reply_markup=kb
            )
        except Exception:
            await bot.send_message(cb.from_user.id, text, parse_mode="HTML", reply_markup=kb)
    else:
        await bot.send_message(cb.from_user.id, text, parse_mode="HTML", reply_markup=kb)
    await cb.answer()

# ── Mode selection ────────────────────────────────────────────
@router.callback_query(F.data == "mode:solo")
async def cb_mode_solo(cb: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.solo_chat)
    await state.update_data(history=[])
    await cb.message.edit_text(
        "👤 <b>Режим: Один</b>\n\nПиши что хочешь — Нейрохрам ответит грубо и смешно.\n\n"
        "Нажми /menu чтобы вернуться в меню.",
        parse_mode="HTML",
        reply_markup=cancel_kb()
    )
    await cb.answer()

@router.callback_query(F.data == "mode:battle")
async def cb_mode_battle(cb: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.battle_choose_opponent)
    user = await get_user(cb.from_user.id)
    await cb.message.edit_text(
        "⚔️ <b>Режим: Битва</b>\n\nВыбери противника для Нейрохрама:",
        parse_mode="HTML",
        reply_markup=battle_opponent_kb(user["plan"])
    )
    await cb.answer()

@router.callback_query(F.data == "mode:roast")
async def cb_mode_roast(cb: CallbackQuery, state: FSMContext):
    user = await get_user(cb.from_user.id)
    if user["plan"] != "max":
        await cb.answer("🔒 Роастинг доступен только на плане MAX!", show_alert=True)
        return
    await state.set_state(UserState.roast_waiting_target)
    await cb.message.edit_text(
        "🔥 <b>Режим: Роастинг</b>\n\n"
        "Напиши имя или описание человека которого Нейрохрам должен уничтожить словами.\n\n"
        "<i>Например: мой сосед Петя, 40 лет, ходит в трениках...</i>",
        parse_mode="HTML",
        reply_markup=cancel_kb()
    )
    await cb.answer()

@router.callback_query(F.data == "roast_locked")
async def cb_roast_locked(cb: CallbackQuery):
    await cb.answer("🔒 Роастинг доступен только на плане MAX! Зайди в /subscriptions", show_alert=True)

@router.callback_query(F.data == "opp_locked")
async def cb_opp_locked(cb: CallbackQuery):
    await cb.answer("🔒 Эта нейросеть доступна с плана ULTRA! Зайди в /subscriptions", show_alert=True)

@router.callback_query(F.data.startswith("opponent:"))
async def cb_choose_opponent(cb: CallbackQuery, state: FSMContext):
    opponent = cb.data.split(":")[1]
    await state.set_state(UserState.battle_chat)
    await state.update_data(opponent=opponent, neyro_history=[], opp_history=[])
    opp_name = PERSONAS[opponent]["name"]
    await cb.message.edit_text(
        f"⚔️ <b>Битва: Нейрохрам vs {opp_name}</b>\n\n"
        f"Напиши тему для спора — и они начнут орать друг на друга!\n\n"
        f"Нажми /menu чтобы остановить.",
        parse_mode="HTML",
        reply_markup=cancel_kb()
    )
    await cb.answer()

# ── Message limit check helper ────────────────────────────────
async def check_limit(message: Message, state: FSMContext) -> bool:
    allowed, user = await can_send_message(message.from_user.id)
    if not allowed:
        await message.answer(
            f"⛔ <b>Лимит исчерпан!</b>\n\n"
            f"Ты использовал все <b>{user['messages_limit']}</b> сообщений на этот месяц.\n"
            f"Обнови план в /subscriptions",
            parse_mode="HTML",
            reply_markup=back_menu_kb()
        )
        await state.set_state(UserState.idle)
        return False
    return True

# ── /menu command ─────────────────────────────────────────────
@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    await send_main_menu(message, state)

# ── SOLO MODE ─────────────────────────────────────────────────
@router.message(UserState.solo_chat)
async def solo_message(message: Message, state: FSMContext):
    if not await check_limit(message, state):
        return

    text = message.text.strip()
    data = await state.get_data()
    history = data.get("history", [])

    if is_banned(text):
        await message.answer("🚫 Нейрохрам отказывается говорить на эту тему. Слишком больно.")
        return

    if is_daniil(text):
        await message.answer(DANIIL_RESPONSE)
        await increment_messages(message.from_user.id)
        return

    thinking = await message.answer("💭 Нейрохрам думает...")
    history.append({"role": "user", "content": text})

    try:
        reply = await call_ai("neyro", history)
        history.append({"role": "assistant", "content": reply})
        if len(history) > 20:
            history = history[-20:]
        await state.update_data(history=history)
        await thinking.delete()
        await increment_messages(message.from_user.id)

        user = await get_user(message.from_user.id)
        left = user["messages_limit"] - user["messages_used"]
        await message.answer(
            f"🔥 <b>НЕЙРОХРАМ:</b>\n{reply}\n\n<i>Осталось сообщений: {left}</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        await thinking.delete()
        await message.answer(f"⚡ Ошибка: {e}")

# ── BATTLE MODE ───────────────────────────────────────────────
@router.message(UserState.battle_chat)
async def battle_message(message: Message, state: FSMContext):
    if not await check_limit(message, state):
        return

    text = message.text.strip()
    data = await state.get_data()
    opponent = data.get("opponent", "gpt")

    if is_banned(text):
        await message.answer("🚫 Нейрохрам отказывается биться на эту тему.")
        return

    thinking = await message.answer(f"⚔️ Битва начинается...")

    try:
        # Round 1: Neyro starts
        neyro_msgs = [{"role": "user", "content": f"Тема спора: \"{text}\". Выскажись первым — грубо, смешно и коротко. Только русский язык."}]
        neyro_reply = await call_ai("neyro", neyro_msgs)
        await increment_messages(message.from_user.id)

        # Round 1: Opponent responds
        opp_msgs = [{"role": "user", "content": f"Тема: \"{text}\". Нейрохрам сказал: \"{neyro_reply}\". Ответь ему. Только русский язык."}]
        opp_reply = await call_ai(opponent, opp_msgs)
        await increment_messages(message.from_user.id)

        # Round 2: Neyro counter
        neyro_msgs.append({"role": "assistant", "content": neyro_reply})
        neyro_msgs.append({"role": "user", "content": f"{PERSONAS[opponent]['name']} сказал: \"{opp_reply}\". Ответь грубо и смешно. Только русский язык."})
        neyro_reply2 = await call_ai("neyro", neyro_msgs)
        await increment_messages(message.from_user.id)

        # Round 2: Opponent counter
        opp_msgs.append({"role": "assistant", "content": opp_reply})
        opp_msgs.append({"role": "user", "content": f"Нейрохрам ответил: \"{neyro_reply2}\". Ответь ему. Только русский язык."})
        opp_reply2 = await call_ai(opponent, opp_msgs)
        await increment_messages(message.from_user.id)

        await thinking.delete()

        opp_name = PERSONAS[opponent]["name"]
        user = await get_user(message.from_user.id)
        left = user["messages_limit"] - user["messages_used"]

        battle_text = (
            f"⚔️ <b>БИТВА: Нейрохрам vs {opp_name}</b>\n"
            f"<b>Тема:</b> {text}\n\n"
            f"━━━ Раунд 1 ━━━\n"
            f"🔥 <b>НЕЙРОХРАМ:</b> {neyro_reply}\n\n"
            f"🤖 <b>{opp_name}:</b> {opp_reply}\n\n"
            f"━━━ Раунд 2 ━━━\n"
            f"🔥 <b>НЕЙРОХРАМ:</b> {neyro_reply2}\n\n"
            f"🤖 <b>{opp_name}:</b> {opp_reply2}\n\n"
            f"<i>Израсходовано 4 сообщения. Осталось: {left}</i>"
        )
        await message.answer(battle_text, parse_mode="HTML", reply_markup=cancel_kb())

    except Exception as e:
        await thinking.delete()
        await message.answer(f"⚡ Ошибка: {e}")

# ── ROAST MODE ────────────────────────────────────────────────
@router.message(UserState.roast_waiting_target)
async def roast_target(message: Message, state: FSMContext):
    if not await check_limit(message, state):
        return

    target = message.text.strip()

    if is_banned(target):
        await message.answer("🚫 Нейрохрам не будет роастить это. Закрыто.")
        return

    if is_daniil(target):
        await message.answer(DANIIL_RESPONSE, reply_markup=roast_kb())
        await increment_messages(message.from_user.id)
        await state.set_state(UserState.roast_chat)
        await state.update_data(roast_target=target, roast_history=[])
        return

    thinking = await message.answer(f"🎯 Нейрохрам изучает жертву: <b>{target}</b>...", parse_mode="HTML")

    msgs = [{"role": "user", "content": f"Сделай смешной роастинг этого человека: \"{target}\". Придумай абсурдную биографию, странные привычки, смешные факты. Только русский язык."}]
    try:
        reply = await call_ai("roaster", msgs)
        await increment_messages(message.from_user.id)
        await thinking.delete()

        user = await get_user(message.from_user.id)
        left = user["messages_limit"] - user["messages_used"]

        await state.set_state(UserState.roast_chat)
        await state.update_data(
            roast_target=target,
            roast_history=[{"role": "user", "content": f"Расскажи про {target}"}, {"role": "assistant", "content": reply}]
        )
        await message.answer(
            f"🔥 <b>РОАСТИНГ: {target}</b>\n\n{reply}\n\n"
            f"<i>Осталось сообщений: {left}\nМожешь задавать вопросы про жертву!</i>",
            parse_mode="HTML",
            reply_markup=roast_kb()
        )
    except Exception as e:
        await thinking.delete()
        await message.answer(f"⚡ Ошибка: {e}")

@router.message(UserState.roast_chat)
async def roast_chat(message: Message, state: FSMContext):
    if not await check_limit(message, state):
        return

    text = message.text.strip()
    data = await state.get_data()
    history = data.get("roast_history", [])

    thinking = await message.answer("💭 Нейрохрам вспоминает жертву...")
    history.append({"role": "user", "content": text})

    try:
        reply = await call_ai("roaster", history)
        history.append({"role": "assistant", "content": reply})
        await state.update_data(roast_history=history)
        await thinking.delete()
        await increment_messages(message.from_user.id)

        user = await get_user(message.from_user.id)
        left = user["messages_limit"] - user["messages_used"]
        await message.answer(
            f"🔥 <b>НЕЙРОХРАМ:</b>\n{reply}\n\n<i>Осталось сообщений: {left}</i>",
            parse_mode="HTML",
            reply_markup=roast_kb()
        )
    except Exception as e:
        await thinking.delete()
        await message.answer(f"⚡ Ошибка: {e}")

# ── PAYMENTS (Telegram Stars) ─────────────────────────────────
@router.callback_query(F.data.startswith("buy:"))
async def cb_buy(cb: CallbackQuery, bot: Bot):
    plan = cb.data.split(":")[1]
    info = PLANS[plan]
    if info["stars"] == 0:
        await cb.answer("Это бесплатный план!", show_alert=True)
        return

    prices = [LabeledPrice(label=f"НЕЙРОХРАМ {info['label']}", amount=info["stars"])]
    await bot.send_invoice(
        chat_id=cb.from_user.id,
        title=f"НЕЙРОХРАМ {info['label']}",
        description=f"{info['messages']} сообщений на 30 дней",
        payload=f"plan:{plan}",
        currency="XTR",
        prices=prices,
        reply_markup=None
    )
    await cb.answer()

@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@router.message(F.successful_payment)
async def successful_payment(message: Message, state: FSMContext):
    payload = message.successful_payment.invoice_payload
    plan = payload.split(":")[1]
    info = PLANS[plan]
    await upgrade_plan(message.from_user.id, plan, info["messages"])
    await state.clear()
    await message.answer(
        f"✅ <b>Оплата прошла!</b>\n\n"
        f"Твой план: <b>{info['emoji']} {info['label']}</b>\n"
        f"Доступно сообщений: <b>{info['messages']}</b>\n\n"
        f"Приятного общения с Нейрохрамом! 🔥",
        parse_mode="HTML"
    )
    await send_main_menu(message, state)

# ── Fallback ──────────────────────────────────────────────────
@router.message(UserState.idle)
async def idle_message(message: Message, state: FSMContext):
    await message.answer("Выбери режим через меню 👇", reply_markup=back_menu_kb())

@router.message()
async def any_message(message: Message, state: FSMContext):
    await send_main_menu(message, state)
