from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from collections import defaultdict

app = FastAPI()

# Permitir que cualquier bot se conecte a nuestro servidor
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base de datos en memoria (cuando tengas miles de usuarios, la cambias a Supabase)
db_trades = []

class TradeData(BaseModel):
    strategy: str
    symbol: str
    timeframe: str
    outcome: bool
    profit_pips: float
    session: str

@app.post("/api/sync_intel")
def receive_intel(trade: TradeData):
    db_trades.append(trade)
    return {"status": "received", "total_trades": len(db_trades)}

@app.get("/api/get_global_intel")
def get_intel():
    if not db_trades:
        return {}
    
    stats = defaultdict(lambda: {"wins": 0, "total": 0})
    
    for t in db_trades:
        key = f"{t.strategy}_{t.symbol}_{t.session}"
        stats[key]["total"] += 1
        if t.outcome:
            stats[key]["wins"] += 1
            
    result = {}
    for key, val in stats.items():
        if val["total"] > 0:
            result[key] = {
                "win_rate": val["wins"] / val["total"],
                "trades": val["total"]
            }
    return result
