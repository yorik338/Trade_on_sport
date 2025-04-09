# bot_aiogram3.py
import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from server import fetch_external_data, transform_for_storage
from datetime import datetime, timedelta

BOT_TOKEN = "1774436433:AAE5wzqXDRfX91OflpapNXuH_WBrVSeDoUo"
USER_CHAT_ID = "1660278061"
USER_CHAT_ID_2 = "320580576"
FOOTBALL_DATA_TOKEN = "5e996b0afc264877913a2e682f2fdf63"

bot = Bot(token=BOT_TOKEN, )
dp = Dispatcher()

state = {
    "active": True,
    "balance": 10000.0,
    "profit": 0.0,
    "bets": []
    # список словарей: {'match': str, 'tip': str, 'odds': float, 'confidence': float, 'resolved': bool, 'result': Optional[str], 'stake': float}
}


def fetch_tips():
    raw_data = fetch_external_data()
    tips = transform_for_storage(raw_data)
    return tips


def get_match_result(home, away):
    try:
        headers = {"X-Auth-Token": FOOTBALL_DATA_TOKEN}
        today = datetime.now().date()
        date_from = (today - timedelta(days=365)).isoformat()
        url = f"https://api.football-data.org/v4/matches?dateFrom={date_from}&dateTo={today}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            matches = response.json().get("matches", [])
            for match in matches:
                h = match["homeTeam"]["name"].lower()
                a = match["awayTeam"]["name"].lower()
                if home.lower() in h and away.lower() in a:
                    winner = match.get("score", {}).get("winner")
                    return winner  # HOME_TEAM, AWAY_TEAM, DRAW
    except Exception as e:
        print(f"❌ Ошибка получения результата матча: {e}")
    return None


def place_bet(tip):
    state["bets"].append({
        "match": f"{tip.team_home} vs {tip.team_away}",
        "home": tip.team_home,
        "away": tip.team_away,
        "tip": tip.tip,
        "odds": tip.odds,
        "confidence": tip.confidence,
        "resolved": False,
        "result": None,
        "stake": 200.0
    })


def check_pending_bets():
    for bet in state["bets"]:
        if not bet["resolved"]:
            result = get_match_result(bet["home"], bet["away"])
            if result is None:
                continue  # ещё нет результата
            win = (bet["tip"] == "home" and result == "HOME_TEAM") or \
                  (bet["tip"] == "away" and result == "AWAY_TEAM") or \
                  (bet["tip"] == "draw" and result == "DRAW")
            profit = bet["stake"] * (bet["odds"] - 1) if win else -bet["stake"]
            state["balance"] += profit
            state["profit"] += profit
            bet["resolved"] = True
            bet["result"] = "✅ УГАДАЛ" if win else "❌ НЕ УГАДАЛ"


def format_report():
    lines = []
    for bet in state["bets"][-10:]:
        if bet["resolved"]:
            status = bet["result"]
        else:
            status = "⏳ ожидаем результат"
        side = "на домашнюю" if bet["tip"] == "home" else ("на гостевую" if bet["tip"] == "away" else "на ничью")
        lines.append(
            f"{bet['match']} — ставка {side} — {status} — ставка ${bet['stake']}"
        )
    lines.append(f"\n💼 Баланс: ${state['balance']:.2f}\n📈 Прибыль: ${state['profit']:.2f}")
    return "\n".join(lines)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Включить ставки", callback_data="enable")],
        [InlineKeyboardButton(text="⛔️ Отключить ставки", callback_data="disable")]
    ])
    await message.answer("Добро пожаловать! Управляй ботом кнопками ниже:", reply_markup=keyboard)


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
        tips = fetch_tips()
        if state["active"]:
            for tip in tips:
                already = any(b["match"] == f"{tip.team_home} vs {tip.team_away}" for b in state["bets"])
                if not already:
                    place_bet(tip)
        check_pending_bets()
        if not tips:
            await bot.send_message(USER_CHAT_ID, "ℹ️ Нет новых матчей для ставок.")
            await bot.send_message(USER_CHAT_ID_2, "ℹ️ Нет новых матчей для ставок.")
        else:
            final_text = format_report()
            await bot.send_message(USER_CHAT_ID, final_text)
            await bot.send_message(USER_CHAT_ID_2, final_text)
        await asyncio.sleep(360)


async def main():
    asyncio.create_task(betting_loop())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
