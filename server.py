# server.py
from fastapi import FastAPI, Header, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
import uvicorn
import requests
import asyncio

app = FastAPI()

API_KEYS = {"your-client-key": "paid_user"}

class MatchQuery(BaseModel):
    date: Optional[str] = None

class BettingTip(BaseModel):
    match_id: int
    league: str
    team_home: str
    team_away: str
    tip: str
    odds: float
    confidence: float

# Внутреннее хранилище прогнозов
tip_storage: List[BettingTip] = []

# Запрос к внешнему API (пример: The Odds API)
EXTERNAL_API_KEY = "38286be42b8ef6fe5ef5304ba556b4bc"
EXTERNAL_API_URL = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds/"

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

def transform_for_storage(raw_data):
    tips = []
    for match in raw_data:
        if "bookmakers" not in match or not match["bookmakers"]:
            continue
        bookie = match["bookmakers"][0]
        outcomes = {o["name"]: o["price"] for o in bookie["markets"][0]["outcomes"]}
        tip = BettingTip(
            match_id=match.get("id", 0),
            league=match.get("sport_title", "Unknown"),
            team_home=match["home_team"],
            team_away=match["away_team"],
            tip="home",
            odds=outcomes.get(match["home_team"], 1.5),
            confidence=0.65
        )
        tips.append(tip)
    return tips

@app.on_event("startup")
async def scheduled_fetch():
    async def loop():
        while True:
            raw_data = fetch_external_data()
            if raw_data:
                tips = transform_for_storage(raw_data)
                tip_storage.clear()
                tip_storage.extend(tips)
                print(f"📡 Обновлено {len(tips)} прогнозов")
            await asyncio.sleep(3600)
    asyncio.create_task(loop())

def verify_key(x_api_key: str = Header(...)):
    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return API_KEYS[x_api_key]

@app.post("/api/tips", dependencies=[Depends(verify_key)], response_model=List[BettingTip])
def get_tips(query: MatchQuery):
    return tip_storage

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)