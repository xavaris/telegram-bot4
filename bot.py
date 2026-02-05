import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_KEY = os.getenv("GOOGLE_KEY")

ADMIN_USERS = ["@Pontoderabilia", "@Burwusovy"]

# ------------------------
# GOOGLE GEOCODING
# ------------------------
def get_coords(address):
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": address,
            "key": GOOGLE_KEY
        }
        r = requests.get(url, params=params, timeout=10).json()

        if r["status"] != "OK":
            return None

        loc = r["results"][0]["geometry"]["location"]
        return loc["lat"], loc["lng"]
    except:
        return None

# ------------------------
# GOOGLE DISTANCE MATRIX
# ------------------------
def get_distance_km(start, end):
    try:
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins": start,
            "destinations": end,
            "key": GOOGLE_KEY
        }
        r = requests.get(url, params=params, timeout=10).json()

        if r["rows"][0]["elements"][0]["status"] != "OK":
            return None

        meters = r["rows"][0]["elements"][0]["distance"]["value"]
        return meters / 1000
    except:
        return None

# ------------------------
# TELEGRAM HANDLER
# ------------------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "-" not in text:
        await update.message.reply_text(
            "📍 Podaj adresy w formacie:\n\n"
            "Dzieci Warszawy 43 Warszawa - Czereśniowa 98 Warszawa\n\n"
            "Ulica numerdomu Miasto - Ulica numerdomu Miasto\n\n"
            "ℹ️ Cena ma charakter orientacyjny"
        )
        return

    start, end = text.split("-", 1)
    km = get_distance_km(start.strip(), end.strip())

    if km is None:
        await update.message.reply_text("❌ Nie mogę znaleźć jednego z adresów.")
        return

    price = km * 3 + 10
    fifty = round(price * 0.5, 2)
    thirtyfive = round(price * 0.35, 2)

    await update.message.reply_text(
        f"🚗 Dystans: {round(km,2)} km\n"
        f"💰 Cena orientacyjna: {round(price,2)} zł\n\n"
        f"✅ 50% ceny: {fifty} zł\n"
        f"🔥 35% ceny: {thirtyfive} zł (kurs powyżej 100 zł)\n\n"
        f"👉 Kliknij aby przesłać ofertę:\n"
        f"/wyslij {start.strip()} - {end.strip()} | Cena orientacyjna: {round(price,2)} zł"
    )

# ------------------------
# SEND TO ADMINS
# ------------------------
async def send_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.replace("/wyslij", "").strip()

    user = update.message.from_user
    username = f"@{user.username}" if user.username else user.first_name

    for admin in ADMIN_USERS:
        await context.bot.send_message(
            chat_id=admin,
            text=(
                "📩 NOWE ZAPYTANIE\n"
                f"👤 Od: {username}\n"
                f"{msg}"
            )
        )

    await update.message.reply_text("✅ Wysłano do obsługi.")

# ------------------------
# START
# ------------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.Regex("^/wyslij"), send_offer))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    print("BOT STARTED")
    app.run_polling()
