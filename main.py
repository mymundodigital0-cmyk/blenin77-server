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

JSONBIN_DB_ID = os.environ.get("JSONBIN_DB_ID", "")
JSONBIN_DB_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_DB_ID}"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = "mymundodigital0@gmail.com"
SMTP_PASSWORD = "ysdoqcmnevrnnogy" 

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
# 🧠 SISTEMA DE BASE DE DATOS EN LA NUBE
# ==========================================
def load_dbs():
    try:
        headers = {"X-Master-Key": JSONBIN_API_KEY}
        resp = requests.get(JSONBIN_DB_URL, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()["record"]
            return data.get("licenses_db", {}), data.get("trials_db", {}), data.get("stats_db", {"views": 0, "countries": {}})
    except: pass
    return {}, {}, {"views": 0, "countries": {}}

def save_dbs(lic, trials, stats):
    try:
        headers = {"Content-Type": "application/json", "X-Master-Key": JSONBIN_API_KEY}
        data = {"licenses_db": lic, "trials_db": trials, "stats_db": stats}
        requests.put(JSONBIN_DB_URL, json=data, headers=headers, timeout=5)
    except: pass

licenses_db, trials_db, stats_db = load_dbs()

if not licenses_db:
    licenses_db = {
        "BLENIN-TEST-ORO": {"hwid": None, "expires": "2026-09-15T00:00:00", "active": True, "plan": "ORO", "email": "test-oro@blenin77.com"},
        "BLENIN-TEST-PLATA": {"hwid": None, "expires": "2026-09-15T00:00:00", "active": True, "plan": "PLATA", "email": "test-plata@blenin77.com"},
        "BLENIN-TEST-BRONCE": {"hwid": None, "expires": "2026-09-15T00:00:00", "active": True, "plan": "BRONCE", "email": "test-bronce@blenin77.com"}
    }
    save_dbs(licenses_db, trials_db, stats_db)

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
            {"name": "Bronce", "price": "$49", "features": "✅ 1 Cuenta MT5\n✅ Modo MT5 Puro", "link": "https://paypal.me/bronce", "highlight": False},
            {"name": "Plata", "price": "$99", "features": "✅ 2 Cuentas MT5\n✅ Modo Híbrido + Enjambre", "link": "https://paypal.me/plata", "highlight": True},
            {"name": "Oro", "price": "$199", "features": "✅ Cuentas Ilimitadas\n✅ Deep Learning (PyTorch)", "link": "https://paypal.me/oro", "highlight": False}
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
# 🎛️ PANEL DE ADMINISTRACIÓN (TAILWIND UI)
# ==========================================
@app.get("/admin", response_class=HTMLResponse)
def admin_panel():
    c = get_content()
    pubs = c.get('publications', [])
    plans = c.get('plans', [])
    social = c.get('social_links', {})
    
    pubs_json = json.dumps(pubs)
    plans_json = json.dumps(plans)
    
    return f"""
    <html lang="es"><head><meta charset="UTF-8"><title>Admin - BLENIN77</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>body {{ font-family: 'Inter', sans-serif; }} .tab-active {{ background-color: #0e7490; color: white; }}</style>
    </head>
    <body class="bg-slate-900 text-slate-300 flex flex-col min-h-screen">

    <nav class="bg-slate-950 p-4 shadow-lg border-b border-slate-800 flex justify-between items-center">
        <h1 class="text-xl font-bold text-cyan-400">🎛️ Panel BLENIN77</h1>
        <div class="flex gap-2 flex-wrap">
            <button onclick="showTab('stats')" id="tab-stats" class="tab-active px-4 py-2 rounded text-sm font-medium transition">📊 Estadísticas</button>
            <button onclick="showTab('web')" id="tab-web" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">Página Web</button>
            <button onclick="showTab('plans')" id="tab-plans" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">Planes</button>
            <button onclick="showTab('lic')" id="tab-lic" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">Licencias</button>
            <button onclick="showTab('social')" id="tab-social" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">Redes</button>
        </div>
    </nav>

    <div class="flex-1 container mx-auto p-6 md:p-10 max-w-4xl">
        
        <!-- PESTAÑA ESTADÍSTICAS -->
        <div id="content-stats" class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg text-center">
                    <h3 class="text-sm text-slate-400 uppercase tracking-wider mb-2">Visitas Totales</h3>
                    <p id="stat_views" class="text-5xl font-extrabold text-cyan-400">0</p>
                </div>
                <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg text-center">
                    <h3 class="text-sm text-slate-400 uppercase tracking-wider mb-2">Países Alcanzados</h3>
                    <p id="stat_countries_count" class="text-5xl font-extrabold text-emerald-400">0</p>
                </div>
            </div>
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Top Países de Origen</h3>
                <div id="stat_countries" class="space-y-2"></div>
            </div>
        </div>

        <!-- PESTAÑA WEB -->
        <div id="content-web" class="hidden space-y-6">
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Textos Principales (Hero)</h3>
                <label class="text-sm text-slate-400">Título Principal (H1)</label>
                <input type="text" id="hero_title" value="{c.get('hero_title', '')}" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700 focus:border-cyan-500 outline-none">
                <label class="text-sm text-slate-400">Subtítulo (H2)</label>
                <input type="text" id="hero_subtitle" value="{c.get('hero_subtitle', '')}" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700 focus:border-cyan-500 outline-none">
                <label class="text-sm text-slate-400">Texto Descriptivo</label>
                <textarea id="hero_text" rows="3" class="w-full bg-slate-900 rounded p-2 border border-slate-700 focus:border-cyan-500 outline-none">{c.get('hero_text', '')}</textarea>
            </div>

            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Publicaciones (Galería)</h3>
                <div id="pubs-container" class="space-y-4"></div>
                <button onclick="addPubRow()" class="mt-4 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded text-sm font-bold transition"><i class="fas fa-plus mr-2"></i>Agregar Publicación</button>
            </div>
        </div>

        <!-- PESTAÑA PLANES -->
        <div id="content-plans" class="hidden space-y-6">
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Planes de Suscripción (PayPal)</h3>
                <div id="plans-container" class="space-y-6"></div>
                <button onclick="addPlanRow()" class="mt-4 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded text-sm font-bold transition"><i class="fas fa-plus mr-2"></i>Agregar Plan</button>
            </div>
        </div>

        <!-- PESTAÑA LICENCIAS -->
        <div id="content-lic" class="hidden space-y-6">
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Gestión de Licencias</h3>
                <label class="text-sm text-slate-400">Clave de Licencia</label>
                <input type="text" id="lic_key" placeholder="BLENIN-ORO-XXXX-XXXX" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700 focus:border-cyan-500 outline-none">
                <div class="flex gap-2 flex-wrap">
                    <button onclick="manageLic(true)" class="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded text-sm font-bold transition"><i class="fas fa-check mr-2"></i>Activar</button>
                    <button onclick="manageLic(false)" class="bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded text-sm font-bold transition"><i class="fas fa-times mr-2"></i>Suspender</button>
                    <button onclick="resetHwid()" class="bg-amber-600 hover:bg-amber-500 text-white px-4 py-2 rounded text-sm font-bold transition"><i class="fas fa-sync mr-2"></i>Resetear HWID</button>
                </div>
                <div id="lic_msg" class="mt-4 text-cyan-400 font-bold text-sm hidden"></div>
            </div>
        </div>

        <!-- PESTAÑA REDES -->
        <div id="content-social" class="hidden space-y-6">
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Redes Sociales</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div><label class="text-sm text-slate-400">Facebook URL</label><input type="text" id="fb_link" value="{social.get('facebook', '')}" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
                    <div><label class="text-sm text-slate-400">WhatsApp URL</label><input type="text" id="wa_link" value="{social.get('whatsapp', '')}" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
                    <div><label class="text-sm text-slate-400">YouTube URL</label><input type="text" id="yt_link" value="{social.get('youtube', '')}" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
                    <div><label class="text-sm text-slate-400">TikTok URL</label><input type="text" id="tt_link" value="{social.get('tiktok', '')}" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
                    <div><label class="text-sm text-slate-400">Telegram URL</label><input type="text" id="tg_link" value="{social.get('telegram', '')}" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
                    <div><label class="text-sm text-slate-400">Instagram URL</label><input type="text" id="ig_link" value="{social.get('instagram', '')}" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
                </div>
            </div>
        </div>

    </div>

    <footer class="bg-slate-950 p-4 sticky bottom-0 border-t border-slate-800">
        <div class="container mx-auto max-w-4xl flex justify-between items-center">
            <span class="text-xs text-slate-500">© 2024 BLENIN.G.77 Systems</span>
            <button onclick="saveData()" class="bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold px-6 py-2 rounded shadow-lg transition"><i class="fas fa-save mr-2"></i>Guardar y Publicar</button>
        </div>
    </footer>

    <div id="toast" class="fixed bottom-5 right-5 bg-slate-700 text-white px-4 py-3 rounded-lg shadow-2xl opacity-0 transition-opacity duration-300 pointer-events-none">
        <span id="toast-msg"></span>
    </div>

    <script>
    const existingPubs = {pubs_json};
    const existingPlans = {plans_json};
    
    function showTab(tabId) {{
        ['stats', 'web', 'plans', 'lic', 'social'].forEach(id => {{
            document.getElementById('content-' + id).classList.add('hidden');
            document.getElementById('tab-' + id).classList.remove('tab-active');
            document.getElementById('tab-' + id).classList.add('bg-slate-800', 'hover:bg-slate-700');
        }});
        document.getElementById('content-' + tabId).classList.remove('hidden');
        document.getElementById('tab-' + tabId).classList.add('tab-active');
        document.getElementById('tab-' + tabId).classList.remove('bg-slate-800', 'hover:bg-slate-700');
    }}

    function showToast(msg) {{
        const t = document.getElementById('toast');
        document.getElementById('toast-msg').innerText = msg;
        t.classList.remove('opacity-0');
        setTimeout(() => t.classList.add('opacity-0'), 3000);
    }}

    async function loadStats() {{
        try {{
            const res = await fetch('/api/get_stats');
            const data = await res.json();
            document.getElementById('stat_views').innerText = data.views || 0;
            const countries = data.countries || {{}};
            const countryKeys = Object.keys(countries);
            document.getElementById('stat_countries_count').innerText = countryKeys.length;
            
            let html = '';
            countryKeys.sort((a,b) => countries[b] - countries[a]).forEach(c => {{
                html += `<div class="flex justify-between items-center bg-slate-900 p-2 rounded"><span class="text-sm text-slate-300">${{c}}</span><span class="text-cyan-400 font-bold">${{countries[c]}}</span></div>`;
            }});
            document.getElementById('stat_countries').innerHTML = html || '<p class="text-slate-500 text-sm">Aún no hay datos.</p>';
        }} catch (e) {{ console.error(e); }}
    }}
    loadStats();

    function addPubRow(type = 'video', url = '', desc = '') {{
        const c = document.getElementById('pubs-container');
        const div = document.createElement('div');
        div.className = 'bg-slate-900 p-4 rounded border border-slate-700';
        div.innerHTML = `
            <select class="pub-type w-full bg-slate-800 rounded p-2 mb-2 border border-slate-700 outline-none">
                <option value="video" ${{type=='video'?'selected':''}}>Video de YouTube</option>
                <option value="image" ${{type=='image'?'selected':''}}>Imagen</option>
            </select>
            <input type="text" class="pub-url w-full bg-slate-800 rounded p-2 mb-2 border border-slate-700 outline-none" placeholder="URL (Embed YouTube o Imagen)" value="${{url}}">
            <textarea class="pub-desc w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none" placeholder="Descripción">${{desc}}</textarea>
            <button onclick="this.parentElement.remove()" class="mt-2 text-red-500 text-xs hover:text-red-400"><i class="fas fa-trash mr-1"></i>Eliminar</button>
        `;
        c.appendChild(div);
    }}

    function addPlanRow(name = '', price = '', features = '', link = '', highlight = false) {{
        const c = document.getElementById('plans-container');
        const div = document.createElement('div');
        div.className = 'bg-slate-900 p-4 rounded border border-slate-700';
        div.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
                <input type="text" class="p-name bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Nombre Plan (Ej: Oro)" value="${{name}}">
                <input type="text" class="p-price bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Precio (Ej: $199)" value="${{price}}">
            </div>
            <textarea class="p-features w-full bg-slate-800 rounded p-2 my-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Características">${{features}}</textarea>
            <input type="text" class="p-link w-full bg-slate-800 rounded p-2 mb-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Enlace de pago de PayPal" value="${{link}}">
            <div class="flex justify-between items-center mt-2">
                <label class="text-sm flex items-center gap-2 cursor-pointer"><input type="checkbox" class="p-highlight accent-cyan-500" ${{highlight ? 'checked' : ''}}> Resaltar (Más Popular)</label>
                <button onclick="this.parentElement.parentElement.remove()" class="text-red-500 text-xs hover:text-red-400"><i class="fas fa-trash mr-1"></i>Eliminar</button>
            </div>
        `;
        c.appendChild(div);
    }}

    if(existingPubs.length === 0) addPubRow(); else existingPubs.forEach(p => addPubRow(p.type, p.url, p.desc));
    if(existingPlans.length === 0) addPlanRow(); else existingPlans.forEach(p => addPlanRow(p.name, p.price, p.features, p.link, p.highlight));

    async function saveData() {{
        let pubsArray = [];
        document.querySelectorAll('#pubs-container > div').forEach(div => {{
            if(div.querySelector('.pub-url').value.trim()) {{
                pubsArray.push({{ type: div.querySelector('.pub-type').value, url: div.querySelector('.pub-url').value, desc: div.querySelector('.pub-desc').value }});
            }}
        }});

        let plansArray = [];
        document.querySelectorAll('#plans-container > div').forEach(div => {{
            if(div.querySelector('.p-name').value.trim()) {{
                plansArray.push({{ name: div.querySelector('.p-name').value, price: div.querySelector('.p-price').value, features: div.querySelector('.p-features').value, link: div.querySelector('.p-link').value, highlight: div.querySelector('.p-highlight').checked }});
            }}
        }});

        const data = {{
            hero_title: document.getElementById('hero_title').value,
            hero_subtitle: document.getElementById('hero_subtitle').value,
            hero_text: document.getElementById('hero_text').value,
            publications: pubsArray,
            plans: plansArray,
            social_links: {{
                facebook: document.getElementById('fb_link').value,
                whatsapp: document.getElementById('wa_link').value,
                youtube: document.getElementById('yt_link').value,
                tiktok: document.getElementById('tt_link').value,
                telegram: document.getElementById('tg_link').value,
                instagram: document.getElementById('ig_link').value
            }}
        }};
        
        const res = await fetch('/api/save_content', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(data) }});
        const result = await res.json();
        showToast(result.message);
    }}

    async function manageLic(activeStatus) {{
        const key = document.getElementById('lic_key').value;
        const res = await fetch('/api/manage_license', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{key: key, active: activeStatus}}) }});
        const result = await res.json();
        document.getElementById('lic_msg').classList.remove('hidden');
        document.getElementById('lic_msg').innerText = result.message;
        showToast(result.message);
    }}

    async function resetHwid() {{
        const key = document.getElementById('lic_key').value;
        const res = await fetch('/api/reset_hwid', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{key: key}}) }});
        const result = await res.json();
        document.getElementById('lic_msg').classList.remove('hidden');
        document.getElementById('lic_msg').innerText = result.message;
        showToast(result.message);
    }}
    </script>
    </body></html>
    """

@app.post("/api/save_content")
def api_save_content(data: dict):
    if save_content(data):
        return {"message": "✅ Cambios guardados y publicados correctamente."}
    return {"message": "❌ Error al guardar. Revisa variables de entorno."}

# ==========================================
# 🌐 PÁGINA WEB DE RECUPERACIÓN DE CLAVE
# ==========================================
@app.get("/recuperar-clave", response_class=HTMLResponse)
def recover_page():
    return """
    <html lang="es"><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recuperar Licencia - BLENIN77</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet">
    <style>body { font-family: 'Inter', sans-serif; }</style>
    </head>
    <body class="bg-slate-900 text-slate-300 flex items-center justify-center min-h-screen">
        <div class="bg-slate-800 p-8 rounded-xl shadow-2xl border border-slate-700 w-full max-w-md text-center">
            <h1 class="text-2xl font-bold text-cyan-400 mb-2">🔑 Recuperar Licencia</h1>
            <p class="text-slate-400 mb-6 text-sm">Ingresa el correo electrónico con el que realizaste tu compra.</p>
            <input type="email" id="email" placeholder="tu.correo@gmail.com" class="w-full bg-slate-900 rounded p-3 mb-4 border border-slate-700 outline-none focus:border-cyan-500">
            <button onclick="recover()" class="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold py-3 rounded transition">Enviar mi licencia</button>
            <div id="msg" class="mt-4 text-emerald-400 font-bold text-sm hidden"></div>
        </div>
        <script>
        function recover(){
            var email = document.getElementById('email').value;
            fetch('/api/recover_by_email', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email: email})
            }).then(r => r.json()).then(d => {
                const msgDiv = document.getElementById('msg');
                msgDiv.innerText = d.message;
                msgDiv.classList.remove('hidden');
            });
        }
        </script>
    </body></html>
    """

# ==========================================
# 🌐 PÁGINA WEB DE VENTAS (LANDING PAGE)
# ==========================================
@app.get("/", response_class=HTMLResponse)
def read_root():
    c = get_content()
    
    pubs_html = ""
    for p in c.get('publications', []):
        if p.get('url'):
            if p.get('type') == 'video':
                pubs_html += f"""
                <div class="text-center mb-12">
                    <div class="relative aspect-video w-full max-w-2xl mx-auto shadow-2xl rounded-xl overflow-hidden border-2 border-slate-800">
                        <iframe src="{p['url']}" class="absolute top-0 left-0 w-full h-full" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
                    </div>
                    <p class="mt-4 text-slate-400 max-w-xl mx-auto">{p.get('desc', '')}</p>
                </div>
                """
            elif p.get('type') == 'image':
                pubs_html += f"""
                <div class="text-center mb-12">
                    <img src="{p['url']}" alt="Publicación" class="max-w-2xl mx-auto rounded-xl border-2 border-slate-800 shadow-xl">
                    <p class="mt-4 text-slate-400 max-w-xl mx-auto">{p.get('desc', '')}</p>
                </div>
                """

    plans_html = ""
    for p in c.get('plans', []):
        if p.get('name'):
            highlight_classes = "lg:scale-105 border-cyan-500 shadow-cyan-500/20" if p.get('highlight') else "border-slate-800"
            badge = '<span class="absolute top-0 right-0 bg-cyan-500 text-slate-900 text-xs font-bold px-3 py-1 rounded-bl-lg">MÁS POPULAR</span>' if p.get('highlight') else ''
            features_html = p.get('features', '').replace('\n', '<br>')
            plans_html += f"""
            <div class="relative bg-slate-800 p-8 rounded-xl border {highlight_classes} transition-all duration-300 hover:-translate-y-2 hover:shadow-xl">
                {badge}
                <h3 class="text-xl font-bold text-white mb-2">{p.get('name', '')}</h3>
                <div class="text-4xl font-extrabold text-cyan-400 mb-4">{p.get('price', '')}<span class="text-base font-normal text-slate-500">/mes</span></div>
                <p class="text-slate-300 text-sm mb-6">{features_html}</p>
                <a href="{p.get('link', '#')}" class="block text-center w-full bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold py-3 rounded transition">Suscribirme</a>
            </div>
            """

    social = c.get('social_links', {})
    social_html = ""
    if social.get('facebook'): social_html += f'<a href="{social["facebook"]}" target="_blank" class="bg-slate-800 hover:bg-cyan-500 hover:text-slate-900 text-slate-300 p-3 rounded-full transition-all duration-300 transform hover:-translate-y-1"><i class="fab fa-facebook-f"></i></a>'
    if social.get('whatsapp'): social_html += f'<a href="{social["whatsapp"]}" target="_blank" class="bg-slate-800 hover:bg-cyan-500 hover:text-slate-900 text-slate-300 p-3 rounded-full transition-all duration-300 transform hover:-translate-y-1"><i class="fab fa-whatsapp"></i></a>'
    if social.get('youtube'): social_html += f'<a href="{social["youtube"]}" target="_blank" class="bg-slate-800 hover:bg-cyan-500 hover:text-slate-900 text-slate-300 p-3 rounded-full transition-all duration-300 transform hover:-translate-y-1"><i class="fab fa-youtube"></i></a>'
    if social.get('tiktok'): social_html += f'<a href="{social["tiktok"]}" target="_blank" class="bg-slate-800 hover:bg-cyan-500 hover:text-slate-900 text-slate-300 p-3 rounded-full transition-all duration-300 transform hover:-translate-y-1"><i class="fab fa-tiktok"></i></a>'
    if social.get('telegram'): social_html += f'<a href="{social["telegram"]}" target="_blank" class="bg-slate-800 hover:bg-cyan-500 hover:text-slate-900 text-slate-300 p-3 rounded-full transition-all duration-300 transform hover:-translate-y-1"><i class="fab fa-telegram-plane"></i></a>'
    if social.get('instagram'): social_html += f'<a href="{social["instagram"]}" target="_blank" class="bg-slate-800 hover:bg-cyan-500 hover:text-slate-900 text-slate-300 p-3 rounded-full transition-all duration-300 transform hover:-translate-y-1"><i class="fab fa-instagram"></i></a>'

    template = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BLENIN.G.77 - Institutional Trading AI</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #020617; }
        .glow { text-shadow: 0 0 10px rgba(6, 182, 212, 0.5); }
        .hero-bg { background: linear-gradient(to bottom, rgba(2, 6, 23, 0.8) 0%, rgba(2, 6, 23, 0.9) 100%), url('https://raw.githubusercontent.com/mymundodigital0-cmyk/blenin77-server/main/bienvenida_blenin.png') center/cover no-repeat; }
        /* Ocultar la barra superior de Google Translate */
        .goog-te-banner-frame.skiptranslate {display: none !important;} body {top: 0px !important;}
        .goog-te-gadget {font-size: 0 !important;}
        .goog-te-gadget .goog-te-combo {background-color: #1e293b; color: #fff; padding: 5px 10px; border-radius: 5px; border: 1px solid #334155; outline: none; font-size: 12px; margin-top: 5px;}
    </style>
</head>
<body class="text-slate-300">

    <!-- Navbar -->
    <nav class="bg-slate-950/80 backdrop-blur-md sticky top-0 z-50 border-b border-slate-800">
        <div class="container mx-auto px-6 py-4 flex justify-between items-center">
            <a href="#" class="text-xl font-extrabold text-cyan-400 glow">BLENIN.G.77</a>
            <div class="hidden md:flex space-x-6 text-sm font-medium items-center">
                <a href="#features" class="hover:text-cyan-400 transition">Tecnología</a>
                <a href="#videos" class="hover:text-cyan-400 transition">Galería</a>
                <a href="#pricing" class="hover:text-cyan-400 transition">Precios</a>
                <div id="google_translate_element"></div>
            </div>
            <a href="#pricing" class="bg-cyan-500 text-slate-900 px-4 py-2 rounded text-sm font-bold hover:bg-cyan-400 transition">Comprar Ahora</a>
        </div>
    </nav>

    <!-- Hero Section (Con tu imagen de fondo) -->
    <header class="relative overflow-hidden py-24 md:py-32 hero-bg">
        <div class="container mx-auto px-6 text-center relative z-10">
            <div class="inline-block bg-slate-800/50 border border-slate-700 px-4 py-1 rounded-full text-xs font-medium text-cyan-400 mb-6">🚀 SISTEMA INSTITUCIONAL ACTIVO</div>
            <h1 class="text-4xl md:text-6xl font-extrabold text-white mb-4 glow">{HERO_TITLE}</h1>
            <h2 class="text-lg md:text-xl text-slate-400 font-light mb-6 tracking-wider uppercase">{HERO_SUBTITLE}</h2>
            <p class="text-md md:text-lg text-slate-300 max-w-2xl mx-auto mb-10">{HERO_TEXT}</p>
            <div class="flex justify-center gap-4">
                <a href="#pricing" class="bg-cyan-500 text-slate-900 font-bold py-3 px-8 rounded hover:bg-cyan-400 transition transform hover:-translate-y-1 shadow-lg shadow-cyan-500/20">Ver Planes</a>
                <a href="#videos" class="border border-slate-700 text-slate-300 font-bold py-3 px-8 rounded hover:bg-slate-800 transition">Ver Demo</a>
            </div>
        </div>
    </header>

    <!-- Features -->
    <section id="features" class="py-20 container mx-auto px-6">
        <h2 class="text-3xl font-bold text-center text-white mb-12">Tecnología de Nivel Institucional</h2>
        <div class="grid md:grid-cols-3 gap-8">
            <div class="bg-slate-900 p-8 rounded-xl border border-slate-800 hover:border-cyan-500 transition group">
                <div class="text-cyan-400 text-3xl mb-4 group-hover:scale-110 transition"><i class="fas fa-fish"></i></div>
                <h3 class="text-xl font-bold text-white mb-2">Enjambre 3D</h3>
                <p class="text-slate-400 text-sm">500 agentes virtuales simulan el futuro del mercado en milisegundos basándose en el patrón histórico del activo antes de operar.</p>
            </div>
            <div class="bg-slate-900 p-8 rounded-xl border border-slate-800 hover:border-cyan-500 transition group">
                <div class="text-cyan-400 text-3xl mb-4 group-hover:scale-110 transition"><i class="fas fa-shield-alt"></i></div>
                <h3 class="text-xl font-bold text-white mb-2">Agente Centinela</h3>
                <p class="text-slate-400 text-sm">Un guardaespaldas que lee Reuters, CNBC y la Fed en tiempo real. Si detecta un crash, bloquea al bot para proteger tu capital.</p>
            </div>
            <div class="bg-slate-900 p-8 rounded-xl border border-slate-800 hover:border-cyan-500 transition group">
                <div class="text-cyan-400 text-3xl mb-4 group-hover:scale-110 transition"><i class="fas fa-brain"></i></div>
                <h3 class="text-xl font-bold text-white mb-2">Cerebro Global</h3>
                <p class="text-slate-400 text-sm">Red neuronal descentralizada. Tu bot aprende de las operaciones exitosas y fallidas de todos los usuarios a nivel mundial.</p>
            </div>
        </div>
    </section>

    <!-- Videos / Gallery -->
    <section id="videos" class="py-20 bg-slate-950">
        <div class="container mx-auto px-6">
            <h2 class="text-3xl font-bold text-center text-white mb-12">Mira al Sistema en Acción</h2>
            {PUBLICATIONS_HTML}
        </div>
    </section>

    <!-- Pricing -->
    <section id="pricing" class="py-20 container mx-auto px-6">
        <h2 class="text-3xl font-bold text-center text-white mb-4">Planes de Suscripción</h2>
        <p class="text-slate-400 text-center mb-12">Elige el plan que se adapte a tu capital y estilo de trading.</p>
        <div class="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {PLANS_HTML}
        </div>
    </section>

    <!-- INICIO FORMULARIO MAILERLITE -->
    <div class="section py-16 px-6 bg-slate-950">
        <style type="text/css">@import url("https://assets.mlcdn.com/fonts.css?version=1785409");</style>
        <style type="text/css">
            .ml-form-embedSubmitLoad { display: inline-block; width: 20px; height: 20px; }
            .g-recaptcha { transform: scale(1); -webkit-transform: scale(1); transform-origin: 0 0; -webkit-transform-origin: 0 0; height: ; }
            .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); border: 0; }
            .ml-form-embedSubmitLoad:after { content: " "; display: block; width: 11px; height: 11px; margin: 1px; border-radius: 50%; border: 4px solid #fff; border-color: #ffffff #ffffff #ffffff transparent; animation: ml-form-embedSubmitLoad 1.2s linear infinite; }
            @keyframes ml-form-embedSubmitLoad { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            #mlb2-44360624.ml-form-embedContainer { box-sizing: border-box; display: table; margin: 0 auto; position: static; width: 100% !important; }
            #mlb2-44360624.ml-form-embedContainer h4, #mlb2-44360624.ml-form-embedContainer p, #mlb2-44360624.ml-form-embedContainer span, #mlb2-44360624.ml-form-embedContainer button { text-transform: none !important; letter-spacing: normal !important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper { background-color: #1b263b; border-width: 1px; border-color: #334155; border-radius: 8px; border-style: solid; box-sizing: border-box; display: inline-block !important; margin: 0; padding: 0; position: relative; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper.embedPopup, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper.embedDefault { width: 400px; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper.embedForm { max-width: 400px; width: 100%; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-align-left { text-align: left; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-align-center { text-align: center; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-align-default { display: table-cell !important; vertical-align: middle !important; text-align: center !important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-align-right { text-align: right; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedHeader img { border-top-left-radius: 4px; border-top-right-radius: 4px; height: auto; margin: 0 auto !important; max-width: 100%; width: undefinedpx; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-successBody { padding: 20px 20px 0 20px; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody.ml-form-embedBodyHorizontal { padding-bottom: 0; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedContent, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-successBody .ml-form-successContent { text-align: left; margin: 0 0 20px 0; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedContent h4, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-successBody .ml-form-successContent h4 { color: #00e5ff; font-family: 'Inter', sans-serif; font-size: 25px; font-weight: 700; margin: 0 0 10px 0; text-align: center; word-break: break-word; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedContent p, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-successBody .ml-form-successContent p { color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 400; line-height: 20px; margin: 0 0 10px 0; text-align: center; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedContent ul, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedContent ol, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-successBody .ml-form-successContent ul, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-successBody .ml-form-successContent ol { color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 14px; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedContent ol ol, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-successBody .ml-form-successContent ol ol { list-style-type: lower-alpha; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedContent ol ol ol, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-successBody .ml-form-successContent ol ol ol { list-style-type: lower-roman; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedContent p a, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-successBody .ml-form-successContent p a { color: #000000; text-decoration: underline; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-block-form .ml-field-group { text-align: left!important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-block-form .ml-field-group label { margin-bottom: 5px; color: #e2e8f0; font-size: 14px; font-family: 'Inter', sans-serif; font-weight: bold; font-style: normal; text-decoration: none; display: inline-block; line-height: 20px; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedContent p:last-child, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-successBody .ml-form-successContent p:last-child { margin: 0; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody form { margin: 0; width: 100%; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-formContent, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow { margin: 0 0 20px 0; width: 100%; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow { float: left; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-formContent.horozintalForm { margin: 0; padding: 0 0 20px 0; width: 100%; height: auto; float: left; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow { margin: 0 0 10px 0; width: 100%; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow.ml-last-item { margin: 0; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow.ml-formfieldHorizintal { margin: 0; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow input { background-color: #0f172a !important; color: #ffffff !important; border-color: #334155; border-radius: 4px !important; border-style: solid !important; border-width: 1px !important; font-family: 'Inter', sans-serif; font-size: 14px !important; height: auto; line-height: 21px !important; margin-bottom: 0; margin-top: 0; margin-left: 0; margin-right: 0; padding: 10px 10px !important; width: 100% !important; box-sizing: border-box !important; max-width: 100% !important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow input::-webkit-input-placeholder, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow input::-webkit-input-placeholder { color: #64748b; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow input::-moz-placeholder, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow input::-moz-placeholder { color: #64748b; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow input:-ms-input-placeholder, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow input:-ms-input-placeholder { color: #64748b; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow input:-moz-placeholder, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow input:-moz-placeholder { color: #64748b; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow { height: auto; width: 100%; float: left; }
            .ml-form-formContent.horozintalForm .ml-form-horizontalRow .ml-input-horizontal { width: 70%; float: left; }
            .ml-form-formContent.horozintalForm .ml-form-horizontalRow .ml-button-horizontal { width: 30%; float: left; }
            .ml-form-formContent.horozintalForm .ml-form-horizontalRow .ml-button-horizontal.labelsOn { padding-top: 25px; }
            .ml-form-formContent.horozintalForm .ml-form-horizontalRow .horizontal-fields { box-sizing: border-box; float: left; padding-right: 10px; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow button { background-color: #00e5ff !important; border-color: #00e5ff; border-style: solid; border-width: 1px; border-radius: 4px; box-shadow: none; color: #020617 !important; cursor: pointer; font-family: 'Inter', sans-serif; font-size: 14px !important; font-weight: 700; line-height: 20px; margin: 0 !important; padding: 10px !important; width: 100%; height: auto; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow button:hover { background-color: #22d3ee !important; border-color: #22d3ee !important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow input[type="checkbox"] { box-sizing: border-box; padding: 0; position: absolute; z-index: -1; opacity: 0; margin-top: 5px; margin-left: -1.5rem; overflow: visible; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow .label-description { color: #94a3b8; display: block; font-family: 'Inter', sans-serif; font-size: 12px; text-align: left; margin-bottom: 0; position: relative; vertical-align: top; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow label { font-weight: normal; margin: 0; padding: 0; position: relative; display: block; min-height: 24px; padding-left: 24px; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow label a { color: #00e5ff; text-decoration: underline; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow label p { color: #94a3b8 !important; font-family: 'Inter', sans-serif !important; font-size: 12px !important; font-weight: normal !important; line-height: 18px !important; padding: 0 !important; margin: 0 5px 0 0 !important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow label p:last-child { margin: 0; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedSubmit { margin: 0 0 20px 0; float: left; width: 100%; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedSubmit button { background-color: #00e5ff !important; border: none !important; border-radius: 4px !important; box-shadow: none !important; color: #020617 !important; cursor: pointer; font-family: 'Inter', sans-serif !important; font-size: 14px !important; font-weight: 700 !important; line-height: 21px !important; height: auto; padding: 10px !important; width: 100% !important; box-sizing: border-box !important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedSubmit button.loading { display: none; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedSubmit button:hover { background-color: #22d3ee !important; }
            .ml-subscribe-close { width: 30px; height: 30px; background: url('https://assets.mlcdn.com/ml/images/default/modal_close.png') no-repeat; background-size: 30px; cursor: pointer; margin-top: -10px; margin-right: -10px; position: absolute; top: 0; right: 0; }
            .ml-error input, .ml-error textarea, .ml-error select { border-color: red!important; }
            .ml-error .custom-checkbox-radio-list { border: 1px solid red !important; border-radius: 4px; padding: 10px; }
            .ml-error .label-description, .ml-error .label-description p, .ml-error .label-description p a, .ml-error label:first-child { color: #ff0000 !important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow.ml-error .label-description p, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow.ml-error .label-description p:first-letter { color: #ff0000 !important; }
            @media only screen and (max-width: 400px){ .ml-form-embedWrapper.embedDefault, .ml-form-embedWrapper.embedPopup { width: 100%!important; } .ml-form-formContent.horozintalForm { float: left!important; } .ml-form-formContent.horozintalForm .ml-form-horizontalRow { height: auto!important; width: 100%!important; float: left!important; } .ml-form-formContent.horozintalForm .ml-form-horizontalRow .ml-input-horizontal { width: 100%!important; } .ml-form-formContent.horozintalForm .ml-form-horizontalRow .ml-input-horizontal > div { padding-right: 0px!important; padding-bottom: 10px; } .ml-form-formContent.horozintalForm .ml-form-horizontalRow .ml-button-horizontal { width: 100%!important; } .ml-form-formContent.horozintalForm .ml-form-horizontalRow .ml-button-horizontal.labelsOn { padding-top: 0px!important; } }
        </style>
        <div id="mlb2-44360624" class="ml-form-embedContainer ml-subscribe-form ml-subscribe-form-44360624">
            <div class="ml-form-align-center ">
                <div class="ml-form-embedWrapper embedForm">
                    <div class="ml-form-embedBody ml-form-embedBodyDefault row-form">
                        <div class="ml-form-embedContent" style=" ">
                            <h4>"¿Quieres ver al Bot operando en vivo?"</h4>
                            <p>"Deja tu correo y te enviaremos un video de cómo el Enjambre de Agentes abre operaciones reales."</p>
                        </div>
                        <form class="ml-block-form" action="https://assets.mailerlite.com/jsonp/2548287/forms/194532136823292943/subscribe" data-code="" method="post" target="_blank">
                            <div class="ml-form-formContent">
                                <div class="ml-form-fieldRow ml-last-item">
                                    <div class="ml-field-group ml-field-email ml-validate-email ml-validate-required">
                                        <input aria-label="email" aria-required="true" type="email" class="form-control" data-inputmask="" name="fields[email]" placeholder="Email" autocomplete="email">
                                    </div>
                                </div>
                            </div>
                            <input type="hidden" name="ml-submit" value="1">
                            <div class="ml-form-embedSubmit">
                                <button type="submit" class="primary">"Quiero Acceso"</button>
                                <button disabled="disabled" style="display: none;" type="button" class="loading">
                                    <div class="ml-form-embedSubmitLoad"></div>
                                    <span class="sr-only">Loading...</span>
                                </button>
                            </div>
                            <input type="hidden" name="anticsrf" value="true">
                        </form>
                    </div>
                    <div class="ml-form-successBody row-success" style="display: none">
                        <div class="ml-form-successContent">
                            <h4>Thank you!</h4>
                            <p>You have successfully joined our subscriber list.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <script>
            function ml_webform_success_44360624() {
                var $ = ml_jQuery || jQuery;
                $('.ml-subscribe-form-44360624 .row-success').show();
                $('.ml-subscribe-form-44360624 .row-form').hide();
            }
        </script>
        <script src="https://groot.mailerlite.com/js/w/webforms.min.js?v83147fa8ce2d95cb73ece7f28b469519" type="text/javascript"></script>
        <script>
            fetch("https://assets.mailerlite.com/jsonp/2548287/forms/194532136823292943/takel")
        </script>
    </div>
    <!-- FIN FORMULARIO MAILERLITE -->

    <!-- Social Footer -->
    <section class="py-12 border-t border-slate-800">
        <div class="container mx-auto px-6 text-center">
            <h3 class="text-xl font-bold text-white mb-6">Síguenos en nuestras redes</h3>
            <div class="flex justify-center space-x-4 text-xl">
                {SOCIAL_HTML}
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-slate-950 py-10 border-t border-slate-800">
        <div class="container mx-auto px-6 text-center">
            <p class="text-slate-500 text-sm mb-4 max-w-3xl mx-auto">
                <strong>Aviso de Riesgo:</strong> El trading de divisas y CFDs implica un riesgo sustancial y no es adecuado para todos los inversores. El rendimiento pasado no es indicativo de resultados futuros. Operar con apalancamiento puede resultar en la pérdida de su capital.
            </p>
            <p class="text-slate-600 text-xs">&copy; 2024 BLENIN.G.77 THE BEST FUTURE FOR YOU. Creado por Lenin Benitez.</p>
        </div>
    </footer>

    <!-- CHATBASE BOT -->
    <script>
    (function(){if(!window.chatbase||window.chatbase("getState")!=="initialized"){window.chatbase=(...arguments)=>{if(!window.chatbase.q){window.chatbase.q=[]}window.chatbase.q.push(arguments)};window.chatbase=new Proxy(window.chatbase,{get(target,prop){if(prop==="q"){return target.q}return(...args)=>target(prop,...args)}})}}const onLoad=function(){const script=document.createElement("script");script.src="https://www.chatbase.co/embed.min.js";script.id="gzEjAzK1VCE72hJ_hBfA4";script.domain="www.chatbase.co";document.body.appendChild(script)};if(document.readyState==="complete"){onLoad()}else{window.addEventListener("load",onLoad)}})();
    </script>

    <!-- GOOGLE TRANSLATE WIDGET -->
    <script type="text/javascript">
    function googleTranslateElementInit() {
      new google.translate.TranslateElement({pageLanguage: 'es', includedLanguages: 'en,fr,pt,ru,it,de,zh-CN,ko,hi', layout: google.translate.TranslateElement.InlineLayout.SIMPLE, autoDisplay: false}, 'google_translate_element');
    }
    </script>
    <script type="text/javascript" src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>

    <!-- TRACKING SCRIPT -->
    <script>
        fetch('/api/track_view', { method: 'POST' });
    </script>
</body>
</html>"""

    return template.replace("{HERO_TITLE}", c.get('hero_title', ''))\
                   .replace("{HERO_SUBTITLE}", c.get('hero_subtitle', ''))\
                   .replace("{HERO_TEXT}", c.get('hero_text', ''))\
                   .replace("{PUBLICATIONS_HTML}", pubs_html)\
                   .replace("{PLANS_HTML}", plans_html)\
                   .replace("{SOCIAL_HTML}", social_html)

# ==========================================
# 🧠 BASES DE DATOS Y RUTAS API (Licencias, IA, etc.)
# ==========================================
db_trades = []

class TradeData(BaseModel): strategy: str; symbol: str; timeframe: str; outcome: bool; profit_pips: float; session: str
class LicenseCheck(BaseModel): key: str; hwid: str
class LicenseCreate(BaseModel): plan: str; duration_days: int = 30; email: str = ""
class LicenseAction(BaseModel): key: str
class RecoveryRequest(BaseModel): email: str
class TrialRequest(BaseModel): hwid: str
class LicenseUpdate(BaseModel): key: str; active: bool = False
class ResetHWID(BaseModel): key: str

@app.post("/api/track_view")
def track_view(request: Request):
    global stats_db
    try:
        ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "8.8.8.8").split(",")[0]
        # Usamos GeoJS (gratuito, sin límites e indefinido para uso general)
        geo_resp = requests.get(f"https://get.geojs.io/v1/ip/country.json?ip={ip}", timeout=2)
        country = geo_resp.json().get("country", "Unknown") if geo_resp.status_code == 200 else "Unknown"
    except:
        country = "Unknown"
    
    stats_db["views"] = stats_db.get("views", 0) + 1
    stats_db["countries"][country] = stats_db["countries"].get(country, 0) + 1
    
    save_dbs(licenses_db, trials_db, stats_db)
    return {"status": "tracked"}

@app.get("/api/get_stats")
def get_stats():
    return stats_db

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
    global trials_db
    if data.hwid in trials_db:
        expires = datetime.fromisoformat(trials_db[data.hwid]["expires"])
        if datetime.now() > expires:
            return {"valid": False, "message": "⏳ Prueba expirada."}
        return {"valid": True, "days_left": (expires - datetime.now()).days, "plan": "BRONCE"}
    
    trials_db[data.hwid] = {"expires": (datetime.now() + timedelta(days=30)).isoformat()}
    save_dbs(licenses_db, trials_db, stats_db)
    return {"valid": True, "days_left": 30, "plan": "BRONCE"}

@app.post("/api/validate_license")
def validate_license(data: LicenseCheck):
    global licenses_db
    key = data.key.upper().strip()
    if key not in licenses_db: return {"valid": False, "message": "❌ Licencia no encontrada."}
    info = licenses_db[key]
    if not info["active"]: return {"valid": False, "message": "🚫 Licencia suspendida."}
    
    expires = datetime.fromisoformat(info["expires"])
    if datetime.now() > expires: return {"valid": False, "message": "⏳ Expirada."}
    
    if info["hwid"] is None:
        info["hwid"] = data.hwid
        save_dbs(licenses_db, trials_db, stats_db)
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
    save_dbs(licenses_db, trials_db, stats_db)
    return {"status": "success", "key": key}

@app.post("/api/recover_by_email")
def recover_by_email(req: RecoveryRequest):
    for key, info in licenses_db.items():
        if info.get("email", "").lower() == req.email.lower() and info["active"]:
            send_email(req.email, "🔑 Tu Licencia BLENIN77", f"Tu clave es: {key}\nPlan: {info['plan']}")
            return {"status": "success", "message": "Enviado al correo."}
    return {"status": "error", "message": "Correo no encontrado."}

@app.post("/api/manage_license")
def manage_license(data: LicenseUpdate):
    global licenses_db
    key = data.key.upper().strip()
    if key not in licenses_db:
        return {"status": "error", "message": "❌ Licencia no encontrada."}
    
    licenses_db[key]["active"] = data.active
    save_dbs(licenses_db, trials_db, stats_db)
    status = "activada" if data.active else "suspendida"
    return {"status": "success", "message": f"✅ Licencia {key} {status} correctamente."}

@app.post("/api/reset_hwid")
def reset_hwid(data: ResetHWID):
    global licenses_db
    key = data.key.upper().strip()
    if key not in licenses_db:
        return {"status": "error", "message": "❌ Licencia no encontrada."}
    
    licenses_db[key]["hwid"] = None
    save_dbs(licenses_db, trials_db, stats_db)
    return {"status": "success", "message": f"✅ HWID reseteado para {key}."}
