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

# Importación de Supabase
from supabase import create_client, Client

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
        response.set_cookie(key="blenin_session", value=SESSION_TOKEN, httponly=True, secure=False, samesite="lax", max_age=86400)
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
# 🔧 CONFIGURACIÓN SUPABASE Y CORREO
# ==========================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

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
        return True
    except Exception as e:
        print(f"❌ ERROR ENVIANDO CORREO A {to_email}: {e}")
        return False

# ==========================================
# 🧠 INTELIGENCIA ARTIFICIAL CON GOOGLE GEMINI
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

def generate_dynamic_content_with_llama(prompt, max_tokens=1200):
    """Genera contenido usando Google Gemini API."""
    if not GEMINI_API_KEY:
        print("❌ ERROR: GEMINI_API_KEY no configurada en variables de entorno de Render.", flush=True)
        return None
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.8,
                "maxOutputTokens": max_tokens,
                "topP": 0.95
            },
            "systemInstruction": {
                "parts": [
                    {"text": "Eres un copywriter experto en marketing digital y trading automatizado. Respondes SIEMPRE en español, con tono persuasivo, profesional y orientado a conversión. Usas formato Markdown cuando sea apropiado."}
                ]
            }
        }
        response = requests.post(url, json=payload, timeout=90)
        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            print(f"⚠️ GEMINI: Respuesta vacía. Body: {data}", flush=True)
            return None
        else:
            print(f"❌ GEMINI API ERROR {response.status_code}: {response.text}", flush=True)
            return None
    except Exception as e:
        print(f"❌ EXCEPCIÓN llamando a Gemini: {e}", flush=True)
        return None

# ==========================================
# 🧠 SISTEMA DE BASE DE DATOS (SUPABASE) - VERSIÓN A PRUEBA DE FALLOS
# ==========================================
def get_default_ai_config():
    return {
        "stage1_days": 2,
        "stage1_subject": "🚀 {name}, descubre el poder de la IA Institucional con BLENIN.G.77",
        "stage1_body": "Hola {name},\n\nGracias por tu interés en BLENIN.G.77, el sistema de trading de nivel institucional impulsado por Inteligencia Artificial.\n\nMuchos usuarios nos preguntan si nuestra tecnología reemplaza el trabajo del trader. La respuesta es: es tu copiloto perfecto, diseñado para proteger tu capital y maximizar oportunidades mientras tú vives tu vida.\n\nCon nuestro sistema, tienes acceso a:\n🔹 IA Predictiva y Análisis Global en tiempo real.\n🔹 Un Enjambre de 500 Agentes analizando el mercado.\n🔹 Modo Híbrido (MT5 + Noticias macroeconómicas).\n\n¿Tienes alguna duda sobre cómo adaptar el bot a tu cuenta de MT5? Simplemente responde a este correo y nuestro equipo te ayudará.\n\nUn saludo institucional,\nEquipo de BLENIN.G.77 Trading Systems.\nhttps://blenin77-server.onrender.com/",
        "stage2_days": 5,
        "stage2_subject": "🔥 {name}, esto es lo que estás dejando atrás...",
        "stage2_body": "Hola {name},\n\nQueríamos mostrarte lo que la comunidad de BLENIN.G.77 está logrando hoy. Nuestros usuarios del Plan Oro están reportando resultados excepcionales al combinar nuestra IA Predictiva con el Modo Híbrido (MT5 + Noticias en tiempo real).\n\nSabemos que el trading requiere confianza, pero las oportunidades del mercado no esperan. Si te quedas fuera, el mercado seguirá moviéndose sin tus operaciones optimizadas.\n\nNo dejes tu capital expuesto a la emoción humana. Deja que la matemática y la IA trabajan por ti.\n\nRevisa nuestros planes y elige el que se adapte a tu capital aquí:\n👉 https://blenin77-server.onrender.com/#pricing\n\nUn saludo institucional,\nEquipo de BLENIN.G.77 Trading Systems.",
        "stage3_days": 10,
        "stage3_subject": "⏳ {name}, tu acceso VIP a BLENIN.G.77 está por expirar",
        "stage3_body": "Hola {name},\n\nHemos notado que aún no has dado el paso definitivo para automatizar tu trading con BLENIN.G.77. Entendemos que dar el control a una Inteligencia Artificial puede ser un gran paso.\n\nPor eso, como último intento de ayudarte a dar el salto institucional, hemos habilitado un descuento especial del 10% si adquieres cualquier plan en las próximas 48 horas.\n\nUsa el siguiente código al momento de tu transferencia o responde a este correo para activarlo:\n🎁 Código de descuento: BLENIN10\n\nNo dejes que la volatilidad te tome por sorpresa. Protege tu capital y maximiza tus oportunidades hoy.\n\nUn saludo institucional,\nEquipo de BLENIN.G.77 Trading Systems.\nhttps://blenin77-server.onrender.com/#pricing"
    }

def get_default_update_config():
    return {
        "latest_version": "1.0.0",
        "download_url": "https://blenin77-server.onrender.com/",
        "force_update": False,
        "update_message": "Hay una nueva versión disponible."
    }

def load_dbs():
    try:
        if not supabase: raise Exception("Supabase no configurado")
        response = supabase.table("app_data").select("key, value").execute()
        data = {}
        for item in response.data:
            data[item['key']] = item['value']
        
        pwd = data.get("admin_password", os.environ.get("ADMIN_PASSWORD", "cambiar_esta_clave_123"))
        ai_cfg = data.get("ai_agent_config", get_default_ai_config())
        upd_cfg = data.get("bot_update_config", get_default_update_config())
        
        return data.get("licenses_db", {}), data.get("trials_db", {}), data.get("stats_db", {"views": 0, "countries": {}}), pwd, ai_cfg, upd_cfg
    except Exception as e:
        print(f"Error cargando DBs de Supabase: {e}")
        return {}, {}, {"views": 0, "countries": {}}, os.environ.get("ADMIN_PASSWORD", "cambiar_esta_clave_123"), get_default_ai_config(), get_default_update_config()

def save_dbs(lic, trials, stats, pwd=None, ai_cfg=None, upd_cfg=None):
    try:
        if not supabase: return
        def upsert_data(key, value):
            try:
                res = supabase.table("app_data").upsert({"key": key, "value": value}, on_conflict="key").execute()
                if not res.data: print(f"🚨 ALERTA: Supabase no devolvió datos al guardar {key} (¿RLS activo?)", flush=True)
            except Exception as e:
                print(f"🚨 ERROR SUPABASE GUARDANDO {key}: {e}", flush=True)

        upsert_data("licenses_db", lic)
        upsert_data("trials_db", trials)
        upsert_data("stats_db", stats)
        if pwd: upsert_data("admin_password", pwd)
        if ai_cfg: upsert_data("ai_agent_config", ai_cfg)
        if upd_cfg: upsert_data("bot_update_config", upd_cfg)
    except Exception as e:
        print(f"Error general guardando DBs en Supabase: {e}", flush=True)

licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config = load_dbs()

if not ai_agent_config or "stage1_subject" not in ai_agent_config:
    ai_agent_config = get_default_ai_config()
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)

if not licenses_db:
    licenses_db = {
        "BLENIN-TEST-ORO": {"hwid": None, "expires": "2026-09-15T00:00:00", "active": True, "plan": "ORO", "email": "test-oro@blenin77.com"},
        "BLENIN-TEST-PLATA": {"hwid": None, "expires": "2026-09-15T00:00:00", "active": True, "plan": "PLATA", "email": "test-plata@blenin77.com"},
        "BLENIN-TEST-BRONCE": {"hwid": None, "expires": "2026-09-15T00:00:00", "active": True, "plan": "BRONCE", "email": "test-bronce@blenin77.com"}
    }
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)

def get_default_content(page_name="Principal"):
    return {
        "page_name": page_name,
        "chatbot_id": "gzEjAzK1VCE72hJ_hBfA4",
        "hero_title": "BLENIN.G.77",
        "hero_subtitle": "THE BEST FUTURE FOR YOU",
        "hero_text": "IA Predictiva, Enjambre de 500 Agentes y Análisis Global en Tiempo Real.",
        "affiliate_link": "https://go.hotmart.com/W107659112D",
        "affiliate_text": "🚀 Afíliate (75%)",
        "publications": [{"type": "video", "url": "https://www.youtube.com/embed/dQw4w9WgXcQ", "desc": "Mira cómo el Enjambre de Agentes abre operaciones reales."}],
        "plans": [
            {"name": "Bronce", "price": "$49", "features": "✅ 1 Cuenta MT5\n✅ Modo MT5 Puro", "link": "P-78W24779DJ167620XNKNUHYY", "highlight": False},
            {"name": "Plata", "price": "$99", "features": "✅ 2 Cuentas MT5\n✅ Modo Híbrido + Enjambre", "link": "P-5XY16476VG217634ANKNUHZA", "highlight": True},
            {"name": "Oro", "price": "$199", "features": "✅ Cuentas Ilimitadas\n✅ Deep Learning (PyTorch)", "link": "P-4LL21192X9335681FNKNUHZA", "highlight": False}
        ],
        "social_links": {"facebook": "", "whatsapp": "", "youtube": "", "tiktok": "", "telegram": "", "instagram": ""},
        "bank_transfer_info": {
            "bank_name": "Banco Ejemplo S.A.",
            "account_type": "Cuenta Corriente",
            "account_number": "01234567890123456789",
            "beneficiary": "Lenin Benitez",
            "email_for_proof": "pagos@blenin77.com",
            "whatsapp_for_proof": "593999999999"
        },
        "download_links": ["https://mega.nz/file/tu_enlace"],
        "download_instructions": "1. Descarga el archivo .zip\n2. Extrae el contenido en tu PC\n3. Ejecuta el instalador Blenin77.exe\n4. Ingresa tu licencia al abrir el sistema."
    }

def get_all_pages():
    try:
        if not supabase: raise Exception("Supabase no configurado")
        print("📥 Cargando páginas desde Supabase...", flush=True)
        response = supabase.table("app_data").select("value").eq("key", "pages").execute()
        
        if response.data:
            print("✅ Datos encontrados en Supabase.", flush=True)
            data = response.data[0]["value"]
            if "hero_title" in data and "pages" not in data:
                new_data = {"pages": {"main": data}}
                save_all_pages(new_data)
                return new_data
            return data
        else:
            print("⚠️ Base de datos vacía. Creando páginas por defecto...", flush=True)
            default_data = {"pages": {"main": get_default_content()}}
            save_all_pages(default_data)
            return default_data
    except Exception as e:
        print(f"Error obteniendo páginas: {e}", flush=True)
        default_data = {"pages": {"main": get_default_content()}}
        try: save_all_pages(default_data)
        except: pass
        return default_data

def save_all_pages(data):
    try:
        if not supabase: 
            print("❌ Supabase no configurado. Revisa las variables de entorno en Render.", flush=True)
            return False
            
        print("🔄 Intentando hacer upsert en Supabase...", flush=True)
        res = supabase.table("app_data").upsert({"key": "pages", "value": data}, on_conflict="key").execute()
        
        if hasattr(res, 'error') and res.error:
            print(f"🚨 ERROR EXPLÍCITO DE SUPABASE: {res.error}", flush=True)
            return False
        if not hasattr(res, 'data') or res.data is None or len(res.data) == 0:
            print("🚨 ERROR SILENCIOSO: Supabase no devolvió datos. Revisa si RLS está desactivado.", flush=True)
            return False
            
        print("✅ Páginas guardadas en Supabase correctamente.", flush=True)
        return True
    except Exception as e:
        print(f"🚨 EXCEPCIÓN guardando páginas: {e}", flush=True)
        return False

# ==========================================
# 🔄 SISTEMA DE ACTUALIZACIONES DEL BOT
# ==========================================
@app.get("/api/get_latest_version")
def get_latest_version():
    return bot_update_config

class UpdateConfigData(BaseModel):
    latest_version: str
    download_url: str
    force_update: bool
    update_message: str

@app.get("/api/get_update_config")
def get_update_config_api():
    if not bot_update_config: return get_default_update_config()
    return bot_update_config

@app.post("/api/save_update_config")
def save_update_config_api(request: Request, data: UpdateConfigData):
    global bot_update_config
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    bot_update_config = data.dict()
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
    return {"status": "success", "message": "✅ Configuración de actualización guardada."}

# ==========================================
# 🎛️ PANEL DE ADMINISTRACIÓN (CMS MULTI-PÁGINA)
# ==========================================
@app.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request):
    if not verify_admin(request):
        return RedirectResponse(url="/admin/login", status_code=303)
        
    pages_data = get_all_pages()
    pages_dict = pages_data.get("pages", {})
    pages_json = json.dumps(pages_dict).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    
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
        <div class="flex gap-2 flex-wrap items-center">
            <button onclick="showTab('pages')" id="tab-pages" class="tab-active px-4 py-2 rounded text-sm font-medium transition">🚀 Páginas</button>
            <button onclick="showTab('stats')" id="tab-stats" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">📊 Estadísticas</button>
            <button onclick="showTab('ai')" id="tab-ai" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">🤖 Agente IA</button>
            <button onclick="showTab('lic')" id="tab-lic" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">Licencias</button>
            <button onclick="showTab('updates')" id="tab-updates" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">🔄 Actualizaciones</button>
            <button onclick="showTab('mkt')" id="tab-mkt" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">🧠 Marketing IA</button>
            <button onclick="showTab('settings')" id="tab-settings" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">⚙️ Ajustes</button>
            <a href="/admin/logout" class="bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded text-sm font-bold transition ml-2"><i class="fas fa-sign-out-alt mr-1"></i>Salir</a>
        </div>
    </nav>
    <div class="flex-1 container mx-auto p-6 md:p-10 max-w-4xl">
        <div id="content-pages" class="space-y-6 hidden">
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Gestor de Landing Pages</h3>
                <div class="flex gap-2 mb-4">
                    <select id="page_selector" onchange="loadPageData()" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></select>
                    <button onclick="createPage()" class="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded text-sm font-bold whitespace-nowrap"><i class="fas fa-plus"></i> Nueva</button>
                    <button onclick="duplicatePage()" class="bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-2 rounded text-sm font-bold whitespace-nowrap"><i class="fas fa-copy"></i> Duplicar</button>
                    <button onclick="deletePage()" class="bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded text-sm font-bold whitespace-nowrap"><i class="fas fa-trash"></i></button>
                </div>
                <p class="text-xs text-slate-400 mb-4">URL de la página: <span id="page_url_preview" class="text-cyan-400"></span></p>
            </div>
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Textos Principales (Hero)</h3>
                <input type="hidden" id="current_slug">
                <label class="text-sm text-slate-400">Nombre Interno de la Página</label>
                <input type="text" id="page_name" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700 focus:border-cyan-500 outline-none">
                <label class="text-sm text-slate-400">ID del Chatbot para esta página (Chatbase)</label>
                <div class="flex items-center gap-2 mb-4">
                    <i class="fas fa-robot text-cyan-400"></i>
                    <input type="text" id="chatbot_id" class="w-full bg-slate-900 rounded p-2 border border-slate-700 focus:border-cyan-500 outline-none" placeholder="Ej: gzEjAzK1VCE72hJ_hBfA4">
                </div>
                <label class="text-sm text-slate-400">Título Principal (H1)</label>
                <input type="text" id="hero_title" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700 focus:border-cyan-500 outline-none">
                <label class="text-sm text-slate-400">Subtítulo (H2)</label>
                <input type="text" id="hero_subtitle" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700 focus:border-cyan-500 outline-none">
                <label class="text-sm text-slate-400">Texto Descriptivo</label>
                <textarea id="hero_text" rows="3" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700 focus:border-cyan-500 outline-none"></textarea>
            </div>
            <div class="bg-slate-800 p-6 rounded-xl border border-emerald-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">💰 Programa de Afiliados</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div><label class="text-sm text-slate-400">Enlace de Afiliado (Hotmart)</label><input type="text" id="affiliate_link" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="https://go.hotmart.com/..."></div>
                    <div><label class="text-sm text-slate-400">Texto del Botón</label><input type="text" id="affiliate_text" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="🚀 Afíliate (75%)"></div>
                </div>
            </div>
            <div class="bg-slate-800 p-6 rounded-xl border border-indigo-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">📥 Sistema de Descarga para Clientes</h3>
                <p class="text-sm text-slate-400 mb-4">Agrega uno o varios enlaces (Mega, Google Drive, etc). El usuario verá botones de "Servidor 1", "Servidor 2", etc.</p>
                <label class="text-sm text-slate-400">Enlaces de Descarga</label>
                <div id="dl-links-container" class="space-y-2 mb-4"></div>
                <button onclick="addDlLink()" class="mt-2 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded text-sm font-bold transition"><i class="fas fa-plus mr-2"></i>Agregar Enlace</button>
                <div class="mt-6">
                    <label class="text-sm text-slate-400">Instrucciones de Instalación/Referencia</label>
                    <textarea id="download_instructions" rows="4" class="w-full bg-slate-900 rounded p-2 border border-slate-700 focus:border-cyan-500 outline-none" placeholder="Ej: 1. Descarga el archivo..."></textarea>
                </div>
            </div>
            <div class="bg-slate-800 p-6 rounded-xl border border-amber-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">💳 Pagos por Transferencia Bancaria</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div><label class="text-sm text-slate-400">Nombre del Banco</label><input type="text" id="bt_bank_name" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Ej: Bank of America"></div>
                    <div><label class="text-sm text-slate-400">Tipo de Cuenta</label><input type="text" id="bt_account_type" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Ej: Cuenta Corriente"></div>
                    <div><label class="text-sm text-slate-400">Número de Cuenta / IBAN</label><input type="text" id="bt_account_number" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Ej: 0123456789"></div>
                    <div><label class="text-sm text-slate-400">Beneficiario</label><input type="text" id="bt_beneficiary" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Ej: Lenin Benitez"></div>
                    <div><label class="text-sm text-slate-400">Correo para enviar comprobante</label><input type="email" id="bt_email" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="pagos@blenin77.com"></div>
                    <div><label class="text-sm text-slate-400">WhatsApp para enviar comprobante</label><input type="text" id="bt_whatsapp" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="593999999999"></div>
                </div>
            </div>
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Publicaciones (Galería)</h3>
                <div id="pubs-container" class="space-y-4"></div>
                <button onclick="addPubRow()" class="mt-4 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded text-sm font-bold transition"><i class="fas fa-plus mr-2"></i>Agregar Publicación</button>
            </div>
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Planes de Suscripción (PayPal)</h3>
                <div class="bg-slate-900 p-3 rounded mb-4 text-amber-400 text-xs">💡 IMPORTANTE: En el campo "Enlace de pago", pon únicamente el ID del plan de PayPal (Ej: P-78W24779DJ167620XNKNUHYY). El sistema lo convertirá en un botón automático.</div>
                <div id="plans-container" class="space-y-6"></div>
                <button onclick="addPlanRow()" class="mt-4 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded text-sm font-bold transition"><i class="fas fa-plus mr-2"></i>Agregar Plan</button>
            </div>
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Redes Sociales</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div><label class="text-sm text-slate-400">Facebook URL</label><input type="text" id="fb_link" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
                    <div><label class="text-sm text-slate-400">WhatsApp URL</label><input type="text" id="wa_link" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
                    <div><label class="text-sm text-slate-400">YouTube URL</label><input type="text" id="yt_link" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
                    <div><label class="text-sm text-slate-400">TikTok URL</label><input type="text" id="tt_link" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
                    <div><label class="text-sm text-slate-400">Telegram URL</label><input type="text" id="tg_link" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
                    <div><label class="text-sm text-slate-400">Instagram URL</label><input type="text" id="ig_link" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
                </div>
            </div>
        </div>
        <div id="content-stats" class="hidden space-y-6">
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
            <div class="bg-slate-800 p-6 rounded-xl border border-cyan-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">📧 Leads Capturados (Agente IA de Seguimiento)</h3>
                <div id="stat_leads" class="space-y-2 max-h-96 overflow-y-auto"></div>
            </div>
        </div>
        <div id="content-ai" class="hidden space-y-6">
            <div class="bg-slate-800 p-6 rounded-xl border border-cyan-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">🤖 Configuración del Agente IA (Seguimiento de Leads)</h3>
                <p class="text-sm text-slate-400 mb-6">Usa la variable <code class="bg-slate-900 p-1 rounded text-cyan-400">{{name}}</code> en los mensajes para personalizarlos con el nombre del cliente.</p>
                <div class="space-y-8">
                    <div class="bg-slate-900 p-4 rounded-lg border border-slate-700">
                        <h4 class="text-cyan-400 font-bold mb-3">Seguimiento 1</h4>
                        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-3">
                            <div class="md:col-span-1">
                                <label class="text-sm text-slate-400">Enviar después de (días)</label>
                                <input type="number" id="s1_days" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" value="2">
                            </div>
                            <div class="md:col-span-3">
                                <label class="text-sm text-slate-400">Asunto del Correo</label>
                                <input type="text" id="s1_subject" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500">
                            </div>
                        </div>
                        <label class="text-sm text-slate-400">Mensaje</label>
                        <textarea id="s1_body" rows="4" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></textarea>
                    </div>
                    <div class="bg-slate-900 p-4 rounded-lg border border-slate-700">
                        <h4 class="text-cyan-400 font-bold mb-3">Seguimiento 2</h4>
                        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-3">
                            <div class="md:col-span-1">
                                <label class="text-sm text-slate-400">Enviar después de (días)</label>
                                <input type="number" id="s2_days" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" value="5">
                            </div>
                            <div class="md:col-span-3">
                                <label class="text-sm text-slate-400">Asunto del Correo</label>
                                <input type="text" id="s2_subject" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500">
                            </div>
                        </div>
                        <label class="text-sm text-slate-400">Mensaje</label>
                        <textarea id="s2_body" rows="4" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></textarea>
                    </div>
                    <div class="bg-slate-900 p-4 rounded-lg border border-slate-700">
                        <h4 class="text-cyan-400 font-bold mb-3">Seguimiento 3 (Cierre)</h4>
                        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-3">
                            <div class="md:col-span-1">
                                <label class="text-sm text-slate-400">Enviar después de (días)</label>
                                <input type="number" id="s3_days" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" value="10">
                            </div>
                            <div class="md:col-span-3">
                                <label class="text-sm text-slate-400">Asunto del Correo</label>
                                <input type="text" id="s3_subject" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500">
                            </div>
                        </div>
                        <label class="text-sm text-slate-400">Mensaje</label>
                        <textarea id="s3_body" rows="4" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></textarea>
                    </div>
                </div>
                <button onclick="saveAIConfig()" class="mt-6 w-full bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold py-3 rounded transition"><i class="fas fa-save mr-2"></i>Guardar Configuración del Agente IA</button>
            </div>
        </div>
        <div id="content-lic" class="hidden space-y-6">
            <div class="bg-slate-800 p-6 rounded-xl border border-emerald-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">➕ Crear Licencia Manualmente</h3>
                <p class="text-sm text-slate-400 mb-4">Usa esta función cuando recibas el comprobante de transferencia bancaria de un cliente.</p>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div>
                        <label class="text-sm text-slate-400">Plan</label>
                        <select id="manual_plan" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500">
                            <option value="BRONCE">Bronce</option>
                            <option value="PLATA">Plata</option>
                            <option value="ORO">Oro</option>
                        </select>
                    </div>
                    <div>
                        <label class="text-sm text-slate-400">Duración (días)</label>
                        <input type="number" id="manual_days" value="30" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500">
                    </div>
                    <div>
                        <label class="text-sm text-slate-400">Correo del Cliente</label>
                        <input type="email" id="manual_email" placeholder="cliente@correo.com" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500">
                    </div>
                </div>
                <button onclick="createManualLicense()" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded text-sm font-bold transition"><i class="fas fa-key mr-2"></i>Generar y Guardar Licencia</button>
                <div id="manual_lic_msg" class="mt-4 text-cyan-400 font-bold text-sm hidden bg-slate-900 p-3 rounded"></div>
            </div>
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Gestión de Licencias Existentes</h3>
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
        <div id="content-updates" class="hidden space-y-6">
            <div class="bg-slate-800 p-6 rounded-xl border border-cyan-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">🔄 Gestión de Versiones del Bot</h3>
                <p class="text-sm text-slate-400 mb-4">Configura los parámetros que recibirán los bots de tus usuarios al iniciar sesión. Si la versión del bot del usuario es diferente a la que pongas aquí, se mostrará un aviso.</p>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div><label class="text-sm text-slate-400">Última Versión Disponible</label><input type="text" id="upd_version" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Ej: 1.1.0"></div>
                    <div><label class="text-sm text-slate-400">URL de Descarga del .exe</label><input type="text" id="upd_url" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="https://mega.nz/..."></div>
                </div>
                <div class="mb-4"><label class="text-sm text-slate-400">Mensaje de la Actualización</label><textarea id="upd_message" rows="3" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Ej: Corrección de errores."></textarea></div>
                <div class="flex items-center gap-2 mb-6 p-3 bg-slate-900 rounded border border-slate-700"><input type="checkbox" id="upd_force" class="w-5 h-5 accent-red-500"><label for="upd_force" class="text-sm text-slate-300 cursor-pointer">Forzar Actualización Obligatoria (Bloquear uso de versiones antiguas)</label></div>
                <button onclick="saveUpdateConfig()" class="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold py-3 rounded transition"><i class="fas fa-save mr-2"></i>Guardar y Publicar Versión</button>
            </div>
        </div>
        <div id="content-mkt" class="hidden space-y-6">
            <div class="bg-slate-800 p-6 rounded-xl border border-purple-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">🧠 Generador de Tráfico y Leads con IA</h3>
                <p class="text-sm text-slate-400 mb-6">Elige qué tipo de contenido quieres que la IA (<strong class="text-purple-400">Google Gemini</strong>) cree para atraer clientes a tu web.</p>
                
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <button onclick="setMktType('seo')" id="mkt-btn-seo" class="bg-slate-900 hover:bg-purple-600 border-2 border-purple-500 p-4 rounded-lg text-left transition">
                        <i class="fas fa-search text-2xl text-purple-400 mb-2"></i>
                        <h4 class="text-white font-bold">Artículo SEO (Google)</h4>
                        <p class="text-xs text-slate-400 mt-1">Blog optimizado para rankear en Google.</p>
                    </button>
                    <button onclick="setMktType('tiktok')" id="mkt-btn-tiktok" class="bg-slate-900 hover:bg-purple-600 border-2 border-slate-700 p-4 rounded-lg text-left transition">
                        <i class="fab fa-tiktok text-2xl text-purple-400 mb-2"></i>
                        <h4 class="text-white font-bold">Guion Viral (TikTok/Reels)</h4>
                        <p class="text-xs text-slate-400 mt-1">Guion con hook + desarrollo + CTA.</p>
                    </button>
                    <button onclick="setMktType('reddit')" id="mkt-btn-reddit" class="bg-slate-900 hover:bg-purple-600 border-2 border-slate-700 p-4 rounded-lg text-left transition">
                        <i class="fab fa-reddit text-2xl text-purple-400 mb-2"></i>
                        <h4 class="text-white font-bold">Post para Foros (Reddit)</h4>
                        <p class="text-xs text-slate-400 mt-1">Post natural para generar tráfico orgánico.</p>
                    </button>
                </div>

                <div class="mb-4">
                    <label class="text-sm text-slate-400">Tema / Palabra clave (opcional)</label>
                    <input type="text" id="mkt_topic" placeholder="Ej: bot de trading IA, automatizar forex, señal MT5" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-purple-500">
                </div>

                <input type="hidden" id="mkt_selected_type" value="seo">

                <button onclick="generateMktContent()" id="mkt_generate_btn" class="w-full bg-purple-600 hover:bg-purple-500 text-white font-bold py-3 rounded transition">
                    <i class="fas fa-magic mr-2"></i> Generar Contenido con IA
                </button>

                <div id="mkt_result_box" class="mt-6 hidden">
                    <div class="flex justify-between items-center mb-2">
                        <h4 class="text-white font-bold">📝 Contenido generado:</h4>
                        <div class="flex gap-2">
                            <button onclick="copyMktResult()" class="bg-cyan-500 hover:bg-cyan-400 text-slate-900 px-3 py-1 rounded text-xs font-bold"><i class="fas fa-copy mr-1"></i>Copiar</button>
                            <button onclick="downloadMktResult()" class="bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1 rounded text-xs font-bold"><i class="fas fa-download mr-1"></i>Descargar .txt</button>
                        </div>
                    </div>
                    <textarea id="mkt_result" rows="18" class="w-full bg-slate-900 rounded p-4 border border-slate-700 text-slate-200 font-mono text-sm outline-none focus:border-purple-500"></textarea>
                </div>
            </div>
        </div>
        <div id="content-settings" class="hidden space-y-6">
            <div class="bg-slate-800 p-6 rounded-xl border border-amber-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">🔑 Cambiar Contraseña de Administrador</h3>
                <p class="text-sm text-slate-400 mb-4">Cambia la contraseña de acceso al panel. La nueva contraseña se guardará de forma segura en la base de datos.</p>
                <div class="space-y-4">
                    <div>
                        <label class="text-sm text-slate-400">Contraseña Actual</label>
                        <input type="password" id="current_pwd" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="••••••••">
                    </div>
                    <div>
                        <label class="text-sm text-slate-400">Nueva Contraseña</label>
                        <input type="password" id="new_pwd" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="••••••">
                    </div>
                    <div>
                        <label class="text-sm text-slate-400">Repetir Nueva Contraseña</label>
                        <input type="password" id="confirm_pwd" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="••••••">
                    </div>
                    <button onclick="changePassword()" class="w-full bg-amber-600 hover:bg-amber-500 text-white px-4 py-2 rounded text-sm font-bold transition"><i class="fas fa-save mr-2"></i>Actualizar Contraseña</button>
                    <div id="pwd_msg" class="mt-4 font-bold text-sm hidden"></div>
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
    const allPages = JSON.parse('{pages_json}');
    
    let mktCurrentType = 'seo';
    
    function showTab(tabId) {{
        ['pages', 'stats', 'ai', 'lic', 'updates', 'mkt', 'settings'].forEach(id => {{
            document.getElementById('content-' + id).classList.add('hidden');
            document.getElementById('tab-' + id).classList.remove('tab-active');
            document.getElementById('tab-' + id).classList.add('bg-slate-800', 'hover:bg-slate-700');
        }});
        document.getElementById('content-' + tabId).classList.remove('hidden');
        document.getElementById('tab-' + tabId).classList.add('tab-active');
        document.getElementById('tab-' + tabId).classList.remove('bg-slate-800', 'hover:bg-slate-700');
        if(tabId === 'ai') loadAIConfig();
        if(tabId === 'stats') loadStats();
        if(tabId === 'updates') loadUpdateConfig();
    }}
    
    function showToast(msg) {{
        const t = document.getElementById('toast');
        document.getElementById('toast-msg').innerText = msg;
        t.classList.remove('opacity-0');
        setTimeout(() => t.classList.add('opacity-0'), 3000);
    }}
    
    function updateSelector() {{
        const selector = document.getElementById('page_selector');
        selector.innerHTML = '';
        const slugs = Object.keys(allPages);
        slugs.forEach(slug => {{
            let opt = document.createElement('option');
            opt.value = slug;
            opt.innerText = allPages[slug].page_name || slug;
            selector.appendChild(opt);
        }});
        if (slugs.length > 0) {{
            selector.value = slugs[0];
            loadPageData();
        }}
    }}
    
    function loadPageData() {{
        const slug = document.getElementById('page_selector').value;
        if (!slug) return;
        const p = allPages[slug] || {{}};
        
        document.getElementById('current_slug').value = slug;
        document.getElementById('page_name').value = p.page_name || '';
        document.getElementById('chatbot_id').value = p.chatbot_id || 'gzEjAzK1VCE72hJ_hBfA4';
        document.getElementById('hero_title').value = p.hero_title || '';
        document.getElementById('hero_subtitle').value = p.hero_subtitle || '';
        document.getElementById('hero_text').value = p.hero_text || '';
        document.getElementById('affiliate_link').value = p.affiliate_link || '';
        document.getElementById('affiliate_text').value = p.affiliate_text || '';
        document.getElementById('download_instructions').value = p.download_instructions || '';
        
        document.getElementById('dl-links-container').innerHTML = '';
        let dlLinks = p.download_links || [];
        if (dlLinks.length === 0 && p.download_link) {{
            dlLinks = [p.download_link];
        }}
        if (dlLinks.length === 0) {{
            addDlLink('');
        }} else {{
            dlLinks.forEach(url => addDlLink(url || ''));
        }}
        
        const bt = p.bank_transfer_info || {{}};
        document.getElementById('bt_bank_name').value = bt.bank_name || '';
        document.getElementById('bt_account_type').value = bt.account_type || '';
        document.getElementById('bt_account_number').value = bt.account_number || '';
        document.getElementById('bt_beneficiary').value = bt.beneficiary || '';
        document.getElementById('bt_email').value = bt.email_for_proof || '';
        document.getElementById('bt_whatsapp').value = bt.whatsapp_for_proof || '';
        
        const social = p.social_links || {{}};
        document.getElementById('fb_link').value = social.facebook || '';
        document.getElementById('wa_link').value = social.whatsapp || '';
        document.getElementById('yt_link').value = social.youtube || '';
        document.getElementById('tt_link').value = social.tiktok || '';
        document.getElementById('tg_link').value = social.telegram || '';
        document.getElementById('ig_link').value = social.instagram || '';
        
        document.getElementById('pubs-container').innerHTML = '';
        let pubs = p.publications || [];
        if (pubs.length === 0) {{
            addPubRow();
        }} else {{
            pubs.forEach(pub => addPubRow(pub.type || 'video', pub.url || '', pub.desc || ''));
        }}
        
        document.getElementById('plans-container').innerHTML = '';
        let plans = p.plans || [];
        if (plans.length === 0) {{
            addPlanRow();
        }} else {{
            plans.forEach(plan => addPlanRow(plan.name || '', plan.price || '', plan.features || '', plan.link || '', plan.highlight || false));
        }}
        
        const urlText = slug === 'main' ? 'tudominio.com/' : 'tudominio.com/p/' + slug;
        document.getElementById('page_url_preview').innerText = urlText;
    }}
    
    function createPage() {{
        const name = prompt('Nombre de la nueva página (ej: Promo Black Friday):');
        if(!name) return;
        let slug = prompt('URL de la página (solo letras, números y guiones, ej: black-friday):');
        if(!slug) return;
        slug = slug.toLowerCase().replace(/[^a-z0-9-]/g, '');
        if(allPages[slug]) {{ alert('Esa URL ya existe'); return; }}
        allPages[slug] = {{ 
            page_name: name, 
            chatbot_id: 'gzEjAzK1VCE72hJ_hBfA4', 
            hero_title: name, 
            hero_subtitle: '', 
            hero_text: '', 
            affiliate_link: '', 
            affiliate_text: '', 
            publications: [], 
            plans: [], 
            social_links: {{ facebook: '', whatsapp: '', youtube: '', tiktok: '', telegram: '', instagram: '' }}, 
            bank_transfer_info: {{}}, 
            download_links: [], 
            download_instructions: '' 
        }};
        saveData(true);
    }}
    
    function duplicatePage() {{
        const currentSlug = document.getElementById('page_selector').value;
        const newSlug = prompt('URL para la copia (ej: promo-v2):');
        if(!newSlug) return;
        const slug = newSlug.toLowerCase().replace(/[^a-z0-9-]/g, '');
        if(allPages[slug]) {{ alert('Esa URL ya existe'); return; }}
        allPages[slug] = JSON.parse(JSON.stringify(allPages[currentSlug]));
        allPages[slug].page_name += ' (Copia)';
        saveData(true);
    }}
    
    function deletePage() {{
        const slug = document.getElementById('page_selector').value;
        if(slug === 'main') {{ alert('No puedes eliminar la página principal.'); return; }}
        if(confirm('¿Seguro que quieres eliminar esta página?')) {{
            delete allPages[slug];
            saveData(true);
        }}
    }}
    
    function addDlLink(url = '') {{
        const c = document.getElementById('dl-links-container');
        const div = document.createElement('div');
        div.className = 'flex gap-2';
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'dl-url w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500';
        input.placeholder = 'https://mega.nz/... o https://drive.google.com/...';
        input.value = url;
        const btn = document.createElement('button');
        btn.className = 'bg-red-600 hover:bg-red-500 text-white px-3 py-2 rounded text-sm font-bold whitespace-nowrap';
        btn.innerHTML = '<i class="fas fa-trash"></i>';
        btn.onclick = function() {{ this.parentElement.remove(); }};
        div.appendChild(input);
        div.appendChild(btn);
        c.appendChild(div);
    }}
    
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
            <input type="text" class="p-link w-full bg-slate-800 rounded p-2 mb-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="ID de Plan de PayPal (Ej: P-78W24779DJ167620XNKNUHYY)" value="${{link}}">
            <div class="flex justify-between items-center mt-2">
                <label class="text-sm flex items-center gap-2 cursor-pointer"><input type="checkbox" class="p-highlight accent-cyan-500" ${{highlight ? 'checked' : ''}}> Resaltar (Más Popular)</label>
                <button onclick="this.parentElement.parentElement.remove()" class="text-red-500 text-xs hover:text-red-400"><i class="fas fa-trash mr-1"></i>Eliminar</button>
            </div>
        `;
        c.appendChild(div);
    }}
    
    async function saveData(reloadSelector = false) {{
        const slug = document.getElementById('current_slug').value || document.getElementById('page_selector').value;
        if (!slug) {{
            showToast('❌ No hay página seleccionada.');
            return;
        }}
        
        let pubsArray = [];
        document.querySelectorAll('#pubs-container > div').forEach(div => {{
            const urlInput = div.querySelector('.pub-url');
            if(urlInput && urlInput.value.trim()) {{
                pubsArray.push({{ 
                    type: div.querySelector('.pub-type').value, 
                    url: urlInput.value, 
                    desc: div.querySelector('.pub-desc').value 
                }});
            }}
        }});
        
        let plansArray = [];
        document.querySelectorAll('#plans-container > div').forEach(div => {{
            const nameInput = div.querySelector('.p-name');
            if(nameInput && nameInput.value.trim()) {{
                plansArray.push({{ 
                    name: nameInput.value, 
                    price: div.querySelector('.p-price').value, 
                    features: div.querySelector('.p-features').value, 
                    link: div.querySelector('.p-link').value, 
                    highlight: div.querySelector('.p-highlight').checked 
                }});
            }}
        }});
        
        let dlLinksArray = [];
        document.querySelectorAll('#dl-links-container > div').forEach(div => {{
            const urlInput = div.querySelector('.dl-url');
            if(urlInput && urlInput.value.trim()) {{
                dlLinksArray.push(urlInput.value.trim());
            }}
        }});
        
        allPages[slug] = {{
            page_name: document.getElementById('page_name').value,
            chatbot_id: document.getElementById('chatbot_id').value || 'gzEjAzK1VCE72hJ_hBfA4',
            hero_title: document.getElementById('hero_title').value,
            hero_subtitle: document.getElementById('hero_subtitle').value,
            hero_text: document.getElementById('hero_text').value,
            affiliate_link: document.getElementById('affiliate_link').value,
            affiliate_text: document.getElementById('affiliate_text').value,
            publications: pubsArray,
            plans: plansArray,
            social_links: {{
                facebook: document.getElementById('fb_link').value,
                whatsapp: document.getElementById('wa_link').value,
                youtube: document.getElementById('yt_link').value,
                tiktok: document.getElementById('tt_link').value,
                telegram: document.getElementById('tg_link').value,
                instagram: document.getElementById('ig_link').value
            }},
            bank_transfer_info: {{
                bank_name: document.getElementById('bt_bank_name').value,
                account_type: document.getElementById('bt_account_type').value,
                account_number: document.getElementById('bt_account_number').value,
                beneficiary: document.getElementById('bt_beneficiary').value,
                email_for_proof: document.getElementById('bt_email').value,
                whatsapp_for_proof: document.getElementById('bt_whatsapp').value
            }},
            download_links: dlLinksArray,
            download_instructions: document.getElementById('download_instructions').value
        }};
        
        try {{
            const res = await fetch('/api/save_pages', {{ 
                method: 'POST', 
                headers: {{'Content-Type': 'application/json'}}, 
                body: JSON.stringify(allPages) 
            }});
            const result = await res.json();
            showToast(result.message);
            if(reloadSelector) {{ 
                updateSelector(); 
            }}
        }} catch(e) {{
            showToast('❌ Error de conexión.');
            console.error(e);
        }}
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
            const leads = data.captured_leads || [];
            let leadsHtml = '';
            if(leads.length === 0) {{
                leadsHtml = '<p class="text-slate-500 text-sm">Aún no se han capturado correos.</p>';
            }} else {{
                leads.slice().reverse().forEach(l => {{
                    let stageText = l.follow_up_stage === 0 ? 'Email Inicial Enviado' : 
                                    l.follow_up_stage === 1 ? 'Seguimiento 1 Enviado' : 
                                    l.follow_up_stage === 2 ? 'Seguimiento 2 Enviado' : 'Embudo Finalizado';
                    leadsHtml += `<div class="bg-slate-900 p-3 rounded border border-slate-700">
                        <div class="flex justify-between">
                            <span class="text-cyan-400 font-bold text-sm">${{l.name}} - $${{l.email}}</span>
                            <span class="text-slate-500 text-xs">${{l.date.split('T')[0]}}</span>
                        </div>
                        <div class="text-slate-400 text-xs mt-1">Interés: $${{l.interaction}}</div>
                        <div class="text-emerald-400 text-xs mt-1">🤖 IA: $${{stageText}}</div>
                    </div>`;
                }});
            }}
            document.getElementById('stat_leads').innerHTML = leadsHtml;
        }} catch (e) {{ console.error(e); }}
    }}
    
    async function loadAIConfig() {{
        try {{
            const res = await fetch('/api/get_ai_config');
            const data = await res.json();
            const defaults = {{
                stage1_days: 2, stage1_subject: "🚀 {{name}}, descubre el poder de la IA Institucional con BLENIN.G.77", stage1_body: "Hola {{name}},\\n\\nGracias por tu interés en BLENIN.G.77...",
                stage2_days: 5, stage2_subject: "🔥 {{name}}, esto es lo que estás dejando atrás...", stage2_body: "Hola {{name}},\\n\\nQueríamos mostrarte lo que la comunidad...",
                stage3_days: 10, stage3_subject: "⏳ {{name}}, tu acceso VIP a BLENIN.G.77 está por expirar", stage3_body: "Hola {{name}},\\n\\nHemos notado que aún no has dado el paso..."
            }};
            const cfg = Object.keys(data).length > 0 ? data : defaults;
            document.getElementById('s1_days').value = cfg.stage1_days || 2;
            document.getElementById('s1_subject').value = cfg.stage1_subject || defaults.stage1_subject;
            document.getElementById('s1_body').value = cfg.stage1_body || defaults.stage1_body;
            document.getElementById('s2_days').value = cfg.stage2_days || 5;
            document.getElementById('s2_subject').value = cfg.stage2_subject || defaults.stage2_subject;
            document.getElementById('s2_body').value = cfg.stage2_body || defaults.stage2_body;
            document.getElementById('s3_days').value = cfg.stage3_days || 10;
            document.getElementById('s3_subject').value = cfg.stage3_subject || defaults.stage3_subject;
            document.getElementById('s3_body').value = cfg.stage3_body || defaults.stage3_body;
        }} catch(e) {{ console.error(e); }}
    }}
    
    async function saveAIConfig() {{
        const payload = {{
            stage1_days: parseInt(document.getElementById('s1_days').value),
            stage1_subject: document.getElementById('s1_subject').value,
            stage1_body: document.getElementById('s1_body').value,
            stage2_days: parseInt(document.getElementById('s2_days').value),
            stage2_subject: document.getElementById('s2_subject').value,
            stage2_body: document.getElementById('s2_body').value,
            stage3_days: parseInt(document.getElementById('s3_days').value),
            stage3_subject: document.getElementById('s3_subject').value,
            stage3_body: document.getElementById('s3_body').value
        }};
        const res = await fetch('/api/save_ai_config', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(payload) }});
        const result = await res.json();
        showToast(result.message);
    }}
    
    async function loadUpdateConfig() {{
        try {{
            const res = await fetch('/api/get_update_config');
            const data = await res.json();
            document.getElementById('upd_version').value = data.latest_version || '1.0.0';
            document.getElementById('upd_url').value = data.download_url || '';
            document.getElementById('upd_message').value = data.update_message || '';
            document.getElementById('upd_force').checked = data.force_update || false;
        }} catch(e) {{ console.error(e); }}
    }}
    
    async function saveUpdateConfig() {{
        const payload = {{
            latest_version: document.getElementById('upd_version').value,
            download_url: document.getElementById('upd_url').value,
            force_update: document.getElementById('upd_force').checked,
            update_message: document.getElementById('upd_message').value
        }};
        const res = await fetch('/api/save_update_config', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(payload) }});
        const result = await res.json();
        showToast(result.message);
    }}
    
    async function createManualLicense() {{
        const plan = document.getElementById('manual_plan').value;
        const days = document.getElementById('manual_days').value;
        const email = document.getElementById('manual_email').value;
        if(!email) {{ alert('Por favor ingresa el correo del cliente.'); return; }}
        const res = await fetch('/api/create_license', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{ plan: plan, duration_days: parseInt(days), email: email }}) }});
        const result = await res.json();
        const msgDiv = document.getElementById('manual_lic_msg');
        msgDiv.classList.remove('hidden');
        if(result.status === 'success') {{
            msgDiv.innerHTML = `✅ Licencia creada y guardada en el servidor: <br><br> <input type="text" value="${{result.key}}" readonly class="w-full bg-slate-950 text-cyan-400 p-2 rounded mt-2 cursor-pointer select-all" onclick="this.select()">`;
            document.getElementById('lic_key').value = result.key; 
        }} else {{
            msgDiv.innerText = "❌ " + (result.message || "Error al crear la licencia.");
        }}
        showToast('Proceso de licencia manual completado.');
    }}
    
    async function manageLic(activeStatus) {{
        const key = document.getElementById('lic_key').value;
        if(!key) {{ alert('Por favor ingresa una clave de licencia.'); return; }}
        const res = await fetch('/api/manage_license', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{key: key, active: activeStatus}}) }});
        const result = await res.json();
        document.getElementById('lic_msg').classList.remove('hidden');
        document.getElementById('lic_msg').innerText = result.message;
        showToast(result.message);
    }}
    
    async function resetHwid() {{
        const key = document.getElementById('lic_key').value;
        if(!key) {{ alert('Por favor ingresa una clave de licencia.'); return; }}
        const res = await fetch('/api/reset_hwid', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{key: key}}) }});
        const result = await res.json();
        document.getElementById('lic_msg').classList.remove('hidden');
        document.getElementById('lic_msg').innerText = result.message;
        showToast(result.message);
    }}
    
    async function changePassword() {{
        const current_pwd = document.getElementById('current_pwd').value;
        const new_pwd = document.getElementById('new_pwd').value;
        const confirm_pwd = document.getElementById('confirm_pwd').value;
        if(new_pwd !== confirm_pwd) {{
            const msgDiv = document.getElementById('pwd_msg');
            msgDiv.className = "mt-4 font-bold text-sm text-red-400";
            msgDiv.innerText = "❌ Las nuevas contraseñas no coinciden.";
            msgDiv.classList.remove('hidden');
            return;
        }}
        const res = await fetch('/api/change_password', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{ current_password: current_pwd, new_password: new_pwd }}) }});
        const result = await res.json();
        const msgDiv = document.getElementById('pwd_msg');
        msgDiv.className = "mt-4 font-bold text-sm " + (result.status === 'success' ? 'text-emerald-400' : 'text-red-400');
        msgDiv.innerText = result.message;
        msgDiv.classList.remove('hidden');
        showToast(result.message);
        if(result.status === 'success') {{
            document.getElementById('current_pwd').value = '';
            document.getElementById('new_pwd').value = '';
            document.getElementById('confirm_pwd').value = '';
        }}
    }}
    
    function setMktType(type) {{
        mktCurrentType = type;
        document.getElementById('mkt_selected_type').value = type;
        ['seo','tiktok','reddit'].forEach(t => {{
            const btn = document.getElementById('mkt-btn-' + t);
            if(t === type) {{
                btn.classList.remove('border-slate-700');
                btn.classList.add('border-purple-500', 'bg-purple-900/30');
            }} else {{
                btn.classList.add('border-slate-700');
                btn.classList.remove('border-purple-500', 'bg-purple-900/30');
            }}
        }});
    }}
    
    async function generateMktContent() {{
        const topic = document.getElementById('mkt_topic').value || 'automatizar trading con IA en MT5';
        const btn = document.getElementById('mkt_generate_btn');
        const resultBox = document.getElementById('mkt_result_box');
        const resultArea = document.getElementById('mkt_result');
        
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Gemini está redactando el contenido...';
        resultBox.classList.remove('hidden');
        resultArea.value = '⏳ La IA está redactando el contenido... (esto puede tardar 15-30 segundos)';
        
        try {{
            const res = await fetch('/api/generate_marketing', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{ type: mktCurrentType, topic: topic }})
            }});
            const data = await res.json();
            if(data.status === 'success') {{
                resultArea.value = data.content;
                showToast('✅ Contenido generado correctamente.');
            }} else {{
                resultArea.value = '❌ Error: ' + (data.message || 'La IA no respondió.');
                showToast('❌ Error al generar contenido.');
            }}
        }} catch(e) {{
            resultArea.value = '❌ Error de conexión con el servidor.';
            console.error(e);
            showToast('❌ Error de conexión.');
        }} finally {{
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-magic mr-2"></i> Generar Contenido con IA';
        }}
    }}
    
    function copyMktResult() {{
        const txt = document.getElementById('mkt_result');
        txt.select();
        document.execCommand('copy');
        showToast('✅ Contenido copiado al portapapeles.');
    }}
    
    function downloadMktResult() {{
        const content = document.getElementById('mkt_result').value;
        const blob = new Blob([content], {{type: 'text/plain'}});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'blenin77_marketing_' + mktCurrentType + '.txt';
        a.click();
        URL.revokeObjectURL(url);
        showToast('✅ Archivo descargado.');
    }}
    
    updateSelector();
    </script>
    </body></html>
    """

@app.post("/api/save_pages")
def api_save_pages(request: Request, data: dict):
    print("🔥 RECIBIDA PETICIÓN DE GUARDADO DE PÁGINAS...", flush=True)
    if not verify_admin(request): 
        print("❌ NO AUTORIZADO", flush=True)
        return {"message": "❌ No autorizado."}
    
    print("✅ USUARIO VERIFICADO, PROCEDIENDO A GUARDAR...", flush=True)
    try:
        if save_all_pages({"pages": data}):
            return {"message": "✅ Página guardada correctamente."}
        else:
            return {"message": "❌ Error al guardar en Supabase (Revisa los logs de Render)."}
    except Exception as e:
        print(f"🚨 EXCEPCIÓN EN api_save_pages: {e}", flush=True)
        return {"message": f"❌ Error interno del servidor: {str(e)}"}

@app.post("/api/change_password")
def api_change_password(request: Request, data: ChangePasswordData):
    global admin_password_db
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    if data.current_password != admin_password_db: return {"status": "error", "message": "❌ La contraseña actual es incorrecta."}
    if len(data.new_password) < 4: return {"status": "error", "message": "❌ La nueva contraseña debe tener al menos 4 caracteres."}
    admin_password_db = data.new_password
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
    return {"status": "success", "message": "✅ Contraseña actualizada correctamente."}

@app.get("/recuperar-clave", response_class=HTMLResponse)
def recover_page():
    return """
    <html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Recuperar Licencia - BLENIN77</title><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet"><style>body { font-family: 'Inter', sans-serif; }</style></head>
    <body class="bg-slate-900 text-slate-300 flex items-center justify-center min-h-screen"><div class="bg-slate-800 p-8 rounded-xl shadow-2xl border border-slate-700 w-full max-w-md text-center"><h1 class="text-2xl font-bold text-cyan-400 mb-2">🔑 Recuperar Licencia</h1><p class="text-slate-400 mb-6 text-sm">Ingresa el correo electrónico con el que realizaste tu compra.</p><input type="email" id="email" placeholder="tu.correo@gmail.com" class="w-full bg-slate-900 rounded p-3 mb-4 border border-slate-700 outline-none focus:border-cyan-500"><button onclick="recover()" class="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold py-3 rounded transition">Enviar mi licencia</button><div id="msg" class="mt-4 text-emerald-400 font-bold text-sm hidden"></div></div><script>function recover(){var email = document.getElementById('email').value;fetch('/api/recover_by_email', {method: 'POST',headers: {'Content-Type': 'application/json'},body: JSON.stringify({email: email})}).then(r => r.json()).then(d => {const msgDiv = document.getElementById('msg');msgDiv.innerText = d.message;msgDiv.classList.remove('hidden');});}</script></body></html>
    """

def render_landing_page(c):
    pubs_html = ""
    for p in c.get('publications', []):
        if p.get('url'):
            if p.get('type') == 'video':
                pubs_html += f"""<div class="text-center mb-12"><div class="relative aspect-video w-full max-w-2xl mx-auto shadow-2xl rounded-xl overflow-hidden border-2 border-slate-800"><iframe src="{p['url']}" class="absolute top-0 left-0 w-full h-full" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div><p class="mt-4 text-slate-400 max-w-xl mx-auto">{p.get('desc', '')}</p></div>"""
            elif p.get('type') == 'image':
                pubs_html += f"""<div class="text-center mb-12"><img src="{p['url']}" alt="Publicación" class="max-w-2xl mx-auto rounded-xl border-2 border-slate-800 shadow-xl"><p class="mt-4 text-slate-400 max-w-xl mx-auto">{p.get('desc', '')}</p></div>"""

    bt = c.get('bank_transfer_info', {})
    has_bank_info = bt.get('account_number')
    
    plans_html = ""
    paypal_scripts = ""
    for p in c.get('plans', []):
        if p.get('name'):
            highlight_classes = "lg:scale-105 border-cyan-500 shadow-cyan-500/20" if p.get('highlight') else "border-slate-800"
            badge = '<span class="absolute top-0 right-0 bg-cyan-500 text-slate-900 text-xs font-bold px-3 py-1 rounded-bl-lg">MÁS POPULAR</span>' if p.get('highlight') else ''
            features_html = p.get('features', '').replace('\n', '<br>')
            
            bank_btn_html = ""
            if has_bank_info:
                bank_btn_html = f"""<button onclick="openBankModal('{p.get('name', '')}', '{p.get('price', '')}')" class="block text-center w-full bg-slate-700 hover:bg-slate-600 text-slate-300 font-medium py-2 rounded text-sm transition mt-2"><i class="fas fa-university mr-2"></i>Pagar por Transferencia Bancaria</button>"""

            plan_link = p.get('link', '#')
            if plan_link.startswith("P-"):
                pay_btn_html = f'<div id="paypal-btn-{plan_link}" class="mt-auto"></div>'
                paypal_scripts += f"""
                <script>
                if (typeof paypal !== 'undefined') {{
                    paypal.Buttons({{
                        style: {{ shape: 'rect', color: 'blue', layout: 'vertical', label: 'subscribe' }},
                        createSubscription: function(data, actions) {{
                            return actions.subscription.create({{ plan_id: '{plan_link}' }});
                        }},
                        onApprove: function(data, actions) {{
                            alert('¡Suscripción procesada con éxito! Te enviaremos tu licencia a tu correo en un momento.');
                        }}
                    }}).render('#paypal-btn-{plan_link}');
                }}
                </script>
                """
            else:
                pay_btn_html = f'<div class="mt-auto"><a href="{plan_link}" class="block text-center w-full bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold py-3 rounded transition">Suscribirme con Tarjeta</a></div>'

            plans_html += f"""
            <div class="relative bg-slate-800 p-8 rounded-xl border {highlight_classes} transition-all duration-300 hover:-translate-y-2 hover:shadow-xl flex flex-col">
                {badge}
                <h3 class="text-xl font-bold text-white mb-2">{p.get('name', '')}</h3>
                <div class="text-4xl font-extrabold text-cyan-400 mb-4">{p.get('price', '')}<span class="text-base font-normal text-slate-500">/mes</span></div>
                <p class="text-slate-300 text-sm mb-6 flex-grow">{features_html}</p>
                {pay_btn_html}
                <div class="mt-2">{bank_btn_html}</div>
            </div>
            """

    social = c.get('social_links')
    if not isinstance(social, dict):
        social = {}
        
    social_html = ""
    if social.get('facebook'): social_html += f'<a href="{social.get("facebook")}" target="_blank" rel="noopener noreferrer" class="bg-slate-800 hover:bg-cyan-500 hover:text-slate-900 text-slate-300 p-3 rounded-full transition-all duration-300 transform hover:-translate-y-1"><i class="fab fa-facebook-f"></i></a>'
    if social.get('whatsapp'): social_html += f'<a href="{social.get("whatsapp")}" target="_blank" rel="noopener noreferrer" class="bg-slate-800 hover:bg-cyan-500 hover:text-slate-900 text-slate-300 p-3 rounded-full transition-all duration-300 transform hover:-translate-y-1"><i class="fab fa-whatsapp"></i></a>'
    if social.get('youtube'): social_html += f'<a href="{social.get("youtube")}" target="_blank" rel="noopener noreferrer" class="bg-slate-800 hover:bg-cyan-500 hover:text-slate-900 text-slate-300 p-3 rounded-full transition-all duration-300 transform hover:-translate-y-1"><i class="fab fa-youtube"></i></a>'
    if social.get('tiktok'): social_html += f'<a href="{social.get("tiktok")}" target="_blank" rel="noopener noreferrer" class="bg-slate-800 hover:bg-cyan-500 hover:text-slate-900 text-slate-300 p-3 rounded-full transition-all duration-300 transform hover:-translate-y-1"><i class="fab fa-tiktok"></i></a>'
    if social.get('telegram'): social_html += f'<a href="{social.get("telegram")}" target="_blank" rel="noopener noreferrer" class="bg-slate-800 hover:bg-cyan-500 hover:text-slate-900 text-slate-300 p-3 rounded-full transition-all duration-300 transform hover:-translate-y-1"><i class="fab fa-telegram-plane"></i></a>'
    if social.get('instagram'): social_html += f'<a href="{social.get("instagram")}" target="_blank" rel="noopener noreferrer" class="bg-slate-800 hover:bg-cyan-500 hover:text-slate-900 text-slate-300 p-3 rounded-full transition-all duration-300 transform hover:-translate-y-1"><i class="fab fa-instagram"></i></a>'
    
    if not social_html:
        social_section_html = ""
    else:
        social_section_html = f'<section class="py-12 border-t border-slate-800"><div class="container mx-auto px-6 text-center"><h3 class="text-xl font-bold text-white mb-6">Síguenos en nuestras redes</h3><div class="flex justify-center space-x-4 text-xl">{social_html}</div></div></section>'

    chatbot_id = c.get('chatbot_id', 'gzEjAzK1VCE72hJ_hBfA4')

    aff_link = c.get('affiliate_link', '')
    aff_text = c.get('affiliate_text', '🚀 Afíliate')
    aff_btn = f'<a href="{aff_link}" target="_blank" class="bg-emerald-500 hover:bg-emerald-400 text-slate-900 px-4 py-2 rounded text-sm font-bold transition">{aff_text}</a>' if aff_link else ''
    
    bank_modal_html = ""
    if has_bank_info:
        wa_link = f"https://wa.me/{bt.get('whatsapp_for_proof', '')}?text=Hola%2C%20adjunto%20el%20comprobante%20de%20pago%20para%20el%20plan%20"
        mail_link = f"mailto:{bt.get('email_for_proof', '')}?subject=Comprobante%20de%20Pago%20Plan%20"
        bank_modal_html = f"""
        <div id="bankModal" class="hidden fixed inset-0 bg-black/80 z-[100] flex items-center justify-center p-4"><div class="bg-slate-800 p-8 rounded-xl max-w-md w-full border border-slate-700 shadow-2xl relative"><button onclick="closeBankModal()" class="absolute top-4 right-4 text-slate-400 hover:text-white text-2xl">&times;</button><h3 class="text-2xl font-bold text-cyan-400 mb-2">Instrucciones de Pago</h3><p class="text-slate-400 text-sm mb-6">Estás comprando el plan: <span id="modal_plan_name" class="font-bold text-white"></span> por <span id="modal_plan_price" class="font-bold text-white"></span></p><div class="bg-slate-900 p-4 rounded-lg border border-slate-700 space-y-3 text-sm"><p><strong class="text-slate-400">Banco:</strong> <span class="text-white">{bt.get('bank_name', '')}</span></p><p><strong class="text-slate-400">Tipo de Cuenta:</strong> <span class="text-white">{bt.get('account_type', '')}</span></p><p><strong class="text-slate-400">Número de Cuenta:</strong> <span class="text-cyan-400 font-mono">{bt.get('account_number', '')}</span></p><p><strong class="text-slate-400">Beneficiario:</strong> <span class="text-white">{bt.get('beneficiary', '')}</span></p></div><div class="mt-6"><h4 class="text-white font-bold mb-2">¿Qué hacer después?</h4><p class="text-slate-400 text-sm mb-4">1. Realiza la transferencia por el monto exacto del plan.<br>2. Envía el comprobante de pago por WhatsApp o Correo.<br>3. Recibirás tu licencia de activación en cuanto confirmemos el pago.</p></div><div class="flex flex-col gap-2 mt-4"><a id="wa_send_btn" href="{wa_link}" target="_blank" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white text-center font-bold py-3 rounded transition"><i class="fab fa-whatsapp mr-2"></i> Enviar comprobante por WhatsApp</a><a id="mail_send_btn" href="{mail_link}" class="w-full bg-slate-600 hover:bg-slate-500 text-white text-center font-bold py-3 rounded transition"><i class="fas fa-envelope mr-2"></i> Enviar comprobante por Correo</a></div></div></div>
        <script>function openBankModal(planName, planPrice) {{document.getElementById('modal_plan_name').innerText = planName;document.getElementById('modal_plan_price').innerText = planPrice;let waLink = "{wa_link}" + encodeURIComponent(planName);let mailLink = "{mail_link}" + encodeURIComponent(planName);document.getElementById('wa_send_btn').href = waLink;document.getElementById('mail_send_btn').href = mailLink;document.getElementById('bankModal').classList.remove('hidden');}}function closeBankModal() {{document.getElementById('bankModal').classList.add('hidden');}}</script>
        """

    download_instructions_html = c.get('download_instructions', 'Descarga el archivo, extrae y ejecuta el instalador.').replace('\n', '<br>')
    download_links = c.get('download_links', [])
    if not download_links and c.get('download_link'): 
        download_links = [c.get('download_link')]

    download_buttons_html = ""
    if download_links:
        if len(download_links) == 1:
            download_buttons_html = f"""<a href="{download_links[0]}" target="_blank" rel="noopener noreferrer" class="bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold py-3 px-8 rounded transition transform hover:-translate-y-1 shadow-lg inline-block w-full"><i class="fas fa-download mr-2"></i> Descargar Blenin77</a>"""
        else:
            for i, link in enumerate(download_links):
                download_buttons_html += f"""<a href="{link}" target="_blank" rel="noopener noreferrer" class="bg-slate-700 hover:bg-cyan-500 hover:text-slate-900 text-slate-300 font-bold py-3 px-8 rounded transition transform hover:-translate-y-1 shadow-lg inline-block w-full mb-2"><i class="fas fa-server mr-2"></i> Servidor de Descarga {i+1}</a>"""

    display_style = "block" if download_links else "none"

    template = """<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>BLENIN.G.77 - Institutional Trading AI</title>
    <meta name="description" content="BLENIN.G.77: Sistema de Trading con IA Predictiva, Enjambre de 500 Agentes y Análisis Global en Tiempo Real para MetaTrader 5. Automatiza tus operaciones hoy.">
    <meta name="keywords" content="trading IA, bot metatrader 5, inteligencia artificial trading, EA forex, bot automático MT5, enjambre de agentes trading, blenin77">
    <meta name="robots" content="index, follow">
    <meta property="og:title" content="BLENIN.G.77 - IA Predictiva para Trading Institucional">
    <meta property="og:description" content="El mejor sistema de IA para automatizar tus operaciones en MT5. Enjambre de 500 agentes trabajando por ti.">
    <meta property="og:image" content="https://raw.githubusercontent.com/mymundodigital0-cmyk/blenin77-server/main/bienvenida_blenin.png">
    <meta property="og:url" content="https://blenin77-server.onrender.com/">
    <script src="https://cdn.tailwindcss.com"></script><script src="https://www.paypal.com/sdk/js?client-id=AYybGelHI0tT0nLaGtRnRG2sc8z4FnGqAazhHUyP9Vc_DFJAxp_psxzTqe2QBKwwSCO1UbNx2ehJ28Eg&vault=true&intent=subscription"></script><link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap" rel="stylesheet"><link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"><script>window.embeddedChatbotConfig = {chatbotId: "{CHATBOT_ID}",domain: "www.chatbase.co"}</script><script src="https://www.chatbase.co/embed.min.js" chatbotId="{CHATBOT_ID}" domain="www.chatbase.co" defer></script><style>body { font-family: 'Inter', sans-serif; background-color: #020617; }.glow { text-shadow: 0 0 10px rgba(6, 182, 212, 0.5); }.hero-bg { background: linear-gradient(to bottom, rgba(2, 6, 23, 0.8) 0%, rgba(2, 6, 23, 0.9) 100%), url('https://raw.githubusercontent.com/mymundodigital0-cmyk/blenin77-server/main/bienvenida_blenin.png') center/cover no-repeat; }.chatbase-bubble-button, iframe[src*="chatbase.co"] { z-index: 99999 !important; display: block !important; visibility: visible !important; opacity: 1 !important; pointer-events: auto !important; }.goog-te-banner-frame.skiptranslate { display: none !important; } body { top: 0px !important; }.goog-tooltip, .goog-tooltip:hover { display: none !important; }.goog-text-highlight { background-color: transparent !important; box-shadow: none !important; }#google_translate_element { position: absolute; top: -9999px; left: -9999px; opacity: 0; }.goog-te-gadget { font-size: 0 !important; }#lang-menu::-webkit-scrollbar { width: 6px; }#lang-menu::-webkit-scrollbar-track { background: #1e293b; border-radius: 10px; }#lang-menu::-webkit-scrollbar-thumb { background: #0e7490; border-radius: 10px; }</style></head>
<body class="text-slate-300">
    <nav class="bg-slate-950/80 backdrop-blur-md sticky top-0 z-50 border-b border-slate-800"><div class="container mx-auto px-6 py-4 flex justify-between items-center"><a href="/" class="text-xl font-extrabold text-cyan-400 glow">BLENIN.G.77</a><div class="hidden md:flex space-x-6 text-sm font-medium items-center"><a href="#features" class="hover:text-cyan-400 transition">Tecnología</a><a href="#videos" class="hover:text-cyan-400 transition">Galería</a><a href="#pricing" class="hover:text-cyan-400 transition">Precios</a><div class="relative inline-block text-left"><button id="lang-btn" class="inline-flex justify-center items-center gap-2 rounded-md border border-slate-700 px-3 py-1.5 bg-slate-800 text-sm font-medium text-slate-300 hover:bg-slate-700 transition"><i class="fas fa-globe text-cyan-400"></i> <span id="current-lang-name">🇪🇸 Español</span> <i class="fas fa-chevron-down text-xs"></i></button><div id="lang-menu" class="hidden absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-slate-800 ring-1 ring-black ring-opacity-5 z-50 max-h-80 overflow-y-auto"><div class="py-1"><a href="#" onclick="changeLang('es', '🇪🇸 Español'); return false;" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-slate-700 hover:text-cyan-400">🇪🇸 Español</a><a href="#" onclick="changeLang('en', '🇬🇧 English'); return false;" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-slate-700 hover:text-cyan-400">🇬🇧 English</a><a href="#" onclick="changeLang('fr', '🇫🇷 Français'); return false;" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-slate-700 hover:text-cyan-400">🇫🇷 Français</a><a href="#" onclick="changeLang('pt', '🇵🇹 Portugués'); return false;" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-slate-700 hover:text-cyan-400">🇵🇹 Portugués</a><a href="#" onclick="changeLang('ru', '🇷🇺 Русский'); return false;" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-slate-700 hover:text-cyan-400">🇷🇺 Русский</a><a href="#" onclick="changeLang('it', '🇮🇹 Italiano'); return false;" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-slate-700 hover:text-cyan-400">🇮🇹 Italiano</a><a href="#" onclick="changeLang('de', '🇩🇪 Deutsch'); return false;" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-slate-700 hover:text-cyan-400">🇩🇪 Deutsch</a><a href="#" onclick="changeLang('zh-CN', '🇨🇳 中文'); return false;" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-slate-700 hover:text-cyan-400">🇨🇳 中文</a><a href="#" onclick="changeLang('ko', '🇰🇷 한국어'); return false;" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-slate-700 hover:text-cyan-400">🇰🇷 한국어</a><a href="#" onclick="changeLang('hi', '🇮🇳 हिन्दी'); return false;" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-slate-700 hover:text-cyan-400">🇮🇳 हिन्दी</a></div></div></div></div><div class="flex gap-2 items-center">{AFF_BTN}<a href="#pricing" class="bg-cyan-500 text-slate-900 px-4 py-2 rounded text-sm font-bold hover:bg-cyan-400 transition">Comprar Ahora</a></div></nav>
    <div id="urgency-banner" class="bg-gradient-to-r from-amber-500 to-red-500 text-slate-900 text-center py-2 px-4 text-sm font-bold flex justify-center items-center gap-3"><i class="fas fa-fire animate-pulse"></i><span>OFERTA DE LANZAMIENTO: Termina en</span><span id="countdown-timer" class="font-mono bg-slate-900 text-amber-400 px-2 py-1 rounded">23:59:59</span></div>
    <script>function startCountdown() {let now = new Date();let midnight = new Date();midnight.setHours(23, 59, 59, 999);let diff = midnight - now;let hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));let minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));let seconds = Math.floor((diff % (1000 * 60)) / 1000);document.getElementById('countdown-timer').innerText = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;}setInterval(startCountdown, 1000);</script>
    <header class="relative overflow-hidden py-24 md:py-32 hero-bg"><div class="container mx-auto px-6 text-center relative z-10"><div class="inline-block bg-slate-800/50 border border-slate-700 px-4 py-1 rounded-full text-xs font-medium text-cyan-400 mb-6">🚀 SISTEMA INSTITUCIONAL ACTIVO</div><h1 class="text-4xl md:text-6xl font-extrabold text-white mb-4 glow">{HERO_TITLE}</h1><h2 class="text-lg md:text-xl text-slate-400 font-light mb-6 tracking-wider uppercase">{HERO_SUBTITLE}</h2><p class="text-md md:text-lg text-slate-300 max-w-2xl mx-auto mb-10">{HERO_TEXT}</p><div class="flex justify-center gap-4"><a href="#pricing" class="bg-cyan-500 text-slate-900 font-bold py-3 px-8 rounded hover:bg-cyan-400 transition transform hover:-translate-y-1 shadow-lg shadow-cyan-500/20">Ver Planes</a><a href="#videos" class="border border-slate-700 text-slate-300 font-bold py-3 px-8 rounded hover:bg-slate-800 transition">Ver Demo</a></div></div></header>
    <section id="features" class="py-20 container mx-auto px-6"><h2 class="text-3xl font-bold text-center text-white mb-12">Tecnología de Nivel Institucional</h2><div class="grid md:grid-cols-3 gap-8"><div class="bg-slate-900 p-8 rounded-xl border border-slate-800 hover:border-cyan-500 transition group"><div class="text-cyan-400 text-3xl mb-4 group-hover:scale-110 transition"><i class="fas fa-fish"></i></div><h3 class="text-xl font-bold text-white mb-2">Enjambre 3D</h3><p class="text-slate-400 text-sm">500 agentes virtuales simulan el futuro del mercado en milisegundos basándose en el patrón histórico del activo antes de operar.</p></div><div class="bg-slate-900 p-8 rounded-xl border border-slate-800 hover:border-cyan-500 transition group"><div class="text-cyan-400 text-3xl mb-4 group-hover:scale-110 transition"><i class="fas fa-shield-alt"></i></div><h3 class="text-xl font-bold text-white mb-2">Agente Centinela</h3><p class="text-slate-400 text-sm">Un guardaespaldas que lee Reuters, CNBC y la Fed en tiempo real. Si detecta un crash, bloquea al bot para proteger tu capital.</p></div><div class="bg-slate-900 p-8 rounded-xl border border-slate-800 hover:border-cyan-500 transition group"><div class="text-cyan-400 text-3xl mb-4 group-hover:scale-110 transition"><i class="fas fa-brain"></i></div><h3 class="text-xl font-bold text-white mb-2">Cerebro Global</h3><p class="text-slate-400 text-sm">Red neuronal descentralizada. Tu bot aprende de las operaciones exitosas y fallidas de todos los usuarios a nivel mundial.</p></div></div></section>
    <section id="videos" class="py-20 bg-slate-950"><div class="container mx-auto px-6"><h2 class="text-3xl font-bold text-center text-white mb-12">Mira al Sistema en Acción</h2>{PUBLICATIONS_HTML}</div></section>
    <section id="pricing" class="py-20 container mx-auto px-6"><h2 class="text-3xl font-bold text-center text-white mb-4">Planes de Suscripción</h2><p class="text-slate-400 text-center mb-12">Elige el plan que se adapte a tu capital y estilo de trading.</p><div class="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">{PLANS_HTML}</div></section>
    <div class="py-16 px-6 bg-slate-950"><div class="max-w-md mx-auto bg-slate-800 p-8 rounded-xl border border-slate-700 shadow-lg text-center" id="ml-form-wrapper"><h3 class="text-2xl font-bold text-white mb-2">¿Quieres ver al Bot operando en vivo?</h3><p class="text-slate-400 text-sm mb-6">Deja tu correo y te enviaremos un video de cómo el Enjambre de Agentes abre operaciones reales, además de darte acceso al sistema.</p><div class="ml-form-embedContainer ml-subscribe-form ml-subscribe-form-44360624"><div class="ml-form-align-center"><div class="ml-form-embedWrapper embedForm"><div class="ml-form-embedBody ml-form-embedBodyDefault row-form"><div class="ml-form-embedContent"><p style="color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 400; line-height: 20px; margin: 0 0 10px 0; text-align: center;">Ingresa tu correo para continuar.</p></div><form class="ml-block-form" action="https://assets.mailerlite.com/jsonp/2548287/forms/194532136823292943/subscribe" data-code="" method="post" target="_blank" onsubmit="return ml_reveal_download()"><div class="ml-form-formContent"><div class="ml-form-fieldRow ml-last-item"><div class="ml-field-group ml-field-email ml-validate-email ml-validate-required"><input aria-label="email" aria-required="true" type="email" class="form-control" data-inputmask="" name="fields[email]" placeholder="Email" autocomplete="email" style="background-color: #0f172a !important; color: #fff !important; border: 1px solid #334155 !important; border-radius: 6px !important; padding: 12px !important; width: 100% !important; margin-bottom: 10px !important;"></div></div></div><input type="hidden" name="ml-submit" value="1"><div class="ml-form-embedSubmit" style="margin-top: 0;"><button type="submit" class="primary" style="background-color: #00e5ff !important; color: #020617 !important; border-radius: 6px !important; font-weight: 700; font-family: 'Inter', sans-serif; padding: 12px !important; width: 100% !important; border: none !important; cursor: pointer;">Quiero Acceso y Descargar</button><button disabled="disabled" style="display: none;" type="button" class="loading"><div class="ml-form-embedSubmitLoad"></div><span class="sr-only">Loading...</span></button></div><input type="hidden" name="anticsrf" value="true"></form></div></div></div></div><script>function ml_webform_success_44360624() {var $ = ml_jQuery || jQuery;$('.ml-subscribe-form-44360624 .row-success').show();$('.ml-subscribe-form-44360624 .row-form').hide();}</script><script src="https://groot.mailerlite.com/js/w/webforms.min.js?v83147fa8ce2d95cb73ece7f28b469519" type="text/javascript"></script><script>fetch("https://assets.mailerlite.com/jsonp/2548287/forms/194532136823292943/takel")</script></div>
    <div id="download-box" class="max-w-md mx-auto bg-slate-800 p-8 rounded-xl border border-cyan-500 shadow-cyan-500/10 shadow-lg text-center mt-6" style="display: {DISPLAY_STYLE};"><i class="fas fa-check-circle text-emerald-400 text-4xl mb-4"></i><h4 class="text-xl font-bold text-cyan-400 mb-4">¡Listo! Aquí tienes tu descarga:</h4><div class="text-slate-300 text-sm mb-6 text-left bg-slate-900 p-4 rounded-lg border border-slate-700">{DOWNLOAD_INSTRUCTIONS_HTML}</div><div class="flex flex-col gap-3">{DOWNLOAD_BUTTONS_HTML}</div></div><script>function ml_reveal_download() {setTimeout(function() {document.getElementById('download-box').style.display = 'block';document.getElementById('ml-form-wrapper').style.display = 'none';document.getElementById('download-box').scrollIntoView({behavior: "smooth", block: "center"});}, 1000);return true;}</script></div>
    {SOCIAL_SECTION_HTML}
    <footer class="bg-slate-950 py-10 border-t border-slate-800"><div class="container mx-auto px-6 text-center"><p class="text-slate-500 text-sm mb-4 max-w-3xl mx-auto"><strong>Aviso de Riesgo:</strong> El trading de divisas y CFDs implica un riesgo sustancial y no es adecuado para todos los inversores. El rendimiento pasado no es indicativo de resultados futuros. Operar con apalancamiento puede resultar en la pérdida de su capital.</p><p class="text-slate-600 text-xs">&copy; 2024 BLENIN.G.77 THE BEST FUTURE FOR YOU. Creado por Lenin Benitez.</p></div></footer>
    {BANK_MODAL_HTML}
    <div id="google_translate_element"></div><script type="text/javascript">function googleTranslateElementInit() { new google.translate.TranslateElement({pageLanguage: 'es', includedLanguages: 'en,fr,pt,ru,it,de,zh-CN,ko,hi', layout: google.translate.TranslateElement.InlineLayout.SIMPLE, autoDisplay: false}, 'google_translate_element'); }</script><script type="text/javascript" src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>
    <script>const langBtn = document.getElementById('lang-btn');const langMenu = document.getElementById('lang-menu');langBtn.addEventListener('click', (e) => { e.stopPropagation(); langMenu.classList.toggle('hidden'); });window.addEventListener('click', (e) => { if (!langMenu.contains(e.target) && !langBtn.contains(e.target)) { langMenu.classList.add('hidden'); } });function changeLang(langCode, langName) {document.getElementById('current-lang-name').innerText = langName;langMenu.classList.add('hidden');var date = new Date(); date.setTime(date.getTime() + (365 * 24 * 60 * 60 * 1000)); var expires = "; expires=" + date.toUTCString();var hostname = window.location.hostname;if (langCode === 'es') {document.cookie = "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/";document.cookie = "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=" + hostname;document.cookie = "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=." + hostname;} else {var cookieValue = "/es/" + langCode;document.cookie = "googtrans=" + cookieValue + expires + "; path=/";document.cookie = "googtrans=" + cookieValue + expires + "; path=/; domain=" + hostname;document.cookie = "googtrans=" + cookieValue + expires + "; path=/; domain=." + hostname;}window.location.reload();}window.onload = function() {var match = document.cookie.match(/googtrans=\/es\/([a-zA-Z\-]+)/);if (match && match[1]) {var langMap = { 'en': '🇬🇧 English', 'fr': '🇫🇷 Français', 'pt': '🇵🇹 Portugués', 'ru': '🇷🇺 Русский', 'it': '🇮🇹 Italiano', 'de': '🇩🇪 Deutsch', 'zh-CN': '🇨🇳 中文', 'ko': '🇰🇷 한국어', 'hi': '🇮🇳 हिन्दी' };if (langMap[match[1]]) document.getElementById('current-lang-name').innerText = langMap[match[1]];}};</script>
    <script>fetch('/api/track_view', { method: 'POST' });</script>
    <div id="social-proof-toast" class="fixed bottom-5 left-5 bg-slate-800 border border-cyan-500 text-slate-300 p-4 rounded-lg shadow-2xl flex items-center gap-3 transition-all duration-500 opacity-0 translate-y-10 z-[9998] max-w-xs"><i class="fas fa-check-circle text-cyan-400 text-2xl"></i><div><p id="sp-name" class="font-bold text-white text-sm">Carlos de México</p><p id="sp-action" class="text-xs text-slate-400">Acaba de adquirir el Plan Oro</p></div></div>
    <script>function showSocialProof() {const names = ["Carlos M.", "Ana G.", "John D.", "María F.", "Alex R.", "Sofía L.", "David P.", "Elena V."];const countries = ["México", "España", "Argentina", "Colombia", "Estados Unidos", "Chile", "Perú", "Ecuador"];const actions = ["Acaba de adquirir el Plan Oro", "Acaba de adquirir el Plan Plata", "Está viendo una demostración en vivo", "Solicitó prueba gratuita de 30 días"];const toast = document.getElementById('social-proof-toast');document.getElementById('sp-name').innerText = `${names[Math.floor(Math.random()*names.length)]} de ${countries[Math.floor(Math.random()*countries.length)]}`;document.getElementById('sp-action').innerText = actions[Math.floor(Math.random()*actions.length)];toast.classList.remove('opacity-0', 'translate-y-10');setTimeout(() => toast.classList.add('opacity-0', 'translate-y-10'), 5000);}setTimeout(showSocialProof, 5000);setInterval(showSocialProof, Math.floor(Math.random() * (25000 - 15000 + 1)) + 15000);</script>
    <div id="exit-modal" class="hidden fixed inset-0 bg-black/90 z-[9999] flex items-center justify-center p-4"><div class="bg-slate-800 p-8 rounded-xl border border-cyan-500 max-w-md w-full text-center relative"><button onclick="document.getElementById('exit-modal').classList.add('hidden')" class="absolute top-3 right-4 text-slate-500 hover:text-white text-2xl">&times;</button><i class="fas fa-gift text-cyan-400 text-5xl mb-4"></i><h3 class="text-2xl font-bold text-white mb-2">¡Espera! No te vayas sin tu regalo</h3><p class="text-slate-400 mb-6 text-sm">Suscríbete ahora y recibe un <strong class="text-cyan-400">Ebook Gratuito</strong> además de un descuento del 10% en tu primer mes.</p><input type="text" id="exit_name_input" placeholder="Tu Nombre" class="w-full bg-slate-900 rounded p-3 mb-3 border border-slate-700 text-white"><input type="email" id="exit_email_input" placeholder="Tu mejor correo" class="w-full bg-slate-900 rounded p-3 mb-4 border border-slate-700 text-white"><button onclick="submitLead('Modal de Abandono')" class="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold py-3 rounded transition">Quiero mi Descuento</button></div></div>
    <script>document.addEventListener('mouseleave', function(e) {if (e.clientY < 0 && !localStorage.getItem('exit_modal_shown')) {document.getElementById('exit-modal').classList.remove('hidden');localStorage.setItem('exit_modal_shown', 'true');}});</script>
    <div id="lead-capture-widget" class="fixed bottom-5 right-5 bg-slate-800 p-6 rounded-xl border border-cyan-500 shadow-2xl w-80 z-[9998] transition-all duration-500 translate-y-[150%] hidden"><button onclick="closeLeadWidget()" class="absolute top-2 right-3 text-slate-500 hover:text-white text-xl">&times;</button><div class="text-center mb-4"><i class="fas fa-robot text-cyan-400 text-3xl mb-2"></i><h4 class="text-white font-bold text-lg">¿Te gusta lo que ves?</h4><p class="text-slate-400 text-sm">Déjanos tu nombre y correo. Nuestra IA te enviará un video privado de cómo opera + un descuento.</p></div><input type="text" id="lead_name_input" placeholder="Tu Nombre" class="w-full bg-slate-900 rounded p-2 mb-3 border border-slate-700 text-white outline-none focus:border-cyan-500"><input type="email" id="lead_email_input" placeholder="tu.correo@gmail.com" class="w-full bg-slate-900 rounded p-2 mb-3 border border-slate-700 text-white outline-none focus:border-cyan-500"><button onclick="submitLead('Widget Flotante')" class="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold py-2 rounded transition">Quiero el Video y Descuento</button><div id="lead_thanks" class="hidden text-center text-emerald-400 text-sm font-bold mt-4"><i class="fas fa-check-circle"></i> ¡Revisa tu correo en 2 minutos!</div></div>
    <script>let leadTriggered = false;function showLeadWidget(interactionType) {if (leadTriggered || localStorage.getItem('lead_captured')) return;const widget = document.getElementById('lead-capture-widget');widget.classList.remove('hidden');setTimeout(() => widget.classList.remove('translate-y-[150%]'), 50);leadTriggered = true;widget.dataset.interaction = interactionType;}function closeLeadWidget() {const widget = document.getElementById('lead-capture-widget');widget.classList.add('translate-y-[150%]');setTimeout(() => widget.classList.add('hidden'), 500);setTimeout(() => { leadTriggered = false; }, 3600000);}async function submitLead(source) {let email = '';let name = '';if(source === 'Modal de Abandono') {name = document.getElementById('exit_name_input').value || 'Usuario';email = document.getElementById('exit_email_input').value;} else {name = document.getElementById('lead_name_input').value || 'Usuario';email = document.getElementById('lead_email_input').value;}if (!email || !email.includes('@')) {alert('Por favor ingresa un correo válido.');return;}let interaction = source;if(source !== 'Modal de Abandono') {interaction = document.getElementById('lead-capture-widget').dataset.interaction || source;}try {await fetch('/api/capture_lead', {method: 'POST',headers: { 'Content-Type': 'application/json' },body: JSON.stringify({ name: name, email: email, interaction: interaction })});if(source === 'Modal de Abandono') {document.getElementById('exit-modal').classList.add('hidden');} else {document.getElementById('lead_name_input').style.display = 'none';document.getElementById('lead_email_input').style.display = 'none';document.querySelector('#lead-capture-widget button[onclick^="submitLead"]').style.display = 'none';document.getElementById('lead_thanks').classList.remove('hidden');}localStorage.setItem('lead_captured', 'true');setTimeout(closeLeadWidget, 4000);} catch (e) {alert('Hubo un error, intenta de nuevo.');}}document.querySelectorAll('a[href="#videos"]').forEach(btn => {btn.addEventListener('click', () => {setTimeout(() => showLeadWidget('Clic en Ver Demo'), 3000);});});const pricingSection = document.getElementById('pricing');if (pricingSection) {pricingSection.addEventListener('mouseenter', () => {setTimeout(() => showLeadWidget('Mirando los Planes'), 5000);});}setTimeout(() => {if (!leadTriggered && !localStorage.getItem('lead_captured')) showLeadWidget('Lectura profunda (40s)');}, 40000);</script>
    {PAYPAL_SCRIPTS}
</body></html>"""
    return template.replace("{CHATBOT_ID}", chatbot_id)\
                   .replace("{AFF_BTN}", aff_btn)\
                   .replace("{HERO_TITLE}", c.get('hero_title', ''))\
                   .replace("{HERO_SUBTITLE}", c.get('hero_subtitle', ''))\
                   .replace("{HERO_TEXT}", c.get('hero_text', ''))\
                   .replace("{PUBLICATIONS_HTML}", pubs_html)\
                   .replace("{PLANS_HTML}", plans_html)\
                   .replace("{SOCIAL_SECTION_HTML}", social_section_html)\
                   .replace("{BANK_MODAL_HTML}", bank_modal_html)\
                   .replace("{DISPLAY_STYLE}", display_style)\
                   .replace("{DOWNLOAD_BUTTONS_HTML}", download_buttons_html)\
                   .replace("{DOWNLOAD_INSTRUCTIONS_HTML}", download_instructions_html)\
                   .replace("{PAYPAL_SCRIPTS}", paypal_scripts)

# ==========================================
# 🔍 VERIFICACIÓN DE GOOGLE SEARCH CONSOLE
# ==========================================
@app.get("/google80facc731870c13b.html", response_class=PlainTextResponse)
def google_verification():
    return "google-site-verification: google80facc731870c13b.html"

# ==========================================
# 📝 BLOG SEO AUTOMÁTICO (IA GEMINI)
# ==========================================
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
# 🌍 RUTA PRINCIPAL CON GEO-TARGETING
# ==========================================
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
    if user_country_name in latam_countries:
        c['hero_text'] = f"🔥 ¡Descuento especial activado para {user_country_name}! " + c.get('hero_text', 'Protege tu capital con IA.')
    elif user_country_name != "Internacional":
        c['hero_text'] = f"🚀 Usuarios de {user_country_name} ya están multiplicando su capital. " + c.get('hero_text', '')
        
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
class LeadCapture(BaseModel): 
    name: str = "Usuario"
    email: str
    interaction: str = "Visualizó demo"
class UserRiskReport(BaseModel):
    license_key: str
    consecutive_losses: int
    current_drawdown_pct: float
class MarketingRequest(BaseModel):
    type: str = "seo"
    topic: str = "automatizar trading con IA"

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
def get_ai_config():
    if not ai_agent_config or "stage1_subject" not in ai_agent_config:
        return get_default_ai_config()
    return ai_agent_config

@app.post("/api/save_ai_config")
def save_ai_config(request: Request, data: dict):
    global ai_agent_config
    if not verify_admin(request): return {"status": "error", "message": "❌ No autorizado."}
    ai_agent_config = data
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
    return {"status": "success", "message": "✅ Configuración del Agente IA guardada correctamente."}

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
        if datetime.now() > expires: return {"valid": False, "message": "⏳ Prueba expirada."}
        return {"valid": True, "days_left": (expires - datetime.now()).days, "plan": "BRONCE"}
    trials_db[data.hwid] = {"expires": (datetime.now() + timedelta(days=30)).isoformat()}
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
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
    if key not in licenses_db: return {"status": "error", "message": "❌ Licencia no encontrada."}
    licenses_db[key]["active"] = data.active
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
    status = "activada" if data.active else "suspendida"
    return {"status": "success", "message": f"✅ Licencia {key} {status} correctamente."}

@app.post("/api/reset_hwid")
def reset_hwid(request: Request, data: ResetHWID):
    if not verify_admin(request): return {"status": "error", "message": "❌ No autorizado."}
    global licenses_db
    key = data.key.upper().strip()
    if key not in licenses_db: return {"status": "error", "message": "❌ Licencia no encontrada."}
    licenses_db[key]["hwid"] = None
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
    return {"status": "success", "message": f"✅ HWID reseteado para {key}."}

# ==========================================
# 🧠 ENDPOINT DE MARKETING CON GEMINI
# ==========================================
@app.post("/api/generate_marketing")
def generate_marketing_content(request: Request, data: MarketingRequest):
    if not verify_admin(request):
        return {"status": "error", "message": "❌ No autorizado."}

    topic = (data.topic or "").strip() or "automatizar trading con IA en MT5"
    base_url = "https://blenin77-server.onrender.com/#pricing"

    if data.type == "seo":
        prompt = f"""Eres un experto en SEO y copywriting. Escribe un artículo de blog de unas 600-800 palabras optimizado para Google sobre el tema: "{topic}".

Requisitos:
- Empieza con un título H1 (# Título) atractivo que incluya la palabra clave.
- Incluye 3-5 subtítulos H2 (## Subtítulo).
- Menciona de forma natural el bot BLENIN.G.77 destacando: IA Predictiva, Enjambre de 500 agentes, Modo Híbrido MT5 + Noticias macroeconómicas.
- Usa **negritas** en conceptos clave.
- Termina con un CTA hacia: {base_url}
- Formato Markdown.

Responde SOLO con el artículo, sin comentarios extra."""
    
    elif data.type == "tiktok":
        prompt = f"""Eres un guionista viral de TikTok/Reels experto en trading. Crea un guion de 45-60 segundos sobre: "{topic}".

Formato estricto:
[HOOK 0-3s]: Frase impactante que detenga el scroll.
[DESARROLLO 3-45s]: 3 puntos clave en lenguaje simple y dinámico.
[CTA 45-60s]: Llamada a la acción hacia el bot BLENIN.G.77 ({base_url}).

Incluye sugerencias de texto en pantalla y música recomendada.
Responde SOLO con el guion, sin comentarios extra."""
    
    else:  # reddit
        prompt = f"""Eres un usuario real de Reddit (r/Forex, r/Trading). Escribe un post genuino y NO spammy sobre: "{topic}".

Requisitos:
- Tono casual, como un trader compartiendo su experiencia.
- Menciona BLENIN.G.77 de forma natural, como si lo hubieras descubierto y probado.
- No uses lenguaje comercial ni mayúsculas excesivas.
- Título atractivo (máx 100 caracteres).
- Cuerpo de 200-300 palabras.
- Al final, enlace sutil a {base_url}

Responde SOLO con el post, sin comentarios extra."""

    content = generate_dynamic_content_with_llama(prompt, max_tokens=2000)
    if not content:
        return {
            "status": "error",
            "message": "La IA no respondió. Revisa los logs de Render o si la API Key de Gemini es correcta."
        }

    return {"status": "success", "content": content, "type": data.type}

# ==========================================
# 🛡️ ALERTA DE RIESGO DEL BOT (ANTI-BAJAS)
# ==========================================
@app.post("/api/report_user_risk")
def report_user_risk(data: UserRiskReport):
    global licenses_db
    updated = False
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

# ==========================================
# 🔥 WEBHOOK DE HOTMART
# ==========================================
@app.post("/api/hotmart_webhook")
def hotmart_webhook(request: Request):
    try:
        data = request.json()
        if data.get("event") == "PURCHASE_APPROVED" or data.get("event_type") == "PURCHASE_APPROVED":
            buyer_data = data.get("data", {}).get("buyer", {})
            product_data = data.get("data", {}).get("product", {})
            
            email = buyer_data.get("email")
            if not email:
                email = data.get("data", {}).get("purchase", {}).get("buyer", {}).get("email")
                
            product_name = (product_data.get("name") or "BRONCE").upper()
            
            if "ORO" in product_name: plan_upper = "ORO"
            elif "PLATA" in product_name: plan_upper = "PLATA"
            else: plan_upper = "BRONCE"
            
            global licenses_db
            key = generate_license_key(plan_upper)
            licenses_db[key] = {
                "hwid": None, 
                "expires": (datetime.now() + timedelta(days=30)).isoformat(), 
                "active": True, 
                "plan": plan_upper, 
                "email": email.lower()
            }
            save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
            
            client_subject = "✅ Pago Confirmado - Aquí tienes tu Licencia BLENIN77"
            client_body = f"¡Gracias por tu compra!\n\nTu pago ha sido confirmado exitosamente.\n\nAquí tienes tu clave de licencia:\n{key}\n\nPlan: {plan_upper}\nDuración: 30 días\n\nPara descargar el sistema, ingresa a: https://blenin77-server.onrender.com/\n\nSaludos,\nEquipo BLENIN77."
            send_email(email, client_subject, client_body)
            
            admin_subject = f"💰 ¡Nueva Venta en Hotmart! Plan {plan_upper}"
            admin_body = f"Se ha procesado una venta en Hotmart.\n\nCliente: {email}\nPlan: {plan_upper}\nLicencia generada: {key}"
            send_email(SMTP_EMAIL, admin_subject, admin_body)
            
            return {"status": "success", "message": "Licencia generada por Hotmart."}
        return {"status": "ignored", "message": "Evento no es de compra aprobada."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==========================================
# 🔗 WEBHOOK DE MAKE.COM
# ==========================================
class MakeWebhookData(BaseModel):
    email: str
    plan: str
    duration_days: int = 30
    secret_token: str

MAKE_WEBHOOK_TOKEN = "blenin_secret_token_2024"

@app.post("/api/make_payment_webhook")
def make_payment_webhook(data: MakeWebhookData):
    if data.secret_token != MAKE_WEBHOOK_TOKEN:
        raise HTTPException(status_code=403, detail="Acceso denegado.")
    try:
        global licenses_db
        plan_upper = data.plan.upper()
        if "ORO" in plan_upper: plan_upper = "ORO"
        elif "PLATA" in plan_upper: plan_upper = "PLATA"
        else: plan_upper = "BRONCE"
        
        key = generate_license_key(plan_upper)
        licenses_db[key] = {
            "hwid": None, 
            "expires": (datetime.now() + timedelta(days=data.duration_days)).isoformat(), 
            "active": True, 
            "plan": plan_upper, 
            "email": data.email.lower()
        }
        save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
        
        client_subject = "✅ Pago Confirmado - Aquí tienes tu Licencia BLENIN77"
        client_body = f"¡Gracias por tu compra!\n\nTu pago ha sido confirmado exitosamente.\n\nAquí tienes tu clave de licencia:\n{key}\n\nPlan: {plan_upper}\nDuración: {data.duration_days} días\n\nPara descargar el sistema, ingresa a: https://blenin77-server.onrender.com/\n\nSaludos,\nEquipo BLENIN77."
        send_email(data.email, client_subject, client_body)
        
        admin_subject = f"💰 ¡Nueva Venta Automática! Plan {plan_upper}"
        admin_body = f"Se ha procesado un pago automáticamente a través de PayPal.\n\nCliente: {data.email}\nPlan: {plan_upper}\nLicencia generada: {key}"
        send_email(SMTP_EMAIL, admin_subject, admin_body)
        
        return {"status": "success", "message": "Licencia generada y enviada por correo."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==========================================
# 📧 CAPTURA DE LEADS DINÁMICA (IA GEMINI)
# ==========================================
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
        
        if dynamic_body:
            client_body = dynamic_body
        else:
            client_body = f"Hola {lead.name},\n\nGracias por tu interés en BLENIN.G.77. Saludos,\nEquipo BLENIN77."
            
        send_email(lead.email, f"🚀 ¡Bienvenido {lead.name}! Tu acceso a BLENIN.G.77", client_body)
        send_email(SMTP_EMAIL, f"🔥 Nuevo Lead: {lead.name}", f"Nombre: {lead.name}\nCorreo: {lead.email}\nInteracción: {lead.interaction}")
        return {"status": "success", "message": "Información enviada."}
    except Exception as e: return {"status": "error", "message": str(e)}

# ==========================================
# 🤖 AGENTE IA DE SEGUIMIENTO AUTOMÁTICO
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
                lead["follow_up_stage"] = 1
                lead["last_email_sent"] = now.isoformat()
                leads_updated = True

        elif stage == 1 and days_since_last >= int(ai_agent_config.get("stage2_days", 5)):
            subject = ai_agent_config.get("stage2_subject", "").replace("{name}", lead["name"])
            body = ai_agent_config.get("stage2_body", "").replace("{name}", lead["name"])
            if send_email(lead["email"], subject, body):
                lead["follow_up_stage"] = 2
                lead["last_email_sent"] = now.isoformat()
                leads_updated = True

        elif stage == 2 and days_since_last >= int(ai_agent_config.get("stage3_days", 10)):
            subject = ai_agent_config.get("stage3_subject", "").replace("{name}", lead["name"])
            body = ai_agent_config.get("stage3_body", "").replace("{name}", lead["name"])
            if send_email(lead["email"], subject, body):
                lead["follow_up_stage"] = 3
                lead["last_email_sent"] = now.isoformat()
                leads_updated = True

    if leads_updated:
        save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)

# ==========================================
# 🎁 AGENTE DE RETENCIÓN AUTOMÁTICO
# ==========================================
def ai_retention_agent():
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
                    email_body = f"Hola,\n\nExtrañamos tenerte en la familia BLENIN77.\n\nMientras no estuviste, nuestra IA ha estado operando con excelentes resultados:\n{win_stats_text}\n\nQueremos que vuelvas. Usa el código VOLVER30 al reactivar tu plan y obtén un 30% de descuento.\n\n👉 https://blenin77-server.onrender.com/#pricing"
                send_email(email, "🎁 Te extrañamos en BLENIN77 - Tenemos un regalo para ti", email_body)
                info["retention_email_sent"] = True
                updated = True
    if updated:
        save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)

# ==========================================
# 🚀 INICIALIZACIÓN DE AGENTES AUTOMÁTICOS
# ==========================================
scheduler = BackgroundScheduler()
scheduler.add_job(ai_follow_up_agent, 'interval', hours=1)
scheduler.add_job(ai_retention_agent, 'interval', hours=24)
scheduler.start()
