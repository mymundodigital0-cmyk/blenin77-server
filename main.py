from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional
import random, string, smtplib, os, requests, json, re, uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler
from supabase import create_client, Client

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ==========================================
# 🔐 SEGURIDAD Y LOGIN
# ==========================================
SESSION_TOKEN = "blenin_secure_session_2024"

class AdminLoginData(BaseModel):
    password: str

class ChangePasswordData(BaseModel):
    current_password: str
    new_password: str

class UpdateConfigData(BaseModel):
    latest_version: str
    download_url: str
    force_update: bool
    update_message: str

class DownloadEntry(BaseModel):
    id: Optional[str] = None
    version: str
    os: str
    download_url: str
    description: str
    file_size: str = ""
    release_date: str = ""
    is_active: bool = True

@app.get("/admin/login", response_class=HTMLResponse)
def admin_login_page():
    return """
    <html lang="es"><head><meta charset="UTF-8">
    <title>Login Admin - BLENIN77</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet">
    <style>body { font-family: 'Inter', sans-serif; }</style>
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
            async function doLogin() {
                const pwd = document.getElementById('pwd').value;
                const res = await fetch('/api/login', {
                    method: 'POST', credentials: 'same-origin',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ password: pwd })
                });
                if(res.ok) { window.location.href = '/admin'; }
                else { document.getElementById('err_msg').classList.remove('hidden'); }
            }
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
    return request.cookies.get("blenin_session") == SESSION_TOKEN

# ==========================================
# 🔧 SUPABASE Y CORREO
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
# 🧠 IA (GEMINI)
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
# 🗄️ BASE DE DATOS
# ==========================================
def get_default_ai_config():
    return {
        "stage1_days": 2,
        "stage1_subject": "🚀 {name}, descubre el poder de la IA Institucional con BLENIN.G.77",
        "stage1_body": "Hola {name},\n\nGracias por tu interés en BLENIN.G.77, el sistema de trading de nivel institucional impulsado por Inteligencia Artificial.\n\nMuchos usuarios nos preguntan si nuestra tecnología reemplaza el trabajo del trader. La respuesta es: es tu copiloto perfecto, diseñado para proteger tu capital y maximizar oportunidades mientras tú vives tu vida.\n\nCon nuestro sistema, tienes acceso a:\n🔹 IA Predictiva y Análisis Global en tiempo real.\n🔹 Un Enjambre de 500 Agentes analizando el mercado.\n🔹 Modo Híbrido (MT5 + Noticias macroeconómicas).\n\n¿Tienes alguna duda sobre cómo adaptar el bot a tu cuenta de MT5? Simplemente responde a este correo y nuestro equipo te ayudará.\n\nUn saludo institucional,\nEquipo de BLENIN.G.77 Trading Systems.\nhttps://blenin77-server.onrender.com/",
        "stage2_days": 5,
        "stage2_subject": "🔥 {name}, esto es lo que estás dejando atrás...",
        "stage2_body": "Hola {name},\n\nQueríamos mostrarte lo que la comunidad de BLENIN.G.77 está logrando hoy. Nuestros usuarios del Plan Oro están reportando resultados excepcionales al combinar nuestra IA Predictiva con el Modo Híbrido (MT5 + Noticias en tiempo real).\n\nSabemos que el trading requiere confianza, pero las oportunidades del mercado no esperan. Si te quedas fuera, el mercado seguirá moviéndose sin tus operaciones optimizadas.\n\nNo dejes tu capital expuesto a la emoción humana. Deja que la matemática y la IA trabajan por ti.\n\nRevisa nuestros planes y elige el que se adapta a tu capital aquí:\n👉 https://blenin77-server.onrender.com/#pricing\n\nUn saludo institucional,\nEquipo de BLENIN.G.77 Trading Systems.",
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
                if not res.data: print(f"🚨 ALERTA: Supabase no devolvió datos al guardar {key}", flush=True)
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

# ==========================================
# 📥 SISTEMA DE DESCARGAS MULTI-OS
# ==========================================
def get_default_downloads():
    return [
        {
            "id": "dl_001",
            "version": "16.03",
            "os": "Windows",
            "download_url": "https://mega.nz/file/tu_enlace",
            "description": "Versión completa con IA Deep Learning (PyTorch), Enjambre de 500 Agentes y Modo Híbrido.",
            "file_size": "85 MB",
            "release_date": "2024-12-01",
            "is_active": True
        }
    ]

def load_downloads_db():
    try:
        if not supabase: return get_default_downloads()
        response = supabase.table("app_data").select("value").eq("key", "downloads_db").execute()
        if response.data:
            return response.data[0]["value"]
        else:
            save_downloads_db(get_default_downloads())
            return get_default_downloads()
    except:
        return get_default_downloads()

def save_downloads_db(downloads):
    try:
        if not supabase: return False
        res = supabase.table("app_data").upsert({"key": "downloads_db", "value": downloads}, on_conflict="key").execute()
        return bool(res.data)
    except Exception as e:
        print(f"Error guardando downloads: {e}")
        return False

# ==========================================
# 📄 PÁGINAS (LANDING PAGES)
# ==========================================
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
            print("❌ Supabase no configurado.", flush=True)
            return False
        res = supabase.table("app_data").upsert({"key": "pages", "value": data}, on_conflict="key").execute()
        if hasattr(res, 'error') and res.error:
            print(f"🚨 ERROR EXPLÍCITO DE SUPABASE: {res.error}", flush=True)
            return False
        if not hasattr(res, 'data') or res.data is None or len(res.data) == 0:
            print("🚨 ERROR SILENCIOSO: Supabase no devolvió datos.", flush=True)
            return False
        print("✅ Páginas guardadas en Supabase correctamente.", flush=True)
        return True
    except Exception as e:
        print(f"🚨 EXCEPCIÓN guardando páginas: {e}", flush=True)
        return False

# ==========================================
# 🌐 LANDING PAGE + CAPTURA EMAIL
# ==========================================
@app.get("/", response_class=HTMLResponse)
@app.get("/p/{slug}", response_class=HTMLResponse)
def landing_page(slug: str = "main"):
    pages_data = get_all_pages()
    page = pages_data.get("pages", {}).get(slug, get_default_content())
    
    plans_html = ""
    for plan in page.get("plans", []):
        highlight = "border-cyan-500 scale-105" if plan.get("highlight") else "border-slate-700"
        plans_html += f"""
        <div class="bg-slate-800 p-6 rounded-xl border-2 {highlight} text-center">
            <h3 class="text-xl font-bold text-white">{plan.get('name','')}</h3>
            <p class="text-3xl font-extrabold text-cyan-400 my-2">{plan.get('price','')}</p>
            <p class="text-slate-400 text-sm whitespace-pre-line">{plan.get('features','')}</p>
            <a href="/download" class="mt-4 inline-block bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold px-6 py-2 rounded-lg transition"><i class="fas fa-download mr-2"></i>Descargar</a>
        </div>"""
    
    pubs_html = ""
    for pub in page.get("publications", []):
        if pub.get("type") == "video":
            pubs_html += f'<div class="bg-slate-800 rounded-xl overflow-hidden border border-slate-700"><div class="aspect-video"><iframe src="{pub.get("url","")}" frameborder="0" allowfullscreen class="w-full h-full"></iframe></div><p class="p-4 text-slate-400 text-sm">{pub.get("desc","")}</p></div>'
        else:
            pubs_html += f'<div class="bg-slate-800 rounded-xl overflow-hidden border border-slate-700"><img src="{pub.get("url","")}" class="w-full"><p class="p-4 text-slate-400 text-sm">{pub.get("desc","")}</p></div>'
    
    social = page.get("social_links", {})
    social_html = ""
    icons = {"facebook": "fab fa-facebook", "whatsapp": "fab fa-whatsapp", "youtube": "fab fa-youtube", "tiktok": "fab fa-tiktok", "telegram": "fab fa-telegram", "instagram": "fab fa-instagram"}
    for name, url in social.items():
        if url:
            social_html += f'<a href="{url}" target="_blank" class="text-slate-400 hover:text-cyan-400 text-2xl transition"><i class="{icons.get(name,"fas fa-link")}"></i></a>'
    
    bt = page.get("bank_transfer_info", {})
    bt_html = ""
    if bt.get("bank_name"):
        bt_html = f"""
        <div class="bg-slate-800 p-6 rounded-xl border border-amber-700 mt-8">
            <h3 class="text-lg font-bold text-white mb-4">💳 Transferencia Bancaria</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div><span class="text-slate-400">Banco:</span> <span class="text-white">{bt.get('bank_name','')}</span></div>
                <div><span class="text-slate-400">Tipo:</span> <span class="text-white">{bt.get('account_type','')}</span></div>
                <div><span class="text-slate-400">Cuenta:</span> <span class="text-cyan-400 font-mono">{bt.get('account_number','')}</span></div>
                <div><span class="text-slate-400">Beneficiario:</span> <span class="text-white">{bt.get('beneficiary','')}</span></div>
            </div>
        </div>"""
    
    affiliate_link = page.get("affiliate_link", '')
    affiliate_text = page.get("affiliate_text', '🚀 Afíliate') if page.get('affiliate_text') else '🚀 Afíliate'
    
    return f"""
    <html lang="es"><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page.get('hero_title','BLENIN77')}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>body {{ font-family: 'Inter', sans-serif; }}</style>
    </head>
    <body class="bg-slate-900 text-slate-300">
    
    <nav class="bg-slate-950/80 backdrop-blur-md p-4 sticky top-0 z-50 border-b border-slate-800">
        <div class="container mx-auto max-w-6xl flex justify-between items-center">
            <span class="text-2xl font-extrabold text-cyan-400">BLENIN<span class="text-white">.G.77</span></span>
            <div class="flex gap-4 items-center">
                <a href="/download" class="text-cyan-400 hover:text-cyan-300 text-sm font-bold transition"><i class="fas fa-download mr-1"></i>Descargar</a>
                <a href="{affiliate_link}" class="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg text-sm font-bold transition">{affiliate_text}</a>
            </div>
        </div>
    </nav>
    
    <div class="container mx-auto max-w-6xl px-4 py-20 text-center">
        <h1 class="text-5xl md:text-7xl font-extrabold text-white mb-4">{page.get('hero_title','')}</h1>
        <p class="text-2xl text-cyan-400 font-bold mb-6">{page.get('hero_subtitle','')}</p>
        <p class="text-slate-400 text-lg max-w-2xl mx-auto mb-10">{page.get('hero_text','')}</p>
        
        <div class="max-w-md mx-auto bg-slate-800 p-8 rounded-2xl border border-slate-700 shadow-2xl">
            <h2 class="text-xl font-bold text-white mb-2"><i class="fas fa-envelope text-cyan-400 mr-2"></i>Descarga el Sistema</h2>
            <p class="text-slate-400 text-sm mb-4">Deja tu correo y te redirigiremos a la página de descargas.</p>
            <form onsubmit="captureEmail(event)">
                <input type="email" id="email_input" required placeholder="tu@correo.com" class="w-full bg-slate-900 rounded-lg p-3 mb-3 border border-slate-700 outline-none focus:border-cyan-500 text-white">
                <input type="text" id="name_input" placeholder="Tu nombre (opcional)" class="w-full bg-slate-900 rounded-lg p-3 mb-4 border border-slate-700 outline-none focus:border-cyan-500 text-white">
                <button type="submit" class="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold py-3 rounded-lg transition"><i class="fas fa-download mr-2"></i>Ir a Descargas</button>
            </form>
        </div>
    </div>
    
    {('<div class="container mx-auto max-w-6xl px-4 py-12"><div class="grid grid-cols-1 md:grid-cols-3 gap-6">' + pubs_html + '</div></div>') if pubs_html else ''}
    
    {('<div class="container mx-auto max-w-6xl px-4 py-12"><h2 class="text-3xl font-bold text-white text-center mb-8">Planes</h2><div class="grid grid-cols-1 md:grid-cols-3 gap-6">' + plans_html + '</div>' + bt_html + '</div>') if plans_html else ''}
    
    {('<div class="container mx-auto max-w-6xl px-4 py-8 text-center"><div class="flex justify-center gap-6">' + social_html + '</div></div>') if social_html else ''}
    
    <footer class="bg-slate-950 p-6 border-t border-slate-800">
        <div class="container mx-auto max-w-6xl text-center">
            <p class="text-slate-500 text-sm">© 2024 BLENIN.G.77 Trading Systems.</p>
        </div>
    </footer>
    
    <script>
        async function captureEmail(e) {{
            e.preventDefault();
            const email = document.getElementById('email_input').value;
            const name = document.getElementById('name_input').value || 'Usuario';
            try {{
                await fetch('/api/capture_lead', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ email: email, name: name, interaction: 'Download Page' }})
                }});
            }} catch(e) {{}}
            window.location.href = '/download?email=' + encodeURIComponent(email);
        }}
    </script>
    </body></html>
    """

# ==========================================
# 📥 PÁGINA DE DESCARGA PROFESIONAL
# ==========================================
@app.get("/download", response_class=HTMLResponse)
def download_page(email: str = ""):
    downloads = load_downloads_db()
    active_downloads = [d for d in downloads if d.get("is_active", True)]
    
    os_groups = {}
    for dl in active_downloads:
        os_name = dl.get("os", "Otros")
        if os_name not in os_groups:
            os_groups[os_name] = []
        os_groups[os_name].append(dl)
    
    os_styles = {
        "Windows": {"icon": "fab fa-windows", "color": "#00a4ef", "bg": "from-blue-600 to-blue-800"},
        "Linux": {"icon": "fab fa-linux", "color": "#fcc624", "bg": "from-yellow-600 to-orange-700"},
        "macOS": {"icon": "fab fa-apple", "color": "#ffffff", "bg": "from-gray-600 to-gray-800"},
        "Android": {"icon": "fab fa-android", "color": "#3ddc84", "bg": "from-green-600 to-green-800"},
        "iOS": {"icon": "fab fa-app-store-ios", "color": "#0d96f6", "bg": "from-cyan-600 to-blue-800"},
    }
    
    cards_html = ""
    for os_name, dls in os_groups.items():
        style = os_styles.get(os_name, {"icon": "fas fa-download", "color": "#00e5ff", "bg": "from-slate-600 to-slate-800"})
        cards_html += f'''
        <div class="bg-slate-800 rounded-2xl border border-slate-700 overflow-hidden shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105">
            <div class="bg-gradient-to-br {style['bg']} p-6 text-center">
                <i class="{style['icon']} text-5xl mb-2" style="color: {style['color']};"></i>
                <h3 class="text-xl font-bold text-white">{os_name}</h3>
            </div>
            <div class="p-6 space-y-4">
        '''
        for dl in dls:
            size_badge = f'<span class="text-xs text-slate-500">📦 {dl.get("file_size", "N/D")}</span>' if dl.get("file_size") else ""
            date_str = dl.get("release_date", "")
            if date_str:
                try:
                    date_obj = datetime.fromisoformat(date_str)
                    date_str = date_obj.strftime("%d/%m/%Y")
                except: pass
            date_badge = f'<span class="text-xs text-slate-500">📅 {date_str}</span>' if date_str else ""
            cards_html += f'''
                <div class="bg-slate-900 rounded-xl p-4 border border-slate-700 hover:border-cyan-500 transition">
                    <div class="flex justify-between items-start mb-2">
                        <span class="text-cyan-400 font-bold text-lg">v{dl.get("version", "1.0")}</span>
                        <div class="flex gap-2">{size_badge}</div>
                    </div>
                    <p class="text-slate-400 text-sm mb-4">{dl.get("description", "Sin descripción.")}</p>
                    <div class="flex justify-between items-center">
                        {date_badge}
                        <a href="{dl.get("download_url", "#")}" target="_blank"
                           class="bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold px-6 py-2 rounded-lg transition inline-flex items-center gap-2">
                            <i class="fas fa-download"></i> Descargar
                        </a>
                    </div>
                </div>
            '''
        cards_html += """</div></div>"""
    
    if not cards_html:
        cards_html = '<div class="text-center py-20"><i class="fas fa-box-open text-6xl text-slate-600 mb-4"></i><p class="text-slate-400 text-xl">No hay descargas disponibles en este momento.</p></div>'
    
    email_banner = ""
    if email:
        email_banner = f'''
        <div class="bg-emerald-900/30 border border-emerald-700 rounded-xl p-4 mb-8 text-center">
            <p class="text-emerald-400 text-sm"><i class="fas fa-check-circle mr-2"></i>Correo registrado: <strong>{email}</strong></p>
            <p class="text-slate-400 text-xs mt-1">Te enviaremos novedades y actualizaciones del sistema.</p>
        </div>'''
    
    return f"""
    <html lang="es"><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Descargas - BLENIN.G.77</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body {{ font-family: 'Inter', sans-serif; background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%); }}
        @keyframes fadeInUp {{ from {{ opacity: 0; transform: translateY(30px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .fade-in {{ animation: fadeInUp 0.6s ease-out forwards; }}
        .fade-in-1 {{ animation: fadeInUp 0.6s ease-out 0.15s forwards; opacity: 0; }}
        .fade-in-2 {{ animation: fadeInUp 0.6s ease-out 0.3s forwards; opacity: 0; }}
    </style>
    </head>
    <body class="text-slate-300 min-h-screen">
    <nav class="bg-slate-950/80 backdrop-blur-md p-4 sticky top-0 z-50 border-b border-slate-800">
        <div class="container mx-auto max-w-6xl flex justify-between items-center">
            <a href="/" class="text-2xl font-extrabold text-cyan-400">BLENIN<span class="text-white">.G.77</span></a>
            <a href="/" class="text-slate-400 hover:text-cyan-400 text-sm transition"><i class="fas fa-arrow-left mr-1"></i>Volver al inicio</a>
        </div>
    </nav>
    <div class="container mx-auto max-w-6xl px-4 py-16 text-center fade-in">
        <div class="inline-block bg-cyan-500/10 border border-cyan-500/30 rounded-full px-4 py-1 mb-6">
            <span class="text-cyan-400 text-sm font-semibold"><i class="fas fa-rocket mr-1"></i> Centro de Descargas Oficial</span>
        </div>
        <h1 class="text-5xl md:text-6xl font-extrabold text-white mb-4">Descarga tu Sistema</h1>
        <p class="text-slate-400 text-lg max-w-2xl mx-auto mb-8">Elige tu sistema operativo y descarga la última versión del Bot de Trading Automatizado con IA Institucional.</p>
        {email_banner}
    </div>
    <div class="container mx-auto max-w-6xl px-4 pb-16">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 fade-in-1">{cards_html}</div>
    </div>
    <div class="container mx-auto max-w-4xl px-4 pb-16 fade-in-2">
        <div class="bg-slate-800/50 rounded-2xl border border-slate-700 p-8">
            <h2 class="text-2xl font-bold text-white mb-6 text-center"><i class="fas fa-info-circle text-cyan-400 mr-2"></i>Guía de Instalación</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="text-center"><div class="bg-cyan-500/10 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3"><span class="text-2xl font-bold text-cyan-400">1</span></div><h3 class="text-white font-bold mb-2">Descarga</h3><p class="text-slate-400 text-sm">Haz clic en el botón de descarga de tu sistema operativo.</p></div>
                <div class="text-center"><div class="bg-cyan-500/10 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3"><span class="text-2xl font-bold text-cyan-400">2</span></div><h3 class="text-white font-bold mb-2">Extrae</h3><p class="text-slate-400 text-sm">Descomprime el archivo .zip en tu escritorio o carpeta de preferencia.</p></div>
                <div class="text-center"><div class="bg-cyan-500/10 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3"><span class="text-2xl font-bold text-cyan-400">3</span></div><h3 class="text-white font-bold mb-2">Ejecuta</h3><p class="text-slate-400 text-sm">Abre el archivo .exe e ingresa tu clave de licencia al iniciar.</p></div>
            </div>
        </div>
    </div>
    <div class="container mx-auto max-w-4xl px-4 pb-16 fade-in-2">
        <div class="bg-amber-900/20 border border-amber-700/50 rounded-xl p-6">
            <h3 class="text-amber-400 font-bold mb-2"><i class="fas fa-exclamation-triangle mr-2"></i>Antes de instalar</h3>
            <ul class="text-slate-400 text-sm space-y-1 ml-6 list-disc">
                <li>Asegúrate de tener <strong class="text-white">MetaTrader 5</strong> instalado y conectado a tu cuenta.</li>
                <li>Para Windows: Se requiere <strong class="text-white">Windows 10 (64-bit)</strong> o superior.</li>
                <li>Para activar el Deep Learning (PyTorch): Mínimo <strong class="text-white">8 GB de RAM</strong>.</li>
                <li>El bot funciona como tu copiloto. El rendimiento pasado no garantiza resultados futuros.</li>
            </ul>
        </div>
    </div>
    <footer class="bg-slate-950 p-6 border-t border-slate-800">
        <div class="container mx-auto max-w-6xl text-center">
            <p class="text-slate-500 text-sm">© 2024 BLENIN.G.77 Trading Systems. Todos los derechos reservados.</p>
            <p class="text-slate-600 text-xs mt-2">El trading conlleva riesgo. Opere con capital que pueda permitirse perder.</p>
        </div>
    </footer>
    </body></html>
    """

# ==========================================
# 📥 API DESCARGAS
# ==========================================
@app.get("/api/get_downloads")
def get_downloads_api():
    return load_downloads_db()

@app.post("/api/save_download")
def save_download_api(request: Request, entry: DownloadEntry):
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    downloads = load_downloads_db()
    if not entry.id:
        entry.id = f"dl_{uuid.uuid4().hex[:8]}"
        downloads.append(entry.dict())
    else:
        found = False
        for i, d in enumerate(downloads):
            if d.get("id") == entry.id:
                downloads[i] = entry.dict()
                found = True
                break
        if not found: downloads.append(entry.dict())
    save_downloads_db(downloads)
    return {"status": "success", "message": "✅ Descarga guardada correctamente.", "id": entry.id}

@app.post("/api/delete_download")
def delete_download_api(request: Request, data: dict):
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    downloads = load_downloads_db()
    downloads = [d for d in downloads if d.get("id") != data.get("id")]
    save_downloads_db(downloads)
    return {"status": "success", "message": "🗑️ Descarga eliminada."}

# ==========================================
# 🔄 ACTUALIZACIONES DEL BOT
# ==========================================
@app.get("/api/get_latest_version")
def get_latest_version():
    return bot_update_config

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
# 📧 CAPTURA DE LEADS
# ==========================================
@app.post("/api/capture_lead")
def capture_lead(data: dict):
    global stats_db
    email = data.get("email", "")
    name = data.get("name", "Usuario")
    interaction = data.get("interaction", "Download")
    if not email: raise HTTPException(status_code=400, detail="Email requerido")
    
    if "captured_leads" not in stats_db:
        stats_db["captured_leads"] = []
    
    lead = {"email": email, "name": name, "interaction": interaction, "date": datetime.now().isoformat(), "follow_up_stage": 0}
    
    existing = [l for l in stats_db["captured_leads"] if l.get("email") == email]
    if not existing:
        stats_db["captured_leads"].append(lead)
        save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
        try:
            subject = ai_agent_config.get("stage1_subject", "Bienvenido").replace("{name}", name)
            body = ai_agent_config.get("stage1_body", "Hola...").replace("{name}", name)
            send_email(email, subject, body)
        except: pass
    
    return {"status": "success", "message": "Correo registrado. Redirigiendo a descargas..."}

# ==========================================
# 📊 ESTADÍSTICAS Y VISITAS
# ==========================================
@app.get("/api/get_stats")
def get_stats_api(request: Request):
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    return stats_db

@app.middleware("http")
async def track_visits(request: Request, call_next):
    global stats_db
    response = await call_next(request)
    path = request.url.path
    if not path.startswith("/admin") and not path.startswith("/api"):
        try:
            stats_db["views"] = stats_db.get("views", 0) + 1
            if "countries" not in stats_db: stats_db["countries"] = {}
            save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
        except: pass
    return response

# ==========================================
# 🤖 AGENTE IA CONFIG
# ==========================================
@app.get("/api/get_ai_config")
def get_ai_config_api(request: Request):
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    return ai_agent_config

@app.post("/api/save_ai_config")
def save_ai_config_api(request: Request, data: dict):
    global ai_agent_config
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    ai_agent_config = data
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
    return {"status": "success", "message": "✅ Configuración del Agente IA guardada."}

# ==========================================
# 📄 PÁGINAS API
# ==========================================
@app.post("/api/save_pages")
def save_pages_api(request: Request, data: dict):
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    if save_all_pages(data):
        return {"status": "success", "message": "✅ Páginas guardadas y publicadas correctamente."}
    return {"status": "error", "message": "❌ Error guardando en Supabase. Revisa la configuración."}

# ==========================================
# 🔑 LICENCIAS API
# ==========================================
@app.post("/api/validate_license")
def validate_license(data: dict):
    key = data.get("key", "").upper()
    hwid = data.get("hwid", "")
    if key in licenses_db:
        lic = licenses_db[key]
        if not lic.get("active", False):
            return {"valid": False, "message": "Licencia suspendada."}
        try:
            expires = datetime.fromisoformat(lic["expires"])
            if datetime.now() > expires:
                return {"valid": False, "message": "Licencia expirada."}
        except: pass
        if lic.get("hwid") and lic["hwid"] != hwid:
            return {"valid": False, "message": "HWID no coincide."}
        if not lic.get("hwid"):
            lic["hwid"] = hwid
            save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
        days_left = (datetime.fromisoformat(lic["expires"]) - datetime.now()).days
        return {"valid": True, "plan": lic.get("plan", "BRONCE"), "days_left": days_left}
    return {"valid": False, "message": "Licencia no encontrada."}

@app.post("/api/start_trial")
def start_trial(data: dict):
    hwid = data.get("hwid", "")
    if hwid in trials_db:
        trial = trials_db[hwid]
        try:
            expires = datetime.fromisoformat(trial["expires"])
            if datetime.now() > expires:
                return {"valid": False, "message": "Prueba expirada."}
            days_left = (expires - datetime.now()).days
            return {"valid": True, "plan": "BRONCE", "days_left": days_left}
        except: pass
    else:
        expires = (datetime.now() + timedelta(days=30)).isoformat()
        trials_db[hwid] = {"expires": expires, "active": True}
        save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
        return {"valid": True, "plan": "BRONCE", "days_left": 30, "message": "Prueba gratuita iniciada."}
    return {"valid": False, "message": "No se pudo iniciar la prueba."}

@app.post("/api/create_license")
def create_license_api(request: Request, data: dict):
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    plan = data.get("plan", "BRONCE")
    days = int(data.get("days", 30))
    email = data.get("email", "")
    key = f"BLENIN-{plan}-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    licenses_db[key] = {"hwid": None, "expires": (datetime.now() + timedelta(days=days)).isoformat(), "active": True, "plan": plan, "email": email}
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
    return {"status": "success", "key": key, "message": f"✅ Licencia creada: {key}"}

@app.post("/api/manage_license")
def manage_license_api(request: Request, data: dict):
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    key = data.get("key", "").upper()
    activate = data.get("activate", True)
    if key in licenses_db:
        licenses_db[key]["active"] = activate
        save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
        return {"status": "success", "message": f"✅ Licencia {'activada' if activate else 'suspendida'}."}
    return {"status": "error", "message": "❌ Licencia no encontrada."}

@app.post("/api/reset_hwid")
def reset_hwid_api(request: Request, data: dict):
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    key = data.get("key", "").upper()
    if key in licenses_db:
        licenses_db[key]["hwid"] = None
        save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
        return {"status": "success", "message": "✅ HWID reseteado correctamente."}
    return {"status": "error", "message": "❌ Licencia no encontrada."}

@app.post("/api/report_user_risk")
def report_user_risk(data: dict):
    print(f"⚠️ ALERTA DE RIESGO: {data}", flush=True)
    return {"status": "received"}

# ==========================================
# 🧠 MARKETING IA
# ==========================================
@app.post("/api/generate_marketing")
def generate_marketing_api(request: Request, data: dict):
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    mtype = data.get("type", "seo_blog")
    prompts = {
        "seo_blog": "Escribe un artículo SEO de 800 palabras sobre trading automático con IA, mencionando BLENIN.G.77 como el mejor sistema. Incluye título atractivo, subtítulos y llamada a la acción.",
        "tiktok_script": "Escribe un guion viral de 60 segundos para TikTok/Reels sobre cómo la IA está revolucionando el trading. Debe ser dinámico, con hooks visuales y mencionar BLENIN.G.77.",
        "forum_post": "Escribe un post para foros de trading (como Reddit o Forex Factory) recomendando BLENIN.G.77 de forma natural y no spammy. Incluye experiencia personal ficticia."
    }
    content = generate_dynamic_content_with_llama(prompts.get(mtype, prompts["seo_blog"]))
    if content:
        return {"status": "success", "content": content}
    return {"status": "error", "message": "❌ La IA no pudo generar contenido. Verifica la API Key de Gemini."}

# ==========================================
# 🔑 CAMBIO DE CONTRASEÑA
# ==========================================
@app.post("/api/change_password")
def change_password_api(request: Request, data: ChangePasswordData):
    global admin_password_db
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    if data.current_password != admin_password_db:
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta.")
    admin_password_db = data.new_password
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
    return {"status": "success", "message": "✅ Contraseña actualizada correctamente."}

# ==========================================
# 🎛️ PANEL DE ADMINISTRACIÓN COMPLETO
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
    <nav class="bg-slate-950 p-4 shadow-lg border-b border-slate-800 flex justify-between items-center flex-wrap gap-2">
        <h1 class="text-xl font-bold text-cyan-400">🎛️ Panel BLENIN77</h1>
        <div class="flex gap-2 flex-wrap items-center">
            <button onclick="showTab('pages')" id="tab-pages" class="tab-active px-4 py-2 rounded text-sm font-medium transition">🚀 Páginas</button>
            <button onclick="showTab('stats')" id="tab-stats" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">📊 Estadísticas</button>
            <button onclick="showTab('ai')" id="tab-ai" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">🤖 Agente IA</button>
            <button onclick="showTab('lic')" id="tab-lic" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">Licencias</button>
            <button onclick="showTab('updates')" id="tab-updates" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">🔄 Actualizaciones</button>
            <button onclick="showTab('downloads')" id="tab-downloads" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">📥 Descargas</button>
            <button onclick="showTab('marketing')" id="tab-marketing" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">🧠 Marketing IA</button>
            <button onclick="showTab('settings')" id="tab-settings" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">⚙️ Ajustes</button>
            <a href="/admin/logout" class="bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded text-sm font-bold transition ml-2"><i class="fas fa-sign-out-alt mr-1"></i>Salir</a>
        </div>
    </nav>
    <div class="flex-1 container mx-auto p-6 md:p-10 max-w-4xl">
    
    <!-- PÁGINAS -->
    <div id="content-pages" class="space-y-6 hidden">
        <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
            <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Gestor de Landing Pages</h3>
            <div class="flex gap-2 mb-4">
                <select id="page_selector" onchange="loadPageData()" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none"></select>
                <button onclick="createPage()" class="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded text-sm font-bold whitespace-nowrap"><i class="fas fa-plus"></i> Nueva</button>
                <button onclick="duplicatePage()" class="bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-2 rounded text-sm font-bold whitespace-nowrap"><i class="fas fa-copy"></i> Duplicar</button>
                <button onclick="deletePage()" class="bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded text-sm font-bold whitespace-nowrap"><i class="fas fa-trash"></i></button>
            </div>
            <p class="text-xs text-slate-400 mb-4">URL de la página: <span id="page_url_preview" class="text-cyan-400"></span></p>
        </div>
        <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
            <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Textos Principales (Hero)</h3>
            <input type="hidden" id="current_slug">
            <label class="text-sm text-slate-400">Nombre Interno</label>
            <input type="text" id="page_name" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700 focus:border-cyan-500 outline-none">
            <label class="text-sm text-slate-400">ID del Chatbot (Chatbase)</label>
            <input type="text" id="chatbot_id" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700 focus:border-cyan-500 outline-none" placeholder="gzEjAzK1VCE72hJ_hBfA4">
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
            <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">📥 Enlaces de Descarga</h3>
            <p class="text-sm text-slate-400 mb-4">Agrega uno o varios enlaces. El usuario verá botones de "Servidor 1", "Servidor 2", etc.</p>
            <div id="dl-links-container" class="space-y-2 mb-4"></div>
            <button onclick="addDlLink()" class="mt-2 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded text-sm font-bold"><i class="fas fa-plus mr-2"></i>Agregar Enlace</button>
            <div class="mt-6">
                <label class="text-sm text-slate-400">Instrucciones de Instalación</label>
                <textarea id="download_instructions" rows="4" class="w-full bg-slate-900 rounded p-2 border border-slate-700 focus:border-cyan-500 outline-none" placeholder="Ej: 1. Descarga el archivo..."></textarea>
            </div>
        </div>
        <div class="bg-slate-800 p-6 rounded-xl border border-amber-700 shadow-lg">
            <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">💳 Pagos por Transferencia Bancaria</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div><label class="text-sm text-slate-400">Nombre del Banco</label><input type="text" id="bt_bank_name" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
                <div><label class="text-sm text-slate-400">Tipo de Cuenta</label><input type="text" id="bt_account_type" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
                <div><label class="text-sm text-slate-400">Número de Cuenta / IBAN</label><input type="text" id="bt_account_number" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
                <div><label class="text-sm text-slate-400">Beneficiario</label><input type="text" id="bt_beneficiary" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
                <div><label class="text-sm text-slate-400">Correo para comprobante</label><input type="email" id="bt_email" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
                <div><label class="text-sm text-slate-400">WhatsApp para comprobante</label><input type="text" id="bt_whatsapp" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
            </div>
        </div>
        <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
            <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Publicaciones (Galería)</h3>
            <div id="pubs-container" class="space-y-4"></div>
            <button onclick="addPubRow()" class="mt-4 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded text-sm font-bold"><i class="fas fa-plus mr-2"></i>Agregar Publicación</button>
        </div>
        <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
            <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Planes de Suscripción (PayPal)</h3>
            <div class="bg-slate-900 p-3 rounded mb-4 text-amber-400 text-xs">💡 IMPORTANTE: En "Enlace de pago", pon únicamente el ID del plan de PayPal (Ej: P-78W24779DJ167620XNKNUHYY).</div>
            <div id="plans-container" class="space-y-6"></div>
            <button onclick="addPlanRow()" class="mt-4 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded text-sm font-bold"><i class="fas fa-plus mr-2"></i>Agregar Plan</button>
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
    
    <!-- STATS -->
    <div id="content-stats" class="hidden space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 text-center">
                <h3 class="text-sm text-slate-400 uppercase tracking-wider mb-2">Visitas Totales</h3>
                <p id="stat_views" class="text-5xl font-extrabold text-cyan-400">0</p>
            </div>
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 text-center">
                <h3 class="text-sm text-slate-400 uppercase tracking-wider mb-2">Leads Capturados</h3>
                <p id="stat_leads_count" class="text-5xl font-extrabold text-emerald-400">0</p>
            </div>
        </div>
        <div class="bg-slate-800 p-6 rounded-xl border border-slate-700">
            <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">📧 Leads Capturados (Agente IA)</h3>
            <div id="stat_leads" class="space-y-2 max-h-96 overflow-y-auto"></div>
        </div>
    </div>
    
    <!-- AGENTE IA -->
    <div id="content-ai" class="hidden space-y-6">
        <div class="bg-slate-800 p-6 rounded-xl border border-cyan-700">
            <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">🤖 Agente IA (Seguimiento de Leads)</h3>
            <p class="text-sm text-slate-400 mb-6">Usa la variable <code class="bg-slate-900 p-1 rounded text-cyan-400">{{name}}</code> para personalizar.</p>
            <div class="space-y-8">
                <div class="bg-slate-900 p-4 rounded-lg border border-slate-700">
                    <h4 class="text-cyan-400 font-bold mb-3">Seguimiento 1</h4>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-3">
                        <div><label class="text-sm text-slate-400">Días</label><input type="number" id="s1_days" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none" value="2"></div>
                        <div class="md:col-span-3"><label class="text-sm text-slate-400">Asunto</label><input type="text" id="s1_subject" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none"></div>
                    </div>
                    <label class="text-sm text-slate-400">Mensaje</label>
                    <textarea id="s1_body" rows="4" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none"></textarea>
                </div>
                <div class="bg-slate-900 p-4 rounded-lg border border-slate-700">
                    <h4 class="text-cyan-400 font-bold mb-3">Seguimiento 2</h4>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-3">
                        <div><label class="text-sm text-slate-400">Días</label><input type="number" id="s2_days" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none" value="5"></div>
                        <div class="md:col-span-3"><label class="text-sm text-slate-400">Asunto</label><input type="text" id="s2_subject" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none"></div>
                    </div>
                    <label class="text-sm text-slate-400">Mensaje</label>
                    <textarea id="s2_body" rows="4" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none"></textarea>
                </div>
                <div class="bg-slate-900 p-4 rounded-lg border border-slate-700">
                    <h4 class="text-cyan-400 font-bold mb-3">Seguimiento 3 (Cierre)</h4>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-3">
                        <div><label class="text-sm text-slate-400">Días</label><input type="number" id="s3_days" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none" value="10"></div>
                        <div class="md:col-span-3"><label class="text-sm text-slate-400">Asunto</label><input type="text" id="s3_subject" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none"></div>
                    </div>
                    <label class="text-sm text-slate-400">Mensaje</label>
                    <textarea id="s3_body" rows="4" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none"></textarea>
                </div>
            </div>
            <button onclick="saveAIConfig()" class="mt-6 w-full bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold py-3 rounded transition"><i class="fas fa-save mr-2"></i>Guardar Configuración IA</button>
        </div>
    </div>
    
    <!-- LICENCIAS -->
    <div id="content-lic" class="hidden space-y-6">
        <div class="bg-slate-800 p-6 rounded-xl border border-emerald-700">
            <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">➕ Crear Licencia Manualmente</h3>
            <p class="text-sm text-slate-400 mb-4">Usa esta función cuando recibas el comprobante de transferencia bancaria.</p>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <select id="manual_plan" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500">
                    <option value="BRONCE">Bronce</option><option value="PLATA">Plata</option><option value="ORO">Oro</option>
                </select>
                <input type="number" id="manual_days" value="30" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500">
                <input type="email" id="manual_email" placeholder="cliente@correo.com" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500">
            </div>
            <button onclick="createManualLicense()" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded text-sm font-bold transition"><i class="fas fa-key mr-2"></i>Generar Licencia</button>
            <div id="manual_lic_msg" class="mt-4 text-cyan-400 font-bold text-sm hidden bg-slate-900 p-3 rounded"></div>
        </div>
        <div class="bg-slate-800 p-6 rounded-xl border border-slate-700">
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
    
    <!-- UPDATES -->
    <div id="content-updates" class="hidden space-y-6">
        <div class="bg-slate-800 p-6 rounded-xl border border-cyan-700">
            <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">🔄 Gestión de Versiones del Bot</h3>
            <p class="text-sm text-slate-400 mb-4">Configura los parámetros que recibirán los bots al iniciar sesión.</p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div><label class="text-sm text-slate-400">Última Versión</label><input type="text" id="upd_version" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Ej: 1.1.0"></div>
                <div><label class="text-sm text-slate-400">URL de Descarga</label><input type="text" id="upd_url" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="https://mega.nz/..."></div>
            </div>
            <div class="mb-4"><label class="text-sm text-slate-400">Mensaje de la Actualización</label><textarea id="upd_message" rows="3" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Ej: Corrección de errores."></textarea></div>
            <div class="flex items-center gap-2 mb-6 p-3 bg-slate-900 rounded border border-slate-700"><input type="checkbox" id="upd_force" class="w-5 h-5 accent-red-500"><label for="upd_force" class="text-sm text-slate-300 cursor-pointer">Forzar Actualización Obligatoria</label></div>
            <button onclick="saveUpdateConfig()" class="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold py-3 rounded transition"><i class="fas fa-save mr-2"></i>Guardar y Publicar Versión</button>
        </div>
    </div>
    
    <!-- DESCARGAS MULTI-OS -->
    <div id="content-downloads" class="hidden space-y-6">
        <div class="bg-slate-800 p-6 rounded-xl border border-indigo-700 shadow-lg">
            <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">📥 Gestión de Descargas Multi-OS</h3>
            <p class="text-sm text-slate-400 mb-4">Agrega versiones para diferentes SO. Los usuarios las verán en <code class="bg-slate-900 p-1 rounded text-cyan-400">/download</code>.</p>
            <div class="bg-slate-900 p-4 rounded-lg border border-slate-700 mb-4">
                <h4 class="text-cyan-400 font-bold mb-3">➕ Nueva / Editar Descarga</h4>
                <input type="hidden" id="dl_edit_id">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div><label class="text-sm text-slate-400">Versión</label><input type="text" id="dl_version" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Ej: 16.03"></div>
                    <div><label class="text-sm text-slate-400">Sistema Operativo</label>
                        <select id="dl_os" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500">
                            <option value="Windows">🪟 Windows</option>
                            <option value="Linux">🐧 Linux</option>
                            <option value="macOS">🍎 macOS</option>
                            <option value="Android">🤖 Android</option>
                            <option value="iOS">📱 iOS</option>
                        </select>
                    </div>
                    <div><label class="text-sm text-slate-400">URL de Descarga</label><input type="text" id="dl_url" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="https://mega.nz/..."></div>
                    <div><label class="text-sm text-slate-400">Tamaño del Archivo</label><input type="text" id="dl_size" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Ej: 85 MB"></div>
                    <div><label class="text-sm text-slate-400">Fecha de Lanzamiento</label><input type="date" id="dl_date" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
                    <div class="flex items-end"><label class="text-sm flex items-center gap-2 cursor-pointer"><input type="checkbox" id="dl_active" class="w-5 h-5 accent-emerald-500" checked> <span class="text-slate-300">Activa (visible para usuarios)</span></label></div>
                </div>
                <div class="mt-4"><label class="text-sm text-slate-400">Descripción de la Versión</label><textarea id="dl_description" rows="3" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Novedades de esta versión..."></textarea></div>
                <div class="flex gap-2 mt-4">
                    <button onclick="saveDownload()" class="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2 rounded text-sm font-bold transition"><i class="fas fa-save mr-2"></i>Guardar Descarga</button>
                    <button onclick="clearDownloadForm()" class="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded text-sm transition">Limpiar</button>
                </div>
            </div>
            <h4 class="text-white font-bold mb-3">📋 Descargas Existentes</h4>
            <div id="downloads_list" class="space-y-3"></div>
        </div>
    </div>
    
    <!-- MARKETING -->
    <div id="content-marketing" class="hidden space-y-6">
        <div class="bg-slate-800 p-6 rounded-xl border border-purple-700">
            <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">🧠 Generador de Tráfico y Leads con IA</h3>
            <p class="text-sm text-slate-400 mb-4">Elige qué tipo de contenido quieres que la IA (Google Gemini) cree.</p>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <button onclick="generateMarketing('seo_blog')" class="bg-purple-600 hover:bg-purple-500 text-white p-4 rounded text-sm font-bold transition"><i class="fas fa-blog mr-2"></i>Artículo SEO</button>
                <button onclick="generateMarketing('tiktok_script')" class="bg-pink-600 hover:bg-pink-500 text-white p-4 rounded text-sm font-bold transition"><i class="fab fa-tiktok mr-2"></i>Guion TikTok</button>
                <button onclick="generateMarketing('forum_post')" class="bg-blue-600 hover:bg-blue-500 text-white p-4 rounded text-sm font-bold transition"><i class="fab fa-reddit mr-2"></i>Post Foro</button>
            </div>
            <div id="marketing_output" class="bg-slate-900 p-4 rounded border border-slate-700 text-slate-300 text-sm whitespace-pre-wrap min-h-[200px]">El contenido generado aparecerá aquí...</div>
            <button onclick="copyMarketing()" class="mt-4 bg-cyan-500 hover:bg-cyan-400 text-slate-900 px-4 py-2 rounded text-sm font-bold transition"><i class="fas fa-copy mr-2"></i>Copiar Contenido</button>
        </div>
    </div>
    
    <!-- AJUSTES -->
    <div id="content-settings" class="hidden space-y-6">
        <div class="bg-slate-800 p-6 rounded-xl border border-amber-700">
            <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">🔑 Cambiar Contraseña</h3>
            <p class="text-sm text-slate-400 mb-4">Cambia la contraseña de acceso al panel.</p>
            <div class="space-y-4">
                <div><label class="text-sm text-slate-400">Contraseña Actual</label><input type="password" id="current_pwd" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="••••••••"></div>
                <div><label class="text-sm text-slate-400">Nueva Contraseña</label><input type="password" id="new_pwd" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="••••••"></div>
                <div><label class="text-sm text-slate-400">Repetir Nueva Contraseña</label><input type="password" id="confirm_pwd" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="••••••"></div>
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
    <div id="toast" class="fixed bottom-5 right-5 bg-slate-700 text-white px-4 py-3 rounded-lg shadow-2xl opacity-0 transition-opacity duration-300 pointer-events-none"><span id="toast-msg"></span></div>
    
    <script id="pages-data" type="application/json">{pages_json}</script>
    <script>
    const allPages = JSON.parse(document.getElementById('pages-data').textContent);
    let currentMarketingText = "";
    
    function showTab(tabId) {{
        ['pages','stats','ai','lic','updates','downloads','marketing','settings'].forEach(id => {{
            document.getElementById('content-' + id).classList.add('hidden');
            document.getElementById('tab-' + id).classList.remove('tab-active');
            document.getElementById('tab-' + id).classList.add('bg-slate-800','hover:bg-slate-700');
        }});
        document.getElementById('content-' + tabId).classList.remove('hidden');
        document.getElementById('tab-' + tabId).classList.add('tab-active');
        document.getElementById('tab-' + tabId).classList.remove('bg-slate-800','hover:bg-slate-700');
        if(tabId === 'stats') loadStats();
        if(tabId === 'ai') loadAIConfig();
        if(tabId === 'updates') loadUpdateConfig();
        if(tabId === 'downloads') loadDownloads();
    }}
    
    function showToast(msg) {{
        const t = document.getElementById('toast');
        document.getElementById('toast-msg').innerText = msg;
        t.classList.remove('opacity-0');
        setTimeout(() => t.classList.add('opacity-0'), 3000);
    }}
    
    function updateSelector() {{
        const sel = document.getElementById('page_selector');
        sel.innerHTML = '';
        Object.keys(allPages).forEach(slug => {{
            let opt = document.createElement('option');
            opt.value = slug;
            opt.innerText = allPages[slug].page_name || slug;
            sel.appendChild(opt);
        }});
        if(Object.keys(allPages).length > 0) {{ sel.value = Object.keys(allPages)[0]; loadPageData(); }}
    }}
    
    function loadPageData() {{
        const slug = document.getElementById('page_selector').value;
        if(!slug) return;
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
        if(dlLinks.length === 0) addDlLink(''); else dlLinks.forEach(url => addDlLink(url || ''));
        
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
        (p.publications || []).length === 0 ? addPubRow() : p.publications.forEach(pub => addPubRow(pub.type, pub.url, pub.desc));
        
        document.getElementById('plans-container').innerHTML = '';
        (p.plans || []).length === 0 ? addPlanRow() : p.plans.forEach(pl => addPlanRow(pl.name, pl.price, pl.features, pl.link, pl.highlight));
        
        document.getElementById('page_url_preview').innerText = slug === 'main' ? 'tudominio.com/' : 'tudominio.com/p/' + slug;
    }}
    
    function createPage() {{
        const name = prompt('Nombre de la nueva página:');
        if(!name) return;
        let slug = prompt('URL (ej: promo-black):');
        if(!slug) return;
        slug = slug.toLowerCase().replace(/[^a-z0-9-]/g,'');
        if(allPages[slug]) {{ alert('Ya existe'); return; }}
        allPages[slug] = {{page_name:name,chatbot_id:'gzEjAzK1VCE72hJ_hBfA4',hero_title:name,hero_subtitle:'',hero_text:'',affiliate_link:'',affiliate_text:'',publications:[],plans:[],social_links:{{}},bank_transfer_info:{{}},download_links:[],download_instructions:''}};
        saveData(true);
    }}
    
    function duplicatePage() {{
        const cur = document.getElementById('page_selector').value;
        const newSlug = prompt('URL para la copia:');
        if(!newSlug) return;
        const slug = newSlug.toLowerCase().replace(/[^a-z0-9-]/g,'');
        if(allPages[slug]) {{ alert('Ya existe'); return; }}
        allPages[slug] = JSON.parse(JSON.stringify(allPages[cur]));
        allPages[slug].page_name += ' (Copia)';
        saveData(true);
    }}
    
    function deletePage() {{
        const slug = document.getElementById('page_selector').value;
        if(slug === 'main') {{ alert('No puedes eliminar la principal'); return; }}
        if(confirm('¿Eliminar?')) {{ delete allPages[slug]; saveData(true); }}
    }}
    
    function addDlLink(url='') {{
        const c = document.getElementById('dl-links-container');
        const div = document.createElement('div');
        div.className = 'flex gap-2';
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'dl-url w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500';
        input.placeholder = 'https://mega.nz/...';
        input.value = url;
        const btn = document.createElement('button');
        btn.className = 'bg-red-600 hover:bg-red-500 text-white px-3 py-2 rounded text-sm font-bold';
        btn.innerHTML = '<i class="fas fa-trash"></i>';
        btn.onclick = function() {{ this.parentElement.remove(); }};
        div.appendChild(input); div.appendChild(btn);
        c.appendChild(div);
    }}
    
    function addPubRow(type='video', url='', desc='') {{
        const c = document.getElementById('pubs-container');
        const div = document.createElement('div');
        div.className = 'bg-slate-900 p-4 rounded border border-slate-700';
        div.innerHTML = '<select class="pub-type w-full bg-slate-800 rounded p-2 mb-2 border border-slate-700 outline-none"><option value="video"'+(type=='video'?' selected':'')+'>Video YouTube</option><option value="image"'+(type=='image'?' selected':'')+'>Imagen</option></select><input type="text" class="pub-url w-full bg-slate-800 rounded p-2 mb-2 border border-slate-700 outline-none" placeholder="URL" value="'+url+'"><textarea class="pub-desc w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none" placeholder="Descripción">'+desc+'</textarea><button onclick="this.parentElement.remove()" class="mt-2 text-red-500 text-xs"><i class="fas fa-trash mr-1"></i>Eliminar</button>';
        c.appendChild(div);
    }}
    
    function addPlanRow(name='', price='', features='', link='', highlight=false) {{
        const c = document.getElementById('plans-container');
        const div = document.createElement('div');
        div.className = 'bg-slate-900 p-4 rounded border border-slate-700';
        div.innerHTML = '<div class="grid grid-cols-1 md:grid-cols-2 gap-2"><input type="text" class="p-name bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Nombre" value="'+name+'"><input type="text" class="p-price bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Precio" value="'+price+'"></div><textarea class="p-features w-full bg-slate-800 rounded p-2 my-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Características">'+features+'</textarea><input type="text" class="p-link w-full bg-slate-800 rounded p-2 mb-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="ID PayPal" value="'+link+'"><div class="flex justify-between items-center"><label class="text-sm flex items-center gap-2"><input type="checkbox" class="p-highlight accent-cyan-500" '+(highlight?'checked':'')+'> Destacar</label><button onclick="this.parentElement.parentElement.remove()" class="text-red-500 text-xs"><i class="fas fa-trash"></i></button></div>';
        c.appendChild(div);
    }}
    
    async function saveData(reload=false) {{
        const slug = document.getElementById('current_slug').value || document.getElementById('page_selector').value;
        if(!slug) {{ showToast('❌ No hay página'); return; }}
        let pubs = [];
        document.querySelectorAll('#pubs-container > div').forEach(div => {{
            const u = div.querySelector('.pub-url');
            if(u && u.value.trim()) pubs.push({{type:div.querySelector('.pub-type').value, url:u.value, desc:div.querySelector('.pub-desc').value}});
        }});
        let plans = [];
        document.querySelectorAll('#plans-container > div').forEach(div => {{
            const n = div.querySelector('.p-name');
            if(n && n.value.trim()) plans.push({{name:n.value, price:div.querySelector('.p-price').value, features:div.querySelector('.p-features').value, link:div.querySelector('.p-link').value, highlight:div.querySelector('.p-highlight').checked}});
        }});
        let dlLinks = [];
        document.querySelectorAll('#dl-links-container > div').forEach(div => {{
            const u = div.querySelector('.dl-url');
            if(u && u.value.trim()) dlLinks.push(u.value.trim());
        }});
        allPages[slug] = {{
            page_name: document.getElementById('page_name').value,
            chatbot_id: document.getElementById('chatbot_id').value || 'gzEjAzK1VCE72hJ_hBfA4',
            hero_title: document.getElementById('hero_title').value,
            hero_subtitle: document.getElementById('hero_subtitle').value,
            hero_text: document.getElementById('hero_text').value,
            affiliate_link: document.getElementById('affiliate_link').value,
            affiliate_text: document.getElementById('affiliate_text').value,
            publications: pubs, plans: plans,
            social_links: {{facebook:document.getElementById('fb_link').value,whatsapp:document.getElementById('wa_link').value,youtube:document.getElementById('yt_link').value,tiktok:document.getElementById('tt_link').value,telegram:document.getElementById('tg_link').value,instagram:document.getElementById('ig_link').value}},
            bank_transfer_info: {{bank_name:document.getElementById('bt_bank_name').value,account_type:document.getElementById('bt_account_type').value,account_number:document.getElementById('bt_account_number').value,beneficiary:document.getElementById('bt_beneficiary').value,email_for_proof:document.getElementById('bt_email').value,whatsapp_for_proof:document.getElementById('bt_whatsapp').value}},
            download_links: dlLinks,
            download_instructions: document.getElementById('download_instructions').value
        }};
        const res = await fetch('/api/save_pages', {{method:'POST',credentials:'same-origin',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(allPages)}});
        const r = await res.json();
        showToast(r.message);
        if(reload) updateSelector();
    }}
    
    async function loadStats() {{
        const res = await fetch('/api/get_stats', {{credentials:'same-origin'}});
        const data = await res.json();
        document.getElementById('stat_views').innerText = data.views || 0;
        const leads = data.captured_leads || [];
        document.getElementById('stat_leads_count').innerText = leads.length;
        let html = '';
        leads.slice().reverse().forEach(l => {{
            let stage = l.follow_up_stage === 0 ? 'Email Inicial' : l.follow_up_stage === 1 ? 'Seguimiento 1' : l.follow_up_stage === 2 ? 'Seguimiento 2' : 'Finalizado';
            html += '<div class="bg-slate-900 p-3 rounded border border-slate-700"><div class="flex justify-between"><span class="text-cyan-400 font-bold text-sm">'+l.name+' - '+l.email+'</span><span class="text-slate-500 text-xs">'+(l.date?l.date.split('T')[0]:'')+'</span></div><div class="text-emerald-400 text-xs mt-1">🤖 '+stage+'</div></div>';
        }});
        document.getElementById('stat_leads').innerHTML = html || '<p class="text-slate-500 text-sm">Sin leads.</p>';
    }}
    
    async function loadAIConfig() {{
        const res = await fetch('/api/get_ai_config', {{credentials:'same-origin'}});
        const cfg = await res.json();
        document.getElementById('s1_days').value = cfg.stage1_days || 2;
        document.getElementById('s1_subject').value = cfg.stage1_subject || '';
        document.getElementById('s1_body').value = cfg.stage1_body || '';
        document.getElementById('s2_days').value = cfg.stage2_days || 5;
        document.getElementById('s2_subject').value = cfg.stage2_subject || '';
        document.getElementById('s2_body').value = cfg.stage2_body || '';
        document.getElementById('s3_days').value = cfg.stage3_days || 10;
        document.getElementById('s3_subject').value = cfg.stage3_subject || '';
        document.getElementById('s3_body').value = cfg.stage3_body || '';
    }}
    
    async function saveAIConfig() {{
        const payload = {{
            stage1_days:parseInt(document.getElementById('s1_days').value),stage1_subject:document.getElementById('s1_subject').value,stage1_body:document.getElementById('s1_body').value,
            stage2_days:parseInt(document.getElementById('s2_days').value),stage2_subject:document.getElementById('s2_subject').value,stage2_body:document.getElementById('s2_body').value,
            stage3_days:parseInt(document.getElementById('s3_days').value),stage3_subject:document.getElementById('s3_subject').value,stage3_body:document.getElementById('s3_body').value
        }};
        const res = await fetch('/api/save_ai_config', {{method:'POST',credentials:'same-origin',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(payload)}});
        showToast((await res.json()).message);
    }}
    
    async function loadUpdateConfig() {{
        const res = await fetch('/api/get_update_config', {{credentials:'same-origin'}});
        const data = await res.json();
        document.getElementById('upd_version').value = data.latest_version || '';
        document.getElementById('upd_url').value = data.download_url || '';
        document.getElementById('upd_message').value = data.update_message || '';
        document.getElementById('upd_force').checked = data.force_update || false;
    }}
    
    async function saveUpdateConfig() {{
        const payload = {{
            latest_version:document.getElementById('upd_version').value,
            download_url:document.getElementById('upd_url').value,
            force_update:document.getElementById('upd_force').checked,
            update_message:document.getElementById('upd_message').value
        }};
        const res = await fetch('/api/save_update_config', {{method:'POST',credentials:'same-origin',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(payload)}});
        showToast((await res.json()).message);
    }}
    
    async function loadDownloads() {{
        const res = await fetch('/api/get_downloads');
        const data = await res.json();
        const list = document.getElementById('downloads_list');
        if(!data || data.length === 0) {{ list.innerHTML = '<p class="text-slate-500 text-sm text-center py-4">Sin descargas.</p>'; return; }}
        const icons = {{'Windows':'🪟','Linux':'🐧','macOS':'🍎','Android':'🤖','iOS':'📱'}};
        let html = '';
        data.forEach(d => {{
            const icon = icons[d.os] || '📦';
            const active = d.is_active ? '<span class="text-emerald-400 text-xs">✅ Activa</span>' : '<span class="text-red-400 text-xs">❌ Inactiva</span>';
            html += '<div class="bg-slate-900 p-4 rounded-lg border border-slate-700 flex justify-between items-center"><div><div class="flex items-center gap-2 mb-1"><span class="text-2xl">'+icon+'</span><span class="text-cyan-400 font-bold">v'+d.version+'</span><span class="text-slate-500 text-xs">('+d.os+')</span>'+active+'</div><p class="text-slate-400 text-xs">'+(d.description||'').substring(0,80)+'</p></div><div class="flex gap-2"><button onclick="editDownload(\\''+d.id+'\\')" class="bg-amber-600 hover:bg-amber-500 text-white px-3 py-1 rounded text-xs font-bold"><i class="fas fa-edit"></i></button><button onclick="deleteDownload(\\''+d.id+'\\')" class="bg-red-600 hover:bg-red-500 text-white px-3 py-1 rounded text-xs font-bold"><i class="fas fa-trash"></i></button></div></div>';
        }});
        list.innerHTML = html;
    }}
    
    async function saveDownload() {{
        const payload = {{
            id: document.getElementById('dl_edit_id').value || null,
            version: document.getElementById('dl_version').value,
            os: document.getElementById('dl_os').value,
            download_url: document.getElementById('dl_url').value,
            description: document.getElementById('dl_description').value,
            file_size: document.getElementById('dl_size').value,
            release_date: document.getElementById('dl_date').value,
            is_active: document.getElementById('dl_active').checked
        }};
        if(!payload.version || !payload.download_url) {{ showToast('❌ Versión y URL obligatorios'); return; }}
        const res = await fetch('/api/save_download', {{method:'POST',credentials:'same-origin',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(payload)}});
        showToast((await res.json()).message);
        clearDownloadForm();
        loadDownloads();
    }}
    
    function clearDownloadForm() {{
        document.getElementById('dl_edit_id').value = '';
        document.getElementById('dl_version').value = '';
        document.getElementById('dl_os').value = 'Windows';
        document.getElementById('dl_url').value = '';
        document.getElementById('dl_description').value = '';
        document.getElementById('dl_size').value = '';
        document.getElementById('dl_date').value = '';
        document.getElementById('dl_active').checked = true;
    }}
    
    async function editDownload(id) {{
        const res = await fetch('/api/get_downloads');
        const data = await res.json();
        const dl = data.find(d => d.id === id);
        if(!dl) return;
        document.getElementById('dl_edit_id').value = dl.id;
        document.getElementById('dl_version').value = dl.version || '';
        document.getElementById('dl_os').value = dl.os || 'Windows';
        document.getElementById('dl_url').value = dl.download_url || '';
        document.getElementById('dl_description').value = dl.description || '';
        document.getElementById('dl_size').value = dl.file_size || '';
        document.getElementById('dl_date').value = dl.release_date || '';
        document.getElementById('dl_active').checked = dl.is_active !== false;
    }}
    
    async function deleteDownload(id) {{
        if(!confirm('¿Eliminar?')) return;
        const res = await fetch('/api/delete_download', {{method:'POST',credentials:'same-origin',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{id:id}})}});
        showToast((await res.json()).message);
        loadDownloads();
    }}
    
    async function createManualLicense() {{
        const payload = {{plan:document.getElementById('manual_plan').value,days:document.getElementById('manual_days').value,email:document.getElementById('manual_email').value}};
        const res = await fetch('/api/create_license', {{method:'POST',credentials:'same-origin',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(payload)}});
        const r = await res.json();
        if(r.key) {{ document.getElementById('manual_lic_msg').innerText = '✅ Licencia: ' + r.key; document.getElementById('manual_lic_msg').classList.remove('hidden'); }}
        else {{ showToast(r.message || 'Error'); }}
    }}
    
    async function manageLic(activate) {{
        const res = await fetch('/api/manage_license', {{method:'POST',credentials:'same-origin',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{key:document.getElementById('lic_key').value,activate:activate}})}});
        showToast((await res.json()).message);
    }}
    
    async function resetHwid() {{
        const res = await fetch('/api/reset_hwid', {{method:'POST',credentials:'same-origin',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{key:document.getElementById('lic_key').value}})}});
        showToast((await res.json()).message);
    }}
    
    async function generateMarketing(type) {{
        document.getElementById('marketing_output').innerText = '🧠 La IA está generando contenido...';
        const res = await fetch('/api/generate_marketing', {{method:'POST',credentials:'same-origin',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{type:type}})}});
        const r = await res.json();
        if(r.content) {{ currentMarketingText = r.content; document.getElementById('marketing_output').innerText = r.content; }}
        else {{ showToast('❌ Error generando contenido'); }}
    }}
    
    function copyMarketing() {{ navigator.clipboard.writeText(currentMarketingText); showToast('✅ Copiado'); }}
    
    async function changePassword() {{
        if(document.getElementById('new_pwd').value !== document.getElementById('confirm_pwd').value) {{ showToast('❌ Las contraseñas no coinciden'); return; }}
        const payload = {{current_password:document.getElementById('current_pwd').value,new_password:document.getElementById('new_pwd').value}};
        const res = await fetch('/api/change_password', {{method:'POST',credentials:'same-origin',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(payload)}});
        const r = await res.json();
        if(res.ok) {{ document.getElementById('pwd_msg').innerText = r.message; document.getElementById('pwd_msg').classList.remove('hidden'); document.getElementById('pwd_msg').className = 'mt-4 font-bold text-sm text-emerald-400'; }}
        else {{ showToast(r.detail || 'Error'); }}
    }}
    
    updateSelector();
    </script>
    </body></html>
    """
