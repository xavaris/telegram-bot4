import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

# -----------------------------
# GEOCODING - PHOTON (OSM)
# -----------------------------
def get_coords(address):
    try:
        url = "https://photon.komoot.io/api/"
        params = {"q": address, "limit": 1}
        r = requests.get(url, params=params, timeout=10)

        if r.status_code != 200:
            return None

        data = r.json()

        if "features" not in data or len(data["features"]) == 0:
            return None

        lon, lat = data["features"][0]["geometry"]["coordinates"]
        return lat, lon
    except:
        return None

# -----------------------------
# DISTANCE - OSRM
# -----------------------------
def get_distance_km(start, end):
    try:
        s = get_coords(start)
        e = get_coords(end)

        if not s or not e:
            return None

        url = f"https://router.project-osrm.org/route/v1/driving/{s[1]},{s[0]};{e[1]},{e[0]}?overview=false"
        r = requests.get(url, timeout=10)

        if r.status_code != 200:
            return None

        data = r.json()

        if "routes" not in data or len(data["routes"]) == 0:
            return None

        meters = data["routes"][0]["distance"]
        return meters / 1000
    except:
        return None

# -----------------------------
# TELEGRAM HANDLER
# -----------------------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
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
    except:
        await update.message.reply_text("⚠️ Wystąpił błąd. Spróbuj ponownie.")

# -----------------------------
# START BOT
# -----------------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, handle))
    print("BOT 9999.0 STARTED")
    app.run_polling()
