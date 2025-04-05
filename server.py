# server.py
from fastapi import FastAPI, Header, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel

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

DUMMY_TIPS = [
    BettingTip(match_id=1, league="EPL", team_home="Arsenal", team_away="Chelsea", tip="home", odds=1.95, confidence=0.68),
    BettingTip(match_id=2, league="La Liga", team_home="Real Madrid", team_away="Sevilla", tip="home", odds=1.70, confidence=0.74),
]

async def verify_key(x_api_key: str = Header(...)):
    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return API_KEYS[x_api_key]

@app.post("/api/tips", dependencies=[Depends(verify_key)], response_model=List[BettingTip])
async def get_tips(query: MatchQuery):
    return DUMMY_TIPS

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
