from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from collections import defaultdict
from datetime import datetime, timedelta

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base de datos del Cerebro Global
db_trades = []

# Base de datos de Licencias (Key: {hwid, expires, active})
# Añadimos una licencia de prueba por 30 días: "BLENIN-TEST-1234"
licenses_db = {
    "BLENIN-TEST-1234": {"hwid": None, "expires": datetime.now() + timedelta(days=30), "active": True}
}

class TradeData(BaseModel):
    strategy: str
    symbol: str
    timeframe: str
    outcome: bool
    profit_pips: float
    session: str

class LicenseCheck(BaseModel):
    key: str
    hwid: str

@app.post("/api/sync_intel")
def receive_intel(trade: TradeData):
    db_trades.append(trade)
    return {"status": "received", "total_trades": len(db_trades)}

@app.get("/api/get_global_intel")
def get_intel():
    if not db_trades: return {}
    stats = defaultdict(lambda: {"wins": 0, "total": 0})
    for t in db_trades:
        key = f"{t.strategy}_{t.symbol}_{t.session}"
        stats[key]["total"] += 1
        if t.outcome: stats[key]["wins"] += 1
    result = {}
    for key, val in stats.items():
        if val["total"] > 0:
            result[key] = {"win_rate": val["wins"] / val["total"], "trades": val["total"]}
    return result

@app.post("/api/validate_license")
def validate_license(data: LicenseCheck):
    key = data.key.upper().strip()
    if key not in licenses_db:
        return {"valid": False, "message": "❌ Licencia no encontrada."}
    
    license_info = licenses_db[key]
    
    if not license_info["active"]:
        return {"valid": False, "message": "🚫 Licencia suspendada por falta de pago."}
        
    if datetime.now() > license_info["expires"]:
        return {"valid": False, "message": "⏳ Tu suscripción ha expirado. Renueva en blenin77.com."}
        
    # Vincular HWID (Hardware ID) la primera vez que se usa
    if license_info["hwid"] is None:
        license_info["hwid"] = data.hwid
    elif license_info["hwid"] != data.hwid:
        return {"valid": False, "message": "🔒 Esta licencia ya está activada en otra PC."}
        
    days_left = (license_info["expires"] - datetime.now()).days
    return {"valid": True, "message": f"✅ Licencia activa. Quedan {days_left} días.", "days_left": days_left}
