from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional
import random, string, smtplib, os, requests, json, re
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
                    credentials: 'same-origin',
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
# 🧠 INTELIGENCIA ARTIFICIAL (GOOGLE GEMINI API)
# ==========================================
def generate_dynamic_content_with_llama(prompt, max_tokens=800):
    gemini_api_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_api_key:
        print("❌ ERROR: Falta la variable de entorno GEMINI_API_KEY en Render.", flush=True)
        return None
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={gemini_api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.7}
        }
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            return response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        else:
            print(f"❌ ERROR EN API DE GEMINI: {response.text}", flush=True)
            return None
    except Exception as e:
        print(f"❌ EXCEPCIÓN CONECTANDO A GEMINI: {e}", flush=True)
        return None

# ==========================================
# 🧠 SISTEMA DE BASE DE DATOS (SUPABASE)
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
        "stage3_body": "Hola {name},\n\nHemos notado que aún no has dado el paso definitivo para automatizar tu trading con BLENIN.G.77. Entendemos que dar el control a una Inteligencia Artificial puede ser un gran paso.\n\nPor eso, como último intento de ayudarte a dar el salto institucional, hemos habilitado un descuento especial del 10% si adquieres cualquier plan en las próximas 48 horas.\n\nUsa el siguiente código al momento de tu transferencia o responde a este correo para activarlo:\n🎁 Código de descuento: BLENIN10\n\nNo dejes que la volatilidad te toma por sorpresa. Protege tu capital y maximiza tus oportunidades hoy.\n\nUn saludo institucional,\nEquipo de BLENIN.G.77 Trading Systems.\nhttps://blenin77-server.onrender.com/#pricing"
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
                if not res.data: print(f"🚨 ALERTA: Supabase no devolvió datos al guardar {key} (¿RLS activo o falta UNIQUE?)", flush=True)
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
        response = supabase.table("app_data").select("value").eq("key", "pages").execute()
        if response.data:
            data = response.data[0]["value"]
            if "hero_title" in data and "pages" not in data:
                new_data = {"pages": {"main": data}}
                save_all_pages(new_data)
                return new_data
            return data
        else:
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
            
        res = supabase.table("app_data").upsert({"key": "pages", "value": data}, on_conflict="key").execute()
        
        if hasattr(res, 'error') and res.error:
            print(f"🚨 ERROR EXPLÍCITO DE SUPABASE: {res.error}", flush=True)
            return False
        if not hasattr(res, 'data') or res.data is None or len(res.data) == 0:
            print("🚨 ERROR SILENCIOSO: Supabase no devolvió datos. Revisa si RLS está desactivado o si falta UNIQUE en 'key'.", flush=True)
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
    pages_json = json.dumps(pages_dict, ensure_ascii=False).replace('</', '<\\/')
    
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
            <button onclick="showTab('marketing')" id="tab-marketing" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">🧠 Marketing IA</button>
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
        <div id="content-marketing" class="hidden space-y-6">
            <div class="bg-slate-800 p-6 rounded-xl border border-purple-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">🧠 Generador de Tráfico y Leads con IA</h3>
                <p class="text-sm text-slate-400 mb-4">Elige qué tipo de contenido quieres que la IA (Google Gemini) cree para atraer clientes a tu web.</p>
                
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <button onclick="generateMarketing('seo_blog')" class="bg-purple-600 hover:bg-purple-500 text-white p-4 rounded text-sm font-bold transition"><i class="fas fa-blog mr-2"></i>Artículo SEO (Google)</button>
                    <button onclick="generateMarketing('tiktok_script')" class="bg-pink-600 hover:bg-pink-500 text-white p-4 rounded text-sm font-bold transition"><i class="fab fa-tiktok mr-2"></i>Guion Viral (TikTok/Reels)</button>
                    <button onclick="generateMarketing('forum_post')" class="bg-blue-600 hover:bg-blue-500 text-white p-4 rounded text-sm font-bold transition"><i class="fab fa-reddit mr-2"></i>Post para Foros (Reddit)</button>
                </div>
                
                <div id="marketing_output" class="bg-slate-900 p-4 rounded border border-slate-700 text-slate-300 text-sm whitespace-pre-wrap min-h-[200px]">
                    El contenido generado por la IA aparecerá aquí...
                </div>
                <button onclick="copyMarketing()" class="mt-4 bg-cyan-500 hover:bg-cyan-400 text-slate-900 px-4 py-2 rounded text-sm font-bold transition"><i class="fas fa-copy mr-2"></i>Copiar Contenido</button>
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
                        <input type="password" id="new_pwd" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="•••••••">
                    </div>
                    <div>
                        <label class="text-sm text-slate-400">Repetir Nueva Contraseña</label>
                        <input type="password" id="confirm_pwd" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="•••••••">
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
    <script id="pages-data" type="application/json">{pages_json}</script>
    <script>
    const allPages = JSON.parse(document.getElementById('pages-data').textContent);
    let currentMarketingText = "";
    
    function showTab(tabId) {{
        ['pages', 'stats', 'ai', 'lic', 'updates', 'marketing', 'settings'].forEach(id => {{
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
                credentials: 'same-origin', 
                headers: {{'Content-Type': 'application/json'}}, 
                body: JSON.stringify(allPages) 
            }});
            const result = await res.json();
            showToast(result.message);
            if (result.status === 'error') {{
                console.error('Error guardando:', result);
                return;
            }}
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
            const res = await fetch('/api/get_stats', {{ credentials: 'same-origin' }});
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
            const res = await fetch('/api/get_ai_config', {{ credentials: 'same-origin' }});
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
        const res = await fetch('/api/save_ai_config', {{ method: 'POST', credentials: 'same-origin', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(payload) }});
        const result = await res.json();
        showToast(result.message);
    }}
    
    async function loadUpdateConfig() {{
        try {{
            const res = await fetch('/api/get_update_config', {{ credentials: 'same-origin' }});
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
        const res = await fetch('/api/save_update_config', {{ method: 'POST', credentials: 'same-origin', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(payload) }});
        const result = await res.json();
        showToast(result.message);
    }}
    async function generateMarketing(type) {{
        const outputDiv = document.getElementById('marketing_output');
        outputDiv.innerText = "🧠 La IA está pensando y redactando el contenido... (Esto puede tardar 15-30 segundos)";
        const res = await fetch('/api/generate_marketing', {{
            method: 'POST',

