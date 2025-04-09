# server.py
from typing import List
from pydantic import BaseModel
import requests

# API от The Odds API
EXTERNAL_API_KEY = "38286be42b8ef6fe5ef5304ba556b4bc"
EXTERNAL_API_URL = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds/"

class BettingTip(BaseModel):
    match_id: str
    league: str
    team_home: str
    team_away: str
    tip: str
    odds: float
    confidence: float

def calculate_confidence(odds: float) -> float:
    if odds <= 1.5:
        return 0.85
    elif odds <= 1.8:
        return 0.75
    elif odds <= 2.1:
        return 0.65
    elif odds <= 2.5:
        return 0.55
    else:
        return 0.45

def fetch_external_data():
    params = {
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal",
        "apiKey": EXTERNAL_API_KEY
    }
    try:
        response = requests.get(EXTERNAL_API_URL, params=params)
        if response.status_code == 200:
            print("✅ Данные получены с внешнего API")
            return response.json()
        else:
            print(f"❌ Ошибка API: {response.status_code} — {response.text}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
    return []

def transform_for_storage(raw_data) -> List[BettingTip]:
    tips = []
    for match in raw_data:
        if "bookmakers" not in match or not match["bookmakers"]:
            continue
        bookie = match["bookmakers"][0]
        outcomes = {o["name"]: o["price"] for o in bookie["markets"][0]["outcomes"]}
        if not outcomes:
            continue
        home_team = match["home_team"]
        odds_value = outcomes.get(home_team, 1.5)
        confidence = calculate_confidence(odds_value)
        tip = BettingTip(
            match_id=str(match.get("id", "")),
            league=match.get("sport_title", "Unknown"),
            team_home=home_team,
            team_away=match["away_team"],
            tip="home",
            odds=odds_value,
            confidence=confidence
        )
        tips.append(tip)
    return tips