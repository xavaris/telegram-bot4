import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_KEY = os.getenv("GOOGLE_KEY")

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
            "📍 FORMAT:\n"
            "adres startowy - adres końcowy\n\n"
            "Przykład:\n"
            "kartuska 46 gdynia - morska 99 gdynia"
        )
        return

    start, end = text.split("-", 1)
    km = get_distance_km(start.strip(), end.strip())

    if km is None:
        await update.message.reply_text("❌ Nie mogę znaleźć jednego z adresów.")
        return

    price = km * 3 + 10
    forty = round(price * 0.4, 2)

    await update.message.reply_text(
        f"🚗 Dystans: {round(km,2)} km\n"
        f"💰 Szacowana cena: {round(price,2)} zł\n"
        f"🔥 40% ceny: {forty} zł"
    )

# ------------------------
# START
# ------------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, handle))
    print("BOT STARTED")
    app.run_polling()
