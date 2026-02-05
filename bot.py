import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ---------- GEOCODING (Photon) ----------
def get_coords(address):
    url = "https://photon.komoot.io/api/"
    params = {
        "q": address,
        "limit": 1
    }
    r = requests.get(url, params=params, timeout=10)
    data = r.json()

    if not data["features"]:
        return None

    lon, lat = data["features"][0]["geometry"]["coordinates"]
    return lat, lon

# ---------- DISTANCE (OSRM) ----------
def get_distance_km(start, end):
    s = get_coords(start)
    e = get_coords(end)

    if not s or not e:
        return None

    url = f"https://router.project-osrm.org/route/v1/driving/{s[1]},{s[0]};{e[1]},{e[0]}?overview=false"
    r = requests.get(url, timeout=10)
    data = r.json()

    meters = data["routes"][0]["distance"]
    return meters / 1000

# ---------- TELEGRAM HANDLER ----------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "-" not in text:
        await update.message.reply_text(
            "📍 Podaj adresy w formacie:\n"
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

# ---------- START ----------
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, handle))
    print("Bot started...")
    app.run_polling()
