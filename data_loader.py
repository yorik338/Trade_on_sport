import requests

# 🔐 Ключ от внешнего API (например, The Odds API)
EXTERNAL_API_KEY = "850b0f7258944b119358a2ce75350533"
EXTERNAL_API_URL = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds/"

# 🔐 Адрес нашего сервера
LOCAL_SERVER_URL = "http://localhost:8000/api/feed"
LOCAL_SERVER_API_KEY = "your-client-key"

# Шаг 1: Получаем данные с внешнего API
def fetch_external_data():
    params = {
        "regions": "eu",             # Европа
        "markets": "h2h",            # исходы (1X2)
        "oddsFormat": "decimal",
        "apiKey": EXTERNAL_API_KEY
    }
    response = requests.get(EXTERNAL_API_URL, params=params)
    if response.status_code == 200:
        print("✅ Получены данные от внешнего API")
        return response.json()
    else:
        print(f"❌ Ошибка: {response.status_code} — {response.text}")
        return []

# Шаг 2: Преобразуем в наш формат
def transform_for_server(raw_data):
    tips = []
    for match in raw_data:
        if "bookmakers" not in match or not match["bookmakers"]:
            continue
        bookie = match["bookmakers"][0]
        outcomes = {o["name"]: o["price"] for o in bookie["markets"][0]["outcomes"]}
        tip = {
            "match_id": match.get("id", 0),
            "league": match.get("sport_title", "Unknown"),
            "team_home": match["home_team"],
            "team_away": match["away_team"],
            "tip": "home",  # можно встроить свою логику
            "odds": outcomes.get(match["home_team"], 1.5),
            "confidence": 0.65  # тестово; можно прикрутить модель
        }
        tips.append(tip)
    return tips

# Шаг 3: Отправляем данные на наш сервер
def send_to_server(tips):
    headers = {"x-api-key": LOCAL_SERVER_API_KEY}
    response = requests.post(LOCAL_SERVER_URL, json=tips, headers=headers)
    if response.status_code == 200:
        print("✅ Успешно передано на сервер")
    else:
        print(f"❌ Ошибка при отправке: {response.status_code} — {response.text}")

if __name__ == "__main__":
    data = fetch_external_data()
    if data:
        transformed = transform_for_server(data)
        send_to_server(transformed)
