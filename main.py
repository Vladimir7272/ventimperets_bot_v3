from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import random
import os

TOKEN = os.getenv("BOT_TOKEN")

OBJECTS = [
    "Квартира без кондиционера",
    "Офис задыхается от духоты",
    "Магазин с плесенью на стенах",
    "Цех, где люди тают от жары",
    "Дом, где окна не открываются",
    "Коттедж с плесенью и затхлостью"
]

HUMOR_PHRASES = [
    "На складе больше не пахнет кефиром!",
    "Ты спас бабушку с гипсовым мопсом от духоты!",
    "Жара сдалась без боя!",
    "Теперь в офисе снова можно дышать!",
    "Плесень кричит: 'Мы сдаёмся!'"
]

TOOLS = {
    "🔧 Быстрый перфоратор": {"cost": 50, "bonus": "+10% XP"},
    "📦 Склад фильтров": {"cost": 100, "bonus": "+1 заказ в день"},
    "💼 Эмблема Про": {"cost": 150, "bonus": "Элитные заказы"}
}

user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = {
        "coins": 0,
        "xp": 0,
        "level": 1,
        "orders": 0,
        "tools": [],
        "active_task": None,
        "last_emergency": False
    }
    keyboard = [["🚧 Взять заказ", "🔥 Срочный вызов"], ["📊 Профиль", "🛒 Магазин"], ["🏆 Рейтинг"]]
    await update.message.reply_text(
        "Привет, монтажник! Добро пожаловать в игру *ВентИмперец v3*!",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode="Markdown"
    )

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_states:
        await start(update, context)
        return

    user = user_states[user_id]

    if text == "🚧 Взять заказ":
        task = random.choice(OBJECTS)
        user["active_task"] = task
        keyboard = [["🔧 Установить систему"]]
        await update.message.reply_text(
            f"🛠️ Новый объект: *{task}*\n\nНажми кнопку, чтобы установить вентиляцию!",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
            parse_mode="Markdown"
        )

    elif text == "🔥 Срочный вызов":
        if user["last_emergency"]:
            await update.message.reply_text("❗ Срочный заказ уже был сегодня. Возвращайся завтра!")
            return
        user["last_emergency"] = True
        user["coins"] += 30
        user["xp"] += 20
        await update.message.reply_text("🚨 Срочный объект обслужен! +20 XP, +30 КлиматКоинов")

    elif text == "🔧 Установить систему":
        if not user.get("active_task"):
            await update.message.reply_text("Сначала возьми заказ! 🧐")
            return

        user["orders"] += 1
        base_xp = 10
        bonus = 1.1 if "🔧 Быстрый перфоратор" in user["tools"] else 1.0
        gained_xp = int(base_xp * bonus)
        user["xp"] += gained_xp
        user["coins"] += 10

        humor = random.choice(HUMOR_PHRASES)

        if user["xp"] >= user["level"] * 50:
            user["level"] += 1
            user["coins"] += 5
            await update.message.reply_text(f"🎉 Уровень повышен! Теперь ты уровень {user['level']} и получил +5 КлиматКоинов! 🥳")

        user["active_task"] = None
        keyboard = [["🚧 Взять заказ", "🔥 Срочный вызов"], ["📊 Профиль", "🛒 Магазин"], ["🏆 Рейтинг"]]
        await update.message.reply_text(
            f"✅ Установка завершена! +{gained_xp} XP, +10 КлиматКоинов\n💬 {humor}",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    elif text == "📊 Профиль":
        await update.message.reply_text(
            f"📊 Профиль:\n"
            f"🔹 Уровень: {user['level']}\n"
            f"🔧 Заказов: {user['orders']}\n"
            f"💰 КлиматКоины: {user['coins']}\n"
            f"⭐ XP: {user['xp']}\n"
            f"🧰 Инструменты: {', '.join(user['tools']) if user['tools'] else 'нет'}\n"
            f"🚶 Спасено людей: {user['orders'] * 3}"
        )

    elif text == "🛒 Магазин":
        message = "🛒 Магазин инструментов:\n"
        for tool, data in TOOLS.items():
            message += f"{tool} — {data['cost']} коинов ({data['bonus']})\n"
        message += "\nНапиши название инструмента, чтобы купить."
        await update.message.reply_text(message)

    elif text in TOOLS:
        if text in user["tools"]:
            await update.message.reply_text("У тебя уже есть этот инструмент.")
            return
        if user["coins"] >= TOOLS[text]["cost"]:
            user["coins"] -= TOOLS[text]["cost"]
            user["tools"].append(text)
            await update.message.reply_text(f"✅ Покупка успешна: {text}")
        else:
            await update.message.reply_text("Недостаточно КлиматКоинов 💸")

    elif text == "🏆 Рейтинг":
        top = sorted(user_states.items(), key=lambda x: x[1]['xp'], reverse=True)[:5]
        msg = "🏆 ТОП монтажников:\n"
        for i, (uid, udata) in enumerate(top, 1):
            msg += f"{i}. ID {uid} — {udata['xp']} XP\n"
        await update.message.reply_text(msg)

    else:
        await update.message.reply_text("Выбирай действие из меню ⬇️")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_choice))

app.run_polling()
