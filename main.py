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

def get_content():
    """Lee los textos, videos y planes desde JSONBin"""
    try:
        headers = {"X-Master-Key": JSONBIN_API_KEY}
        resp = requests.get(JSONBIN_URL, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()["record"]
            if "videos" not in data: data["videos"] = []
            if "plans" not in data: data["plans"] = []
            return data
    except: pass
    
    # Valores por defecto si falla la conexión o es la primera vez
    return {
        "hero_title": "BLENIN.G.77",
        "hero_subtitle": "THE BEST FUTURE FOR YOU",
        "hero_text": "IA Predictiva, Enjambre de 500 Agentes y Análisis Global en Tiempo Real.",
        "videos": [
            {"url": "https://www.youtube.com/embed/dQw4w9WgXcQ", "desc": "Mira cómo el Enjambre de Agentes abre operaciones reales."}
        ],
        "plans": [
            {"name": "🥉 Bronce", "price": "$49", "features": "✅ 1 Cuenta MT5\n✅ Modo MT5 Puro", "link": "https://buy.stripe.com/test_4gw3eq8eV6YX7OEdQQ", "highlight": False},
            {"name": "🥈 Plata", "price": "$99", "features": "✅ 2 Cuentas MT5\n✅ Modo Híbrido + Enjambre", "link": "https://buy.stripe.com/test_28o5mA4gF2AS5xO000", "highlight": True},
            {"name": "🥇 Oro", "price": "$199", "features": "✅ Cuentas Ilimitadas\n✅ Deep Learning (PyTorch)", "link": "https://buy.stripe.com/test_8wM3eqdEj9zC5xO146", "highlight": False}
        ]
    }

def save_content(data):
    try:
        headers = {"Content-Type": "application/json", "X-Master-Key": JSONBIN_API_KEY}
        requests.put(JSONBIN_URL, json=data, headers=headers, timeout=5)
        return True
    except: return False

# ==========================================
# 🎛️ PANEL DE ADMINISTRACIÓN (Texto, Videos y Planes)
# ==========================================
@app.get("/admin", response_class=HTMLResponse)
def admin_panel():
    c = get_content()
    videos = c.get('videos', [])
    plans = c.get('plans', [])
    
    videos_json = str(videos).replace("'", '"').replace('"', '&quot;')
    plans_json = str(plans).replace("'", '"').replace('"', '&quot;')
    
    return f"""
    <html><head><title>Admin Panel - BLENIN77</title>
    <style>
        body{{font-family:sans-serif;background:#1e293b;color:#fff;padding:40px;max-width:800px;margin:auto;}}
        input,textarea,select{{width:100%;padding:10px;margin:10px 0;border-radius:5px;border:none;background:#334155;color:#fff;box-sizing:border-box;}}
        button{{background:#00e5ff;color:#000;padding:15px 30px;border:none;border-radius:5px;font-weight:bold;cursor:pointer;}}
        .row{{background:#0f172a;padding:15px;border-radius:8px;margin-bottom:15px;border:1px solid #334155;}}
        .btn-del{{background:#ef4444;color:white;padding:8px 15px;font-size:12px;}}
        .btn-add{{background:#10b981;color:white;padding:10px 20px;font-size:14px;margin-bottom:20px;}}
        h3{{border-bottom:1px solid #334155;padding-bottom:10px;margin-top:40px;}}
    </style></head>
    <body><h1>🎛️ Panel de Control de la Página Web</h1>
    
    <h3>Textos Principales</h3>
    <label>Título Principal (H1):</label>
    <input type="text" id="hero_title" value="{c.get('hero_title', '')}" required>
    <label>Subtítulo (H2):</label>
    <input type="text" id="hero_subtitle" value="{c.get('hero_subtitle', '')}" required>
    <label>Texto descriptivo:</label>
    <textarea id="hero_text" rows="3" required>{c.get('hero_text', '')}</textarea>

    <h3>Videos de YouTube</h3>
    <div id="videos-container"></div>
    <button class="btn-add" onclick="addVideoRow()">➕ Agregar Nuevo Video</button>

    <h3>Planes de Suscripción</h3>
    <div id="plans-container"></div>
    <button class="btn-add" onclick="addPlanRow()">➕ Agregar Nuevo Plan</button>

    <br><br>
    <button onclick="saveData()">💾 Guardar y Publicar Cambios</button>
    <p id="msg" style="color:green;font-weight:bold;font-size:18px;"></p>

    <script>
    const existingVideos = {videos_json};
    const existingPlans = {plans_json};
    
    function addVideoRow(url = '', desc = '') {{
        const container = document.getElementById('videos-container');
        const div = document.createElement('div');
        div.className = 'row';
        div.innerHTML = `
            <input type="text" class="v-url" placeholder="URL Embed de YouTube" value="${{url}}">
            <textarea class="v-desc" placeholder="Anuncio o descripción">${{desc}}</textarea>
            <button class="btn-del" onclick="this.parentElement.remove()">🗑️ Eliminar Video</button>
        `;
        container.appendChild(div);
    }}

    function addPlanRow(name = '', price = '', features = '', link = '', highlight = false) {{
        const container = document.getElementById('plans-container');
        const div = document.createElement('div');
        div.className = 'row';
        div.innerHTML = `
            <input type="text" class="p-name" placeholder="Nombre del Plan (ej. 🥈 Plata)" value="${{name}}">
            <input type="text" class="p-price" placeholder="Precio (ej. $99)" value="${{price}}">
            <textarea class="p-features" placeholder="Características (usa Enter para saltos de línea)">${{features}}</textarea>
            <input type="text" class="p-link" placeholder="Enlace de pago de Stripe" value="${{link}}">
            <label><input type="checkbox" class="p-highlight" ${{highlight ? 'checked' : ''}}> Resaltar este plan (borde cian)</label>
            <button class="btn-del" onclick="this.parentElement.remove()">🗑️ Eliminar Plan</button>
        `;
        container.appendChild(div);
    }}

    if(existingVideos.length === 0) addVideoRow();
    else existingVideos.forEach(v => addVideoRow(v.url, v.desc));

    if(existingPlans.length === 0) addPlanRow();
    else existingPlans.forEach(p => addPlanRow(p.name, p.price, p.features, p.link, p.highlight));

    async function saveData() {{
        let videosArray = [];
        document.querySelectorAll('#videos-container .row').forEach(div => {{
            const url = div.querySelector('.v-url').value;
            if(url.trim()) videosArray.push({{url: url, desc: div.querySelector('.v-desc').value}});
        }});

        let plansArray = [];
        document.querySelectorAll('#plans-container .row').forEach(div => {{
            const name = div.querySelector('.p-name').value;
            if(name.trim()) {{
                plansArray.push({{
                    name: name,
                    price: div.querySelector('.p-price').value,
                    features: div.querySelector('.p-features').value,
                    link: div.querySelector('.p-link').value,
                    highlight: div.querySelector('.p-highlight').checked
                }});
            }}
        }});

        const data = {{
            hero_title: document.getElementById('hero_title').value,
            hero_subtitle: document.getElementById('hero_subtitle').value,
            hero_text: document.getElementById('hero_text').value,
            videos: videosArray,
            plans: plansArray
        }};
        
        const res = await fetch('/api/save_content', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify(data)
        }});
        const result = await res.json();
        document.getElementById('msg').innerText = result.message;
    }}
    </script>
    </body></html>
    """

@app.post("/api/save_content")
def api_save_content(data: dict):
    if save_content(data):
        return {"message": "✅ Cambios guardados y publicados en la web correctamente."}
    return {"message": "❌ Error al guardar. Revisa las variables de entorno en Render."}

# ==========================================
# 🌐 PÁGINA WEB DE RECUPERACIÓN DE CLAVE
# ==========================================
@app.get("/recuperar-clave", response_class=HTMLResponse)
def recover_page():
    return """
    <html><head><title>Recuperar Licencia - BLENIN77</title>
    <style>body{font-family:sans-serif;background:#0d1b2a;color:white;text-align:center;padding:50px;}
    input{padding:15px;width:300px;border-radius:5px;border:none;margin:10px;font-size:16px;}
    button{padding:15px 30px;background:#00e5ff;color:black;border:none;border-radius:5px;font-weight:bold;cursor:pointer;font-size:16px;}
    #msg{margin-top:20px;font-size:18px;color:#4caf50;font-weight:bold;}
    </style></head>
    <body><h1>🔑 Recuperar Licencia BLENIN77</h1>
    <p>Ingresa el correo electrónico con el que realizaste tu compra:</p>
    <input type="email" id="email" placeholder="tu.correo@gmail.com">
    <br><button onclick="recover()">Enviar mi licencia por correo</button>
    <div id="msg"></div>
    <script>
    function recover(){
        var email = document.getElementById('email').value;
        fetch('/api/recover_by_email', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email: email})
        }).then(r => r.json()).then(d => {
            document.getElementById('msg').innerText = d.message;
        });
    }
    </script>
    </body></html>
    """

# ==========================================
# 🌐 PÁGINA WEB DE VENTAS (Landing Page)
# ==========================================
@app.get("/", response_class=HTMLResponse)
def read_root():
    c = get_content()
    
    # Generar el HTML dinámico para todos los videos
    videos_html = ""
    for v in c.get('videos', []):
        if v.get('url'):
            videos_html += f"""
            <div style="text-align: center; margin-bottom: 50px;">
                <iframe src="{v['url']}" width="560" height="315" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="border-radius: 10px; border: 2px solid var(--cyan); max-width: 100%;"></iframe>
                <p style="margin-top: 15px; font-size: 1.1rem; color: #94a3b8; max-width: 600px; margin-left: auto; margin-right: auto;">{v.get('desc', '')}</p>
            </div>
            """

    # Generar el HTML dinámico para los planes de suscripción
    plans_html = ""
    for p in c.get('plans', []):
        if p.get('name'):
            highlight_style = "border: 2px solid var(--cyan); transform: scale(1.05);" if p.get('highlight') else ""
            features_html = p.get('features', '').replace('\n', '<br>')
            plans_html += f"""
            <div class="card" style="{highlight_style}">
                <h3>{p.get('name', '')}</h3>
                <div style="font-size: 2rem; color: var(--cyan); margin: 15px 0;">{p.get('price', '')}<span style="font-size:1rem; color:#94a3b8;">/mes</span></div>
                <p>{features_html}</p>
                <a href="{p.get('link', '#')}" class="btn-primary" style="margin-top: 20px;">Suscribirme</a>
            </div>
            """

    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BLENIN.G.77 THE BEST FUTURE FOR YOU</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {{ --cyan: #00e5ff; --dark: #0d1b2a; --card: #1b263b; --text: #e0e1dd; }}
        body {{ margin: 0; font-family: 'Segoe UI', sans-serif; background: var(--dark); color: var(--text); scroll-behavior: smooth; }}
        nav {{ background: rgba(13, 27, 42, 0.9); backdrop-filter: blur(10px); padding: 15px 5%; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 100; border-bottom: 1px solid #334155; flex-wrap: wrap; }}
        nav .logo {{ color: var(--cyan); font-size: 1rem; font-weight: bold; text-decoration: none; max-width: 60%; line-height: 1.4; }}
        nav ul {{ list-style: none; display: flex; gap: 20px; }}
        nav ul li a {{ color: var(--text); text-decoration: none; transition: 0.3s; }}
        nav ul li a:hover {{ color: var(--cyan); }}
        
        /* ✅ MEJORA DE IMAGEN: Degradado más claro en la parte superior para iluminar la foto */
        .hero {{ text-align: center; padding: 120px 20px; background: linear-gradient(to bottom, rgba(0, 0, 0, 0.2) 0%, rgba(13, 27, 42, 0.8) 100%), url('https://raw.githubusercontent.com/mymundodigital0-cmyk/blenin77-server/main/bienvenida_blenin.png') center/cover no-repeat; color: white; }}
        .hero h1 {{ font-size: 2.5rem; color: var(--cyan); margin: 0; text-shadow: 0 0 20px rgba(0, 0, 0, 1); }}
        .hero h2 {{ font-size: 1.2rem; color: #fff; margin: 10px 0; text-shadow: 2px 2px 4px rgba(0,0,0,1); font-weight: normal; }}
        .hero p {{ font-size: 1.3rem; max-width: 600px; margin: 20px auto; color: #e0e1dd; text-shadow: 2px 2px 4px rgba(0,0,0,1); }}
        
        .btn-primary {{ background: var(--cyan); color: #000; padding: 15px 30px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; font-size: 1rem; transition: 0.3s; text-decoration: none; display: inline-block; }}
        .btn-primary:hover {{ background: #fff; transform: translateY(-2px); }}
        .section {{ padding: 60px 10%; max-width: 1200px; margin: 0 auto; }}
        .section h2 {{ text-align: center; font-size: 2.5rem; color: #fff; margin-bottom: 40px; }}
        .grid-3 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; }}
        .card {{ background: var(--card); padding: 30px; border-radius: 15px; border: 1px solid #334155; transition: 0.3s; }}
        .card:hover {{ transform: translateY(-5px); border-color: var(--cyan); }}
        .card h3 {{ color: var(--cyan); font-size: 1.5rem; margin-top: 0; }}
        .video-container {{ display: flex; flex-direction: column; align-items: center; gap: 20px; flex-wrap: wrap; }}
        footer {{ background: #000; padding: 40px 20px; text-align: center; margin-top: 0; }}
        .copyright {{ color: #64748b; font-size: 0.9rem; max-width: 800px; margin: 0 auto; }}
    </style>
</head>
<body>
    <nav>
        <a href="#" class="logo">BLENIN.G.77 THE BEST FUTURE FOR YOU ܐܠܗܐ ܪܥܐ ܠܝ ܘܠܐ ܐܟܣܪ ܠܝ ܒܟܠ ܫܘܡܐ</a>
        <ul>
            <li><a href="#features">Funciones</a></li>
            <li><a href="#videos">Videos</a></li>
            <li><a href="#pricing">Precios</a></li>
        </ul>
    </nav>

    <div class="hero">
        <h1>{c.get('hero_title')}</h1>
        <h2>{c.get('hero_subtitle')}</h2>
        <p>{c.get('hero_text')}</p>
    </div>

    <div id="features" class="section">
        <h2>Tecnología de Nivel Institucional</h2>
        <div class="grid-3">
            <div class="card"><h3>🐟 Enjambre 3D</h3><p>Antes de abrir una operación, 500 agentes virtuales simulan el futuro del mercado en milisegundos basándose en el patrón histórico del activo.</p></div>
            <div class="card"><h3>🛡️ Agente Centinela</h3><p>Un guardaespaldas que lee Reuters, CNBC y la Fed en tiempo real. Si detecta un crash, bloquea al bot para proteger tu capital.</p></div>
            <div class="card"><h3>🧠 Cerebro Global</h3><p>Red neuronal descentralizada. Tu bot aprende de las operaciones exitosas y fallidas de todos los usuarios a nivel mundial.</p></div>
        </div>
    </div>

    <div id="videos" class="section">
        <h2>Mira al Sistema en Acción</h2>
        <div class="video-container">
            {videos_html}
        </div>
    </div>

    <div id="pricing" class="section">
        <h2>Planes de Suscripción</h2>
        <div class="grid-3">
            {plans_html}
        </div>
    </div>

    <footer>
        <p class="copyright">&copy; 2026 BLENIN.G.77 THE BEST FUTURE FOR YOU. Todos los derechos reservados. Creado por Lenin Benitez.</p>
    </footer>

    <!-- 🤖 INICIO AGENTE IA DE SOPORTE (Chatbase) -->
    <script>
    (function(){{if(!window.chatbase||window.chatbase("getState")!=="initialized"){{window.chatbase=(...arguments)=>{{if(!window.chatbase.q){{window.chatbase.q=[]}}window.chatbase.q.push(arguments)}};window.chatbase=new Proxy(window.chatbase,{{get(target,prop){{if(prop==="q"){{return target.q}}return(...args)=>target(prop,...args)}}}})}}const onLoad=function(){{const script=document.createElement("script");script.src="https://www.chatbase.co/embed.min.js";script.id="gzEjAzK1VCE72hJ_hBfA4";script.domain="www.chatbase.co";document.body.appendChild(script)}};if(document.readyState==="complete"){{onLoad()}}else{{window.addEventListener("load",onLoad)}}}})();
    </script>
    <!-- 🤖 FIN AGENTE IA DE SOPORTE -->

</body>
</html>
"""

# ==========================================
# 🧠 BASES DE DATOS Y RUTAS API (Licencias, IA, etc.)
# ==========================================
db_trades = []
licenses_db = {
    "BLENIN-TEST-ORO": {"hwid": None, "expires": datetime.now() + timedelta(days=30), "active": True, "plan": "ORO", "email": "test-oro@blenin77.com"}
}
trials_db = {}

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
    db_trades.append(trade)
    return {"status": "received", "total_trades": len(db_trades)}

@app.get("/api/get_global_intel")
def get_intel():
    if not db_trades: return {}
    stats = defaultdict(lambda: {"wins": 0, "total": 0})
    for t in db_trades:
        k = f"{t.strategy}_{t.symbol}_{t.session}"
        stats[k]["total"] += 1
        if t.outcome: stats[k]["wins"] += 1
    return {k: {"win_rate": v["wins"]/v["total"], "trades": v["total"]} for k, v in stats.items() if v["total"] > 0}

@app.post("/api/start_trial")
def start_trial(data: TrialRequest):
    if data.hwid in trials_db:
        if datetime.now() > trials_db[data.hwid]["expires"]:
            return {"valid": False, "message": "⏳ Prueba expirada."}
        return {"valid": True, "days_left": (trials_db[data.hwid]["expires"] - datetime.now()).days, "plan": "BRONCE"}
    trials_db[data.hwid] = {"expires": datetime.now() + timedelta(days=30)}
    return {"valid": True, "days_left": 30, "plan": "BRONCE"}

@app.post("/api/validate_license")
def validate_license(data: LicenseCheck):
    key = data.key.upper().strip()
    if key not in licenses_db: return {"valid": False, "message": "❌ Licencia no encontrada."}
    info = licenses_db[key]
    if not info["active"]: return {"valid": False, "message": "🚫 Licencia suspendada."}
    if datetime.now() > info["expires"]: return {"valid": False, "message": "⏳ Expirada."}
    if info["hwid"] is None: info["hwid"] = data.hwid
    elif info["hwid"] != data.hwid: return {"valid": False, "message": "🔒 En uso en otra PC."}
    return {"valid": True, "days_left": (info["expires"] - datetime.now()).days, "plan": info["plan"]}

@app.post("/api/create_license")
def create_license(data: LicenseCreate):
    key = generate_license_key(data.plan)
    licenses_db[key] = {"hwid": None, "expires": datetime.now() + timedelta(days=data.duration_days), "active": True, "plan": data.plan.upper(), "email": data.email.lower()}
    return {"status": "success", "key": key}

@app.post("/api/recover_by_email")
def recover_by_email(req: RecoveryRequest):
    for key, info in licenses_db.items():
        if info.get("email", "").lower() == req.email.lower() and info["active"]:
            send_email(req.email, "🔑 Tu Licencia BLENIN77", f"Tu clave es: {key}\nPlan: {info['plan']}")
            return {"status": "success", "message": "Enviado al correo."}
    return {"status": "error", "message": "Correo no encontrado."}
