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
# 🧠 SISTEMA DE BASE DE DATOS MULTI-PÁGINA
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

def get_default_content(page_name="Principal"):
    return {
        "page_name": page_name,
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

def get_all_pages():
    try:
        headers = {"X-Master-Key": JSONBIN_API_KEY}
        resp = requests.get(JSONBIN_URL, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()["record"]
            # MIGRACIÓN AUTOMÁTICA: Si está en formato antiguo, lo convierte
            if "hero_title" in data and "pages" not in data:
                new_data = {"pages": {"main": data}}
                save_all_pages(new_data)
                return new_data
            return data
    except: pass
    # Si no existe nada, crea la página principal
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
# 🎛️ PANEL DE ADMINISTRACIÓN (CMS MULTI-PÁGINA)
# ==========================================
@app.get("/admin", response_class=HTMLResponse)
def admin_panel():
    pages_data = get_all_pages()
    pages_dict = pages_data.get("pages", {})
    pages_json = json.dumps(pages_dict)
    
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
            <button onclick="showTab('pages')" id="tab-pages" class="tab-active px-4 py-2 rounded text-sm font-medium transition">🚀 Páginas</button>
            <button onclick="showTab('stats')" id="tab-stats" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">📊 Estadísticas</button>
            <button onclick="showTab('lic')" id="tab-lic" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm font-medium transition">Licencias</button>
        </div>
    </nav>

    <div class="flex-1 container mx-auto p-6 md:p-10 max-w-4xl">
        
        <!-- GESTOR DE PÁGINAS -->
        <div id="content-pages" class="space-y-6">
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
                <label class="text-sm text-slate-400">Título Principal (H1)</label>
                <input type="text" id="hero_title" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700 focus:border-cyan-500 outline-none">
                <label class="text-sm text-slate-400">Subtítulo (H2)</label>
                <input type="text" id="hero_subtitle" class="w-full bg-slate-900 rounded p-2 mb-4 border border-slate-700 focus:border-cyan-500 outline-none">
                <label class="text-sm text-slate-400">Texto Descriptivo</label>
                <textarea id="hero_text" rows="3" class="w-full bg-slate-900 rounded p-2 border border-slate-700 focus:border-cyan-500 outline-none"></textarea>
            </div>

            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Publicaciones (Galería)</h3>
                <div id="pubs-container" class="space-y-4"></div>
                <button onclick="addPubRow()" class="mt-4 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded text-sm font-bold transition"><i class="fas fa-plus mr-2"></i>Agregar Publicación</button>
            </div>

            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                <h3 class="text-lg font-bold text-white border-b border-slate-700 pb-3 mb-4">Planes de Suscripción (PayPal)</h3>
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
    const allPages = {pages_json};
    
    function showTab(tabId) {{
        ['pages', 'stats', 'lic'].forEach(id => {{
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

    function updateSelector() {{
        const selector = document.getElementById('page_selector');
        selector.innerHTML = '';
        Object.keys(allPages).forEach(slug => {{
            let opt = document.createElement('option');
            opt.value = slug;
            opt.innerText = allPages[slug].page_name || slug;
            selector.appendChild(opt);
        }});
    }}

    function loadPageData() {{
        const slug = document.getElementById('page_selector').value;
        const p = allPages[slug];
        if(!p) return;
        
        document.getElementById('current_slug').value = slug;
        document.getElementById('page_name').value = p.page_name || '';
        document.getElementById('hero_title').value = p.hero_title || '';
        document.getElementById('hero_subtitle').value = p.hero_subtitle || '';
        document.getElementById('hero_text').value = p.hero_text || '';
        
        document.getElementById('fb_link').value = p.social_links?.facebook || '';
        document.getElementById('wa_link').value = p.social_links?.whatsapp || '';
        document.getElementById('yt_link').value = p.social_links?.youtube || '';
        document.getElementById('tt_link').value = p.social_links?.tiktok || '';
        document.getElementById('tg_link').value = p.social_links?.telegram || '';
        document.getElementById('ig_link').value = p.social_links?.instagram || '';

        document.getElementById('pubs-container').innerHTML = '';
        (p.publications || []).forEach(pub => addPubRow(pub.type, pub.url, pub.desc));
        if((p.publications || []).length === 0) addPubRow();

        document.getElementById('plans-container').innerHTML = '';
        (p.plans || []).forEach(plan => addPlanRow(plan.name, plan.price, plan.features, plan.link, plan.highlight));
        if((p.plans || []).length === 0) addPlanRow();

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
        
        allPages[slug] = {page_name: name, hero_title: name, hero_subtitle: '', hero_text: '', publications: [], plans: [], social_links: {{}}};
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
            <input type="text" class="p-link w-full bg-slate-800 rounded p-2 mb-2 border border-slate-700 outline-none focus:border-cyan-500" placeholder="Enlace de pago de PayPal" value="${{link}}">
            <div class="flex justify-between items-center mt-2">
                <label class="text-sm flex items-center gap-2 cursor-pointer"><input type="checkbox" class="p-highlight accent-cyan-500" ${{highlight ? 'checked' : ''}}> Resaltar (Más Popular)</label>
                <button onclick="this.parentElement.parentElement.remove()" class="text-red-500 text-xs hover:text-red-400"><i class="fas fa-trash mr-1"></i>Eliminar</button>
            </div>
        `;
        c.appendChild(div);
    }}

    async function saveData(reloadSelector = false) {{
        const slug = document.getElementById('current_slug').value || document.getElementById('page_selector').value;
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

        allPages[slug] = {{
            page_name: document.getElementById('page_name').value,
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
        
        const res = await fetch('/api/save_pages', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(allPages) }});
        const result = await res.json();
        showToast(result.message);
        if(reloadSelector) {{ updateSelector(); document.getElementById('page_selector').value = Object.keys(allPages).pop(); loadPageData(); }}
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

    // Init
    updateSelector();
    loadPageData();
    loadStats();
    </script>
    </body></html>
    """

@app.post("/api/save_pages")
def api_save_pages(data: dict):
    if save_all_pages({"pages": data}):
        return {"message": "✅ Página guardada correctamente."}
    return {"message": "❌ Error al guardar."}

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
# 🌐 RENDERIZADO DE LANDING PAGES (MULTI-PÁGINA)
# ==========================================
def render_landing_page(c):
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
    
    <!-- 🤖 CHATBASE BOT (Se inyecta en todas las páginas automáticamente) -->
    <script>
        (function(){if(!window.chatbase||window.chatbase("getState")!=="initialized"){window.chatbase=(...arguments)=>{if(!window.chatbase.q){window.chatbase.q=[]}window.chatbase.q.push(arguments)};window.chatbase=new Proxy(window.chatbase,{get(target,prop){if(prop==="q"){return target.q}return(...args)=>target(prop,...args)}})}}const onLoad=function(){const script=document.createElement("script");script.src="https://www.chatbase.co/embed.min.js";script.id="gzEjAzK1VCE72hJ_hBfA4";script.domain="www.chatbase.co";document.body.appendChild(script)};if(document.readyState==="complete"){onLoad()}else{window.addEventListener("load",onLoad)}})();
    </script>

    <style>
        body { font-family: 'Inter', sans-serif; background-color: #020617; }
        .glow { text-shadow: 0 0 10px rgba(6, 182, 212, 0.5); }
        .hero-bg { background: linear-gradient(to bottom, rgba(2, 6, 23, 0.8) 0%, rgba(2, 6, 23, 0.9) 100%), url('https://raw.githubusercontent.com/mymundodigital0-cmyk/blenin77-server/main/bienvenida_blenin.png') center/cover no-repeat; }
        .chatbase-bubble-button, iframe[src*="chatbase.co"] { z-index: 99999 !important; display: block !important; visibility: visible !important; opacity: 1 !important; }
        .goog-te-banner-frame.skiptranslate { display: none !important; } body { top: 0px !important; }
        .goog-tooltip, .goog-tooltip:hover { display: none !important; }
        .goog-text-highlight { background-color: transparent !important; box-shadow: none !important; }
        #google_translate_element { position: absolute; top: -9999px; left: -9999px; opacity: 0; }
        .goog-te-gadget { font-size: 0 !important; }
        #lang-menu::-webkit-scrollbar { width: 6px; }
        #lang-menu::-webkit-scrollbar-track { background: #1e293b; border-radius: 10px; }
        #lang-menu::-webkit-scrollbar-thumb { background: #0e7490; border-radius: 10px; }
    </style>
</head>
<body class="text-slate-300">
    <nav class="bg-slate-950/80 backdrop-blur-md sticky top-0 z-50 border-b border-slate-800">
        <div class="container mx-auto px-6 py-4 flex justify-between items-center">
            <a href="/" class="text-xl font-extrabold text-cyan-400 glow">BLENIN.G.77</a>
            <div class="hidden md:flex space-x-6 text-sm font-medium items-center">
                <a href="#features" class="hover:text-cyan-400 transition">Tecnología</a>
                <a href="#videos" class="hover:text-cyan-400 transition">Galería</a>
                <a href="#pricing" class="hover:text-cyan-400 transition">Precios</a>
                <div class="relative inline-block text-left">
                    <button id="lang-btn" class="inline-flex justify-center items-center gap-2 rounded-md border border-slate-700 px-3 py-1.5 bg-slate-800 text-sm font-medium text-slate-300 hover:bg-slate-700 transition">
                        <i class="fas fa-globe text-cyan-400"></i> <span id="current-lang-name">🇪🇸 Español</span> <i class="fas fa-chevron-down text-xs"></i>
                    </button>
                    <div id="lang-menu" class="hidden absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-slate-800 ring-1 ring-black ring-opacity-5 z-50 max-h-80 overflow-y-auto">
                        <div class="py-1">
                            <a href="#" onclick="changeLang('es', '🇪🇸 Español'); return false;" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-slate-700 hover:text-cyan-400">🇪🇸 Español</a>
                            <a href="#" onclick="changeLang('en', '🇬🇧 English'); return false;" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-slate-700 hover:text-cyan-400">🇬🇧 English</a>
                            <a href="#" onclick="changeLang('fr', '🇫🇷 Français'); return false;" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-slate-700 hover:text-cyan-400">🇫🇷 Français</a>
                            <a href="#" onclick="changeLang('pt', '🇵🇹 Português'); return false;" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-slate-700 hover:text-cyan-400">🇵🇹 Português</a>
                            <a href="#" onclick="changeLang('ru', '🇷🇺 Русский'); return false;" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-slate-700 hover:text-cyan-400">🇷🇺 Русский</a>
                            <a href="#" onclick="changeLang('it', '🇮🇹 Italiano'); return false;" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-slate-700 hover:text-cyan-400">🇮🇹 Italiano</a>
                            <a href="#" onclick="changeLang('de', '🇩🇪 Deutsch'); return false;" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-slate-700 hover:text-cyan-400">🇩🇪 Deutsch</a>
                            <a href="#" onclick="changeLang('zh-CN', '🇨🇳 中文'); return false;" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-slate-700 hover:text-cyan-400">🇨🇳 中文</a>
                            <a href="#" onclick="changeLang('ko', '🇰🇷 한국어'); return false;" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-slate-700 hover:text-cyan-400">🇰🇷 한국어</a>
                            <a href="#" onclick="changeLang('hi', '🇮🇳 हिन्दी'); return false;" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-slate-700 hover:text-cyan-400">🇮🇳 हिन्दी</a>
                        </div>
                    </div>
                </div>
            </div>
            <a href="#pricing" class="bg-cyan-500 text-slate-900 px-4 py-2 rounded text-sm font-bold hover:bg-cyan-400 transition">Comprar Ahora</a>
        </div>
    </nav>

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

    <section id="videos" class="py-20 bg-slate-950">
        <div class="container mx-auto px-6">
            <h2 class="text-3xl font-bold text-center text-white mb-12">Mira al Sistema en Acción</h2>
            {PUBLICATIONS_HTML}
        </div>
    </section>

    <section id="pricing" class="py-20 container mx-auto px-6">
        <h2 class="text-3xl font-bold text-center text-white mb-4">Planes de Suscripción</h2>
        <p class="text-slate-400 text-center mb-12">Elige el plan que se adapte a tu capital y estilo de trading.</p>
        <div class="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {PLANS_HTML}
        </div>
    </section>

    <section class="py-12 border-t border-slate-800">
        <div class="container mx-auto px-6 text-center">
            <h3 class="text-xl font-bold text-white mb-6">Síguenos en nuestras redes</h3>
            <div class="flex justify-center space-x-4 text-xl">
                {SOCIAL_HTML}
            </div>
        </div>
    </section>

    <footer class="bg-slate-950 py-10 border-t border-slate-800">
        <div class="container mx-auto px-6 text-center">
            <p class="text-slate-500 text-sm mb-4 max-w-3xl mx-auto">
                <strong>Aviso de Riesgo:</strong> El trading de divisas y CFDs implica un riesgo sustancial y no es adecuado para todos los inversores. El rendimiento pasado no es indicativo de resultados futuros. Operar con apalancamiento puede resultar en la pérdida de su capital.
            </p>
            <p class="text-slate-600 text-xs">&copy; 2024 BLENIN.G.77 THE BEST FUTURE FOR YOU. Creado por Lenin Benitez.</p>
        </div>
    </footer>

    <div id="google_translate_element"></div>
    <script type="text/javascript">
    function googleTranslateElementInit() { new google.translate.TranslateElement({pageLanguage: 'es', includedLanguages: 'en,fr,pt,ru,it,de,zh-CN,ko,hi', layout: google.translate.TranslateElement.InlineLayout.SIMPLE, autoDisplay: false}, 'google_translate_element'); }
    </script>
    <script type="text/javascript" src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>
    
    <script>
        const langBtn = document.getElementById('lang-btn');
        const langMenu = document.getElementById('lang-menu');
        langBtn.addEventListener('click', (e) => { e.stopPropagation(); langMenu.classList.toggle('hidden'); });
        window.addEventListener('click', (e) => { if (!langMenu.contains(e.target) && !langBtn.contains(e.target)) { langMenu.classList.add('hidden'); } });
        function changeLang(langCode, langName) {
            document.getElementById('current-lang-name').innerText = langName;
            langMenu.classList.add('hidden');
            var date = new Date(); date.setTime(date.getTime() + (365 * 24 * 60 * 60 * 1000)); var expires = "; expires=" + date.toUTCString();
            var hostname = window.location.hostname;
            if (langCode === 'es') {
                document.cookie = "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/";
                document.cookie = "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=" + hostname;
                document.cookie = "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=." + hostname;
            } else {
                var cookieValue = "/es/" + langCode;
                document.cookie = "googtrans=" + cookieValue + expires + "; path=/";
                document.cookie = "googtrans=" + cookieValue + expires + "; path=/; domain=" + hostname;
                document.cookie = "googtrans=" + cookieValue + expires + "; path=/; domain=." + hostname;
            }
            window.location.reload();
        }
        window.onload = function() {
            var match = document.cookie.match(/googtrans=\/es\/([a-zA-Z\-]+)/);
            if (match && match[1]) {
                var langMap = { 'en': '🇬🇧 English', 'fr': '🇫🇷 Français', 'pt': '🇵🇹 Português', 'ru': '🇷🇺 Русский', 'it': '🇮🇹 Italiano', 'de': '🇩🇪 Deutsch', 'zh-CN': '🇨🇳 中文', 'ko': '🇰🇷 한국어', 'hi': '🇮🇳 हिन्दी' };
                if (langMap[match[1]]) document.getElementById('current-lang-name').innerText = langMap[match[1]];
            }
        };
    </script>
    <script>fetch('/api/track_view', { method: 'POST' });</script>
</body>
</html>"""
    return template.replace("{HERO_TITLE}", c.get('hero_title', ''))\
                   .replace("{HERO_SUBTITLE}", c.get('hero_subtitle', ''))\
                   .replace("{HERO_TEXT}", c.get('hero_text', ''))\
                   .replace("{PUBLICATIONS_HTML}", pubs_html)\
                   .replace("{PLANS_HTML}", plans_html)\
                   .replace("{SOCIAL_HTML}", social_html)

@app.get("/", response_class=HTMLResponse)
def read_root():
    pages_data = get_all_pages()
    c = pages_data.get("pages", {}).get("main", get_default_content())
    return render_landing_page(c)

@app.get("/p/{slug}", response_class=HTMLResponse)
def read_dynamic_page(slug: str):
    pages_data = get_all_pages()
    c = pages_data.get("pages", {}).get(slug)
    if c:
        return render_landing_page(c)
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

@app.post("/api/track_view")
def track_view(request: Request):
    global stats_db
    try:
        ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "8.8.8.8").split(",")[0]
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
