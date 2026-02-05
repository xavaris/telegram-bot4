import os
import requests
from geopy.geocoders import Nominatim
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

geolocator = Nominatim(user_agent="telegram-price-bot")

def get_coords(address):
    location = geolocator.geocode(address)
    if not location:
        return None
    return location.latitude, location.longitude

def get_distance_km(start, end):
    s = get_coords(start)
    e = get_coords(end)

    if not s or not e:
        return None

    url = f"https://router.project-osrm.org/route/v1/driving/{s[1]},{s[0]};{e[1]},{e[0]}?overview=false"
    data = requests.get(url).json()

    meters = data["routes"][0]["distance"]
    return meters / 1000

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "-" not in text:
        await update.message.reply_text(
            "Format:\nadres startowy - adres końcowy"
        )
        return

    start, end = text.split("-")
    km = get_distance_km(start.strip(), end.strip())

    if km is None:
        await update.message.reply_text("Nie mogę znaleźć jednego z adresów 😕")
        return

    price = km * 3 + 10
    forty = round(price * 0.4, 2)

    await update.message.reply_text(
        f"Dystans: {round(km,2)} km\n"
        f"Szacowana cena: {round(price,2)} zł\n"
        f"40% ceny: {forty} zł"
    )

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT, handle))
app.run_polling()
