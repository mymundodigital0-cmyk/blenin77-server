from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional
import random, string, smtplib, os, requests, json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 🔐 SISTEMA DE SEGURIDAD Y LOGIN
# ==========================================
SESSION_TOKEN = "blenin_secure_session_2024"

class AdminLoginData(BaseModel):
    password: str

class ChangePasswordData(BaseModel):
    current_password: str
    new_password: str

@app.get("/admin/login", response_class=HTMLResponse)
def admin_login_page():
    return f"""
    <html lang="es"><head><meta charset="UTF-8">
    <title>Login Admin - BLENIN77</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet">
    <style>body {{ font-family: 'Inter', sans-serif; }}</style>
    </head>
    <body class="bg-slate-900 text-slate-300 flex items-center justify-center min-h-screen">
        <div class="bg-slate-800 p-8 rounded-xl shadow-2xl border border-slate-700 w-full max-w-sm text-center">
            <h1 class="text-2xl font-bold text-cyan-400 mb-2">🔒 Acceso Restringido</h1>
            <p class="text-slate-400 mb-6 text-sm">Panel de Control BLENIN77</p>
            <p id="err_msg" class="text-red-400 text-sm mb-4 hidden">Contraseña incorrecta.</p>
            <input type="password" id="pwd" placeholder="Contraseña de Administrador" class="w-full bg-slate-900 rounded p-3 mb-4 border border-slate-700 outline-none focus:border-cyan-500">
            <button onclick="doLogin()" class="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold py-3 rounded transition">Ingresar</button>
        </div>
        <script>
            async function doLogin() {{
                const pwd = document.getElementById('pwd').value;
                const res = await fetch('/api/login', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ password: pwd }})
                }});
                if(res.ok) {{
                    window.location.href = '/admin';
                }} else {{
                    document.getElementById('err_msg').classList.remove('hidden');
                }}
            }}
        </script>
    </body></html>
    """

@app.post("/api/login")
def admin_login_verify(data: AdminLoginData, response: Response):
    global admin_password_db
    if data.password == admin_password_db:
        response.set_cookie(key="blenin_session", value=SESSION_TOKEN, httponly=True, secure=True, samesite="lax", max_age=86400)
        return {"status": "success"}
    raise HTTPException(status_code=401, detail="Contraseña incorrecta")

@app.get("/admin/logout")
def admin_logout(response: Response):
    response.delete_cookie(key="blenin_session")
    return RedirectResponse(url="/admin/login", status_code=303)

def verify_admin(request: Request):
    if request.cookies.get("blenin_session") != SESSION_TOKEN:
        return False
    return True

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
SMTP_PASSWORD = "dpfgpzdccpmhllim"

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
        print(f"✅ Correo enviado a {to_email}")
        return True
    except Exception as e:
        print(f"❌ ERROR ENVIANDO A {to_email}: {e}")
        return False

# ==========================================
# 🧠 SISTEMA DE BASE DE DATOS MULTI-PÁGINA
# ==========================================
def get_default_ai_config():
    return {
        "stage1_days": 2,
        "stage1_subject": "🚀 {name}, descubre el poder de la IA Institucional con BLENIN.G.77",
        "stage1_body": "Hola {name},\n\nGracias por tu interés en BLENIN.G.77, el sistema de trading de nivel institucional impulsado por Inteligencia Artificial.\n\nUn saludo institucional,\nEquipo de BLENIN.G.77.",
        "stage2_days": 5,
        "stage2_subject": "🔥 {name}, esto es lo que estás dejando atrás...",
        "stage2_body": "Hola {name},\n\nNo dejes tu capital expuesto a la emoción humana.\n\n👉 https://blenin77-server.onrender.com/#pricing",
        "stage3_days": 10,
        "stage3_subject": "⏳ {name}, tu acceso VIP a BLENIN.G.77 está por expirar",
        "stage3_body": "Hemos habilitado un descuento especial del 10%.\n\nUsa el código: BLENIN10"
    }

def get_default_update_config():
    return {"latest_version": "1.0.0", "download_url": "https://blenin77-server.onrender.com/", "force_update": False, "update_message": "Hay una nueva versión disponible."}

def load_dbs():
    try:
        headers = {"X-Master-Key": JSONBIN_API_KEY}
        resp = requests.get(JSONBIN_DB_URL, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()["record"]
            pwd = data.get("admin_password", os.environ.get("ADMIN_PASSWORD", "cambiar_esta_clave_123"))
            ai_cfg = data.get("ai_agent_config", get_default_ai_config())
            upd_cfg = data.get("bot_update_config", get_default_update_config())
            return data.get("licenses_db", {}), data.get("trials_db", {}), data.get("stats_db", {"views": 0, "countries": {}}), pwd, ai_cfg, upd_cfg
    except: pass
    return {}, {}, {"views": 0, "countries": {}}, os.environ.get("ADMIN_PASSWORD", "cambiar_esta_clave_123"), get_default_ai_config(), get_default_update_config()

def save_dbs(lic, trials, stats, pwd=None, ai_cfg=None, upd_cfg=None):
    try:
        headers = {"Content-Type": "application/json", "X-Master-Key": JSONBIN_API_KEY}
        data = {"licenses_db": lic, "trials_db": trials, "stats_db": stats}
        if pwd: data["admin_password"] = pwd
        if ai_cfg: data["ai_agent_config"] = ai_cfg
        if upd_cfg: data["bot_update_config"] = upd_cfg
        requests.put(JSONBIN_DB_URL, json=data, headers=headers, timeout=5)
    except: pass

licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config = load_dbs()

if not ai_agent_config or "BLENIN.G.77" not in ai_agent_config.get("stage1_subject", ""):
    ai_agent_config = get_default_ai_config()
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)

if not licenses_db:
    licenses_db = {"BLENIN-TEST-ORO": {"hwid": None, "expires": "2026-09-15T00:00:00", "active": True, "plan": "ORO", "email": "test@blenin77.com"}}
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)

def get_default_content(page_name="Principal"):
    return {
        "page_name": page_name, "chatbot_id": "gzEjAzK1VCE72hJ_hBfA4",
        "hero_title": "BLENIN.G.77", "hero_subtitle": "THE BEST FUTURE FOR YOU",
        "hero_text": "IA Predictiva, Enjambre de 500 Agentes y Análisis Global en Tiempo Real.",
        "affiliate_link": "https://go.hotmart.com/W107659112D",
        "affiliate_text": "🚀 Afíliate (75%)",
        "publications": [{"type": "video", "url": "https://www.youtube.com/embed/dQw4w9WgXcQ", "desc": "Mira cómo el Enjambre de Agentes abre operaciones."}],
        "plans": [
            {"name": "Bronce", "price": "$49", "features": "✅ 1 Cuenta MT5\n✅ Modo MT5 Puro", "link": "P-78W24779DJ167620XNKNUHYY", "highlight": False},
            {"name": "Plata", "price": "$99", "features": "✅ 2 Cuentas MT5\n✅ Modo Híbrido + Enjambre", "link": "P-5XY16476VG217634ANKNUHZA", "highlight": True},
            {"name": "Oro", "price": "$199", "features": "✅ Cuentas Ilimitadas\n✅ Deep Learning", "link": "P-4LL21192X9335681FNKNUHZA", "highlight": False}
        ],
        "social_links": {"facebook": "", "whatsapp": "", "youtube": "", "tiktok": "", "telegram": "", "instagram": ""},
        "bank_transfer_info": {"bank_name": "Banco Ejemplo", "account_type": "Cuenta Corriente", "account_number": "01234567890123456789", "beneficiary": "Lenin Benitez", "email_for_proof": "pagos@blenin77.com", "whatsapp_for_proof": "593999999999"},
        "download_links": ["https://mega.nz/file/09AmGTwI#-u8CeWSK0WySVN4oeJINNIaKQbP-lDKTOeEASr3jA54"],
        "download_instructions": "1. Descarga el archivo .zip\n2. Extrae el contenido\n3. Ejecuta Blenin77.exe\n4. Ingresa tu licencia."
    }

def get_all_pages():
    try:
        headers = {"X-Master-Key": JSONBIN_API_KEY}
        resp = requests.get(JSONBIN_URL, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()["record"]
            if "hero_title" in data and "pages" not in data:
                save_all_pages({"pages": {"main": data}})
                return {"pages": {"main": data}}
            return data
    except: pass
    default_data = {"pages": {"main": get_default_content()}}
    save_all_pages(default_data)
    return default_data

def save_all_pages(data):
    try:
        headers = {"Content-Type": "application/json", "X-Master-Key": JSONBIN_API_KEY}
        requests.put(JSONBIN_URL, json=data, headers=headers, timeout=5)
        return True
    except: return False

# ==========================================
# 🧠 INTELIGENCIA ARTIFICIAL LOCAL (LLAMA 3)
# ==========================================
def generate_dynamic_content_with_llama(prompt, max_tokens=500):
    try:
        payload = {"model": "llama3", "prompt": prompt, "stream": False, "options": {"temperature": 0.7, "num_predict": max_tokens}}
        response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=60)
        if response.status_code == 200: return response.json().get("response", "")
    except: pass
    return None

@app.get("/blog", response_class=HTMLResponse)
def blog_index():
    return HTMLResponse("""
    <html><head><title>Blog - BLENIN77</title><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet"><style>body { font-family: 'Inter', sans-serif; background-color: #020617; }</style></head>
    <body class="text-slate-300 p-10"><div class="max-w-3xl mx-auto"><h1 class="text-3xl font-bold text-cyan-400 mb-6">📈 Blog de Trading Inteligente</h1><ul class="mt-6 space-y-4">
    <li class="bg-slate-800 p-4 rounded"><a href="/blog/como-invertir-con-ia-forex" class="text-xl hover:text-cyan-400">¿Cómo invertir en Forex usando IA?</a></li>
    <li class="bg-slate-800 p-4 rounded"><a href="/blog/mejores-estrategias-automaticas-mt5" class="text-xl hover:text-cyan-400">Top 5 Estrategias para MT5</a></li>
    </ul><a href="/" class="text-cyan-400 mt-6 inline-block">← Volver al Inicio</a></div></body></html>
    """)

@app.get("/blog/{slug}", response_class=HTMLResponse)
def blog_article(slug: str):
    title = slug.replace('-', ' ').title()
    prompt = f"Eres un experto en trading y SEO. Escribe un artículo persuasivo de 400 palabras sobre: '{title}'. Menciona cómo el bot BLENIN77 con IA ayuda. Usa HTML (<h2>, <p>, <strong>)."
    article_html = generate_dynamic_content_with_llama(prompt, max_tokens=800) or f"<p>Contenido en construcción para {title}.</p>"
    return HTMLResponse(f"""
    <html><head><title>{title} - BLENIN77</title><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet"><style>body {{ font-family: 'Inter', sans-serif; background-color: #020617; }}</style></head>
    <body class="text-slate-300 p-10"><div class="max-w-3xl mx-auto prose prose-invert"><a href="/blog" class="text-cyan-400 mb-4 inline-block">← Volver al Blog</a>{article_html}
    <div class="mt-8 p-6 bg-slate-800 rounded-xl border border-cyan-500 text-center"><h3 class="text-xl font-bold text-white mb-2">¿Listo para automatizar?</h3><a href="/#pricing" class="bg-cyan-500 text-slate-900 font-bold py-2 px-6 rounded hover:bg-cyan-400">Ver Planes</a></div></div></body></html>
    """)

# ==========================================
# 🔄 SISTEMA DE ACTUALIZACIONES DEL BOT
# ==========================================
@app.get("/api/get_latest_version")
def get_latest_version(): return bot_update_config

class UpdateConfigData(BaseModel):
    latest_version: str
    download_url: str
    force_update: bool
    update_message: str

@app.post("/api/save_update_config")
def save_update_config_api(request: Request, data: UpdateConfigData):
    global bot_update_config
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    bot_update_config = data.dict()
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
    return {"status": "success", "message": "✅ Guardado."}

# ==========================================
# 🎛️ PANEL DE ADMINISTRACIÓN (CMS)
# ==========================================
@app.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request):
    if not verify_admin(request): return RedirectResponse(url="/admin/login", status_code=303)
    pages_data = get_all_pages()
    pages_dict = pages_data.get("pages", {})
    pages_json = json.dumps(pages_dict)
    return f"""
    <html lang="es"><head><meta charset="UTF-8"><title>Admin - BLENIN77</title><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet"><style>body {{ font-family: 'Inter', sans-serif; }} .tab-active {{ background-color: #0e7490; color: white; }}</style></head>
    <body class="bg-slate-900 text-slate-300 flex flex-col min-h-screen">
    <nav class="bg-slate-950 p-4 border-b border-slate-800 flex justify-between items-center"><h1 class="text-xl font-bold text-cyan-400">🎛️ Panel BLENIN77</h1>
    <div class="flex gap-2 flex-wrap items-center">
        <button onclick="showTab('pages')" id="tab-pages" class="tab-active px-4 py-2 rounded text-sm">🚀 Páginas</button>
        <button onclick="showTab('stats')" id="tab-stats" class="bg-slate-800 px-4 py-2 rounded text-sm">📊 Estadísticas</button>
        <button onclick="showTab('ai')" id="tab-ai" class="bg-slate-800 px-4 py-2 rounded text-sm">🤖 Agente IA</button>
        <button onclick="showTab('lic')" id="tab-lic" class="bg-slate-800 px-4 py-2 rounded text-sm">Licencias</button>
        <a href="/admin/logout" class="bg-red-600 text-white px-4 py-2 rounded text-sm font-bold ml-2">Salir</a>
    </div></nav>
    <div class="flex-1 container mx-auto p-6 md:p-10 max-w-4xl">
        <div id="content-pages" class="space-y-6 hidden">
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700">
                <h3 class="text-lg font-bold text-white mb-4">Gestor de Landing Pages</h3>
                <select id="page_selector" onchange="loadPageData()" class="w-full bg-slate-900 rounded p-2 border border-slate-700 mb-4"></select>
                <input type="hidden" id="current_slug">
                <label class="text-sm text-slate-400">Título Principal (H1)</label><input type="text" id="hero_title" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700">
                <label class="text-sm text-slate-400">Subtítulo</label><input type="text" id="hero_subtitle" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700">
                <label class="text-sm text-slate-400">Texto Descriptivo</label><textarea id="hero_text" rows="3" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700"></textarea>
                <label class="text-sm text-slate-400">Enlace del Botón Afiliados (Hotmart)</label><input type="text" id="aff_link" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700">
                <label class="text-sm text-slate-400">Texto del Botón Afiliados</label><input type="text" id="aff_text" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700">
            </div>
        </div>
        <div id="content-stats" class="hidden">
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 text-center"><h3 class="text-sm text-slate-400 mb-2">Visitas Totales</h3><p id="stat_views" class="text-5xl font-extrabold text-cyan-400">0</p></div>
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 mt-4"><h3 class="text-lg font-bold text-white mb-4">📧 Leads</h3><div id="stat_leads" class="space-y-2 max-h-96 overflow-y-auto"></div></div>
        </div>
        <div id="content-ai" class="hidden">
            <div class="bg-slate-800 p-6 rounded-xl border border-cyan-700">
                <h3 class="text-lg font-bold text-white mb-4">🤖 Agente IA Seguimiento 1</h3>
                <label>Días</label><input type="number" id="s1_days" class="bg-slate-900 rounded p-2 w-full mb-2 border border-slate-700">
                <label>Asunto</label><input type="text" id="s1_subject" class="bg-slate-900 rounded p-2 w-full mb-2 border border-slate-700">
                <label>Cuerpo</label><textarea id="s1_body" rows="4" class="bg-slate-900 rounded p-2 w-full mb-4 border border-slate-700"></textarea>
                <button onclick="saveAIConfig()" class="w-full bg-cyan-500 text-slate-900 font-bold py-3 rounded">Guardar</button>
            </div>
        </div>
        <div id="content-lic" class="hidden">
            <div class="bg-slate-800 p-6 rounded-xl border border-emerald-700">
                <h3 class="text-lg font-bold text-white mb-4">➕ Crear Licencia Manual</h3>
                <input type="text" id="manual_plan" placeholder="Plan" class="w-full bg-slate-900 rounded p-2 mb-2 border border-slate-700">
                <input type="email" id="manual_email" placeholder="Email" class="w-full bg-slate-900 rounded p-2 mb-2 border border-slate-700">
                <button onclick="createManualLicense()" class="w-full bg-emerald-600 text-white font-bold py-3 rounded">Generar</button>
            </div>
        </div>
    </div>
    <footer class="bg-slate-950 p-4 sticky bottom-0 border-t border-slate-800"><div class="container mx-auto max-w-4xl flex justify-between items-center"><span class="text-xs text-slate-500">© BLENIN77</span><button onclick="saveData()" class="bg-cyan-500 text-slate-900 font-bold px-6 py-2 rounded">Guardar y Publicar</button></div></footer>
    <script>
    const allPages = {pages_json};
    function showTab(tabId) {{
        ['pages', 'stats', 'ai', 'lic'].forEach(id => {{
            document.getElementById('content-' + id).classList.add('hidden');
            document.getElementById('tab-' + id).classList.remove('tab-active');
        }});
        document.getElementById('content-' + tabId).classList.remove('hidden');
        document.getElementById('tab-' + tabId).classList.add('tab-active');
        if(tabId === 'stats') loadStats();
        if(tabId === 'ai') loadAIConfig();
    }}
    function updateSelector() {{
        const selector = document.getElementById('page_selector');
        selector.innerHTML = '';
        Object.keys(allPages).forEach(slug => {{ let opt = document.createElement('option'); opt.value = slug; opt.innerText = allPages[slug].page_name || slug; selector.appendChild(opt); }});
    }}
    function loadPageData() {{
        const slug = document.getElementById('page_selector').value;
        const p = allPages[slug];
        document.getElementById('current_slug').value = slug;
        document.getElementById('hero_title').value = p.hero_title || '';
        document.getElementById('hero_subtitle').value = p.hero_subtitle || '';
        document.getElementById('hero_text').value = p.hero_text || '';
        document.getElementById('aff_link').value = p.affiliate_link || '';
        document.getElementById('aff_text').value = p.affiliate_text || '';
    }}
    async function saveData() {{
        const slug = document.getElementById('current_slug').value || document.getElementById('page_selector').value;
        allPages[slug] = {{ page_name: document.getElementById('page_selector').selectedOptions[0].text, hero_title: document.getElementById('hero_title').value, hero_subtitle: document.getElementById('hero_subtitle').value, hero_text: document.getElementById('hero_text').value, affiliate_link: document.getElementById('aff_link').value, affiliate_text: document.getElementById('aff_text').value }};
        const res = await fetch('/api/save_pages', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(allPages) }});
        const result = await res.json(); alert(result.message);
    }}
    async function loadStats() {{
        const res = await fetch('/api/get_stats'); const data = await res.json();
        document.getElementById('stat_views').innerText = data.views || 0;
        const leads = data.captured_leads || []; let html = '';
        leads.slice().reverse().forEach(l => {{ html += `<div class="bg-slate-900 p-3 rounded"><span class="text-cyan-400 font-bold text-sm">${{l.name}} - ${{l.email}}</span></div>`; }});
        document.getElementById('stat_leads').innerHTML = html;
    }}
    async function loadAIConfig() {{ const res = await fetch('/api/get_ai_config'); const data = await res.json(); document.getElementById('s1_days').value = data.stage1_days || 2; document.getElementById('s1_subject').value = data.stage1_subject || ''; document.getElementById('s1_body').value = data.stage1_body || ''; }}
    async function saveAIConfig() {{ const payload = {{ stage1_days: parseInt(document.getElementById('s1_days').value), stage1_subject: document.getElementById('s1_subject').value, stage1_body: document.getElementById('s1_body').value }}; const res = await fetch('/api/save_ai_config', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(payload) }}); alert('Guardado'); }}
    async function createManualLicense() {{ const payload = {{ plan: document.getElementById('manual_plan').value, email: document.getElementById('manual_email').value, duration_days: 30 }}; const res = await fetch('/api/create_license', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(payload) }}); const result = await res.json(); alert(result.key || result.message); }}
    updateSelector(); loadPageData();
    </script></body></html>
    """

@app.post("/api/save_pages")
def api_save_pages(request: Request, data: dict):
    if not verify_admin(request): return {"message": "❌ No autorizado."}
    if save_all_pages({"pages": data}): return {"message": "✅ Página guardada."}
    return {"message": "❌ Error al guardar."}

@app.post("/api/change_password")
def api_change_password(request: Request, data: ChangePasswordData):
    global admin_password_db
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    if data.current_password != admin_password_db: return {"status": "error", "message": "❌ Contraseña incorrecta."}
    admin_password_db = data.new_password
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
    return {"status": "success", "message": "✅ Contraseña actualizada."}

@app.get("/recuperar-clave", response_class=HTMLResponse)
def recover_page():
    return """<html><head><title>Recuperar Licencia</title><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-slate-900 text-slate-300 flex items-center justify-center min-h-screen"><div class="bg-slate-800 p-8 rounded-xl border border-slate-700 w-full max-w-md text-center"><h1 class="text-2xl font-bold text-cyan-400 mb-2">🔑 Recuperar Licencia</h1><input type="email" id="email" placeholder="tu.correo@gmail.com" class="w-full bg-slate-900 rounded p-3 mb-4 border border-slate-700"><button onclick="recover()" class="w-full bg-cyan-500 text-slate-900 font-bold py-3 rounded">Enviar</button><div id="msg" class="mt-4 text-emerald-400 font-bold text-sm hidden"></div></div><script>function recover(){var email = document.getElementById('email').value;fetch('/api/recover_by_email', {method: 'POST',headers: {'Content-Type': 'application/json'},body: JSON.stringify({email: email})}).then(r => r.json()).then(d => {const msgDiv = document.getElementById('msg');msgDiv.innerText = d.message;msgDiv.classList.remove('hidden');});}</script></body></html>"""

def render_landing_page(c):
    pubs_html = ""
    for p in c.get('publications', []):
        if p.get('url'):
            if p.get('type') == 'video': pubs_html += f"""<div class="text-center mb-12"><div class="relative aspect-video w-full max-w-2xl mx-auto shadow-2xl rounded-xl overflow-hidden border-2 border-slate-800"><iframe src="{p['url']}" class="absolute top-0 left-0 w-full h-full" frameborder="0" allowfullscreen></iframe></div><p class="mt-4 text-slate-400 max-w-xl mx-auto">{p.get('desc', '')}</p></div>"""

    plans_html = ""
    for p in c.get('plans', []):
        if p.get('name'):
            highlight_classes = "lg:scale-105 border-cyan-500" if p.get('highlight') else "border-slate-800"
            features_html = p.get('features', '').replace('\n', '<br>')
            plans_html += f"""<div class="bg-slate-800 p-8 rounded-xl border {highlight_classes} flex flex-col"><h3 class="text-xl font-bold text-white mb-2">{p.get('name', '')}</h3><div class="text-4xl font-extrabold text-cyan-400 mb-4">{p.get('price', '')}</div><p class="text-slate-300 text-sm mb-6 flex-grow">{features_html}</p><a href="{p.get('link', '#')}" class="block text-center w-full bg-cyan-500 text-slate-900 font-bold py-3 rounded">Suscribirme</a></div>"""

    download_buttons_html = ""
    for link in c.get('download_links', []): download_buttons_html += f"""<a href="{link}" target="_blank" class="bg-cyan-500 text-slate-900 font-bold py-3 px-8 rounded inline-block w-full mb-2">Descargar</a>"""

    aff_link = c.get('affiliate_link', '')
    aff_text = c.get('affiliate_text', '🚀 Afíliate')
    aff_btn = f'<a href="{aff_link}" target="_blank" class="bg-emerald-500 hover:bg-emerald-400 text-slate-900 px-4 py-2 rounded text-sm font-bold transition">{aff_text}</a>' if aff_link else ''

    template = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{c.get('hero_title', 'BLENIN77')}</title>
    <script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet"><style>body {{ font-family: 'Inter', sans-serif; background-color: #020617; }}</style></head>
<body class="text-slate-300">
    <nav class="bg-slate-950 sticky top-0 z-50 border-b border-slate-800 p-4"><div class="container mx-auto flex justify-between items-center"><a href="/" class="text-xl font-extrabold text-cyan-400">{c.get('hero_title', '')}</a><div class="flex gap-2 items-center">{aff_btn}<a href="#pricing" class="bg-cyan-500 text-slate-900 px-4 py-2 rounded font-bold">Comprar</a></div></div></nav>
    <header class="py-24 text-center px-6"><h1 class="text-4xl font-extrabold text-white mb-4">{c.get('hero_title', '')}</h1><h2 class="text-xl text-slate-400 mb-6">{c.get('hero_subtitle', '')}</h2><p class="text-md text-slate-300 max-w-2xl mx-auto mb-10">{c.get('hero_text', '')}</p><a href="#pricing" class="bg-cyan-500 text-slate-900 font-bold py-3 px-8 rounded">Ver Planes</a></header>
    <section id="videos" class="py-20 bg-slate-950"><div class="container mx-auto px-6"><h2 class="text-3xl font-bold text-center text-white mb-12">Demostraciones</h2>{pubs_html}</div></section>
    <section id="pricing" class="py-20 container mx-auto px-6"><h2 class="text-3xl font-bold text-center text-white mb-12">Planes</h2><div class="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">{plans_html}</div></section>
    <div class="py-16 px-6 bg-slate-950"><div class="max-w-md mx-auto bg-slate-800 p-8 rounded-xl border border-slate-700 shadow-lg text-center" id="ml-form-wrapper"><h3 class="text-2xl font-bold text-white mb-2">¿Quieres ver al Bot en vivo?</h3><p class="text-slate-400 text-sm mb-6">Deja tu correo.</p><form onsubmit="return ml_reveal_download()"><input type="email" placeholder="Tu correo" class="w-full bg-slate-900 rounded p-3 mb-4 border border-slate-700 text-white"><button type="submit" class="w-full bg-cyan-500 text-slate-900 font-bold py-3 rounded">Quiero Acceso</button></form></div><div id="download-box" class="max-w-md mx-auto bg-slate-800 p-8 rounded-xl border border-cyan-500 text-center mt-6" style="display: none;"><i class="fas fa-check-circle text-emerald-400 text-4xl mb-4"></i><h4 class="text-xl font-bold text-cyan-400 mb-4">¡Listo! Aquí tienes tu descarga:</h4><div class="text-slate-300 text-sm mb-6 text-left bg-slate-900 p-4 rounded-lg">{c.get('download_instructions', '').replace('\n', '<br>')}</div><div class="flex flex-col gap-3">{download_buttons_html}</div></div><script>function ml_reveal_download() {{setTimeout(function() {{document.getElementById('download-box').style.display = 'block';document.getElementById('ml-form-wrapper').style.display = 'none';}}, 1000);return true;}}</script></div>
    <footer class="bg-slate-950 py-10 border-t border-slate-800 text-center px-6"><p class="text-slate-500 text-sm mb-4">Aviso de Riesgo: El trading implica riesgo.</p><p class="text-slate-600 text-xs">© 2024 BLENIN.G.77. Creado por Lenin Benitez.</p></footer>
    <script>fetch('/api/track_view', {{ method: 'POST' }});</script>
</body></html>"""
    return template

@app.get("/google80facc731870c13b.html", response_class=PlainTextResponse)
def google_verification(): return "google-site-verification: google80facc731870c13b.html"

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    pages_data = get_all_pages()
    c = pages_data.get("pages", {}).get("main", get_default_content())
    user_country_name = "Internacional"
    try:
        ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "8.8.8.8").split(",")[0]
        geo_resp = requests.get(f"https://get.geojs.io/v1/ip/country.json?ip={ip}", timeout=2)
        if geo_resp.status_code == 200: user_country_name = geo_resp.json().get("country_name", "Internacional")
    except: pass
    latam_countries = ["Ecuador", "Mexico", "Colombia", "Peru", "Argentina", "Chile", "Venezuela", "Dominican Republic"]
    if user_country_name in latam_countries: c['hero_text'] = f"🔥 ¡Descuento especial para {user_country_name}! " + c.get('hero_text', '')
    elif user_country_name != "Internacional": c['hero_text'] = f"🚀 Usuarios de {user_country_name} ya están operando. " + c.get('hero_text', '')
    return render_landing_page(c)

@app.get("/p/{slug}", response_class=HTMLResponse)
def read_dynamic_page(slug: str):
    pages_data = get_all_pages()
    c = pages_data.get("pages", {}).get(slug)
    if c: return render_landing_page(c)
    return HTMLResponse("<h1>404 - Página no encontrada</h1><a href='/'>Volver al inicio</a>")

# ==========================================
# 🧠 BASES DE DATOS Y RUTAS API
# ==========================================
db_trades = []

class TradeData(BaseModel): strategy: str; symbol: str; timeframe: str; outcome: bool; profit_pips: float; session: str
class LicenseCheck(BaseModel): key: str; hwid: str
class LicenseCreate(BaseModel): plan: str; duration_days: int = 30; email: str = ""
class RecoveryRequest(BaseModel): email: str
class TrialRequest(BaseModel): hwid: str
class LicenseUpdate(BaseModel): key: str; active: bool = False
class ResetHWID(BaseModel): key: str
class LeadCapture(BaseModel): name: str = "Usuario"; email: str; interaction: str = "Visualizó demo"

class UserRiskReport(BaseModel):
    license_key: str
    consecutive_losses: int
    current_drawdown_pct: float

@app.post("/api/track_view")
def track_view(request: Request):
    global stats_db
    try:
        ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "8.8.8.8").split(",")[0]
        geo_resp = requests.get(f"https://get.geojs.io/v1/ip/country.json?ip={ip}", timeout=2)
        country = geo_resp.json().get("country", "Unknown") if geo_resp.status_code == 200 else "Unknown"
    except: country = "Unknown"
    stats_db["views"] = stats_db.get("views", 0) + 1
    stats_db["countries"][country] = stats_db["countries"].get(country, 0) + 1
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
    return {"status": "tracked"}

@app.get("/api/get_stats")
def get_stats(): return stats_db

@app.get("/api/get_ai_config")
def get_ai_config(): return ai_agent_config if ai_agent_config else get_default_ai_config()

@app.post("/api/save_ai_config")
def save_ai_config(request: Request, data: dict):
    global ai_agent_config
    if not verify_admin(request): return {"status": "error", "message": "❌ No autorizado."}
    ai_agent_config = data
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
    return {"status": "success", "message": "✅ Guardado."}

def generate_license_key(plan):
    p1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    p2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"BLENIN-{plan.upper()}-{p1}-{p2}"

@app.post("/api/sync_intel")
def receive_intel(trade: TradeData):
    db_trades.append(trade)
    return {"status": "received"}

@app.get("/api/get_global_intel")
def get_intel():
    if not db_trades: return {}
    stats = defaultdict(lambda: {"wins": 0, "total": 0})
    for t in db_trades:
        k = f"{t.strategy}_{t.symbol}_{t.session}"; stats[k]["total"] += 1
        if t.outcome: stats[k]["wins"] += 1
    return {k: {"win_rate": v["wins"]/v["total"], "trades": v["total"]} for k, v in stats.items() if v["total"] > 0}

@app.post("/api/start_trial")
def start_trial(data: TrialRequest):
    global trials_db
    if data.hwid in trials_db:
        expires = datetime.fromisoformat(trials_db[data.hwid]["expires"])
        if datetime.now() > expires: return {"valid": False, "message": "⏳ Expirada."}
        return {"valid": True, "days_left": (expires - datetime.now()).days, "plan": "BRONCE"}
    trials_db[data.hwid] = {"expires": (datetime.now() + timedelta(days=30)).isoformat()}
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
    return {"valid": True, "days_left": 30, "plan": "BRONCE"}

@app.post("/api/validate_license")
def validate_license(data: LicenseCheck):
    global licenses_db
    key = data.key.upper().strip()
    if key not in licenses_db: return {"valid": False, "message": "❌ No encontrada."}
    info = licenses_db[key]
    if not info["active"]: return {"valid": False, "message": "🚫 Suspendida."}
    expires = datetime.fromisoformat(info["expires"])
    if datetime.now() > expires: return {"valid": False, "message": "⏳ Expirada."}
    if info["hwid"] is None:
        info["hwid"] = data.hwid
        save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
    elif info["hwid"] != data.hwid: return {"valid": False, "message": "🔒 En uso en otra PC."}
    return {"valid": True, "days_left": (expires - datetime.now()).days, "plan": info["plan"]}

@app.post("/api/create_license")
def create_license(request: Request, data: LicenseCreate):
    if not verify_admin(request): return {"status": "error", "message": "❌ No autorizado."}
    global licenses_db
    key = generate_license_key(data.plan)
    licenses_db[key] = {"hwid": None, "expires": (datetime.now() + timedelta(days=data.duration_days)).isoformat(), "active": True, "plan": data.plan.upper(), "email": data.email.lower()}
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
    send_email(data.email, "🔑 Tu Licencia BLENIN77", f"Tu licencia es: {key}\nPlan: {data.plan.upper()}")
    return {"status": "success", "key": key}

@app.post("/api/recover_by_email")
def recover_by_email(req: RecoveryRequest):
    global stats_db
    email = req.email.lower()
    for key, info in licenses_db.items():
        if info.get("email", "").lower() == email:
            if info["active"]:
                send_email(email, "🔑 Tu Licencia BLENIN77", f"Tu clave es: {key}\nPlan: {info['plan']}")
                return {"status": "success", "message": "Enviado al correo."}
            else:
                if "captured_leads" not in stats_db: stats_db["captured_leads"] = []
                lead_data = {"name": email.split("@")[0], "email": email, "interaction": "Intento recuperar licencia expirada", "date": datetime.now().isoformat(), "follow_up_stage": 0, "last_email_sent": datetime.now().isoformat()}
                if email not in [l.get("email") for l in stats_db["captured_leads"]]:
                    stats_db["captured_leads"].append(lead_data)
                    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
                prompt = f"Eres un experto en retención. El cliente {email} intentó recuperar su licencia pero expiró. Ofrécele 30% de descuento con el código VOLVER30 para https://blenin77-server.onrender.com/#pricing"
                body = generate_dynamic_content_with_llama(prompt, max_tokens=300) or f"Hola,\n\nTu licencia expiró. Usa el código VOLVER30 para 30% de descuento.\n\n👉 https://blenin77-server.onrender.com/#pricing"
                send_email(email, "⏳ Tu acceso ha expirado - Tenemos un regalo", body)
                return {"status": "success", "message": "Tu licencia expiró. Te enviamos un correo con un 30% de descuento."}
    if "captured_leads" not in stats_db: stats_db["captured_leads"] = []
    if email not in [l.get("email") for l in stats_db["captured_leads"]]:
        stats_db["captured_leads"].append({"name": email.split("@")[0], "email": email, "interaction": "Intento recuperar licencia inexistente", "date": datetime.now().isoformat(), "follow_up_stage": 0, "last_email_sent": datetime.now().isoformat()})
        save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
        prompt = f"Eres un copywriter de trading. El cliente {email} intentó recuperar una licencia que no existe. Ofrécele 10% de descuento con el código BIENVENIDO10 para https://blenin77-server.onrender.com/#pricing"
        body = generate_dynamic_content_with_llama(prompt, max_tokens=300) or f"Hola,\n\nNo encontramos tu licencia. Usa el código BIENVENIDO10 para 10% de descuento.\n\n👉 https://blenin77-server.onrender.com/#pricing"
        send_email(email, "🎁 No encontramos tu licencia, pero tenemos una sorpresa", body)
    return {"status": "success", "message": "Si no recibes tu licencia en 5 minutos, revisa nuestra oferta especial en tu correo."}

@app.post("/api/manage_license")
def manage_license(request: Request, data: LicenseUpdate):
    if not verify_admin(request): return {"status": "error", "message": "❌ No autorizado."}
    global licenses_db
    key = data.key.upper().strip()
    if key not in licenses_db: return {"status": "error", "message": "❌ No encontrada."}
    licenses_db[key]["active"] = data.active
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
    return {"status": "success", "message": f"✅ Licencia {key} actualizada."}

@app.post("/api/reset_hwid")
def reset_hwid(request: Request, data: ResetHWID):
    if not verify_admin(request): return {"status": "error", "message": "❌ No autorizado."}
    global licenses_db
    key = data.key.upper().strip()
    if key not in licenses_db: return {"status": "error", "message": "❌ No encontrada."}
    licenses_db[key]["hwid"] = None
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
    return {"status": "success", "message": f"✅ HWID reseteado."}

@app.post("/api/hotmart_webhook")
def hotmart_webhook(request: Request):
    try:
        data = request.json()
        if data.get("event") == "PURCHASE_APPROVED" or data.get("event_type") == "PURCHASE_APPROVED":
            email = data.get("data", {}).get("buyer", {}).get("email") or data.get("data", {}).get("purchase", {}).get("buyer", {}).get("email")
            product_name = (data.get("data", {}).get("product", {}).get("name") or "BRONCE").upper()
            if "ORO" in product_name: plan_upper = "ORO"
            elif "PLATA" in product_name: plan_upper = "PLATA"
            else: plan_upper = "BRONCE"
            global licenses_db
            key = generate_license_key(plan_upper)
            licenses_db[key] = {"hwid": None, "expires": (datetime.now() + timedelta(days=30)).isoformat(), "active": True, "plan": plan_upper, "email": email.lower()}
            save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
            client_body = f"¡Gracias por tu compra!\n\nTu licencia es:\n{key}\n\nPlan: {plan_upper}\n\nDescarga: https://blenin77-server.onrender.com/"
            send_email(email, "✅ Pago Confirmado - Licencia BLENIN77", client_body)
            send_email(SMTP_EMAIL, "💰 ¡Nueva Venta!", f"Venta de {plan_upper} a {email}.")
            return {"status": "success"}
        return {"status": "ignored"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/make_payment_webhook")
def make_payment_webhook(request: Request):
    data = request.json()
    if data.get("secret_token") != "blenin_secret_token_2024": raise HTTPException(status_code=403, detail="Acceso denegado.")
    try:
        email = data["email"]; plan_upper = data["plan"].upper()
        if "ORO" in plan_upper: plan_upper = "ORO"
        elif "PLATA" in plan_upper: plan_upper = "PLATA"
        else: plan_upper = "BRONCE"
        global licenses_db
        key = generate_license_key(plan_upper)
        licenses_db[key] = {"hwid": None, "expires": (datetime.now() + timedelta(days=data.get("duration_days", 30))).isoformat(), "active": True, "plan": plan_upper, "email": email.lower()}
        save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
        client_body = f"¡Gracias por tu compra!\n\nTu licencia es:\n{key}\n\nDescarga: https://blenin77-server.onrender.com/"
        send_email(email, "✅ Pago Confirmado - Licencia BLENIN77", client_body)
        send_email(SMTP_EMAIL, "💰 ¡Nueva Venta Automática!", f"Venta de {plan_upper} a {email}.")
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/capture_lead")
def capture_lead(lead: LeadCapture):
    global stats_db
    try:
        if "captured_leads" not in stats_db: stats_db["captured_leads"] = []
        existing_emails = [l.get("email") for l in stats_db["captured_leads"]]
        if lead.email.lower() not in existing_emails:
            stats_db["captured_leads"].append({"name": lead.name, "email": lead.email.lower(), "interaction": lead.interaction, "date": datetime.now().isoformat(), "follow_up_stage": 0, "last_email_sent": datetime.now().isoformat()})
            save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
        prompt_email = f"Eres un copywriter de trading. Escribe un correo corto para '{lead.name}'. Él mostró interés en '{lead.interaction}'. Persuádelo de comprar el bot BLENIN77."
        dynamic_body = generate_dynamic_content_with_llama(prompt_email, max_tokens=300)
        client_body = dynamic_body if dynamic_body else f"Hola {lead.name},\n\nGracias por tu interés en BLENIN.G.77. Saludos,\nEquipo BLENIN77."
        send_email(lead.email, f"🚀 ¡Bienvenido {lead.name}! Tu acceso a BLENIN.G.77", client_body)
        send_email(SMTP_EMAIL, f"🔥 Nuevo Lead: {lead.name}", f"Nombre: {lead.name}\nCorreo: {lead.email}\nInteracción: {lead.interaction}")
        return {"status": "success", "message": "Información enviada."}
    except Exception as e: return {"status": "error", "message": str(e)}

# ==========================================
# 🛟 SISTEMA DE RETENCIÓN INTELIGENTE (ANTI-BAJAS)
# ==========================================
@app.post("/api/report_user_risk")
def report_user_risk(data: UserRiskReport):
    """Recibe alertas del bot cuando un usuario va mal para activar retención."""
    global licenses_db
    updated = False
    
    # Buscamos el correo del usuario usando su License Key
    key = data.license_key.upper().strip()
    info = licenses_db.get(key)
    
    if info and info.get("active"):
        email = info.get("email")
        if not email: return {"status": "ignored"}
        
        if data.consecutive_losses >= 3 or data.current_drawdown_pct > 5.0:
            last_retention = info.get("last_retention_email")
            if not last_retention or (datetime.now() - datetime.fromisoformat(last_retention)).days > 15:
                prompt = f"Eres un gerente de cuenta de trading. El cliente {email} tiene {data.consecutive_losses} pérdidas seguidas y un drawdown del {data.current_drawdown_pct}%. Escríbele un correo corto diciéndole que acabas de lanzar una estrategia optimizada por IA (v17) que se adapta a la volatilidad. Invítalo a actualizar su bot."
                email_body = generate_dynamic_content_with_llama(prompt, max_tokens=400)
                if not email_body:
                    email_body = f"Hola,\n\nNotamos que has tenido algunos días difíciles. ¡Buenas noticias! Acabamos de lanzar la actualización v17 de BLENIN77 con un nuevo Agente IA que se adapta automáticamente a la volatilidad.\n\nActualiza tu bot y prueba la nueva estrategia. ¡Recuperaremos el rumbo juntos!\n\nEquipo BLENIN77."
                send_email(email, "🛡️ Estamos monitoreando tu cuenta - Tenemos novedades", email_body)
                info["last_retention_email"] = datetime.now().isoformat()
                updated = True
                
    if updated:
        save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
    return {"status": "success"}

def ai_retention_agent():
    """Busca usuarios cuya licencia haya expirado hace menos de 30 días y les ofrece descuento para volver."""
    global licenses_db
    now = datetime.now()
    updated = False
    recent_wins = [t for t in db_trades if t.outcome][-5:]
    win_stats_text = "\n".join([f"✅ {t.symbol} {t.strategy} (+{t.profit_pips} pips)" for t in recent_wins]) or "Operaciones positivas constantes esta semana."
    for key, info in licenses_db.items():
        email = info.get("email")
        if not email: continue
        expires = datetime.fromisoformat(info["expires"])
        if now > expires and (now - expires).days <= 30:
            if not info.get("retention_email_sent"):
                prompt = f"Eres un experto en retención. El cliente {email} dejó de pagar su suscripción de trading. Escríbele un correo persuasivo. Dile que el bot ha estado ganando operaciones recientemente. Menciona estas estadísticas: {win_stats_text}. Ofrécele un 30% de descuento con el código VOLVER30."
                email_body = generate_dynamic_content_with_llama(prompt, max_tokens=400)
                if not email_body:
                    email_body = f"Hola,\n\nExtrastramos tenerte en la familia BLENIN77.\n\nMientras no estuviste, nuestra IA ha estado operando con excelentes resultados:\n{win_stats_text}\n\nQueremos que vuelvas. Usa el código VOLVER30 al reactivar tu plan y obtén un 30% de descuento.\n\n👉 https://blenin77-server.onrender.com/#pricing"
                send_email(email, "🎁 Te extrañamos en BLENIN77 - Tenemos un regalo para ti", email_body)
                info["retention_email_sent"] = True
                updated = True
    if updated:
        save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)

# ==========================================
# 🧠 AGENTE IA DE SEGUIMIENTO AUTOMÁTICO
# ==========================================
def ai_follow_up_agent():
    global stats_db
    if "captured_leads" not in stats_db: return
    leads_updated = False
    now = datetime.now()
    for lead in stats_db["captured_leads"]:
        stage = lead.get("follow_up_stage", 0)
        last_sent_str = lead.get("last_email_sent")
        if not last_sent_str: continue
        last_sent = datetime.fromisoformat(last_sent_str)
        days_since_last = (now - last_sent).days
        if stage == 0 and days_since_last >= int(ai_agent_config.get("stage1_days", 2)):
            subject = ai_agent_config.get("stage1_subject", "").replace("{name}", lead["name"])
            body = ai_agent_config.get("stage1_body", "").replace("{name}", lead["name"])
            if send_email(lead["email"], subject, body):
                lead["follow_up_stage"] = 1; lead["last_email_sent"] = now.isoformat(); leads_updated = True
        elif stage == 1 and days_since_last >= int(ai_agent_config.get("stage2_days", 5)):
            subject = ai_agent_config.get("stage2_subject", "").replace("{name}", lead["name"])
            body = ai_agent_config.get("stage2_body", "").replace("{name}", lead["name"])
            if send_email(lead["email"], subject, body):
                lead["follow_up_stage"] = 2; lead["last_email_sent"] = now.isoformat(); leads_updated = True
        elif stage == 2 and days_since_last >= int(ai_agent_config.get("stage3_days", 10)):
            subject = ai_agent_config.get("stage3_subject", "").replace("{name}", lead["name"])
            body = ai_agent_config.get("stage3_body", "").replace("{name}", lead["name"])
            if send_email(lead["email"], subject, body):
                lead["follow_up_stage"] = 3; lead["last_email_sent"] = now.isoformat(); leads_updated = True
    if leads_updated:
        save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)

# ==========================================
# 🚀 INICIALIZACIÓN DE AGENTES AUTOMÁTICOS
# ==========================================
scheduler = BackgroundScheduler()
scheduler.add_job(ai_follow_up_agent, 'interval', hours=1)
scheduler.add_job(ai_retention_agent, 'interval', hours=24)
scheduler.start()
