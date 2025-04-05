# bot_aiogram3.py
import asyncio

import requests
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "1774436433:AAE5wzqXDRfX91OflpapNXuH_WBrVSeDoUo"
API_URL = "http://localhost:8000/api/tips"
API_KEY = "your-client-key"
USER_CHAT_ID = "1660278061"
USER_CHAT_ID_2 = "320580576"
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

state = {
    "active": True,
    "balance": 10000.0,
    "profit": 0.0,
    "bets": []
}


def fetch_tips():
    try:
        headers = {"x-api-key": API_KEY}
        response = requests.post(API_URL, headers=headers, json={})
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print("Ошибка запроса:", e)
    return []


def record_bet(tip):
    stake = 200
    win = tip["confidence"] > 0.65
    profit = stake * (tip["odds"] - 1) if win else -stake
    state["balance"] += profit
    state["profit"] += profit
    state["bets"].append({
        "match": f"{tip['team_home']} vs {tip['team_away']}",
        "profit": profit
    })


def format_report():
    lines = [
        f"💼 Баланс: ${state['balance']:.2f}\n📈 Прибыль: ${state['profit']:.2f}"]
    for bet in state["bets"]:
        lines.append(
            f"📝 {bet['match']} → {'+' if bet['profit'] > 0 else ''}${bet['profit']:.2f}")
    return "\n".join(lines)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Включить ставки",
                              callback_data="enable")],
        [InlineKeyboardButton(text="⛔️ Отключить ставки",
                              callback_data="disable")]
    ])
    await message.answer("Добро пожаловать! Управляй ботом кнопками ниже:",
                         reply_markup=keyboard)


@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    text = f"🔄 Ставки: {'включены' if state['active'] else 'отключены'}\n💼 Баланс: ${state['balance']:.2f}\n📈 Прибыль: ${state['profit']:.2f}"
    await message.answer(text)


@dp.message(Command("report"))
async def cmd_report(message: types.Message):
    await message.answer(format_report() or "Ставок ещё не было.")


@dp.callback_query(lambda c: c.data in ["enable", "disable"])
async def process_callback(callback: types.CallbackQuery):
    state["active"] = callback.data == "enable"
    txt = "Ставки включены ✅" if state["active"] else "Ставки отключены ⛔️"
    await callback.message.edit_text(txt)
    await callback.answer()


async def betting_loop():
    while True:
        if state["active"]:
            tips = fetch_tips()
            for tip in tips:
                record_bet(tip)
            if tips:
                await bot.send_message(USER_CHAT_ID,
                                       "📢 Сделаны ставки:\n" + format_report())
                await bot.send_message(USER_CHAT_ID_2,
                                       "📢 Сделаны ставки:\n" + format_report())
        await asyncio.sleep(360)


async def main():
    asyncio.create_task(betting_loop())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
