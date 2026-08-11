from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from collections import defaultdict
from datetime import datetime, timedelta
import random, string, smtplib, os, requests, json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 🔧 CONFIGURACIÓN JSONBIN Y CORREO
# ==========================================
JSONBIN_BIN_ID = os.environ.get("JSONBIN_BIN_ID", "")
JSONBIN_API_KEY = os.environ.get("JSONBIN_API_KEY", "")
JSONBIN_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"

# ✅ NUEVA BASE DE DATIOS PERMANENTE EN LA NUBE
JSONBIN_DB_ID = os.environ.get("JSONBIN_DB_ID", "")
JSONBIN_DB_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_DB_ID}"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = "mymundodigital0@gmail.com"
SMTP_PASSWORD = "ysdoqcmnevrnnogy" # ✅ Tu contraseña de aplicación de Google

def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except: return False

# ==========================================
# 🧠 SISTEMA DE BASE DE DATOS EN LA NUBE (Anti-Reset)
# ==========================================
def load_dbs():
    """Carga las licencias y pruebas desde JSONBin para no perderlas al reiniciar"""
    try:
        headers = {"X-Master-Key": JSONBIN_API_KEY}
        resp = requests.get(JSONBIN_DB_URL, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()["record"]
            return data.get("licenses_db", {}), data.get("trials_db", {})
    except: pass
    return {}, {}

def save_dbs(lic, trials):
    """Guarda las licencias y pruebas en JSONBin permanentemente"""
    try:
        headers = {"Content-Type": "application/json", "X-Master-Key": JSONBIN_API_KEY}
        data = {"licenses_db": lic, "trials_db": trials}
        requests.put(JSONBIN_DB_URL, json=data, headers=headers, timeout=5)
    except: pass

# Cargar bases de datos al arrancar el servidor
licenses_db, trials_db = load_dbs()

# Si está vacío (primera vez), poner la licencia de prueba
if not licenses_db:
    licenses_db = {
        "BLENIN-TEST-ORO": {"hwid": None, "expires": "2026-09-15T00:00:00", "active": True, "plan": "ORO", "email": "test-oro@blenin77.com"},
        "BLENIN-TEST-PLATA": {"hwid": None, "expires": "2026-09-15T00:00:00", "active": True, "plan": "PLATA", "email": "test-plata@blenin77.com"},
        "BLENIN-TEST-BRONCE": {"hwid": None, "expires": "2026-09-15T00:00:00", "active": True, "plan": "BRONCE", "email": "test-bronce@blenin77.com"}
    }
    save_dbs(licenses_db, trials_db)

def get_content():
    try:
        headers = {"X-Master-Key": JSONBIN_API_KEY}
        resp = requests.get(JSONBIN_URL, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()["record"]
            if "publications" not in data: data["publications"] = []
            if "plans" not in data: data["plans"] = []
            if "social_links" not in data: data["social_links"] = {}
            return data
    except: pass
    return {
        "hero_title": "BLENIN.G.77",
        "hero_subtitle": "THE BEST FUTURE FOR YOU",
        "hero_text": "IA Predictiva, Enjambre de 500 Agentes y Análisis Global en Tiempo Real.",
        "publications": [{"type": "video", "url": "https://www.youtube.com/embed/dQw4w9WgXcQ", "desc": "Mira cómo el Enjambre de Agentes abre operaciones reales."}],
        "plans": [
            {"name": "🥉 Bronce", "price": "$49", "features": "✅ 1 Cuenta MT5\n✅ Modo MT5 Puro", "link": "https://buy.stripe.com/test_4gw3eq8eV6YX7OEdQQ", "highlight": False},
            {"name": "🥈 Plata", "price": "$99", "features": "✅ 2 Cuentas MT5\n✅ Modo Híbrido + Enjambre", "link": "https://buy.stripe.com/test_28o5mA4gF2AS5xO000", "highlight": True},
            {"name": "🥇 Oro", "price": "$199", "features": "✅ Cuentas Ilimitadas\n✅ Deep Learning (PyTorch)", "link": "https://buy.stripe.com/test_8wM3eqdEj9zC5xO146", "highlight": False}
        ],
        "social_links": {"facebook": "", "whatsapp": "", "youtube": "", "tiktok": "", "telegram": "", "instagram": ""}
    }

def save_content(data):
    try:
        headers = {"Content-Type": "application/json", "X-Master-Key": JSONBIN_API_KEY}
        requests.put(JSONBIN_URL, json=data, headers=headers, timeout=5)
        return True
    except: return False

# ==========================================
# 🎛️ PANEL DE ADMINISTRACIÓN Y WEB (Acortado por espacio, igual al anterior)
# ==========================================
@app.get("/admin", response_class=HTMLResponse)
def admin_panel():
    # (El código del panel es el mismo que te di en el mensaje anterior, no cambia)
    c = get_content()
    pubs = c.get('publications', [])
    plans = c.get('plans', [])
    social = c.get('social_links', {})
    pubs_json = str(pubs).replace("'", '"').replace('"', '&quot;')
    plans_json = str(plans).replace("'", '"').replace('"', '&quot;')
    return f"""<html><head><title>Admin</title></head><body><h1>Panel</h1><p>Edita tu web aquí.</p></body></html>""" # Reemplaza esto con el código completo del panel anterior

@app.post("/api/save_content")
def api_save_content(data: dict):
    if save_content(data): return {"message": "✅ Guardado."}
    return {"message": "❌ Error."}

@app.get("/recuperar-clave", response_class=HTMLResponse)
def recover_page():
    return "<html><body><h1>Recuperar</h1></body></html>" # Igual al anterior

@app.get("/", response_class=HTMLResponse)
def read_root():
    # (El código de la web es el mismo que te di en el mensaje anterior, no cambia)
    c = get_content()
    return f"<html><body><h1>{c.get('hero_title')}</h1></body></html>" # Reemplaza esto con el código completo de la web anterior

# ==========================================
# 🔒 RUTAS DE LICENCIAS Y PRUEBAS (Modificadas para guardar en la nube)
# ==========================================
class TradeData(BaseModel): strategy: str; symbol: str; timeframe: str; outcome: bool; profit_pips: float; session: str
class LicenseCheck(BaseModel): key: str; hwid: str
class LicenseCreate(BaseModel): plan: str; duration_days: int = 30; email: str = ""
class LicenseAction(BaseModel): key: str
class TrialRequest(BaseModel): hwid: str
class RecoveryRequest(BaseModel): email: str

def generate_license_key(plan):
    p1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    p2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"BLENIN-{plan.upper()}-{p1}-{p2}"

@app.post("/api/sync_intel")
def receive_intel(trade: TradeData):
    return {"status": "received"}

@app.get("/api/get_global_intel")
def get_intel():
    return {}

@app.post("/api/start_trial")
def start_trial(data: TrialRequest):
    """Otorga 30 días de prueba y los guarda en la nube para no reiniciarse"""
    global trials_db
    if data.hwid in trials_db:
        # Si ya existe, revisar fecha
        expires = datetime.fromisoformat(trials_db[data.hwid]["expires"])
        if datetime.now() > expires:
            return {"valid": False, "message": "⏳ Prueba expirada."}
        return {"valid": True, "days_left": (expires - datetime.now()).days, "plan": "BRONCE"}
    
    # Si es nueva PC, dar 30 días
    trials_db[data.hwid] = {"expires": (datetime.now() + timedelta(days=30)).isoformat()}
    save_dbs(licenses_db, trials_db) # ✅ GUARDAR EN NUBE
    return {"valid": True, "days_left": 30, "plan": "BRONCE"}

@app.post("/api/validate_license")
def validate_license(data: LicenseCheck):
    global licenses_db
    key = data.key.upper().strip()
    if key not in licenses_db: return {"valid": False, "message": "❌ Licencia no encontrada."}
    info = licenses_db[key]
    if not info["active"]: return {"valid": False, "message": "🚫 Licencia suspendada."}
    
    expires = datetime.fromisoformat(info["expires"])
    if datetime.now() > expires: return {"valid": False, "message": "⏳ Expirada."}
    
    if info["hwid"] is None:
        info["hwid"] = data.hwid
        save_dbs(licenses_db, trials_db) # ✅ GUARDAR HWID EN NUBE
    elif info["hwid"] != data.hwid: return {"valid": False, "message": "🔒 En uso en otra PC."}
    
    return {"valid": True, "days_left": (expires - datetime.now()).days, "plan": info["plan"]}

@app.post("/api/create_license")
def create_license(data: LicenseCreate):
    global licenses_db
    key = generate_license_key(data.plan)
    licenses_db[key] = {
        "hwid": None, 
        "expires": (datetime.now() + timedelta(days=data.duration_days)).isoformat(), 
        "active": True, "plan": data.plan.upper(), "email": data.email.lower()
    }
    save_dbs(licenses_db, trials_db) # ✅ GUARDAR EN NUBE
    return {"status": "success", "key": key}

@app.post("/api/recover_by_email")
def recover_by_email(req: RecoveryRequest):
    for key, info in licenses_db.items():
        if info.get("email", "").lower() == req.email.lower() and info["active"]:
            send_email(req.email, "🔑 Tu Licencia BLENIN77", f"Tu clave es: {key}\nPlan: {info['plan']}")
            return {"status": "success", "message": "Enviado al correo."}
    return {"status": "error", "message": "Correo no encontrado."}
