from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import random, string, smtplib, os, requests, json, re, uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler
from supabase import create_client, Client

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

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

def verify_admin(request: Request):
    return request.cookies.get("blenin_session") == SESSION_TOKEN

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
        print(f"ERROR ENVIANDO CORREO: {e}")
        return False

def generate_dynamic_content_with_llama(prompt, max_tokens=800):
    gemini_api_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_api_key: return None
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={gemini_api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.7}}
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        return None
    except: return None

def get_default_ai_config():
    return {
        "stage1_days": 2, "stage1_subject": "🚀 {name}, descubre BLENIN.G.77",
        "stage1_body": "Hola {name},\n\nGracias por tu interés en BLENIN.G.77...",
        "stage2_days": 5, "stage2_subject": "🔥 {name}, no te quedes fuera...",
        "stage2_body": "Hola {name},\n\nLas oportunidades del mercado no esperan...",
        "stage3_days": 10, "stage3_subject": "⏳ {name}, tu acceso VIP está por expirar",
        "stage3_body": "Hola {name},\n\nUsa el código BLENIN10 para un 10% de descuento..."
    }

def get_default_update_config():
    return {"latest_version": "1.0.0", "download_url": "https://blenin77-server.onrender.com/", "force_update": False, "update_message": "Hay una nueva versión disponible."}

def load_dbs():
    try:
        if not supabase: raise Exception("Supabase no configurado")
        response = supabase.table("app_data").select("key, value").execute()
        data = {item['key']: item['value'] for item in response.data}
        return (data.get("licenses_db", {}), data.get("trials_db", {}),
                data.get("stats_db", {"views": 0, "countries": {}}),
                data.get("admin_password", os.environ.get("ADMIN_PASSWORD", "cambiar_esta_clave_123")),
                data.get("ai_agent_config", get_default_ai_config()),
                data.get("bot_update_config", get_default_update_config()))
    except:
        return {}, {}, {"views": 0, "countries": {}}, os.environ.get("ADMIN_PASSWORD", "cambiar_esta_clave_123"), get_default_ai_config(), get_default_update_config()

def save_dbs(lic, trials, stats, pwd=None, ai_cfg=None, upd_cfg=None):
    try:
        if not supabase: return
        def upsert(key, value):
            try: supabase.table("app_data").upsert({"key": key, "value": value}, on_conflict="key").execute()
            except Exception as e: print(f"Supabase {key}: {e}", flush=True)
        upsert("licenses_db", lic); upsert("trials_db", trials); upsert("stats_db", stats)
        if pwd: upsert("admin_password", pwd)
        if ai_cfg: upsert("ai_agent_config", ai_cfg)
        if upd_cfg: upsert("bot_update_config", upd_cfg)
    except Exception as e: print(f"save_dbs: {e}", flush=True)

licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config = load_dbs()
if not ai_agent_config or "stage1_subject" not in ai_agent_config:
    ai_agent_config = get_default_ai_config()

def get_default_downloads():
    return [{"id": "dl_001", "version": "16.03", "os": "Windows", "download_url": "https://mega.nz/file/example",
             "description": "Versión completa con IA Deep Learning, Enjambre de 500 Agentes y Modo Híbrido.",
             "file_size": "85 MB", "release_date": "2024-12-01", "is_active": True}]

def load_downloads_db():
    try:
        if not supabase: return get_default_downloads()
        response = supabase.table("app_data").select("value").eq("key", "downloads_db").execute()
        if response.data: return response.data[0]["value"]
        save_downloads_db(get_default_downloads())
        return get_default_downloads()
    except: return get_default_downloads()

def save_downloads_db(downloads):
    try:
        if not supabase: return False
        res = supabase.table("app_data").upsert({"key": "downloads_db", "value": downloads}, on_conflict="key").execute()
        return bool(res.data)
    except: return False

def get_default_content(page_name="Principal"):
    return {
        "page_name": page_name, "chatbot_id": "gzEjAzK1VCE72hJ_hBfA4",
        "hero_title": "BLENIN.G.77", "hero_subtitle": "THE BEST FUTURE FOR YOU",
        "hero_text": "IA Predictiva, Enjambre de 500 Agentes y Análisis Global en Tiempo Real.",
        "affiliate_link": "https://go.hotmart.com/W107659112D", "affiliate_text": "🚀 Afíliate (75%)",
        "publications": [{"type": "video", "url": "https://www.youtube.com/embed/dQw4w9WgXcQ", "desc": "Mira cómo el Enjambre abre operaciones reales."}],
        "plans": [
            {"name": "Bronce", "price": "$49", "features": "✅ 1 Cuenta MT5\n✅ Modo MT5 Puro", "link": "P-78W24779DJ167620XNKNUHYY", "highlight": False},
            {"name": "Plata", "price": "$99", "features": "✅ 2 Cuentas MT5\n✅ Modo Híbrido + Enjambre", "link": "P-5XY16476VG217634ANKNUHZA", "highlight": True},
            {"name": "Oro", "price": "$199", "features": "✅ Cuentas Ilimitadas\n✅ Deep Learning (PyTorch)", "link": "P-4LL21192X9335681FNKNUHZA", "highlight": False}
        ],
        "social_links": {"facebook": "", "whatsapp": "", "youtube": "", "tiktok": "", "telegram": "", "instagram": ""},
        "bank_transfer_info": {"bank_name": "", "account_type": "", "account_number": "", "beneficiary": "", "email_for_proof": "", "whatsapp_for_proof": ""},
        "download_links": [], "download_instructions": "1. Descarga el .zip\n2. Extrae\n3. Ejecuta Blenin77.exe\n4. Ingresa tu licencia."
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
        default_data = {"pages": {"main": get_default_content()}}
        save_all_pages(default_data)
        return default_data
    except:
        return {"pages": {"main": get_default_content()}}

def save_all_pages(data):
    try:
        if not supabase: return False
        res = supabase.table("app_data").upsert({"key": "pages", "value": data}, on_conflict="key").execute()
        return bool(res.data)
    except: return False

# ============ LOGIN ============
@app.get("/admin/login", response_class=HTMLResponse)
def admin_login_page():
    return '''<html lang="es"><head><meta charset="UTF-8"><title>Login Admin</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet">
    <style>body{font-family:'Inter',sans-serif}</style></head>
    <body class="bg-slate-900 text-slate-300 flex items-center justify-center min-h-screen">
    <div class="bg-slate-800 p-8 rounded-xl shadow-2xl border border-slate-700 w-full max-w-sm text-center">
    <h1 class="text-2xl font-bold text-cyan-400 mb-2">🔒 Acceso Restringido</h1>
    <p class="text-slate-400 mb-6 text-sm">Panel de Control BLENIN77</p>
    <p id="err" class="text-red-400 text-sm mb-4 hidden">Contraseña incorrecta.</p>
    <input type="password" id="pwd" placeholder="Contraseña" class="w-full bg-slate-900 rounded p-3 mb-4 border border-slate-700 outline-none focus:border-cyan-500">
    <button onclick="doLogin()" class="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold py-3 rounded">Ingresar</button>
    </div>
    <script>
    async function doLogin(){
    const pwd=document.getElementById('pwd').value;
    const res=await fetch('/api/login',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:pwd})});
    if(res.ok){window.location.href='/admin'}else{document.getElementById('err').classList.remove('hidden')}
    }
    </script></body></html>'''

@app.post("/api/login")
def admin_login_verify(data: AdminLoginData, response: Response):
    if data.password == admin_password_db:
        response.set_cookie(key="blenin_session", value=SESSION_TOKEN, httponly=True, secure=False, samesite="lax", max_age=86400)
        return {"status": "success"}
    raise HTTPException(status_code=401, detail="Contraseña incorrecta")

@app.get("/admin/logout")
def admin_logout(response: Response):
    response.delete_cookie(key="blenin_session")
    return RedirectResponse(url="/admin/login", status_code=303)

# ============ LANDING PAGE ============
@app.get("/", response_class=HTMLResponse)
@app.get("/p/{slug}", response_class=HTMLResponse)
def landing_page(slug: str = "main"):
    pages_data = get_all_pages()
    page = pages_data.get("pages", {}).get(slug, get_default_content())
    
    plans_html = ""
    for plan in page.get("plans", []):
        hl = "border-cyan-500 scale-105" if plan.get("highlight") else "border-slate-700"
        plans_html += f'<div class="bg-slate-800 p-6 rounded-xl border-2 {hl} text-center"><h3 class="text-xl font-bold text-white">{plan.get("name","")}</h3><p class="text-3xl font-extrabold text-cyan-400 my-2">{plan.get("price","")}</p><p class="text-slate-400 text-sm whitespace-pre-line">{plan.get("features","")}</p></div>'
    
    pubs_html = ""
    for pub in page.get("publications", []):
        if pub.get("type") == "video":
            pubs_html += f'<div class="bg-slate-800 rounded-xl overflow-hidden border border-slate-700"><div class="aspect-video"><iframe src="{pub.get("url","")}" frameborder="0" allowfullscreen class="w-full h-full"></iframe></div><p class="p-4 text-slate-400 text-sm">{pub.get("desc","")}</p></div>'
        else:
            pubs_html += f'<div class="bg-slate-800 rounded-xl overflow-hidden border border-slate-700"><img src="{pub.get("url","")}" class="w-full"><p class="p-4 text-slate-400 text-sm">{pub.get("desc","")}</p></div>'
    
    social = page.get("social_links", {})
    social_html = ""
    icons = {"facebook":"fab fa-facebook","whatsapp":"fab fa-whatsapp","youtube":"fab fa-youtube","tiktok":"fab fa-tiktok","telegram":"fab fa-telegram","instagram":"fab fa-instagram"}
    for name, url in social.items():
        if url: social_html += f'<a href="{url}" target="_blank" class="text-slate-400 hover:text-cyan-400 text-2xl transition"><i class="{icons.get(name,"fas fa-link")}"></i></a>'
    
    return f"""<html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{page.get('hero_title','BLENIN77')}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>body{{font-family:'Inter',sans-serif}}</style></head>
    <body class="bg-slate-900 text-slate-300">
    <nav class="bg-slate-950/80 backdrop-blur-md p-4 sticky top-0 z-50 border-b border-slate-800"><div class="container mx-auto max-w-6xl flex justify-between items-center">
    <span class="text-2xl font-extrabold text-cyan-400">BLENIN<span class="text-white">.G.77</span></span>
    <div class="flex gap-4 items-center"><a href="/download" class="text-cyan-400 hover:text-cyan-300 text-sm font-bold transition"><i class="fas fa-download mr-1"></i>Descargar</a>
    <a href="{page.get('affiliate_link','')}" class="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg text-sm font-bold transition">{page.get('affiliate_text','🚀 Afíliate')}</a></div></div></nav>
    <div class="container mx-auto max-w-6xl px-4 py-20 text-center">
    <h1 class="text-5xl md:text-7xl font-extrabold text-white mb-4">{page.get('hero_title','')}</h1>
    <p class="text-2xl text-cyan-400 font-bold mb-6">{page.get('hero_subtitle','')}</p>
    <p class="text-slate-400 text-lg max-w-2xl mx-auto mb-10">{page.get('hero_text','')}</p>
    <div class="max-w-md mx-auto bg-slate-800 p-8 rounded-2xl border border-slate-700 shadow-2xl">
    <h2 class="text-xl font-bold text-white mb-2"><i class="fas fa-envelope text-cyan-400 mr-2"></i>Descarga el Sistema</h2>
    <p class="text-slate-400 text-sm mb-4">Deja tu correo y te redirigiremos a las descargas.</p>
    <form onsubmit="captureEmail(event)">
    <input type="email" id="email_input" required placeholder="tu@correo.com" class="w-full bg-slate-900 rounded-lg p-3 mb-3 border border-slate-700 outline-none focus:border-cyan-500 text-white">
    <input type="text" id="name_input" placeholder="Tu nombre" class="w-full bg-slate-900 rounded-lg p-3 mb-4 border border-slate-700 outline-none focus:border-cyan-500 text-white">
    <button type="submit" class="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold py-3 rounded-lg transition"><i class="fas fa-download mr-2"></i>Ir a Descargas</button>
    </form></div></div>
    {('<div class="container mx-auto max-w-6xl px-4 py-12"><div class="grid grid-cols-1 md:grid-cols-3 gap-6">' + pubs_html + '</div></div>') if pubs_html else ''}
    {('<div class="container mx-auto max-w-6xl px-4 py-12"><h2 class="text-3xl font-bold text-white text-center mb-8">Planes</h2><div class="grid grid-cols-1 md:grid-cols-3 gap-6">' + plans_html + '</div></div>') if plans_html else ''}
    {('<div class="container mx-auto max-w-6xl px-4 py-8 text-center"><div class="flex justify-center gap-6">' + social_html + '</div></div>') if social_html else ''}
    <footer class="bg-slate-950 p-6 border-t border-slate-800"><div class="container mx-auto max-w-6xl text-center"><p class="text-slate-500 text-sm">© 2024 BLENIN.G.77 Trading Systems.</p></div></footer>
    <script>async function captureEmail(e){{e.preventDefault();const email=document.getElementById('email_input').value;const name=document.getElementById('name_input').value||'Usuario';try{{await fetch('/api/capture_lead',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{email:email,name:name,interaction:'Download'}})}})}}catch(e){{}};window.location.href='/download?email='+encodeURIComponent(email)}}</script>
    </body></html>"""

# ============ DOWNLOAD PAGE ============
@app.get("/download", response_class=HTMLResponse)
def download_page(email: str = ""):
    downloads = load_downloads_db()
    active = [d for d in downloads if d.get("is_active", True)]
    groups = {}
    for d in active:
        os_name = d.get("os", "Otros")
        if os_name not in groups: groups[os_name] = []
        groups[os_name].append(d)
    
    styles = {"Windows":("fab fa-windows","#00a4ef","from-blue-600 to-blue-800"),"Linux":("fab fa-linux","#fcc624","from-yellow-600 to-orange-700"),
              "macOS":("fab fa-apple","#ffffff","from-gray-600 to-gray-800"),"Android":("fab fa-android","#3ddc84","from-green-600 to-green-800"),
              "iOS":("fab fa-app-store-ios","#0d96f6","from-cyan-600 to-blue-800")}
    
    cards = ""
    for os_name, dls in groups.items():
        ic, col, bg = styles.get(os_name, ("fas fa-download","#00e5ff","from-slate-600 to-slate-800"))
        cards += f'<div class="bg-slate-800 rounded-2xl border border-slate-700 overflow-hidden shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105"><div class="bg-gradient-to-br {bg} p-6 text-center"><i class="{ic} text-5xl mb-2" style="color:{col}"></i><h3 class="text-xl font-bold text-white">{os_name}</h3></div><div class="p-6 space-y-4">'
        for d in dls:
            sz = f'<span class="text-xs text-slate-500">📦 {d.get("file_size","")}</span>' if d.get("file_size") else ""
            dt = d.get("release_date","")
            if dt:
                try: dt = datetime.fromisoformat(dt).strftime("%d/%m/%Y")
                except: pass
            dtb = f'<span class="text-xs text-slate-500">📅 {dt}</span>' if dt else ""
            cards += f'<div class="bg-slate-900 rounded-xl p-4 border border-slate-700 hover:border-cyan-500 transition"><div class="flex justify-between items-start mb-2"><span class="text-cyan-400 font-bold text-lg">v{d.get("version","1.0")}</span>{sz}</div><p class="text-slate-400 text-sm mb-4">{d.get("description","")}</p><div class="flex justify-between items-center">{dtb}<a href="{d.get("download_url","#")}" target="_blank" class="bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold px-6 py-2 rounded-lg transition inline-flex items-center gap-2"><i class="fas fa-download"></i> Descargar</a></div></div>'
        cards += "</div></div>"
    
    if not cards: cards = '<div class="text-center py-20"><i class="fas fa-box-open text-6xl text-slate-600 mb-4"></i><p class="text-slate-400 text-xl">No hay descargas disponibles.</p></div>'
    
    banner = f'<div class="bg-emerald-900/30 border border-emerald-700 rounded-xl p-4 mb-8 text-center"><p class="text-emerald-400 text-sm"><i class="fas fa-check-circle mr-2"></i>Correo registrado: <strong>{email}</strong></p></div>' if email else ""
    
    return f"""<html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Descargas - BLENIN.G.77</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>body{{font-family:'Inter',sans-serif;background:linear-gradient(135deg,#0f172a 0%,#1e293b 50%,#0f172a 100%)}}@keyframes fadeInUp{{from{{opacity:0;transform:translateY(30px)}}to{{opacity:1;transform:translateY(0)}}}}.fi{{animation:fadeInUp 0.6s ease-out forwards}}.fi1{{animation:fadeInUp 0.6s ease-out 0.15s forwards;opacity:0}}.fi2{{animation:fadeInUp 0.6s ease-out 0.3s forwards;opacity:0}}</style></head>
    <body class="text-slate-300 min-h-screen">
    <nav class="bg-slate-950/80 backdrop-blur-md p-4 sticky top-0 z-50 border-b border-slate-800"><div class="container mx-auto max-w-6xl flex justify-between items-center"><a href="/" class="text-2xl font-extrabold text-cyan-400">BLENIN<span class="text-white">.G.77</span></a><a href="/" class="text-slate-400 hover:text-cyan-400 text-sm transition"><i class="fas fa-arrow-left mr-1"></i>Volver</a></div></nav>
    <div class="container mx-auto max-w-6xl px-4 py-16 text-center fi"><div class="inline-block bg-cyan-500/10 border border-cyan-500/30 rounded-full px-4 py-1 mb-6"><span class="text-cyan-400 text-sm font-semibold"><i class="fas fa-rocket mr-1"></i> Centro de Descargas Oficial</span></div><h1 class="text-5xl md:text-6xl font-extrabold text-white mb-4">Descarga tu Sistema</h1><p class="text-slate-400 text-lg max-w-2xl mx-auto mb-8">Elige tu sistema operativo y descarga la última versión.</p>{banner}</div>
    <div class="container mx-auto max-w-6xl px-4 pb-16"><div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 fi1">{cards}</div></div>
    <div class="container mx-auto max-w-4xl px-4 pb-16 fi2"><div class="bg-slate-800/50 rounded-2xl border border-slate-700 p-8"><h2 class="text-2xl font-bold text-white mb-6 text-center"><i class="fas fa-info-circle text-cyan-400 mr-2"></i>Guía de Instalación</h2><div class="grid grid-cols-1 md:grid-cols-3 gap-6"><div class="text-center"><div class="bg-cyan-500/10 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3"><span class="text-2xl font-bold text-cyan-400">1</span></div><h3 class="text-white font-bold mb-2">Descarga</h3><p class="text-slate-400 text-sm">Haz clic en descargar.</p></div><div class="text-center"><div class="bg-cyan-500/10 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3"><span class="text-2xl font-bold text-cyan-400">2</span></div><h3 class="text-white font-bold mb-2">Extrae</h3><p class="text-slate-400 text-sm">Descomprime el .zip.</p></div><div class="text-center"><div class="bg-cyan-500/10 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3"><span class="text-2xl font-bold text-cyan-400">3</span></div><h3 class="text-white font-bold mb-2">Ejecuta</h3><p class="text-slate-400 text-sm">Abre el .exe e ingresa tu licencia.</p></div></div></div></div>
    <footer class="bg-slate-950 p-6 border-t border-slate-800"><div class="container mx-auto max-w-6xl text-center"><p class="text-slate-500 text-sm">© 2024 BLENIN.G.77 Trading Systems.</p></div></footer>
    </body></html>"""

# ============ DOWNLOAD API ============
@app.get("/api/get_downloads")
def get_downloads_api(): return load_downloads_db()

@app.post("/api/save_download")
def save_download_api(request: Request, entry: DownloadEntry):
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    downloads = load_downloads_db()
    if not entry.id:
        entry.id = f"dl_{uuid.uuid4().hex[:8]}"
        downloads.append(entry.dict())
    else:
        for i, d in enumerate(downloads):
            if d.get("id") == entry.id: downloads[i] = entry.dict(); break
        else: downloads.append(entry.dict())
    save_downloads_db(downloads)
    return {"status": "success", "message": "✅ Descarga guardada.", "id": entry.id}

@app.post("/api/delete_download")
def delete_download_api(request: Request, data: dict):
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    downloads = load_downloads_db()
    downloads = [d for d in downloads if d.get("id") != data.get("id")]
    save_downloads_db(downloads)
    return {"status": "success", "message": "🗑️ Descarga eliminada."}

# ============ UPDATE API ============
@app.get("/api/get_latest_version")
def get_latest_version(): return bot_update_config

@app.get("/api/get_update_config")
def get_update_config_api(): return bot_update_config or get_default_update_config()

@app.post("/api/save_update_config")
def save_update_config_api(request: Request, data: UpdateConfigData):
    global bot_update_config
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    bot_update_config = data.dict()
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
    return {"status": "success", "message": "✅ Configuración guardada."}

# ============ LEADS API ============
@app.post("/api/capture_lead")
def capture_lead(data: dict):
    global stats_db
    email = data.get("email", "")
    name = data.get("name", "Usuario")
    if not email: raise HTTPException(status_code=400, detail="Email requerido")
    if "captured_leads" not in stats_db: stats_db["captured_leads"] = []
    if not any(l.get("email") == email for l in stats_db["captured_leads"]):
        stats_db["captured_leads"].append({"email": email, "name": name, "date": datetime.now().isoformat(), "follow_up_stage": 0})
        save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
        try:
            subject = ai_agent_config.get("stage1_subject","Bienvenido").replace("{name}", name)
            body = ai_agent_config.get("stage1_body","Hola...").replace("{name}", name)
            send_email(email, subject, body)
        except: pass
    return {"status": "success", "message": "Correo registrado."}

# ============ STATS API ============
@app.get("/api/get_stats")
def get_stats_api(request: Request):
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    return stats_db

@app.middleware("http")
async def track_visits(request: Request, call_next):
    global stats_db
    response = await call_next(request)
    if not request.url.path.startswith("/admin") and not request.url.path.startswith("/api"):
        try:
            stats_db["views"] = stats_db.get("views", 0) + 1
            save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
        except: pass
    return response

# ============ AI CONFIG API ============
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
    return {"status": "success", "message": "✅ Configuración IA guardada."}

# ============ PAGES API ============
@app.post("/api/save_pages")
def save_pages_api(request: Request, data: dict):
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    if save_all_pages(data): return {"status": "success", "message": "✅ Páginas guardadas y publicadas."}
    return {"status": "error", "message": "❌ Error guardando en Supabase."}

# ============ LICENSES API ============
@app.post("/api/validate_license")
def validate_license(data: dict):
    key = data.get("key", "").upper()
    hwid = data.get("hwid", "")
    if key in licenses_db:
        lic = licenses_db[key]
        if not lic.get("active", False): return {"valid": False, "message": "Licencia suspendada."}
        try:
            if datetime.now() > datetime.fromisoformat(lic["expires"]): return {"valid": False, "message": "Licencia expirada."}
        except: pass
        if lic.get("hwid") and lic["hwid"] != hwid: return {"valid": False, "message": "HWID no coincide."}
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
        try:
            if datetime.now() > datetime.fromisoformat(trials_db[hwid]["expires"]): return {"valid": False, "message": "Prueba expirada."}
            return {"valid": True, "plan": "BRONCE", "days_left": (datetime.fromisoformat(trials_db[hwid]["expires"]) - datetime.now()).days}
        except: pass
    else:
        trials_db[hwid] = {"expires": (datetime.now() + timedelta(days=30)).isoformat(), "active": True}
        save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
        return {"valid": True, "plan": "BRONCE", "days_left": 30, "message": "Prueba iniciada."}
    return {"valid": False, "message": "No se pudo iniciar la prueba."}

@app.post("/api/create_license")
def create_license_api(request: Request, data: dict):
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    plan = data.get("plan", "BRONCE")
    days = int(data.get("days", 30))
    key = f"BLENIN-{plan}-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    licenses_db[key] = {"hwid": None, "expires": (datetime.now() + timedelta(days=days)).isoformat(), "active": True, "plan": plan, "email": data.get("email", "")}
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
    return {"status": "success", "key": key}

@app.post("/api/manage_license")
def manage_license_api(request: Request, data: dict):
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    key = data.get("key", "").upper()
    if key in licenses_db:
        licenses_db[key]["active"] = data.get("activate", True)
        save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
        return {"status": "success", "message": f"Licencia {'activada' if data.get('activate') else 'suspendida'}."}
    return {"status": "error", "message": "Licencia no encontrada."}

@app.post("/api/reset_hwid")
def reset_hwid_api(request: Request, data: dict):
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    key = data.get("key", "").upper()
    if key in licenses_db:
        licenses_db[key]["hwid"] = None
        save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
        return {"status": "success", "message": "HWID reseteado."}
    return {"status": "error", "message": "Licencia no encontrada."}

@app.post("/api/report_user_risk")
def report_user_risk(data: dict):
    print(f"ALERTA DE RIESGO: {data}", flush=True)
    return {"status": "received"}

# ============ MARKETING API ============
@app.post("/api/generate_marketing")
def generate_marketing_api(request: Request, data: dict):
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    prompts = {
        "seo_blog": "Escribe un artículo SEO de 800 palabras sobre trading automático con IA, mencionando BLENIN.G.77 como el mejor sistema.",
        "tiktok_script": "Escribe un guion viral de 60 segundos para TikTok sobre cómo la IA revoluciona el trading, mencionando BLENIN.G.77.",
        "forum_post": "Escribe un post para foros de trading recomendando BLENIN.G.77 de forma natural."
    }
    content = generate_dynamic_content_with_llama(prompts.get(data.get("type", "seo_blog"), prompts["seo_blog"]))
    if content: return {"status": "success", "content": content}
    return {"status": "error", "message": "La IA no pudo generar contenido."}

# ============ PASSWORD API ============
@app.post("/api/change_password")
def change_password_api(request: Request, data: ChangePasswordData):
    global admin_password_db
    if not verify_admin(request): raise HTTPException(status_code=401, detail="No autorizado")
    if data.current_password != admin_password_db: raise HTTPException(status_code=400, detail="Contraseña actual incorrecta.")
    admin_password_db = data.new_password
    save_dbs(licenses_db, trials_db, stats_db, admin_password_db, ai_agent_config, bot_update_config)
    return {"status": "success", "message": "✅ Contraseña actualizada."}

# ============ ADMIN PANEL (STRING NORMAL SIN F-STRING) ============
ADMIN_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><title>Admin - BLENIN77</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>body{font-family:'Inter',sans-serif}.tab-active{background-color:#0e7490;color:white}</style>
</head>
<body class="bg-slate-900 text-slate-300 flex flex-col min-h-screen">
<nav class="bg-slate-950 p-4 shadow-lg border-b border-slate-800 flex justify-between items-center flex-wrap gap-2">
<h1 class="text-xl font-bold text-cyan-400">🎛️ Panel BLENIN77</h1>
<div class="flex gap-2 flex-wrap items-center">
<button onclick="showTab('pages')" id="tab-pages" class="tab-active px-4 py-2 rounded text-sm font-medium transition">🚀 Páginas</button>
<button onclick="showTab('stats')" id="tab-stats" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">📊 Stats</button>
<button onclick="showTab('ai')" id="tab-ai" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">🤖 Agente IA</button>
<button onclick="showTab('lic')" id="tab-lic" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">Licencias</button>
<button onclick="showTab('updates')" id="tab-updates" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">🔄 Updates</button>
<button onclick="showTab('downloads')" id="tab-downloads" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">📥 Descargas</button>
<button onclick="showTab('marketing')" id="tab-marketing" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">🧠 Marketing</button>
<button onclick="showTab('settings')" id="tab-settings" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">⚙️ Ajustes</button>
<a href="/admin/logout" class="bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded text-sm font-bold ml-2"><i class="fas fa-sign-out-alt mr-1"></i>Salir</a>
</div></nav>
<div class="flex-1 container mx-auto p-6 md:p-10 max-w-4xl">

<!-- PAGES TAB -->
<div id="content-pages" class="space-y-6 hidden">
<div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
<h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Gestor de Landing Pages</h3>
<div class="flex gap-2 mb-4">
<select id="page_selector" onchange="loadPageData()" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none"></select>
<button onclick="createPage()" class="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded text-sm font-bold whitespace-nowrap"><i class="fas fa-plus"></i> Nueva</button>
<button onclick="duplicatePage()" class="bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-2 rounded text-sm font-bold whitespace-nowrap"><i class="fas fa-copy"></i> Duplicar</button>
<button onclick="deletePage()" class="bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded text-sm font-bold whitespace-nowrap"><i class="fas fa-trash"></i></button>
</div><p class="text-xs text-slate-400">URL: <span id="page_url_preview" class="text-cyan-400"></span></p>
</div>
<div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
<h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Textos (Hero)</h3>
<input type="hidden" id="current_slug">
<label class="text-sm text-slate-400">Nombre Interno</label>
<input type="text" id="page_name" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700 outline-none focus:border-cyan-500">
<label class="text-sm text-slate-400">ID Chatbot (Chatbase)</label>
<input type="text" id="chatbot_id" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700 outline-none focus:border-cyan-500" placeholder="gzEjAzK1VCE72hJ_hBfA4">
<label class="text-sm text-slate-400">Título (H1)</label>
<input type="text" id="hero_title" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700 outline-none focus:border-cyan-500">
<label class="text-sm text-slate-400">Subtítulo (H2)</label>
<input type="text" id="hero_subtitle" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700 outline-none focus:border-cyan-500">
<label class="text-sm text-slate-400">Descripción</label>
<textarea id="hero_text" rows="3" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700 outline-none focus:border-cyan-500"></textarea>
</div>
<div class="bg-slate-800 p-6 rounded-xl border border-emerald-700 shadow-lg">
<h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">💰 Afiliados</h3>
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
<div><label class="text-sm text-slate-400">Enlace Hotmart</label><input type="text" id="affiliate_link" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
<div><label class="text-sm text-slate-400">Texto Botón</label><input type="text" id="affiliate_text" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
</div></div>
<div class="bg-slate-800 p-6 rounded-xl border border-indigo-700 shadow-lg">
<h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">📥 Enlaces de Descarga</h3>
<div id="dl-links-container" class="space-y-2 mb-4"></div>
<button onclick="addDlLink()" class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded text-sm font-bold"><i class="fas fa-plus mr-2"></i>Agregar Enlace</button>
<div class="mt-6"><label class="text-sm text-slate-400">Instrucciones</label><textarea id="download_instructions" rows="4" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></textarea></div>
</div>
<div class="bg-slate-800 p-6 rounded-xl border border-amber-700 shadow-lg">
<h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">💳 Transferencia Bancaria</h3>
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
<div><label class="text-sm text-slate-400">Banco</label><input type="text" id="bt_bank_name" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
<div><label class="text-sm text-slate-400">Tipo Cuenta</label><input type="text" id="bt_account_type" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
<div><label class="text-sm text-slate-400">Número/IBAN</label><input type="text" id="bt_account_number" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
<div><label class="text-sm text-slate-400">Beneficiario</label><input type="text" id="bt_beneficiary" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
<div><label class="text-sm text-slate-400">Correo comprobante</label><input type="email" id="bt_email" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
<div><label class="text-sm text-slate-400">WhatsApp comprobante</label><input type="text" id="bt_whatsapp" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
</div></div>
<div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
<h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Publicaciones (Galería)</h3>
<div id="pubs-container" class="space-y-4"></div>
<button onclick="addPubRow()" class="mt-4 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded text-sm font-bold"><i class="fas fa-plus mr-2"></i>Agregar</button>
</div>
<div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
<h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Planes (PayPal)</h3>
<div id="plans-container" class="space-y-6"></div>
<button onclick="addPlanRow()" class="mt-4 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded text-sm font-bold"><i class="fas fa-plus mr-2"></i>Agregar Plan</button>
</div>
<div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
<h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Redes Sociales</h3>
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
<div><label class="text-sm text-slate-400">Facebook</label><input type="text" id="fb_link" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
<div><label class="text-sm text-slate-400">WhatsApp</label><input type="text" id="wa_link" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
<div><label class="text-sm text-slate-400">YouTube</label><input type="text" id="yt_link" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
<div><label class="text-sm text-slate-400">TikTok</label><input type="text" id="tt_link" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
<div><label class="text-sm text-slate-400">Telegram</label><input type="text" id="tg_link" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
<div><label class="text-sm text-slate-400">Instagram</label><input type="text" id="ig_link" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
</div></div>
</div>

<!-- STATS TAB -->
<div id="content-stats" class="hidden space-y-6">
<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
<div class="bg-slate-800 p-6 rounded-xl border border-slate-700 text-center"><h3 class="text-sm text-slate-400 uppercase mb-2">Visitas</h3><p id="stat_views" class="text-5xl font-extrabold text-cyan-400">0</p></div>
<div class="bg-slate-800 p-6 rounded-xl border border-slate-700 text-center"><h3 class="text-sm text-slate-400 uppercase mb-2">Leads</h3><p id="stat_leads_count" class="text-5xl font-extrabold text-emerald-400">0</p></div>
</div>
<div class="bg-slate-800 p-6 rounded-xl border border-slate-700"><h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">📧 Leads Capturados</h3><div id="stat_leads" class="space-y-2 max-h-96 overflow-y-auto"></div></div>
</div>

<!-- AI TAB -->
<div id="content-ai" class="hidden space-y-6">
<div class="bg-slate-800 p-6 rounded-xl border border-cyan-700">
<h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">🤖 Agente IA</h3>
<p class="text-sm text-slate-400 mb-6">Usa <code class="bg-slate-900 p-1 rounded text-cyan-400">{name}</code> para personalizar.</p>
<div class="space-y-8">
<div class="bg-slate-900 p-4 rounded-lg border border-slate-700"><h4 class="text-cyan-400 font-bold mb-3">Seguimiento 1</h4>
<div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-3"><div><label class="text-sm text-slate-400">Días</label><input type="number" id="s1_days" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none" value="2"></div><div class="md:col-span-3"><label class="text-sm text-slate-400">Asunto</label><input type="text" id="s1_subject" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none"></div></div>
<label class="text-sm text-slate-400">Mensaje</label><textarea id="s1_body" rows="4" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none"></textarea></div>
<div class="bg-slate-900 p-4 rounded-lg border border-slate-700"><h4 class="text-cyan-400 font-bold mb-3">Seguimiento 2</h4>
<div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-3"><div><label class="text-sm text-slate-400">Días</label><input type="number" id="s2_days" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none" value="5"></div><div class="md:col-span-3"><label class="text-sm text-slate-400">Asunto</label><input type="text" id="s2_subject" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none"></div></div>
<label class="text-sm text-slate-400">Mensaje</label><textarea id="s2_body" rows="4" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none"></textarea></div>
<div class="bg-slate-900 p-4 rounded-lg border border-slate-700"><h4 class="text-cyan-400 font-bold mb-3">Seguimiento 3 (Cierre)</h4>
<div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-3"><div><label class="text-sm text-slate-400">Días</label><input type="number" id="s3_days" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none" value="10"></div><div class="md:col-span-3"><label class="text-sm text-slate-400">Asunto</label><input type="text" id="s3_subject" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none"></div></div>
<label class="text-sm text-slate-400">Mensaje</label><textarea id="s3_body" rows="4" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none"></textarea></div>
</div>
<button onclick="saveAIConfig()" class="mt-6 w-full bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold py-3 rounded"><i class="fas fa-save mr-2"></i>Guardar</button>
</div></div>

<!-- LICENSES TAB -->
<div id="content-lic" class="hidden space-y-6">
<div class="bg-slate-800 p-6 rounded-xl border border-emerald-700">
<h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">➕ Crear Licencia</h3>
<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
<select id="manual_plan" class="bg-slate-900 rounded p-2 border border-slate-700 outline-none"><option value="BRONCE">Bronce</option><option value="PLATA">Plata</option><option value="ORO">Oro</option></select>
<input type="number" id="manual_days" value="30" class="bg-slate-900 rounded p-2 border border-slate-700 outline-none">
<input type="email" id="manual_email" placeholder="cliente@correo.com" class="bg-slate-900 rounded p-2 border border-slate-700 outline-none">
</div>
<button onclick="createManualLicense()" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded text-sm font-bold"><i class="fas fa-key mr-2"></i>Generar</button>
<div id="manual_lic_msg" class="mt-4 text-cyan-400 font-bold text-sm hidden bg-slate-900 p-3 rounded"></div>
</div>
<div class="bg-slate-800 p-6 rounded-xl border border-slate-700">
<h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Gestión de Licencias</h3>
<input type="text" id="lic_key" placeholder="BLENIN-ORO-XXXX" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700 outline-none">
<div class="flex gap-2 flex-wrap">
<button onclick="manageLic(true)" class="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded text-sm font-bold"><i class="fas fa-check mr-2"></i>Activar</button>
<button onclick="manageLic(false)" class="bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded text-sm font-bold"><i class="fas fa-times mr-2"></i>Suspender</button>
<button onclick="resetHwid()" class="bg-amber-600 hover:bg-amber-500 text-white px-4 py-2 rounded text-sm font-bold"><i class="fas fa-sync mr-2"></i>Reset HWID</button>
</div><div id="lic_msg" class="mt-4 text-cyan-400 font-bold text-sm hidden"></div>
</div></div>

<!-- UPDATES TAB -->
<div id="content-updates" class="hidden space-y-6">
<div class="bg-slate-800 p-6 rounded-xl border border-cyan-700">
<h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">🔄 Versión del Bot</h3>
<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
<div><label class="text-sm text-slate-400">Versión</label><input type="text" id="upd_version" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none"></div>
<div><label class="text-sm text-slate-400">URL Descarga</label><input type="text" id="upd_url" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none"></div>
</div>
<label class="text-sm text-slate-400">Mensaje</label><textarea id="upd_message" rows="3" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700 outline-none"></textarea>
<div class="flex items-center gap-2 mb-6 p-3 bg-slate-900 rounded border border-slate-700"><input type="checkbox" id="upd_force" class="w-5 h-5 accent-red-500"><label class="text-sm text-slate-300 cursor-pointer">Forzar actualización</label></div>
<button onclick="saveUpdateConfig()" class="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold py-3 rounded"><i class="fas fa-save mr-2"></i>Guardar</button>
</div></div>

<!-- DOWNLOADS TAB -->
<div id="content-downloads" class="hidden space-y-6">
<div class="bg-slate-800 p-6 rounded-xl border border-indigo-700 shadow-lg">
<h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">📥 Descargas Multi-OS</h3>
<div class="bg-slate-900 p-4 rounded-lg border border-slate-700 mb-4">
<h4 class="text-cyan-400 font-bold mb-3">➕ Nueva / Editar</h4>
<input type="hidden" id="dl_edit_id">
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
<div><label class="text-sm text-slate-400">Versión</label><input type="text" id="dl_version" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Ej: 16.03"></div>
<div><label class="text-sm text-slate-400">Sistema Operativo</label><select id="dl_os" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"><option value="Windows">🪟 Windows</option><option value="Linux">🐧 Linux</option><option value="macOS">🍎 macOS</option><option value="Android">🤖 Android</option><option value="iOS">📱 iOS</option></select></div>
<div><label class="text-sm text-slate-400">URL Descarga</label><input type="text" id="dl_url" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="https://mega.nz/..."></div>
<div><label class="text-sm text-slate-400">Tamaño</label><input type="text" id="dl_size" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="85 MB"></div>
<div><label class="text-sm text-slate-400">Fecha</label><input type="date" id="dl_date" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500"></div>
<div class="flex items-end"><label class="text-sm flex items-center gap-2 cursor-pointer"><input type="checkbox" id="dl_active" class="w-5 h-5 accent-emerald-500" checked> <span class="text-slate-300">Activa</span></label></div>
</div>
<div class="mt-4"><label class="text-sm text-slate-400">Descripción</label><textarea id="dl_description" rows="3" class="w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Novedades..."></textarea></div>
<div class="flex gap-2 mt-4">
<button onclick="saveDownload()" class="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2 rounded text-sm font-bold"><i class="fas fa-save mr-2"></i>Guardar</button>
<button onclick="clearDownloadForm()" class="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded text-sm">Limpiar</button>
</div></div>
<h4 class="text-white font-bold mb-3">📋 Existentes</h4>
<div id="downloads_list" class="space-y-3"></div>
</div></div>

<!-- MARKETING TAB -->
<div id="content-marketing" class="hidden space-y-6">
<div class="bg-slate-800 p-6 rounded-xl border border-purple-700">
<h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">🧠 Marketing IA</h3>
<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
<button onclick="generateMarketing('seo_blog')" class="bg-purple-600 hover:bg-purple-500 text-white p-4 rounded text-sm font-bold"><i class="fas fa-blog mr-2"></i>SEO</button>
<button onclick="generateMarketing('tiktok_script')" class="bg-pink-600 hover:bg-pink-500 text-white p-4 rounded text-sm font-bold"><i class="fab fa-tiktok mr-2"></i>TikTok</button>
<button onclick="generateMarketing('forum_post')" class="bg-blue-600 hover:bg-blue-500 text-white p-4 rounded text-sm font-bold"><i class="fab fa-reddit mr-2"></i>Foro</button>
</div>
<div id="marketing_output" class="bg-slate-900 p-4 rounded border border-slate-700 text-slate-300 text-sm whitespace-pre-wrap min-h-[200px]">El contenido aparecerá aquí...</div>
<button onclick="copyMarketing()" class="mt-4 bg-cyan-500 hover:bg-cyan-400 text-slate-900 px-4 py-2 rounded text-sm font-bold"><i class="fas fa-copy mr-2"></i>Copiar</button>
</div></div>

<!-- SETTINGS TAB -->
<div id="content-settings" class="hidden space-y-6">
<div class="bg-slate-800 p-6 rounded-xl border border-amber-700">
<h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">🔑 Cambiar Contraseña</h3>
<div class="space-y-4">
<input type="password" id="current_pwd" placeholder="Actual" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none">
<input type="password" id="new_pwd" placeholder="Nueva" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none">
<input type="password" id="confirm_pwd" placeholder="Repetir" class="w-full bg-slate-900 rounded p-2 border border-slate-700 outline-none">
<button onclick="changePassword()" class="w-full bg-amber-600 hover:bg-amber-500 text-white px-4 py-2 rounded text-sm font-bold"><i class="fas fa-save mr-2"></i>Actualizar</button>
<div id="pwd_msg" class="mt-4 font-bold text-sm hidden"></div>
</div></div></div>

</div>
<footer class="bg-slate-950 p-4 sticky bottom-0 border-t border-slate-800"><div class="container mx-auto max-w-4xl flex justify-between items-center"><span class="text-xs text-slate-500">© 2024 BLENIN.G.77</span><button onclick="saveData()" class="bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold px-6 py-2 rounded shadow-lg"><i class="fas fa-save mr-2"></i>Guardar y Publicar</button></div></footer>
<div id="toast" class="fixed bottom-5 right-5 bg-slate-700 text-white px-4 py-3 rounded-lg shadow-2xl opacity-0 transition-opacity duration-300 pointer-events-none"><span id="toast-msg"></span></div>

<script id="pages-data" type="application/json">__PAGES_JSON__</script>
<script>
const allPages = JSON.parse(document.getElementById('pages-data').textContent);
let currentMarketingText = "";

function showTab(tabId) {
    ['pages','stats','ai','lic','updates','downloads','marketing','settings'].forEach(id => {
        document.getElementById('content-' + id).classList.add('hidden');
        document.getElementById('tab-' + id).classList.remove('tab-active');
        document.getElementById('tab-' + id).classList.add('bg-slate-800','hover:bg-slate-700');
    });
    document.getElementById('content-' + tabId).classList.remove('hidden');
    document.getElementById('tab-' + tabId).classList.add('tab-active');
    document.getElementById('tab-' + tabId).classList.remove('bg-slate-800','hover:bg-slate-700');
    if(tabId === 'stats') loadStats();
    if(tabId === 'ai') loadAIConfig();
    if(tabId === 'updates') loadUpdateConfig();
    if(tabId === 'downloads') loadDownloads();
}

function showToast(msg) {
    const t = document.getElementById('toast');
    document.getElementById('toast-msg').innerText = msg;
    t.classList.remove('opacity-0');
    setTimeout(() => t.classList.add('opacity-0'), 3000);
}

function updateSelector() {
    const sel = document.getElementById('page_selector');
    sel.innerHTML = '';
    Object.keys(allPages).forEach(slug => {
        let opt = document.createElement('option');
        opt.value = slug;
        opt.innerText = allPages[slug].page_name || slug;
        sel.appendChild(opt);
    });
    if(Object.keys(allPages).length > 0) { sel.value = Object.keys(allPages)[0]; loadPageData(); }
}

function loadPageData() {
    const slug = document.getElementById('page_selector').value;
    if(!slug) return;
    const p = allPages[slug] || {};
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
    
    const bt = p.bank_transfer_info || {};
    document.getElementById('bt_bank_name').value = bt.bank_name || '';
    document.getElementById('bt_account_type').value = bt.account_type || '';
    document.getElementById('bt_account_number').value = bt.account_number || '';
    document.getElementById('bt_beneficiary').value = bt.beneficiary || '';
    document.getElementById('bt_email').value = bt.email_for_proof || '';
    document.getElementById('bt_whatsapp').value = bt.whatsapp_for_proof || '';
    
    const social = p.social_links || {};
    document.getElementById('fb_link').value = social.facebook || '';
    document.getElementById('wa_link').value = social.whatsapp || '';
    document.getElementById('yt_link').value = social.youtube || '';
    document.getElementById('tt_link').value = social.tiktok || '';
    document.getElementById('tg_link').value = social.telegram || '';
    document.getElementById('ig_link').value = social.instagram || '';
    
    document.getElementById('pubs-container').innerHTML = '';
    if((p.publications||[]).length === 0) addPubRow(); else p.publications.forEach(pub => addPubRow(pub.type, pub.url, pub.desc));
    
    document.getElementById('plans-container').innerHTML = '';
    if((p.plans||[]).length === 0) addPlanRow(); else p.plans.forEach(pl => addPlanRow(pl.name, pl.price, pl.features, pl.link, pl.highlight));
    
    document.getElementById('page_url_preview').innerText = slug === 'main' ? 'tudominio.com/' : 'tudominio.com/p/' + slug;
}

function createPage() {
    const name = prompt('Nombre:');
    if(!name) return;
    let slug = prompt('URL:');
    if(!slug) return;
    slug = slug.toLowerCase().replace(/[^a-z0-9-]/g,'');
    if(allPages[slug]) { alert('Ya existe'); return; }
    allPages[slug] = {page_name:name,chatbot_id:'gzEjAzK1VCE72hJ_hBfA4',hero_title:name,hero_subtitle:'',hero_text:'',affiliate_link:'',affiliate_text:'',publications:[],plans:[],social_links:{},bank_transfer_info:{},download_links:[],download_instructions:''};
    saveData(true);
}

function duplicatePage() {
    const cur = document.getElementById('page_selector').value;
    const newSlug = prompt('URL para la copia:');
    if(!newSlug) return;
    const slug = newSlug.toLowerCase().replace(/[^a-z0-9-]/g,'');
    if(allPages[slug]) { alert('Ya existe'); return; }
    allPages[slug] = JSON.parse(JSON.stringify(allPages[cur]));
    allPages[slug].page_name += ' (Copia)';
    saveData(true);
}

function deletePage() {
    const slug = document.getElementById('page_selector').value;
    if(slug === 'main') { alert('No puedes eliminar la principal'); return; }
    if(confirm('¿Eliminar?')) { delete allPages[slug]; saveData(true); }
}

function addDlLink(url='') {
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
    btn.onclick = function() { this.parentElement.remove(); };
    div.appendChild(input); div.appendChild(btn);
    c.appendChild(div);
}

function addPubRow(type='video', url='', desc='') {
    const c = document.getElementById('pubs-container');
    const div = document.createElement('div');
    div.className = 'bg-slate-900 p-4 rounded border border-slate-700';
    div.innerHTML = '<select class="pub-type w-full bg-slate-800 rounded p-2 mb-2 border border-slate-700 outline-none"><option value="video"'+(type=='video'?' selected':'')+'>Video YouTube</option><option value="image"'+(type=='image'?' selected':'')+'>Imagen</option></select><input type="text" class="pub-url w-full bg-slate-800 rounded p-2 mb-2 border border-slate-700 outline-none" placeholder="URL" value="'+url+'"><textarea class="pub-desc w-full bg-slate-800 rounded p-2 border border-slate-700 outline-none" placeholder="Descripción">'+desc+'</textarea><button onclick="this.parentElement.remove()" class="mt-2 text-red-500 text-xs"><i class="fas fa-trash mr-1"></i>Eliminar</button>';
    c.appendChild(div);
}

function addPlanRow(name='', price='', features='', link='', highlight=false) {
    const c = document.getElementById('plans-container');
    const div = document.createElement('div');
    div.className = 'bg-slate-900 p-4 rounded border border-slate-700';
    div.innerHTML = '<div class="grid grid-cols-1 md:grid-cols-2 gap-2"><input type="text" class="p-name bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Nombre" value="'+name+'"><input type="text" class="p-price bg-slate-800 rounded p-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Precio" value="'+price+'"></div><textarea class="p-features w-full bg-slate-800 rounded p-2 my-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Características">'+features+'</textarea><input type="text" class="p-link w-full bg-slate-800 rounded p-2 mb-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="ID PayPal" value="'+link+'"><div class="flex justify-between items-center"><label class="text-sm flex items-center gap-2"><input type="checkbox" class="p-highlight accent-cyan-500" '+(highlight?'checked':'')+'> Destacar</label><button onclick="this.parentElement.parentElement.remove()" class="text-red-500 text-xs"><i class="fas fa-trash"></i></button></div>';
    c.appendChild(div);
}

async function saveData(reload=false) {
    const slug = document.getElementById('current_slug').value || document.getElementById('page_selector').value;
    if(!slug) { showToast('❌ No hay página'); return; }
    let pubs = [];
    document.querySelectorAll('#pubs-container > div').forEach(div => {
        const u = div.querySelector('.pub-url');
        if(u && u.value.trim()) pubs.push({type:div.querySelector('.pub-type').value, url:u.value, desc:div.querySelector('.pub-desc').value});
    });
    let plans = [];
    document.querySelectorAll('#plans-container > div').forEach(div => {
        const n = div.querySelector('.p-name');
        if(n && n.value.trim()) plans.push({name:n.value, price:div.querySelector('.p-price').value, features:div.querySelector('.p-features').value, link:div.querySelector('.p-link').value, highlight:div.querySelector('.p-highlight').checked});
    });
    let dlLinks = [];
    document.querySelectorAll('#dl-links-container > div').forEach(div => {
        const u = div.querySelector('.dl-url');
        if(u && u.value.trim()) dlLinks.push(u.value.trim());
    });
    allPages[slug] = {
        page_name: document.getElementById('page_name').value,
        chatbot_id: document.getElementById('chatbot_id').value || 'gzEjAzK1VCE72hJ_hBfA4',
        hero_title: document.getElementById('hero_title').value,
        hero_subtitle: document.getElementById('hero_subtitle').value,
        hero_text: document.getElementById('hero_text').value,
        affiliate_link: document.getElementById('affiliate_link').value,
        affiliate_text: document.getElementById('affiliate_text').value,
        publications: pubs, plans: plans,
        social_links: {facebook:document.getElementById('fb_link').value,whatsapp:document.getElementById('wa_link').value,youtube:document.getElementById('yt_link').value,tiktok:document.getElementById('tt_link').value,telegram:document.getElementById('tg_link').value,instagram:document.getElementById('ig_link').value},
        bank_transfer_info: {bank_name:document.getElementById('bt_bank_name').value,account_type:document.getElementById('bt_account_type').value,account_number:document.getElementById('bt_account_number').value,beneficiary:document.getElementById('bt_beneficiary').value,email_for_proof:document.getElementById('bt_email').value,whatsapp_for_proof:document.getElementById('bt_whatsapp').value},
        download_links: dlLinks,
        download_instructions: document.getElementById('download_instructions').value
    };
    const res = await fetch('/api/save_pages', {method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(allPages)});
    const r = await res.json();
    showToast(r.message);
    if(reload) updateSelector();
}

async function loadStats() {
    const res = await fetch('/api/get_stats', {credentials:'same-origin'});
    const data = await res.json();
    document.getElementById('stat_views').innerText = data.views || 0;
    const leads = data.captured_leads || [];
    document.getElementById('stat_leads_count').innerText = leads.length;
    let html = '';
    leads.slice().reverse().forEach(l => {
        let stage = l.follow_up_stage === 0 ? 'Email Inicial' : l.follow_up_stage === 1 ? 'Seguimiento 1' : l.follow_up_stage === 2 ? 'Seguimiento 2' : 'Finalizado';
        html += '<div class="bg-slate-900 p-3 rounded border border-slate-700"><div class="flex justify-between"><span class="text-cyan-400 font-bold text-sm">'+l.name+' - '+l.email+'</span><span class="text-slate-500 text-xs">'+(l.date?l.date.split('T')[0]:'')+'</span></div><div class="text-emerald-400 text-xs mt-1">🤖 '+stage+'</div></div>';
    });
    document.getElementById('stat_leads').innerHTML = html || '<p class="text-slate-500 text-sm">Sin leads.</p>';
}

async function loadAIConfig() {
    const res = await fetch('/api/get_ai_config', {credentials:'same-origin'});
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
}

async function saveAIConfig() {
    const payload = {
        stage1_days:parseInt(document.getElementById('s1_days').value),stage1_subject:document.getElementById('s1_subject').value,stage1_body:document.getElementById('s1_body').value,
        stage2_days:parseInt(document.getElementById('s2_days').value),stage2_subject:document.getElementById('s2_subject').value,stage2_body:document.getElementById('s2_body').value,
        stage3_days:parseInt(document.getElementById('s3_days').value),stage3_subject:document.getElementById('s3_subject').value,stage3_body:document.getElementById('s3_body').value
    };
    const res = await fetch('/api/save_ai_config', {method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    showToast((await res.json()).message);
}

async function loadUpdateConfig() {
    const res = await fetch('/api/get_update_config', {credentials:'same-origin'});
    const data = await res.json();
    document.getElementById('upd_version').value = data.latest_version || '';
    document.getElementById('upd_url').value = data.download_url || '';
    document.getElementById('upd_message').value = data.update_message || '';
    document.getElementById('upd_force').checked = data.force_update || false;
}

async function saveUpdateConfig() {
    const payload = {
        latest_version:document.getElementById('upd_version').value,
        download_url:document.getElementById('upd_url').value,
        force_update:document.getElementById('upd_force').checked,
        update_message:document.getElementById('upd_message').value
    };
    const res = await fetch('/api/save_update_config', {method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    showToast((await res.json()).message);
}

async function loadDownloads() {
    const res = await fetch('/api/get_downloads');
    const data = await res.json();
    const list = document.getElementById('downloads_list');
    if(!data || data.length === 0) { list.innerHTML = '<p class="text-slate-500 text-sm text-center py-4">Sin descargas.</p>'; return; }
    const icons = {'Windows':'🪟','Linux':'🐧','macOS':'🍎','Android':'🤖','iOS':'📱'};
    let html = '';
    data.forEach(d => {
        const icon = icons[d.os] || '📦';
        const active = d.is_active ? '<span class="text-emerald-400 text-xs">✅</span>' : '<span class="text-red-400 text-xs">❌</span>';
        html += '<div class="bg-slate-900 p-4 rounded-lg border border-slate-700 flex justify-between items-center"><div><div class="flex items-center gap-2 mb-1"><span class="text-2xl">'+icon+'</span><span class="text-cyan-400 font-bold">v'+d.version+'</span><span class="text-slate-500 text-xs">('+d.os+')</span>'+active+'</div><p class="text-slate-400 text-xs">'+(d.description||'').substring(0,80)+'</p></div><div class="flex gap-2"><button onclick="editDownload(\\''+d.id+'\\')" class="bg-amber-600 hover:bg-amber-500 text-white px-3 py-1 rounded text-xs font-bold"><i class="fas fa-edit"></i></button><button onclick="deleteDownload(\\''+d.id+'\\')" class="bg-red-600 hover:bg-red-500 text-white px-3 py-1 rounded text-xs font-bold"><i class="fas fa-trash"></i></button></div></div>';
    });
    list.innerHTML = html;
}

async function saveDownload() {
    const payload = {
        id: document.getElementById('dl_edit_id').value || null,
        version: document.getElementById('dl_version').value,
        os: document.getElementById('dl_os').value,
        download_url: document.getElementById('dl_url').value,
        description: document.getElementById('dl_description').value,
        file_size: document.getElementById('dl_size').value,
        release_date: document.getElementById('dl_date').value,
        is_active: document.getElementById('dl_active').checked
    };
    if(!payload.version || !payload.download_url) { showToast('❌ Versión y URL obligatorios'); return; }
    const res = await fetch('/api/save_download', {method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    showToast((await res.json()).message);
    clearDownloadForm();
    loadDownloads();
}

function clearDownloadForm() {
    document.getElementById('dl_edit_id').value = '';
    document.getElementById('dl_version').value = '';
    document.getElementById('dl_os').value = 'Windows';
    document.getElementById('dl_url').value = '';
    document.getElementById('dl_description').value = '';
    document.getElementById('dl_size').value = '';
    document.getElementById('dl_date').value = '';
    document.getElementById('dl_active').checked = true;
}

async function editDownload(id) {
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
}

async function deleteDownload(id) {
    if(!confirm('¿Eliminar?')) return;
    const res = await fetch('/api/delete_download', {method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:id})});
    showToast((await res.json()).message);
    loadDownloads();
}

async function createManualLicense() {
    const payload = {plan:document.getElementById('manual_plan').value,days:document.getElementById('manual_days').value,email:document.getElementById('manual_email').value};
    const res = await fetch('/api/create_license', {method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const r = await res.json();
    if(r.key) { document.getElementById('manual_lic_msg').innerText = '✅ Licencia: ' + r.key; document.getElementById('manual_lic_msg').classList.remove('hidden'); }
    else { showToast(r.message || 'Error'); }
}

async function manageLic(activate) {
    const res = await fetch('/api/manage_license', {method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:document.getElementById('lic_key').value,activate:activate})});
    showToast((await res.json()).message);
}

async function resetHwid() {
    const res = await fetch('/api/reset_hwid', {method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:document.getElementById('lic_key').value})});
    showToast((await res.json()).message);
}

async function generateMarketing(type) {
    document.getElementById('marketing_output').innerText = '🧠 Generando contenido...';
    const res = await fetch('/api/generate_marketing', {method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:type})});
    const r = await res.json();
    if(r.content) { currentMarketingText = r.content; document.getElementById('marketing_output').innerText = r.content; }
    else { showToast('❌ Error generando contenido'); }
}

function copyMarketing() { navigator.clipboard.writeText(currentMarketingText); showToast('✅ Copiado'); }

async function changePassword() {
    if(document.getElementById('new_pwd').value !== document.getElementById('confirm_pwd').value) { showToast('❌ No coinciden'); return; }
    const payload = {current_password:document.getElementById('current_pwd').value,new_password:document.getElementById('new_pwd').value};
    const res = await fetch('/api/change_password', {method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const r = await res.json();
    if(res.ok) { document.getElementById('pwd_msg').innerText = r.message; document.getElementById('pwd_msg').className = 'mt-4 font-bold text-sm text-emerald-400'; }
    else { showToast(r.detail || 'Error'); }
}

updateSelector();
</script>
</body></html>"""

@app.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request):
    if not verify_admin(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    pages_data = get_all_pages()
    pages_dict = pages_data.get("pages", {})
    pages_json = json.dumps(pages_dict, ensure_ascii=False).replace('</', '<\\/')
    return ADMIN_HTML_TEMPLATE.replace("__PAGES_JSON__", pages_json)
