import os
import requests
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_KEY = os.getenv("GOOGLE_KEY")

# ADMIN IDs
ADMIN_IDS = [
    8224330121,
    8482440165
]

# pamięć zapytań
ORDERS = {}

# -------- GOOGLE GEOCODING --------
def get_coords(address):
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": address, "key": GOOGLE_KEY}
        r = requests.get(url, params=params, timeout=10).json()

        if r["status"] != "OK":
            return None

        loc = r["results"][0]["geometry"]["location"]
        return loc["lat"], loc["lng"]
    except:
        return None

# -------- GOOGLE DISTANCE --------
def get_distance_km(start, end):
    try:
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {"origins": start, "destinations": end, "key": GOOGLE_KEY}
        r = requests.get(url, params=params, timeout=10).json()

        if r["rows"][0]["elements"][0]["status"] != "OK":
            return None

        meters = r["rows"][0]["elements"][0]["distance"]["value"]
        return meters / 1000
    except:
        return None

# -------- MAIN HANDLER --------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "-" not in text:
        await update.message.reply_text(
            "📍 FORMAT:\n"
            "Ulica numer_domu Miasto - Ulica numer_domu Miasto\n\n"
            "Przykład:\n"
            "Dzieci Warszawy 43 Warszawa - Czereśniowa 98 Warszawa\n\n"
            "ℹ️ Cena ma charakter orientacyjny"
        )
        return

    start, end = text.split("-", 1)
    km = get_distance_km(start.strip(), end.strip())

    if km is None:
        await update.message.reply_text("❌ Nie mogę znaleźć jednego z adresów.")
        return

    price = km * 3 + 10
    p50 = round(price * 0.5, 2)
    p35 = round(price * 0.35, 2)

    order_text = (
        f"{start.strip()} - {end.strip()}\n"
        f"Dystans: {round(km,2)} km\n"
        f"Cena orientacyjna: {round(price,2)} zł\n"
        f"50% ceny: {p50} zł\n"
        f"35% ceny (kurs powyżej 100 zł): {p35} zł"
    )

    order_id = str(uuid.uuid4())
    ORDERS[order_id] = order_text

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📨 Wyślij do obsługi", callback_data=order_id)]
    ])

    await update.message.reply_text(order_text, reply_markup=keyboard)

# -------- BUTTON HANDLER --------
async def send_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id = query.data
    order = ORDERS.get(order_id)

    if not order:
        await query.message.reply_text("❌ To zapytanie wygasło.")
        return

    user = query.from_user
    username = f"@{user.username}" if user.username else user.first_name

    for admin in ADMIN_IDS:
        await context.bot.send_message(
            chat_id=admin,
            text=f"📩 NOWE ZAPYTANIE\n👤 Od: {username}\n\n{order}"
        )

    await query.edit_message_reply_markup(None)
    await query.message.reply_text("✅ Wysłano do obsługi.")

# -------- START --------
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CallbackQueryHandler(send_offer))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    print("BOT STARTED")
    app.run_polling()
