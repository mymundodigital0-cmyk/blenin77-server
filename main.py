from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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

# ==========================================
# 🌐 PÁGINA WEB DE VENTAS (Landing Page)
# ==========================================
landing_html = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BLENIN77 - Sistema de Trading Cuantitativo con IA</title>
    <style>
        body { margin: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0d1b2a; color: #e0e1dd; }
        header { background-color: #1b263b; padding: 40px 20px; text-align: center; border-bottom: 2px solid #00e5ff; }
        h1 { color: #00e5ff; margin: 0; font-size: 3rem; }
        h2 { color: #fff; text-align: center; margin-top: 40px; }
        p { text-align: center; color: #94a3b8; font-size: 1.2rem; }
        .features { display: flex; justify-content: center; flex-wrap: wrap; padding: 20px; }
        .feature-box { background: #1b263b; padding: 20px; margin: 10px; border-radius: 10px; width: 300px; text-align: center; border: 1px solid #334155; }
        .feature-box h3 { color: #00e5ff; }
        .pricing { display: flex; justify-content: center; flex-wrap: wrap; padding: 40px 20px; }
        .plan { background: #1b263b; border: 1px solid #334155; border-radius: 15px; width: 300px; margin: 15px; padding: 30px; text-align: center; }
        .plan h3 { color: #fff; font-size: 1.5rem; }
        .plan .price { font-size: 3rem; color: #00e5ff; margin: 15px 0; }
        .btn { display: inline-block; background: #00e5ff; color: #000; padding: 15px 30px; text-decoration: none; font-weight: bold; border-radius: 5px; transition: 0.3s; width: 80%; margin-top: 15px; }
        .btn:hover { background: #fff; }
        .plan.gold { border: 2px solid #ffc107; }
        footer { text-align: center; padding: 20px; background: #1b263b; color: #64748b; margin-top: 40px; }
    </style>
</head>
<body>
    <header>
        <h1>BLENIN77</h1>
        <p>El Sistema Definitivo de Trading Algorítmico con Inteligencia Artificial y Enjambre de Agentes</p>
    </header>

    <section class="features">
        <div class="feature-box">
            <h3>🐟 Enjambre 3D</h3>
            <p>500 agentes simulan el futuro del mercado en milisegundos para aprobar o vetar operaciones.</p>
        </div>
        <div class="feature-box">
            <h3>🛡️ Agente Centinela</h3>
            <p>Lee noticias en tiempo real y bloquea operaciones si detecta peligros en la economía global.</p>
        </div>
        <div class="feature-box">
            <h3>🧠 Cerebro Global</h3>
            <p>Aprende de todos los usuarios del mundo para potenciar estrategias ganadoras.</p>
        </div>
    </section>

    <h2>Planes de Suscripción</h2>
    <section class="pricing">
        <div class="plan">
            <h3>🥉 Bronce</h3>
            <div class="price">$49<span style="font-size: 1rem; color: #94a3b8;">/mes</span></div>
            <p>1 Cuenta MT5</p>
            <p>Modo MT5 Puro</p>
            <p>3 Activos Máximos</p>
            <!-- AQUÍ PONES TU ENLACE DE STRIPE PARA BRONCE -->
            <a href="https://buy.stripe.com/test_4gw3eq8eV6YX7OEdQQ" class="btn">Suscribirme</a>
        </div>
        <div class="plan">
            <h3>🥈 Plata</h3>
            <div class="price">$99<span style="font-size: 1rem; color: #94a3b8;">/mes</span></div>
            <p>2 Cuentas MT5</p>
            <p>Modo Híbrido + Centinela</p>
            <p>10 Activos + Enjambre 3D</p>
            <!-- AQUÍ PONES TU ENLACE DE STRIPE PARA PLATA -->
            <a href="https://buy.stripe.com/test_28o5mA4gF2AS5xO000" class="btn">Suscribirme</a>
        </div>
        <div class="plan gold">
            <h3>🥇 Oro</h3>
            <div class="price">$199<span style="font-size: 1rem; color: #94a3b8;">/mes</span></div>
            <p>Cuentas Ilimitadas</p>
            <p>Deep Learning (PyTorch)</p>
            <p>Cerebro Global Premium</p>
            <!-- AQUÍ PONES TU ENLACE DE STRIPE PARA ORO -->
            <a href="https://buy.stripe.com/test_8wM3eqdEj9zC5xO146" class="btn">Suscribirme</a>
        </div>
    </section>

    <footer>
        <p>&copy; 2026 BLENIN77. Todos los derechos reservados. By Lenin Benitez.</p>
    </footer>
</body>
</html>
"""

# ==========================================
# 🧠 BASES DE DATOS EN MEMORIA
# ==========================================
db_trades = []
licenses_db = {
    "BLENIN-TEST-1234": {"hwid": None, "expires": datetime.now() + timedelta(days=30), "active": True, "plan": "ORO"}
}

# ==========================================
# 📦 MODELOS DE DATOS (Pydantic)
# ==========================================
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
    plan_name = plan.upper().split()[0]
    return f"BLENIN-{plan_name}-{part1}-{part2}"

# ==========================================
# 🌐 RUTA WEB (Lo que ve el usuario en internet)
# ==========================================
@app.get("/", response_class=HTMLResponse)
def read_root():
    return landing_html

# ==========================================
# 🐟 RUTAS DEL CEREBRO GLOBAL (IA)
# ==========================================
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

# ==========================================
# 🔒 RUTAS DE LICENCIAS (Sistema de Cobros)
# ==========================================
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
