from fastapi import FastAPI, Request, Response, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional, List
import random, string, smtplib, os, requests, json, re, hashlib, time
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

# Tokens de acceso a página de descarga (generados tras capturar email)
download_access_tokens = {}  # {token: {"email": ..., "name": ..., "expires": timestamp}}

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

def get_default_downloads():
    """Configuración por defecto del sistema de descargas multi-OS"""
    return {
        "page_title": "Centro de Descargas - BLENIN.G.77",
        "page_subtitle": "Descarga la versión más reciente de tu sistema para tu plataforma favorita",
        "instructions": "1. Selecciona tu sistema operativo\n2. Descarga el archivo correspondiente\n3. Extrae el contenido\n4. Ejecuta el instalador\n5. Ingresa tu licencia al abrir el sistema",
        "systems": [
            {
                "id": "sys_windows_v1",
                "name": "BLENIN.G.77 Trading System",
                "version": "1.0.0",
                "os": "windows",
                "description": "Versión completa para Windows con IA Predictiva, Enjambre de 500 Agentes y Modo Híbrido. Compatible con Windows 10/11 (64 bits).",
                "links": [
                    {"label": "Servidor 1 (Mega)", "url": "https://mega.nz/file/tu_enlace_windows_1"},
                    {"label": "Servidor 2 (Drive)", "url": "https://drive.google.com/tu_enlace_windows_2"}
                ],
                "active": True
            },
            {
                "id": "sys_linux_v1",
                "name": "BLENIN.G.77 Trading System",
                "version": "1.0.0",
                "os": "linux",
                "description": "Versión para distribuciones Linux (Ubuntu 20.04+, Debian, Fedora). Incluye soporte para Wine y MT5 nativo vía API.",
                "links": [
                    {"label": "Servidor 1 (Mega)", "url": "https://mega.nz/file/tu_enlace_linux_1"}
                ],
                "active": True
            },
            {
                "id": "sys_android_v1",
                "name": "BLENIN.G.77 Mobile",
                "version": "1.0.0",
                "os": "android",
                "description": "Aplicación móvil para Android 8.0+. Monitorea tus operaciones y recibe alertas en tiempo real.",
                "links": [
                    {"label": "APK Directo", "url": "https://mega.nz/file/tu_enlace_android_apk"}
                ],
                "active": True
            },
            {
                "id": "sys_ios_v1",
                "name": "BLENIN.G.77 Mobile",
                "version": "1.0.0",
                "os": "ios",
                "description": "Aplicación para iOS 13+. Instalación vía TestFlight. Monitoreo y notificaciones push.",
                "links": [
                    {"label": "TestFlight", "url": "https://testflight.apple.com/tu_enlace"}
                ],
                "active": True
            },
            {
                "id": "sys_macos_v1",
                "name": "BLENIN.G.77 Trading System",
                "version": "1.0.0",
                "os": "macos",
                "description": "Versión nativa para macOS (Intel y Apple Silicon). Compatible con macOS 11 Big Sur o superior.",
                "links": [
                    {"label": "Servidor 1 (Mega)", "url": "https://mega.nz/file/tu_enlace_macos_1"}
                ],
                "active": True
            }
        ]
    }

# Mapeo de iconos y colores por sistema operativo
OS_META = {
    "windows": {"icon": "fab fa-windows", "color": "from-blue-500 to-cyan-600", "name": "Windows"},
    "linux": {"icon": "fab fa-linux", "color": "from-amber-500 to-orange-600", "name": "Linux"},
    "android": {"icon": "fab fa-android", "color": "from-green-500 to-emerald-600", "name": "Android"},
    "ios": {"icon": "fab fa-apple", "color": "from-slate-400 to-slate-600", "name": "iOS"},
    "macos": {"icon": "fab fa-apple", "color": "from-slate-500 to-slate-700", "name": "macOS"},
    "other": {"icon": "fas fa-desktop", "color": "from-purple-500 to-pink-600", "name": "Otro"}
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
        dl_cfg = data.get("downloads_config", get_default_downloads())
        
        return data.get("licenses_db", {}), data.get("trials_db", {}), data.get("stats_db", {"views": 0, "countries": {}}), pwd, ai_cfg, upd_cfg, dl_cfg
    except Exception as e:
        print(f"Error cargando DBs de Supabase: {e}")
        return {}, {}, {"views": 0, "countries": {}}, os.environ.get("ADMIN_PASSWORD", "cambiar_esta_clave_123"), get_default_ai_config(), get_default_update_config(), get_default_downloads()

def save_dbs(lic, trials, stats, pwd=None, ai_cfg=None, upd_cfg=None, dl_cfg=None):
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
        if dl_cfg: upsert_data("downloads_config", dl_cfg)
    except Exception as e:
        print(f"Error general guardando DBs en Supabase: {e}", flush=True)

licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config, downloads_config = load_dbs()

if not ai_agent_config or "stage1_subject" not in ai_agent_config:
    ai_agent_config = get_default_ai_config()
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config, downloads_config)

if not licenses_db:
    licenses_db = {
        "BLENIN-TEST-ORO": {"hwid": None, "expires": "2026-09-15T00:00:00", "active": True, "plan": "ORO", "email": "test-oro@blenin77.com"},
        "BLENIN-TEST-PLATA": {"hwid": None, "expires": "2026-09-15T00:00:00", "active": True, "plan": "PLATA", "email": "test-plata@blenin77.com"},
        "BLENIN-TEST-BRONCE": {"hwid": None, "expires": "2026-09-15T00:00:00", "active": True, "plan": "BRONCE", "email": "test-bronce@blenin77.com"}
    }
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config, downloads_config)

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
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config, downloads_config)
    return {"status": "success", "message": "✅ Configuración de actualización guardada."}

# ==========================================
# 📥 SISTEMA DE DESCARGAS MULTI-OS (NUEVO)
# ==========================================
@app.get("/api/get_downloads")
def get_downloads_api():
    """API pública para obtener la configuración de descargas (solo sistemas activos)"""
    cfg = downloads_config or get_default_downloads()
    active_systems = [s for s in cfg.get("systems", []) if s.get("active", True)]
    return {
        "page_title": cfg.get("page_title", "Centro de Descargas"),
        "page_subtitle": cfg.get("page_subtitle", ""),
        "instructions": cfg.get("instructions", ""),
        "systems": active_systems,
        "os_meta": OS_META
    }

@app.get("/api/get_downloads_admin")
def get_downloads_admin_api(request: Request):
    """API para admin - devuelve todos los sistemas (activos e inactivos)"""
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    cfg = downloads_config or get_default_downloads()
    return cfg

class DownloadSystemData(BaseModel):
    page_title: str
    page_subtitle: str
    instructions: str
    systems: list

@app.post("/api/save_downloads")
def save_downloads_api(request: Request, data: DownloadSystemData):
    global downloads_config
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    downloads_config = {
        "page_title": data.page_title,
        "page_subtitle": data.page_subtitle,
        "instructions": data.instructions,
        "systems": data.systems
    }
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config, downloads_config)
    return {"status": "success", "message": "✅ Configuración de descargas guardada correctamente."}

def generate_download_token(email, name=""):
    """Genera un token único de acceso a la página de descargas"""
    raw = f"{email}:{name}:{time.time()}:{random.random()}"
    token = hashlib.sha256(raw.encode()).hexdigest()[:32]
    download_access_tokens[token] = {
        "email": email,
        "name": name,
        "expires": time.time() + (24 * 3600)  # 24 horas de validez
    }
    return token

def validate_download_token(token):
    """Valida que el token exista y no haya expirado"""
    if not token: return None
    info = download_access_tokens.get(token)
    if not info: return None
    if time.time() > info.get("expires", 0):
        download_access_tokens.pop(token, None)
        return None
    return info

@app.get("/download", response_class=HTMLResponse)
def download_page(request: Request, token: Optional[str] = Query(None)):
    """Página pública de descargas - se abre en nueva pestaña"""
    # Validar token (opcional pero recomendado)
    token_info = validate_download_token(token)
    
    cfg = downloads_config or get_default_downloads()
    systems = [s for s in cfg.get("systems", []) if s.get("active", True)]
    
    user_name = token_info.get("name", "") if token_info else ""
    greeting = f"¡Hola {user_name}!" if user_name else "¡Bienvenido!"
    
    # Generar tarjetas HTML para cada sistema
    cards_html = ""
    for s in systems:
        os_key = s.get("os", "other").lower()
        meta = OS_META.get(os_key, OS_META["other"])
        links_html = ""
        for i, link in enumerate(s.get("links", []), 1):
            links_html += f"""
            <a href="{link.get('url', '#')}" target="_blank" rel="noopener noreferrer" 
               class="flex-1 min-w-[160px] bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-cyan-500 text-slate-200 hover:text-cyan-400 font-semibold py-3 px-4 rounded-lg transition-all duration-200 flex items-center justify-center gap-2 group">
                <i class="fas fa-cloud-download-alt group-hover:scale-110 transition-transform"></i>
                <span>{link.get('label', f'Servidor {i}')}</span>
            </a>"""
        
        if not links_html:
            links_html = '<p class="text-slate-500 text-sm italic">No hay enlaces disponibles</p>'
        
        cards_html += f"""
        <div class="bg-slate-800/60 backdrop-blur-sm border border-slate-700 hover:border-cyan-500/50 rounded-2xl overflow-hidden shadow-xl hover:shadow-cyan-500/10 transition-all duration-300 group">
            <div class="bg-gradient-to-br {meta['color']} p-6 flex items-center gap-4">
                <div class="bg-white/15 backdrop-blur rounded-xl w-16 h-16 flex items-center justify-center text-3xl text-white">
                    <i class="{meta['icon']}"></i>
                </div>
                <div class="flex-1 min-w-0">
                    <h3 class="text-white font-bold text-lg truncate">{s.get('name', 'Sistema')}</h3>
                    <div class="flex items-center gap-2 mt-1 flex-wrap">
                        <span class="bg-white/20 text-white text-xs font-semibold px-2 py-0.5 rounded-full">{meta['name']}</span>
                        <span class="bg-black/30 text-cyan-100 text-xs font-semibold px-2 py-0.5 rounded-full">v{s.get('version', '1.0.0')}</span>
                    </div>
                </div>
            </div>
            <div class="p-6">
                <p class="text-slate-300 text-sm leading-relaxed mb-4">{s.get('description', '')}</p>
                <div class="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-2">Enlaces de descarga</div>
                <div class="flex flex-wrap gap-2">
                    {links_html}
                </div>
            </div>
        </div>
        """
    
    if not cards_html:
        cards_html = """
        <div class="col-span-full text-center py-16">
            <i class="fas fa-box-open text-6xl text-slate-600 mb-4"></i>
            <h3 class="text-xl font-bold text-slate-300">No hay sistemas disponibles por ahora</h3>
            <p class="text-slate-500 mt-2">Vuelve a intentarlo más tarde.</p>
        </div>
        """
    
    instructions_html = ""
    if cfg.get("instructions"):
        inst_lines = cfg.get("instructions").split("\n")
        instructions_html = "<ul class='space-y-2'>"
        for line in inst_lines:
            if line.strip():
                instructions_html += f"<li class='flex items-start gap-3 text-slate-300'><i class='fas fa-check-circle text-cyan-400 mt-1'></i><span>{line.strip()}</span></li>"
        instructions_html += "</ul>"
    
    return f"""
    <html lang="es"><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{cfg.get('page_title', 'Centro de Descargas')} - BLENIN.G.77</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body {{ font-family: 'Inter', sans-serif; background: #020617; }}
        .gradient-bg {{
            background: linear-gradient(135deg, #020617 0%, #0c4a6e 50%, #0e7490 100%);
        }}
        .grid-pattern {{
            background-image: radial-gradient(circle at 1px 1px, rgba(34, 211, 238, 0.08) 1px, transparent 0);
            background-size: 32px 32px;
        }}
        .glass {{
            backdrop-filter: blur(12px);
            background: rgba(15, 23, 42, 0.6);
        }}
        @keyframes float {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-10px); }}
        }}
        .float-anim {{ animation: float 4s ease-in-out infinite; }}
        @keyframes pulse-glow {{
            0%, 100% {{ box-shadow: 0 0 20px rgba(34, 211, 238, 0.3); }}
            50% {{ box-shadow: 0 0 40px rgba(34, 211, 238, 0.6); }}
        }}
        .pulse-glow {{ animation: pulse-glow 2.5s infinite; }}
        ::-webkit-scrollbar {{ width: 10px; }}
        ::-webkit-scrollbar-track {{ background: #0f172a; }}
        ::-webkit-scrollbar-thumb {{ background: #0e7490; border-radius: 5px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #06b6d4; }}
    </style>
    </head>
    <body class="text-slate-200 min-h-screen">
        <!-- Header con gradiente -->
        <div class="gradient-bg grid-pattern relative overflow-hidden">
            <div class="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-slate-950"></div>
            <div class="absolute top-10 right-10 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl"></div>
            <div class="absolute bottom-10 left-10 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl"></div>
            
            <div class="relative max-w-6xl mx-auto px-4 py-12 md:py-20">
                <!-- Nav superior -->
                <nav class="flex justify-between items-center mb-12">
                    <a href="/" class="flex items-center gap-2 text-white font-bold text-xl">
                        <div class="w-10 h-10 bg-gradient-to-br from-cyan-400 to-emerald-500 rounded-lg flex items-center justify-center">
                            <i class="fas fa-bolt text-slate-900"></i>
                        </div>
                        BLENIN.G.77
                    </a>
                    <a href="/" class="text-slate-300 hover:text-cyan-400 text-sm flex items-center gap-2 transition">
                        <i class="fas fa-arrow-left"></i> Volver al inicio
                    </a>
                </nav>
                
                <!-- Hero -->
                <div class="text-center max-w-3xl mx-auto">
                    <div class="inline-flex items-center gap-2 bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 px-4 py-1.5 rounded-full text-sm font-semibold mb-6">
                        <i class="fas fa-shield-check"></i> Descarga Segura y Verificada
                    </div>
                    <h1 class="text-4xl md:text-6xl font-extrabold text-white mb-4 leading-tight">
                        {cfg.get('page_title', 'Centro de Descargas')}
                    </h1>
                    <p class="text-lg md:text-xl text-slate-300 mb-2">{greeting}</p>
                    <p class="text-slate-400 max-w-2xl mx-auto">{cfg.get('page_subtitle', '')}</p>
                </div>
            </div>
        </div>
        
        <!-- Contenido principal -->
        <main class="max-w-6xl mx-auto px-4 py-12 md:py-16 -mt-8 relative z-10">
            <!-- Sección de sistemas -->
            <div class="mb-12">
                <div class="flex items-center gap-3 mb-8">
                    <div class="w-1 h-8 bg-gradient-to-b from-cyan-400 to-emerald-500 rounded-full"></div>
                    <h2 class="text-2xl md:text-3xl font-bold text-white">Sistemas Disponibles</h2>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {cards_html}
                </div>
            </div>
            
            <!-- Instrucciones -->
            {f'''
            <div class="glass border border-slate-700 rounded-2xl p-6 md:p-8 mb-12">
                <div class="flex items-center gap-3 mb-6">
                    <div class="w-10 h-10 bg-cyan-500/15 rounded-lg flex items-center justify-center">
                        <i class="fas fa-list-check text-cyan-400"></i>
                    </div>
                    <h3 class="text-xl font-bold text-white">Instrucciones de Instalación</h3>
                </div>
                {instructions_html}
            </div>
            ''' if instructions_html else ''}
            
            <!-- Banner de soporte -->
            <div class="bg-gradient-to-r from-cyan-600/20 to-emerald-600/20 border border-cyan-500/30 rounded-2xl p-6 md:p-8 text-center">
                <div class="float-anim inline-block mb-4">
                    <i class="fas fa-headset text-5xl text-cyan-400"></i>
                </div>
                <h3 class="text-xl md:text-2xl font-bold text-white mb-2">¿Necesitas ayuda con la instalación?</h3>
                <p class="text-slate-300 mb-4">Nuestro equipo de soporte está disponible 24/7 para ayudarte</p>
                <a href="https://t.me/blenin77" target="_blank" class="inline-flex items-center gap-2 bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold px-6 py-3 rounded-lg transition pulse-glow">
                    <i class="fab fa-telegram"></i> Contactar Soporte
                </a>
            </div>
        </main>
        
        <!-- Footer -->
        <footer class="border-t border-slate-800 bg-slate-950 py-8">
            <div class="max-w-6xl mx-auto px-4 text-center">
                <div class="flex items-center justify-center gap-2 text-white font-bold text-lg mb-2">
                    <div class="w-8 h-8 bg-gradient-to-br from-cyan-400 to-emerald-500 rounded-lg flex items-center justify-center">
                        <i class="fas fa-bolt text-slate-900 text-sm"></i>
                    </div>
                    BLENIN.G.77
                </div>
                <p class="text-slate-500 text-sm">© 2024 BLENIN.G.77 Trading Systems. Todos los derechos reservados.</p>
            </div>
        </footer>
    </body></html>
    """

# ==========================================
# 🎯 CAPTURA DE LEADS Y REDIRECCIÓN A DESCARGAS
# ==========================================
class CaptureLeadData(BaseModel):
    email: str
    name: str = ""
    interaction: str = "Descarga del sistema"

@app.post("/api/capture_lead_for_download")
def capture_lead_for_download(request: Request, data: CaptureLeadData):
    """Captura el correo del usuario y devuelve una URL para abrir en nueva pestaña"""
    email = data.email.strip().lower()
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise HTTPException(status_code=400, detail="Correo electrónico inválido.")
    
    name = data.name.strip() if data.name else email.split("@")[0]
    
    # Guardar en trials_db para seguimiento IA
    global trials_db
    if email not in trials_db:
        trials_db[email] = {
            "name": name,
            "email": email,
            "date": datetime.now().isoformat(),
            "interaction": data.interaction,
            "follow_up_stage": 0,
            "last_email_sent": datetime.now().isoformat(),
            "ip": request.client.host if request.client else "unknown"
        }
        save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config, downloads_config)
        
        # Enviar correo inicial de seguimiento
        if ai_agent_config:
            try:
                subj = ai_agent_config.get("stage1_subject", "Bienvenido a BLENIN.G.77").format(name=name)
                body = ai_agent_config.get("stage1_body", "Hola {name}").format(name=name)
                send_email(email, subj, body)
            except Exception as e:
                print(f"Error enviando correo de bienvenida: {e}")
    
    # Generar token de acceso y devolver URL
    token = generate_download_token(email, name)
    download_url = f"/download?token={token}"
    
    return {
        "status": "success",
        "download_url": download_url,
        "message": "Correo registrado. Abriendo centro de descargas..."
    }

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
            <button onclick="showTab('downloads')" id="tab-downloads" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">📥 Descargas</button>
            <button onclick="showTab('stats')" id="tab-stats" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">📊 Estadísticas</button>
            <button onclick="showTab('ai')" id="tab-ai" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">🤖 Agente IA</button>
            <button onclick="showTab('lic')" id="tab-lic" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">Licencias</button>
            <button onclick="showTab('updates')" id="tab-updates" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">🔄 Actualizaciones</button>
            <button onclick="showTab('marketing')" id="tab-marketing" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">🧠 Marketing IA</button>
            <button onclick="showTab('settings')" id="tab-settings" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">⚙️ Ajustes</button>
            <a href="/admin/logout" class="bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded text-sm font-bold transition ml-2"><i class="fas fa-sign-out-alt mr-1"></i>Salir</a>
        </div>
    </nav>
    <div class="flex-1 container mx-auto p-6 md:p-10 max-w-5xl">
        <!-- PESTAÑA PÁGINAS -->
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
        
        <!-- PESTAÑA DESCARGAS (NUEVA) -->
        <div id="content-downloads" class="hidden space-y-6">
            <div class="bg-slate-800 p-6 rounded-xl border border-cyan-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">📥 Centro de Descargas Multi-OS</h3>
                <p class="text-sm text-slate-400 mb-4">Configura los sistemas disponibles para descarga. Cuando un usuario deje su correo en la landing, se abrirá una nueva pestaña con esta página de descargas.</p>
                <div class="bg-slate-900 p-3 rounded mb-6 text-cyan-400 text-xs flex items-center gap-2">
                    <i class="fas fa-info-circle"></i>
                    <span>URL pública de descargas: <code class="text-emerald-400">/download</code></span>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div>
                        <label class="text-sm text-slate-400">Título de la Página</label>
                        <input type="text" id="dl_page_title" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Centro de Descargas - BLENIN.G.77">
                    </div>
                    <div>
                        <label class="text-sm text-slate-400">Subtítulo</label>
                        <input type="text" id="dl_page_subtitle" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Descarga la versión más reciente...">
                    </div>
                </div>
                <div class="mb-6">
                    <label class="text-sm text-slate-400">Instrucciones de Instalación (una por línea)</label>
                    <textarea id="dl_instructions" rows="4" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="1. Selecciona tu sistema operativo&#10;2. Descarga el archivo..."></textarea>
                </div>
            </div>
            
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                <div class="flex justify-between items-center border-b border-slate-700 pb-3 mb-4">
                    <h3 class="text-lg font-bold text-white">Sistemas / Versiones</h3>
                    <button onclick="addDownloadSystem()" class="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded text-sm font-bold transition"><i class="fas fa-plus mr-2"></i>Agregar Sistema</button>
                </div>
                <div id="downloads-systems-container" class="space-y-4"></div>
            </div>
            
            <div class="bg-slate-900 p-4 rounded-xl border border-cyan-700/50">
                <div class="flex items-center gap-3 text-cyan-400 text-sm">
                    <i class="fas fa-lightbulb"></i>
                    <p>💡 <strong>Tip:</strong> Puedes crear múltiples versiones del mismo sistema operativo. Por ejemplo: "v1.0.0 Windows" y "v1.1.0 Beta Windows". Cada uno puede tener varios enlaces (servidores) de descarga.</p>
                </div>
            </div>
        </div>
        
        <!-- PESTAÑA ESTADÍSTICAS -->
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
        
        <!-- PESTAÑA AI -->
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
        
        <!-- PESTAÑA LICENCIAS -->
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
        
        <!-- PESTAÑA ACTUALIZACIONES -->
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
        
        <!-- PESTAÑA MARKETING -->
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
        
        <!-- PESTAÑA AJUSTES -->
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
        <div class="container mx-auto max-w-5xl flex justify-between items-center">
            <span class="text-xs text-slate-500">© 2024 BLENIN.G.77 Systems</span>
            <div class="flex gap-2">
                <button onclick="saveDownloadsData()" id="btn-save-downloads" class="hidden bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold px-6 py-2 rounded shadow-lg transition"><i class="fas fa-save mr-2"></i>Guardar Descargas</button>
                <button onclick="saveData()" class="bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold px-6 py-2 rounded shadow-lg transition"><i class="fas fa-save mr-2"></i>Guardar y Publicar</button>
            </div>
        </div>
    </footer>
    <div id="toast" class="fixed bottom-5 right-5 bg-slate-700 text-white px-4 py-3 rounded-lg shadow-2xl opacity-0 transition-opacity duration-300 pointer-events-none">
        <span id="toast-msg"></span>
    </div>
    <script id="pages-data" type="application/json">{pages_json}</script>
    <script>
    const allPages = JSON.parse(document.getElementById('pages-data').textContent);
    let currentMarketingText = "";
    let downloadsConfig = null;
    
    const OS_META = {{
        "windows": {{ "icon": "fab fa-windows", "color": "from-blue-500 to-cyan-600", "name": "Windows" }},
        "linux": {{ "icon": "fab fa-linux", "color": "from-amber-500 to-orange-600", "name": "Linux" }},
        "android": {{ "icon": "fab fa-android", "color": "from-green-500 to-emerald-600", "name": "Android" }},
        "ios": {{ "icon": "fab fa-apple", "color": "from-slate-400 to-slate-600", "name": "iOS" }},
        "macos": {{ "icon": "fab fa-apple", "color": "from-slate-500 to-slate-700", "name": "macOS" }},
        "other": {{ "icon": "fas fa-desktop", "color": "from-purple-500 to-pink-600", "name": "Otro" }}
    }};
    
    function showTab(tabId) {{
        ['pages', 'downloads', 'stats', 'ai', 'lic', 'updates', 'marketing', 'settings'].forEach(id => {{
            const c = document.getElementById('content-' + id);
            const t = document.getElementById('tab-' + id);
            if(c) c.classList.add('hidden');
            if(t) {{ t.classList.remove('tab-active'); t.classList.add('bg-slate-800', 'hover:bg-slate-700'); }}
        }});
        const c = document.getElementById('content-' + tabId);
        const t = document.getElementById('tab-' + tabId);
        if(c) c.classList.remove('hidden');
        if(t) {{ t.classList.add('tab-active'); t.classList.remove('bg-slate-800', 'hover:bg-slate-700'); }}
        
        const btnSaveDl = document.getElementById('btn-save-downloads');
        if(btnSaveDl) btnSaveDl.classList.toggle('hidden', tabId !== 'downloads');
        
        if(tabId === 'ai') loadAIConfig();
        if(tabId === 'stats') loadStats();
        if(tabId === 'updates') loadUpdateConfig();
        if(tabId === 'downloads') loadDownloadsConfig();
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
        if (pubs.length === 0) {{ addPubRow(); }} 
        else {{ pubs.forEach(pub => addPubRow(pub.type || 'video', pub.url || '', pub.desc || '')); }}
        
        document.getElementById('plans-container').innerHTML = '';
        let plans = p.plans || [];
        if (plans.length === 0) {{ addPlanRow(); }} 
        else {{ plans.forEach(plan => addPlanRow(plan.name || '', plan.price || '', plan.features || '', plan.link || '', plan.highlight || false)); }}
        
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
            page_name: name, chatbot_id: 'gzEjAzK1VCE72hJ_hBfA4', hero_title: name, 
            hero_subtitle: '', hero_text: '', affiliate_link: '', affiliate_text: '', 
            publications: [], plans: [], 
            social_links: {{ facebook: '', whatsapp: '', youtube: '', tiktok: '', telegram: '', instagram: '' }}, 
            bank_transfer_info: {{}}, download_links: [], download_instructions: '' 
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
    
    // ==========================================
    // 📥 GESTIÓN DE DESCARGAS (NUEVO)
    // ==========================================
    async function loadDownloadsConfig() {{
        try {{
            const res = await fetch('/api/get_downloads_admin', {{ credentials: 'same-origin' }});
            const data = await res.json();
            downloadsConfig = data;
            document.getElementById('dl_page_title').value = data.page_title || '';
            document.getElementById('dl_page_subtitle').value = data.page_subtitle || '';
            document.getElementById('dl_instructions').value = data.instructions || '';
            
            const container = document.getElementById('downloads-systems-container');
            container.innerHTML = '';
            const systems = data.systems || [];
            if (systems.length === 0) {{
                addDownloadSystem();
            }} else {{
                systems.forEach(s => addDownloadSystemRow(s));
            }}
        }} catch(e) {{ console.error('Error cargando descargas:', e); }}
    }}
    
    function addDownloadSystemRow(sys = null) {{
        const container = document.getElementById('downloads-systems-container');
        const id = sys ? sys.id : 'sys_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5);
        const div = document.createElement('div');
        div.className = 'bg-slate-900 p-4 rounded-lg border border-slate-700';
        div.dataset.sysId = id;
        
        const osValue = sys ? sys.os : 'windows';
        const osOptions = Object.keys(OS_META).map(k => 
            `<option value="${{k}}" ${{osValue===k?'selected':''}}>${{OS_META[k].name}}</option>`
        ).join('');
        
        const meta = OS_META[osValue] || OS_META['other'];
        
        div.innerHTML = `
            <div class="flex justify-between items-start mb-3">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-gradient-to-br ${{meta.color}} rounded-lg flex items-center justify-center text-white text-xl">
                        <i class="${{meta.icon}} sys-icon-display"></i>
                    </div>
                    <div>
                        <div class="text-sm font-bold text-white sys-name-display">${{sys ? (sys.name + ' v' + sys.version) : 'Nuevo Sistema'}}</div>
                        <div class="text-xs text-slate-500 sys-os-display">${{meta.name}}</div>
                    </div>
                </div>
                <button onclick="this.closest('[data-sys-id]').remove()" class="text-red-500 hover:text-red-400 text-sm"><i class="fas fa-trash"></i></button>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                <div>
                    <label class="text-xs text-slate-400">Nombre del Sistema</label>
                    <input type="text" class="sys-name w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500 text-sm" placeholder="BLENIN.G.77 Trading System" value="${{sys ? sys.name : ''}}">
                </div>
                <div>
                    <label class="text-xs text-slate-400">Versión</label>
                    <input type="text" class="sys-version w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500 text-sm" placeholder="1.0.0" value="${{sys ? sys.version : '1.0.0'}}">
                </div>
            </div>
            <div class="mb-3">
                <label class="text-xs text-slate-400">Sistema Operativo</label>
                <select class="sys-os w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500 text-sm" onchange="updateOsDisplay(this)">
                    ${{osOptions}}
                </select>
            </div>
            <div class="mb-3">
                <label class="text-xs text-slate-400">Descripción</label>
                <textarea class="sys-description w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500 text-sm" rows="2" placeholder="Descripción de esta versión...">${{sys ? sys.description : ''}}</textarea>
            </div>
            <div class="mb-3">
                <div class="flex justify-between items-center mb-2">
                    <label class="text-xs text-slate-400">Enlaces de Descarga</label>
                    <button onclick="addDownloadLink(this.closest('[data-sys-id]'))" class="text-cyan-400 hover:text-cyan-300 text-xs"><i class="fas fa-plus"></i> Agregar enlace</button>
                </div>
                <div class="sys-links space-y-2"></div>
            </div>
            <div class="flex items-center gap-2 pt-2 border-t border-slate-700">
                <input type="checkbox" class="sys-active accent-cyan-500" ${{(sys ? sys.active : true) ? 'checked' : ''}}>
                <label class="text-xs text-slate-300 cursor-pointer">Sistema activo (visible para los usuarios)</label>
            </div>
        `;
        container.appendChild(div);
        
        // Agregar enlaces existentes
        const linksContainer = div.querySelector('.sys-links');
        if (sys && sys.links && sys.links.length > 0) {{
            sys.links.forEach(link => addDownloadLink(div, link.label, link.url));
        }} else {{
            addDownloadLink(div);
        }}
        
        // Event listeners para actualizar display
        div.querySelector('.sys-name').addEventListener('input', function() {{
            const v = div.querySelector('.sys-version').value;
            div.querySelector('.sys-name-display').textContent = this.value + (v ? ' v' + v : '');
        }});
        div.querySelector('.sys-version').addEventListener('input', function() {{
            const n = div.querySelector('.sys-name').value;
            div.querySelector('.sys-name-display').textContent = (n || 'Sistema') + ' v' + this.value;
        }});
    }}
    
    function addDownloadSystem() {{
        addDownloadSystemRow();
    }}
    
    function updateOsDisplay(selectEl) {{
        const div = selectEl.closest('[data-sys-id]');
        const osKey = selectEl.value;
        const meta = OS_META[osKey] || OS_META['other'];
        const iconEl = div.querySelector('.sys-icon-display');
        const osDisplay = div.querySelector('.sys-os-display');
        const iconWrap = iconEl.parentElement;
        iconEl.className = meta.icon + ' sys-icon-display';
        iconWrap.className = `w-10 h-10 bg-gradient-to-br ${{meta.color}} rounded-lg flex items-center justify-center text-white text-xl`;
        osDisplay.textContent = meta.name;
    }}
    
    function addDownloadLink(sysDiv, label = '', url = '') {{
        const linksContainer = sysDiv.querySelector('.sys-links');
        const linkDiv = document.createElement('div');
        linkDiv.className = 'flex gap-2';
        linkDiv.innerHTML = `
            <input type="text" class="link-label bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500 text-xs w-1/3" placeholder="Etiqueta (Servidor 1)" value="${{label}}">
            <input type="text" class="link-url bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500 text-xs flex-1" placeholder="https://mega.nz/..." value="${{url}}">
            <button onclick="this.parentElement.remove()" class="bg-red-600 hover:bg-red-500 text-white px-2 py-1 rounded text-xs"><i class="fas fa-times"></i></button>
        `;
        linksContainer.appendChild(linkDiv);
    }}
    
    async function saveDownloadsData() {{
        const systems = [];
        document.querySelectorAll('#downloads-systems-container > [data-sys-id]').forEach(div => {{
            const name = div.querySelector('.sys-name').value.trim();
            if (!name) return;
            const links = [];
            div.querySelectorAll('.sys-links > div').forEach(linkDiv => {{
                const url = linkDiv.querySelector('.link-url').value.trim();
                if (url) {{
                    links.push({{
                        label: linkDiv.querySelector('.link-label').value.trim() || 'Servidor',
                        url: url
                    }});
                }}
            }});
            systems.push({{
                id: div.dataset.sysId,
                name: name,
                version: div.querySelector('.sys-version').value.trim() || '1.0.0',
                os: div.querySelector('.sys-os').value,
                description: div.querySelector('.sys-description').value.trim(),
                links: links,
                active: div.querySelector('.sys-active').checked
            }});
        }});
        
        const payload = {{
            page_title: document.getElementById('dl_page_title').value || 'Centro de Descargas',
            page_subtitle: document.getElementById('dl_page_subtitle').value,
            instructions: document.getElementById('dl_instructions').value,
            systems: systems
        }};
        
        try {{
            const res = await fetch('/api/save_downloads', {{
                method: 'POST',
                credentials: 'same-origin',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(payload)
            }});
            const result = await res.json();
            showToast(result.message);
        }} catch(e) {{
            showToast('❌ Error guardando descargas.');
            console.error(e);
        }}
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
            }}
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
            if (result.status === 'error') {{ console.error('Error guardando:', result); return; }}
            if(reloadSelector) {{ updateSelector(); }}
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
            const cfg = data || {{}};
            document.getElementById('s1_days').value = cfg.stage1_days || 2;
            document.getElementById('s1_subject').value = cfg.stage1_subject || '';
            document.getElementById('s1_body').value = cfg.stage1_body || '';
            document.getElementById('s2_days').value = cfg.stage2_days || 5;
            document.getElementById('s2_subject').value = cfg.stage2_subject || '';
            document.getElementById('s2_body').value = cfg.stage2_body || '';
            document.getElementById('s3_days').value = cfg.stage3_days || 10;
            document.getElementById('s3_subject').value = cfg.stage3_subject || '';
            document.getElementById('s3_body').value = cfg.stage3_body || '';
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
        try {{
            const res = await fetch('/api/generate_marketing', {{
                method: 'POST',
                credentials: 'same-origin',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{ type: type }})
            }});
            const data = await res.json();
            if (data.status === 'success') {{
                outputDiv.innerText = data.content;
                currentMarketingText = data.content;
            }} else {{
                outputDiv.innerText = "❌ Error: " + (data.message || "No se pudo generar");
            }}
        }} catch(e) {{
            outputDiv.innerText = "❌ Error de conexión con el servidor.";
            console.error(e);
        }}
    }}
    
    function copyMarketing() {{
        if (!currentMarketingText) {{ showToast('No hay contenido para copiar'); return; }}
        navigator.clipboard.writeText(currentMarketingText).then(() => showToast('✅ Contenido copiado al portapapeles'));
    }}
    
    async function createManualLicense() {{
        const plan = document.getElementById('manual_plan').value;
        const days = parseInt(document.getElementById('manual_days').value);
        const email = document.getElementById('manual_email').value.trim();
        if(!email) {{ showToast('⚠️ Ingresa el correo del cliente'); return; }}
        try {{
            const res = await fetch('/api/create_manual_license', {{
                method: 'POST', credentials: 'same-origin',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{ plan: plan, days: days, email: email }})
            }});
            const data = await res.json();
            const msg = document.getElementById('manual_lic_msg');
            msg.classList.remove('hidden');
            if (data.status === 'success') {{
                msg.innerText = '✅ Licencia generada: ' + data.license_key;
                msg.className = 'mt-4 text-cyan-400 font-bold text-sm bg-slate-900 p-3 rounded';
            }} else {{
                msg.innerText = '❌ ' + (data.detail || 'Error');
                msg.className = 'mt-4 text-red-400 font-bold text-sm bg-slate-900 p-3 rounded';
            }}
        }} catch(e) {{ console.error(e); }}
    }}
    
    async function manageLic(activate) {{
        const key = document.getElementById('lic_key').value.trim();
        if(!key) {{ showToast('⚠️ Ingresa una clave de licencia'); return; }}
        try {{
            const res = await fetch('/api/manage_license', {{
                method: 'POST', credentials: 'same-origin',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{ key: key, active: activate }})
            }});
            const data = await res.json();
            const msg = document.getElementById('lic_msg');
            msg.classList.remove('hidden');
            msg.innerText = data.message;
            msg.className = 'mt-4 text-cyan-400 font-bold text-sm';
        }} catch(e) {{ console.error(e); }}
    }}
    
    async function resetHwid() {{
        const key = document.getElementById('lic_key').value.trim();
        if(!key) {{ showToast('⚠️ Ingresa una clave de licencia'); return; }}
        try {{
            const res = await fetch('/api/reset_hwid', {{
                method: 'POST', credentials: 'same-origin',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{ key: key }})
            }});
            const data = await res.json();
            const msg = document.getElementById('lic_msg');
            msg.classList.remove('hidden');
            msg.innerText = data.message;
        }} catch(e) {{ console.error(e); }}
    }}
    
    async function changePassword() {{
        const cur = document.getElementById('current_pwd').value;
        const newP = document.getElementById('new_pwd').value;
        const conf = document.getElementById('confirm_pwd').value;
        if (newP !== conf) {{
            const msg = document.getElementById('pwd_msg');
            msg.classList.remove('hidden');
            msg.className = 'mt-4 font-bold text-sm text-red-400';
            msg.innerText = '❌ Las contraseñas no coinciden.';
            return;
        }}
        try {{
            const res = await fetch('/api/change_password', {{
                method: 'POST', credentials: 'same-origin',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{ current_password: cur, new_password: newP }})
            }});
            const data = await res.json();
            const msg = document.getElementById('pwd_msg');
            msg.classList.remove('hidden');
            msg.innerText = data.message;
            msg.className = 'mt-4 font-bold text-sm ' + (data.status === 'success' ? 'text-emerald-400' : 'text-red-400');
        }} catch(e) {{ console.error(e); }}
    }}
    
    // Init
    updateSelector();
    </script>
    </body></html>
    """

# ==========================================
# 🌐 APIs PÚBLICAS Y DE PÁGINAS
# ==========================================
@app.post("/api/save_pages")
def save_pages_api(request: Request, data: dict):
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    success = save_all_pages({"pages": data})
    if success:
        return {"status": "success", "message": "✅ Páginas guardadas correctamente."}
    return {"status": "error", "message": "❌ Error guardando en Supabase."}

@app.get("/api/get_stats")
def get_stats_api(request: Request):
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    return {
        "views": stats_db.get("views", 0),
        "countries": stats_db.get("countries", {}),
        "captured_leads": list(trials_db.values()) if trials_db else []
    }

@app.get("/api/get_ai_config")
def get_ai_config_api(request: Request):
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    return ai_agent_config

class AIData(BaseModel):
    stage1_days: int
    stage1_subject: str
    stage1_body: str
    stage2_days: int
    stage2_subject: str
    stage2_body: str
    stage3_days: int
    stage3_subject: str
    stage3_body: str

@app.post("/api/save_ai_config")
def save_ai_config_api(request: Request, data: AIData):
    global ai_agent_config
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    ai_agent_config = data.dict()
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config, downloads_config)
    return {"status": "success", "message": "✅ Configuración del Agente IA guardada."}

class ManualLicData(BaseModel):
    plan: str
    days: int
    email: str

@app.post("/api/create_manual_license")
def create_manual_license_api(request: Request, data: ManualLicData):
    global licenses_db
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    
    prefix = "BLENIN-" + data.plan.upper() + "-"
    code = prefix + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    expires = (datetime.now() + timedelta(days=data.days)).isoformat()
    licenses_db[code] = {
        "hwid": None, "expires": expires, "active": True,
        "plan": data.plan, "email": data.email
    }
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config, downloads_config)
    return {"status": "success", "license_key": code}

class ManageLicData(BaseModel):
    key: str
    active: bool

@app.post("/api/manage_license")
def manage_license_api(request: Request, data: ManageLicData):
    global licenses_db
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    if data.key in licenses_db:
        licenses_db[data.key]["active"] = data.active
        save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config, downloads_config)
        return {"message": f"✅ Licencia {'activada' if data.active else 'suspendida'} correctamente."}
    return {"message": "❌ Licencia no encontrada."}

class ResetHwidData(BaseModel):
    key: str

@app.post("/api/reset_hwid")
def reset_hwid_api(request: Request, data: ResetHwidData):
    global licenses_db
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    if data.key in licenses_db:
        licenses_db[data.key]["hwid"] = None
        save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config, downloads_config)
        return {"message": "✅ HWID reseteado correctamente."}
    return {"message": "❌ Licencia no encontrada."}

@app.post("/api/change_password")
def change_password_api(request: Request, data: ChangePasswordData):
    global admin_password_db
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    if data.current_password != admin_password_db:
        return {"status": "error", "message": "❌ La contraseña actual es incorrecta."}
    if len(data.new_password) < 6:
        return {"status": "error", "message": "❌ La nueva contraseña debe tener al menos 6 caracteres."}
    admin_password_db = data.new_password
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config, downloads_config)
    return {"status": "success", "message": "✅ Contraseña actualizada correctamente."}

class MarketingRequest(BaseModel):
    type: str

@app.post("/api/generate_marketing")
def generate_marketing_api(request: Request, data: MarketingRequest):
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    
    prompts = {
        "seo_blog": "Escribe un artículo SEO optimizado de 800 palabras sobre BLENIN.G.77, un sistema de trading institucional con IA Predictiva, enjambre de 500 agentes y modo híbrido (MT5 + noticias macroeconómicas). Incluye títulos H2, palabras clave como 'trading algorítmico', 'IA para trading', 'bot MT5'. Tono profesional pero accesible.",
        "tiktok_script": "Crea un guion viral para TikTok/Reels (60 segundos) sobre BLENIN.G.77. Debe tener gancho en los primeros 3 segundos, mostrar resultados impactantes de trading con IA, y llamada a la acción clara. Incluye indicaciones visuales entre corchetes.",
        "forum_post": "Escribe un post para foros como Reddit (r/algotrading) presentando BLENIN.G.77. Debe ser genuino, no spammy, enfocarse en la tecnología (IA predictiva, enjambre de agentes, modo híbrido), y generar discusión técnica. Máximo 500 palabras."
    }
    
    prompt = prompts.get(data.type, prompts["seo_blog"])
    content = generate_dynamic_content_with_llama(prompt, max_tokens=1500)
    
    if content:
        return {"status": "success", "content": content}
    return {"status": "error", "message": "No se pudo generar el contenido. Verifica la API key de Gemini."}

# ==========================================
# 🌍 RENDERIZADO DE PÁGINAS PÚBLICAS
# ==========================================
def render_landing_page(page_data: dict, slug: str = "main"):
    """Renderiza la landing page pública con el formulario de captura que redirige a /download"""
    plans_html = ""
    for plan in page_data.get("plans", []):
        highlight_class = "border-cyan-500 scale-105 shadow-2xl shadow-cyan-500/20" if plan.get("highlight") else "border-slate-700"
        badge = '<div class="absolute -top-3 left-1/2 -translate-x-1/2 bg-cyan-500 text-slate-900 text-xs font-bold px-3 py-1 rounded-full">MÁS POPULAR</div>' if plan.get("highlight") else ''
        features_html = plan.get("features", "").replace("\n", "<br>")
        plans_html += f"""
        <div class="bg-slate-800 border-2 {highlight_class} rounded-2xl p-6 relative transition-all hover:scale-105">
            {badge}
            <h3 class="text-2xl font-bold text-white mb-2">{plan.get('name', '')}</h3>
            <p class="text-4xl font-extrabold text-cyan-400 mb-4">{plan.get('price', '')}</p>
            <div class="text-slate-300 text-sm mb-6">{features_html}</div>
            <form action="https://www.paypal.com/checkoutnow" method="post" target="_blank">
                <input type="hidden" name="cmd" value="_s-xclick">
                <input type="hidden" name="hosted_button_id" value="{plan.get('link', '')}">
                <button type="submit" class="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold py-3 rounded transition">Adquirir Plan</button>
            </form>
        </div>
        """
    
    pubs_html = ""
    for pub in page_data.get("publications", []):
        if pub.get("type") == "video":
            pubs_html += f"""
            <div class="bg-slate-800 rounded-xl overflow-hidden border border-slate-700">
                <div class="aspect-video"><iframe class="w-full h-full" src="{pub.get('url', '')}" allowfullscreen></iframe></div>
                <div class="p-4 text-sm text-slate-400">{pub.get('desc', '')}</div>
            </div>"""
        else:
            pubs_html += f"""
            <div class="bg-slate-800 rounded-xl overflow-hidden border border-slate-700">
                <img src="{pub.get('url', '')}" class="w-full">
                <div class="p-4 text-sm text-slate-400">{pub.get('desc', '')}</div>
            </div>"""
    
    social = page_data.get("social_links", {})
    social_html = ""
    icon_map = {"facebook": "fab fa-facebook", "whatsapp": "fab fa-whatsapp", "youtube": "fab fa-youtube", 
                "tiktok": "fab fa-tiktok", "telegram": "fab fa-telegram", "instagram": "fab fa-instagram"}
    for k, v in social.items():
        if v:
            social_html += f'<a href="{v}" target="_blank" class="w-10 h-10 bg-slate-800 hover:bg-cyan-500 hover:text-slate-900 rounded-full flex items-center justify-center transition"><i class="{icon_map.get(k, "fas fa-link")}"></i></a>'
    
    bt = page_data.get("bank_transfer_info", {})
    bt_html = ""
    if bt.get("bank_name"):
        bt_html = f"""
        <div class="bg-slate-800 border border-amber-700/50 rounded-2xl p-6 mt-8">
            <h3 class="text-lg font-bold text-white mb-4">💳 Pago por Transferencia Bancaria</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-slate-300">
                <div><span class="text-slate-500">Banco:</span> {bt.get('bank_name', '')}</div>
                <div><span class="text-slate-500">Tipo:</span> {bt.get('account_type', '')}</div>
                <div><span class="text-slate-500">Cuenta:</span> {bt.get('account_number', '')}</div>
                <div><span class="text-slate-500">Beneficiario:</span> {bt.get('beneficiary', '')}</div>
            </div>
            <p class="text-xs text-slate-400 mt-4">Envía tu comprobante a: <strong>{bt.get('email_for_proof', '')}</strong> o WhatsApp: <strong>{bt.get('whatsapp_for_proof', '')}</strong></p>
        </div>"""
    
    # Formulario de captura que redirige a nueva pestaña
    capture_form = """
    <div id="download-capture" class="bg-gradient-to-br from-cyan-900/40 to-emerald-900/40 border border-cyan-500/30 rounded-2xl p-6 md:p-8 text-center">
        <div class="inline-flex items-center gap-2 bg-cyan-500/15 text-cyan-400 px-4 py-1.5 rounded-full text-xs font-semibold mb-4">
            <i class="fas fa-download"></i> DESCARGA GRATUITA
        </div>
        <h3 class="text-2xl md:text-3xl font-bold text-white mb-2">Descarga el Sistema Ahora</h3>
        <p class="text-slate-300 mb-6">Deja tu correo y te redirigiremos a nuestro centro de descargas oficial</p>
        <form id="lead-form" class="flex flex-col sm:flex-row gap-3 max-w-md mx-auto" onsubmit="submitLead(event)">
            <input type="email" id="lead-email" required placeholder="tu@correo.com" class="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white outline-none focus:border-cyan-500">
            <input type="text" id="lead-name" placeholder="Tu nombre (opcional)" class="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white outline-none focus:border-cyan-500">
            <button type="submit" id="lead-btn" class="bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold px-6 py-3 rounded-lg transition whitespace-nowrap">
                <i class="fas fa-download mr-2"></i>Descargar
            </button>
        </form>
        <p id="lead-msg" class="mt-4 text-sm hidden"></p>
        <p class="text-xs text-slate-500 mt-4"><i class="fas fa-shield-alt mr-1"></i>Tu correo está seguro. No spam.</p>
    </div>
    <script>
    async function submitLead(e) {
        e.preventDefault();
        const email = document.getElementById('lead-email').value;
        const name = document.getElementById('lead-name').value;
        const btn = document.getElementById('lead-btn');
        const msg = document.getElementById('lead-msg');
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Procesando...';
        msg.classList.add('hidden');
        try {
            const res = await fetch('/api/capture_lead_for_download', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ email: email, name: name, interaction: 'Descarga desde landing' })
            });
            const data = await res.json();
            if (data.status === 'success') {
                msg.className = 'mt-4 text-sm text-emerald-400';
                msg.innerHTML = '<i class="fas fa-check-circle mr-1"></i>' + data.message;
                msg.classList.remove('hidden');
                // ABRIR EN NUEVA PESTAÑA
                setTimeout(() => {
                    window.open(data.download_url, '_blank');
                }, 500);
                btn.innerHTML = '<i class="fas fa-check mr-2"></i>¡Descarga lista!';
            } else {
                throw new Error(data.detail || 'Error');
            }
        } catch(err) {
            msg.className = 'mt-4 text-sm text-red-400';
            msg.innerHTML = '<i class="fas fa-exclamation-circle mr-1"></i>Error: ' + err.message;
            msg.classList.remove('hidden');
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-download mr-2"></i>Reintentar';
        }
    }
    </script>
    """
    
    return f"""
    <html lang="es"><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_data.get('hero_title', 'BLENIN.G.77')} - {page_data.get('hero_subtitle', '')}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body {{ font-family: 'Inter', sans-serif; background: #020617; }}
        .gradient-bg {{ background: linear-gradient(135deg, #020617 0%, #0c4a6e 50%, #0e7490 100%); }}
        .grid-pattern {{ background-image: radial-gradient(circle at 1px 1px, rgba(34, 211, 238, 0.08) 1px, transparent 0); background-size: 32px 32px; }}
    </style>
    </head>
    <body class="text-slate-200">
        <div class="gradient-bg grid-pattern">
            <div class="absolute top-10 right-10 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl"></div>
            <nav class="relative max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
                <div class="flex items-center gap-2 text-white font-bold text-xl">
                    <div class="w-10 h-10 bg-gradient-to-br from-cyan-400 to-emerald-500 rounded-lg flex items-center justify-center">
                        <i class="fas fa-bolt text-slate-900"></i>
                    </div>
                    BLENIN.G.77
                </div>
                <a href="#pricing" class="text-slate-300 hover:text-cyan-400 text-sm">Planes</a>
            </nav>
            <div class="relative max-w-4xl mx-auto px-4 py-20 text-center">
                <h1 class="text-5xl md:text-7xl font-extrabold text-white mb-4">{page_data.get('hero_title', '')}</h1>
                <p class="text-xl md:text-2xl text-cyan-400 font-semibold mb-4">{page_data.get('hero_subtitle', '')}</p>
                <p class="text-lg text-slate-300 mb-8 max-w-2xl mx-auto">{page_data.get('hero_text', '')}</p>
                <div class="flex gap-3 justify-center flex-wrap">
                    <a href="#download-capture" class="bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold px-8 py-3 rounded-lg transition"><i class="fas fa-download mr-2"></i>Descargar Ahora</a>
                    <a href="#pricing" class="bg-slate-800 hover:bg-slate-700 text-white font-bold px-8 py-3 rounded-lg transition border border-slate-700">Ver Planes</a>
                </div>
            </div>
        </div>
        
        <main class="max-w-6xl mx-auto px-4 py-16 space-y-16">
            {capture_form}
            
            {'<section><h2 class="text-3xl font-bold text-white text-center mb-8">Galería</h2><div class="grid grid-cols-1 md:grid-cols-2 gap-6">' + pubs_html + '</div></section>' if pubs_html else ''}
            
            <section id="pricing">
                <h2 class="text-3xl font-bold text-white text-center mb-8">Planes de Suscripción</h2>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
                    {plans_html}
                </div>
                {bt_html}
            </section>
        </main>
        
        <footer class="border-t border-slate-800 bg-slate-950 py-8">
            <div class="max-w-6xl mx-auto px-4 text-center">
                <div class="flex justify-center gap-3 mb-4">{social_html}</div>
                <p class="text-slate-500 text-sm">© 2024 BLENIN.G.77 Trading Systems</p>
            </div>
        </footer>
    </body></html>
    """

@app.get("/", response_class=HTMLResponse)
def render_main_page(request: Request):
    pages_data = get_all_pages()
    main_page = pages_data.get("pages", {}).get("main", get_default_content())
    return render_landing_page(main_page, "main")

@app.get("/p/{slug}", response_class=HTMLResponse)
def render_custom_page(slug: str, request: Request):
    pages_data = get_all_pages()
    page = pages_data.get("pages", {}).get(slug)
    if not page:
        raise HTTPException(status_code=404, detail="Página no encontrada")
    return render_landing_page(page, slug)

# ==========================================
# 🔄 SCHEDULER DE SEGUIMIENTO AUTOMÁTICO
# ==========================================
def process_follow_ups():
    global trials_db
    if not trials_db or not ai_agent_config:
        return
    
    now = datetime.now()
    changed = False
    for email, info in trials_db.items():
        try:
            stage = info.get("follow_up_stage", 0)
            if stage >= 3: continue
            last_sent = datetime.fromisoformat(info.get("last_email_sent", now.isoformat()))
            days_required = ai_agent_config.get(f"stage{{stage+1}}_days", 5)
            if (now - last_sent).days >= days_required:
                subject = ai_agent_config.get(f"stage{{stage+1}}_subject", "").format(name=info.get("name", ""))
                body = ai_agent_config.get(f"stage{{stage+1}}_body", "").format(name=info.get("name", ""))
                if send_email(email, subject, body):
                    trials_db[email]["follow_up_stage"] = stage + 1
                    trials_db[email]["last_email_sent"] = now.isoformat()
                    changed = True
                    print(f"✅ Seguimiento {{stage+1}} enviado a {{email}}", flush=True)
        except Exception as e:
            print(f"❌ Error en seguimiento de {{email}}: {{e}}", flush=True)
    
    if changed:
        save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config, downloads_config)

# Limpieza periódica de tokens expirados
def cleanup_tokens():
    now = time.time()
    expired = [t for t, v in download_access_tokens.items() if v.get("expires", 0) < now]
    for t in expired:
        download_access_tokens.pop(t, None)

scheduler = BackgroundScheduler()
scheduler.add_job(process_follow_ups, 'interval', hours=1)
scheduler.add_job(cleanup_tokens, 'interval', hours=6)
scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

