from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from collections import defaultdict
from datetime import datetime, timedelta
import random
import string

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base de datos del Cerebro Global
db_trades = []

# Base de datos de Licencias
licenses_db = {
    "BLENIN-TEST-1234": {"hwid": None, "expires": datetime.now() + timedelta(days=30), "active": True, "plan": "ORO"}
}

# Modelos de datos
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

class LicenseCreate(BaseModel):
    plan: str
    duration_days: int = 30

class LicenseAction(BaseModel):
    key: str

def generate_license_key(plan):
    part1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    part2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    plan_name = plan.upper().split()[0] # Toma la primera palabra (BRONCE, PLATA, ORO)
    return f"BLENIN-{plan_name}-{part1}-{part2}"

# === RUTAS DEL CEREBRO GLOBAL ===
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

# === RUTAS DE LICENCIAS ===
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
        
    if license_info["hwid"] is None:
        license_info["hwid"] = data.hwid
    elif license_info["hwid"] != data.hwid:
        return {"valid": False, "message": "🔒 Esta licencia ya está activada en otra PC."}
        
    days_left = (license_info["expires"] - datetime.now()).days
    return {"valid": True, "message": f"✅ Licencia activa. Quedan {days_left} días.", "days_left": days_left}

@app.post("/api/create_license")
def create_license(data: LicenseCreate):
    """Make.com llama esta ruta cuando Stripe confirma un pago"""
    key = generate_license_key(data.plan)
    licenses_db[key] = {
        "hwid": None,
        "expires": datetime.now() + timedelta(days=data.duration_days),
        "active": True,
        "plan": data.plan
    }
    return {"status": "success", "key": key}

@app.post("/api/suspend_license")
def suspend_license(data: LicenseAction):
    """Make.com llama esta ruta cuando Stripe reporta que el pago falló"""
    key = data.key.upper().strip()
    if key in licenses_db:
        licenses_db[key]["active"] = False
        return {"status": "success", "message": "Licencia suspendida."}
    return {"status": "error", "message": "Licencia no encontrada."}

@app.post("/api/renew_license")
def renew_license(data: LicenseAction):
    """Make.com llama esta ruta para renovar 30 días más"""
    key = data.key.upper().strip()
    if key in licenses_db:
        licenses_db[key]["active"] = True
        licenses_db[key]["expires"] = datetime.now() + timedelta(days=30)
        return {"status": "success", "message": "Licencia renovada."}
    return {"status": "error", "message": "Licencia no encontrada."}
