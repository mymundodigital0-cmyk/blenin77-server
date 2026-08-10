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
    try:
        headers = {"X-Master-Key": JSONBIN_API_KEY}
        resp = requests.get(JSONBIN_URL, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()["record"]
            if "publications" not in data: data["publications"] = []
            if "plans" not in data: data["plans"] = []
            return data
    except: pass
    return {
        "hero_title": "BLENIN.G.77",
        "hero_subtitle": "THE BEST FUTURE FOR YOU",
        "hero_text": "IA Predictiva, Enjambre de 500 Agentes y Análisis Global en Tiempo Real.",
        "publications": [
            {"type": "video", "url": "https://www.youtube.com/embed/dQw4w9WgXcQ", "desc": "Mira cómo el Enjambre de Agentes abre operaciones reales."}
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
# 🎛️ PANEL DE ADMINISTRACIÓN
# ==========================================
@app.get("/admin", response_class=HTMLResponse)
def admin_panel():
    c = get_content()
    pubs = c.get('publications', [])
    plans = c.get('plans', [])
    
    pubs_json = str(pubs).replace("'", '"').replace('"', '&quot;')
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

    <h3>Publicaciones (Videos e Imágenes)</h3>
    <div id="pubs-container"></div>
    <button class="btn-add" onclick="addPubRow()">➕ Agregar Nueva Publicación</button>

    <h3>Planes de Suscripción</h3>
    <div id="plans-container"></div>
    <button class="btn-add" onclick="addPlanRow()">➕ Agregar Nuevo Plan</button>

    <br><br>
    <button onclick="saveData()">💾 Guardar y Publicar Cambios</button>
    <p id="msg" style="color:green;font-weight:bold;font-size:18px;"></p>

    <script>
    const existingPubs = {pubs_json};
    const existingPlans = {plans_json};
    
    function addPubRow(type = 'video', url = '', desc = '') {{
        const container = document.getElementById('pubs-container');
        const div = document.createElement('div');
        div.className = 'row';
        div.innerHTML = `
            <select class="pub-type" onchange="updatePlaceholder(this)">
                <option value="video" ${{type=='video'?'selected':''}}>Video de YouTube</option>
                <option value="image" ${{type=='image'?'selected':''}}>Imagen</option>
            </select>
            <input type="text" class="pub-url" placeholder="URL Embed de YouTube" value="${{url}}">
            <textarea class="pub-desc" placeholder="Texto de referencia o anuncio">${{desc}}</textarea>
            <button class="btn-del" onclick="this.parentElement.remove()">🗑️ Eliminar Publicación</button>
        `;
        container.appendChild(div);
        updatePlaceholder(div.querySelector('.pub-type'));
    }}

    function updatePlaceholder(selectElem) {{
        const input = selectElem.nextElementSibling;
        if(selectElem.value === 'video') input.placeholder = 'URL Embed de YouTube (ej: https://youtube.com/embed/123)';
        else input.placeholder = 'URL directa de la Imagen (ej: https://i.imgur.com/imagen.jpg)';
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

    if(existingPubs.length === 0) addPubRow();
    else existingPubs.forEach(p => addPubRow(p.type, p.url, p.desc));

    if(existingPlans.length === 0) addPlanRow();
    else existingPlans.forEach(p => addPlanRow(p.name, p.price, p.features, p.link, p.highlight));

    async function saveData() {{
        let pubsArray = [];
        document.querySelectorAll('#pubs-container .row').forEach(div => {{
            const url = div.querySelector('.pub-url').value;
            if(url.trim()) {{
                pubsArray.push({{
                    type: div.querySelector('.pub-type').value,
                    url: url,
                    desc: div.querySelector('.pub-desc').value
                }});
            }}
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
            publications: pubsArray,
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
    
    # Generar HTML de Publicaciones (Videos/Imágenes)
    pubs_html = ""
    for p in c.get('publications', []):
        if p.get('url'):
            if p.get('type') == 'video':
                pubs_html += f"""
                <div style="text-align: center; margin-bottom: 50px;">
                    <iframe src="{p['url']}" width="560" height="315" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="border-radius: 10px; border: 2px solid var(--cyan); max-width: 100%;"></iframe>
                    <p style="margin-top: 15px; font-size: 1.1rem; color: #94a3b8; max-width: 600px; margin-left: auto; margin-right: auto;">{p.get('desc', '')}</p>
                </div>
                """
            elif p.get('type') == 'image':
                pubs_html += f"""
                <div style="text-align: center; margin-bottom: 50px;">
                    <img src="{p['url']}" alt="Publicación" style="max-width: 100%; border-radius: 10px; border: 2px solid var(--cyan);">
                    <p style="margin-top: 15px; font-size: 1.1rem; color: #94a3b8; max-width: 600px; margin-left: auto; margin-right: auto;">{p.get('desc', '')}</p>
                </div>
                """

    # Generar HTML de Planes
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

    # Plantilla principal usando string replace para no romper el CSS/JS de MailerLite
    template = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BLENIN.G.77 THE BEST FUTURE FOR YOU</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --cyan: #00e5ff; --dark: #0d1b2a; --card: #1b263b; --text: #e0e1dd; }
        body { margin: 0; font-family: 'Segoe UI', sans-serif; background: var(--dark); color: var(--text); scroll-behavior: smooth; }
        nav { background: rgba(13, 27, 42, 0.9); backdrop-filter: blur(10px); padding: 15px 5%; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 100; border-bottom: 1px solid #334155; flex-wrap: wrap; }
        nav .logo { color: var(--cyan); font-size: 1rem; font-weight: bold; text-decoration: none; max-width: 60%; line-height: 1.4; }
        nav ul { list-style: none; display: flex; gap: 20px; }
        nav ul li a { color: var(--text); text-decoration: none; transition: 0.3s; }
        nav ul li a:hover { color: var(--cyan); }
        .hero { text-align: center; padding: 120px 20px; background: linear-gradient(to bottom, rgba(0, 0, 0, 0.2) 0%, rgba(13, 27, 42, 0.8) 100%), url('https://raw.githubusercontent.com/mymundodigital0-cmyk/blenin77-server/main/bienvenida_blenin.png') center/cover no-repeat; color: white; }
        .hero h1 { font-size: 2.5rem; color: var(--cyan); margin: 0; text-shadow: 0 0 20px rgba(0, 0, 0, 1); }
        .hero h2 { font-size: 1.2rem; color: #fff; margin: 10px 0; text-shadow: 2px 2px 4px rgba(0,0,0,1); font-weight: normal; }
        .hero p { font-size: 1.3rem; max-width: 600px; margin: 20px auto; color: #e0e1dd; text-shadow: 2px 2px 4px rgba(0,0,0,1); }
        .btn-primary { background: var(--cyan); color: #000; padding: 15px 30px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; font-size: 1rem; transition: 0.3s; text-decoration: none; display: inline-block; }
        .btn-primary:hover { background: #fff; transform: translateY(-2px); }
        .section { padding: 60px 10%; max-width: 1200px; margin: 0 auto; }
        .section h2 { text-align: center; font-size: 2.5rem; color: #fff; margin-bottom: 40px; }
        .grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; }
        .card { background: var(--card); padding: 30px; border-radius: 15px; border: 1px solid #334155; transition: 0.3s; }
        .card:hover { transform: translateY(-5px); border-color: var(--cyan); }
        .card h3 { color: var(--cyan); font-size: 1.5rem; margin-top: 0; }
        .video-container { display: flex; flex-direction: column; align-items: center; gap: 20px; flex-wrap: wrap; }
        .social-footer { text-align: center; margin-top: 40px; }
        .social-footer h3 { color: #fff; margin-bottom: 20px; }
        .social-icons-footer { display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; }
        .social-icons-footer a { width: 50px; height: 50px; border-radius: 50%; background: #334155; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; transition: 0.3s; text-decoration: none; }
        .social-icons-footer a:hover { transform: scale(1.2); background: var(--cyan); color: #000; }
        footer { background: #000; padding: 40px 20px; text-align: center; margin-top: 0; }
        .copyright { color: #64748b; font-size: 0.9rem; max-width: 800px; margin: 0 auto; }
        .ml-form-embedWrapper { margin: 30px auto !important; max-width: 400px !important; }
    </style>
</head>
<body>
    <nav>
        <a href="#" class="logo">BLENIN.G.77 THE BEST FUTURE FOR YOU ܐܠܗܐ ܪܥܐ ܠܝ ܘܠܐ ܐܟܣܪ ܠܝ ܒܟܠ ܫܘܡܐ</a>
        <ul>
            <li><a href="#features">Funciones</a></li>
            <li><a href="#videos">Galería</a></li>
            <li><a href="#pricing">Precios</a></li>
        </ul>
    </nav>

    <div class="hero">
        <h1>{HERO_TITLE}</h1>
        <h2>{HERO_SUBTITLE}</h2>
        <p>{HERO_TEXT}</p>
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
            {PUBLICATIONS_HTML}
        </div>
    </div>

    <div id="pricing" class="section">
        <h2>Planes de Suscripción</h2>
        <div class="grid-3">
            {PLANS_HTML}
        </div>
    </div>

    <!-- INICIO FORMULARIO MAILERLITE -->
    <div class="section" style="max-width: 600px; margin: 0 auto 60px auto;">
        <style type="text/css">@import url("https://assets.mlcdn.com/fonts.css?version=1785409");</style>
        <style type="text/css">
            .ml-form-embedSubmitLoad { display: inline-block; width: 20px; height: 20px; }
            .g-recaptcha { transform: scale(1); -webkit-transform: scale(1); transform-origin: 0 0; -webkit-transform-origin: 0 0; height: ; }
            .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); border: 0; }
            .ml-form-embedSubmitLoad:after { content: " "; display: block; width: 11px; height: 11px; margin: 1px; border-radius: 50%; border: 4px solid #fff; border-color: #ffffff #ffffff #ffffff transparent; animation: ml-form-embedSubmitLoad 1.2s linear infinite; }
            @keyframes ml-form-embedSubmitLoad { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            #mlb2-44360624.ml-form-embedContainer { box-sizing: border-box; display: table; margin: 0 auto; position: static; width: 100% !important; }
            #mlb2-44360624.ml-form-embedContainer h4, #mlb2-44360624.ml-form-embedContainer p, #mlb2-44360624.ml-form-embedContainer span, #mlb2-44360624.ml-form-embedContainer button { text-transform: none !important; letter-spacing: normal !important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper { background-color: #ffffff; border-width: 0px; border-color: transparent; border-radius: 4px; border-style: solid; box-sizing: border-box; display: inline-block !important; margin: 0; padding: 0; position: relative; }
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
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedContent h4, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-successBody .ml-form-successContent h4 { color: #7e84c7; font-family: 'Roboto', Arial, Helvetica, sans-serif; font-size: 25px; font-weight: 700; margin: 0 0 10px 0; text-align: center; word-break: break-word; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedContent p, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-successBody .ml-form-successContent p { color: #293788; font-family: 'Open Sans', Arial, Helvetica, sans-serif; font-size: 14px; font-weight: 400; line-height: 20px; margin: 0 0 10px 0; text-align: center; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedContent ul, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedContent ol, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-successBody .ml-form-successContent ul, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-successBody .ml-form-successContent ol { color: #293788; font-family: 'Open Sans', Arial, Helvetica, sans-serif; font-size: 14px; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedContent ol ol, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-successBody .ml-form-successContent ol ol { list-style-type: lower-alpha; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedContent ol ol ol, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-successBody .ml-form-successContent ol ol ol { list-style-type: lower-roman; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedContent p a, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-successBody .ml-form-successContent p a { color: #000000; text-decoration: underline; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-block-form .ml-field-group { text-align: left!important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-block-form .ml-field-group label { margin-bottom: 5px; color: #333333; font-size: 14px; font-family: 'Open Sans', Arial, Helvetica, sans-serif; font-weight: bold; font-style: normal; text-decoration: none; display: inline-block; line-height: 20px; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedContent p:last-child, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-successBody .ml-form-successContent p:last-child { margin: 0; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody form { margin: 0; width: 100%; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-formContent, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow { margin: 0 0 20px 0; width: 100%; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow { float: left; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-formContent.horozintalForm { margin: 0; padding: 0 0 20px 0; width: 100%; height: auto; float: left; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow { margin: 0 0 10px 0; width: 100%; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow.ml-last-item { margin: 0; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow.ml-formfieldHorizintal { margin: 0; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow input { background-color: #3dffff !important; color: #3e0e4a !important; border-color: #cccccc; border-radius: 4px !important; border-style: solid !important; border-width: 1px !important; font-family: 'Open Sans', Arial, Helvetica, sans-serif; font-size: 14px !important; height: auto; line-height: 21px !important; margin-bottom: 0; margin-top: 0; margin-left: 0; margin-right: 0; padding: 10px 10px !important; width: 100% !important; box-sizing: border-box !important; max-width: 100% !important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow input::-webkit-input-placeholder, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow input::-webkit-input-placeholder { color: #3e0e4a; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow input::-moz-placeholder, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow input::-moz-placeholder { color: #3e0e4a; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow input:-ms-input-placeholder, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow input:-ms-input-placeholder { color: #3e0e4a; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow input:-moz-placeholder, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow input:-moz-placeholder { color: #3e0e4a; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow textarea, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow textarea { background-color: #3dffff !important; color: #3e0e4a !important; border-color: #cccccc; border-radius: 4px !important; border-style: solid !important; border-width: 1px !important; font-family: 'Open Sans', Arial, Helvetica, sans-serif; font-size: 14px !important; height: auto; line-height: 21px !important; margin-bottom: 0; margin-top: 0; padding: 10px 10px !important; width: 100% !important; box-sizing: border-box !important; max-width: 100% !important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow .custom-radio .custom-control-label::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow .custom-radio .custom-control-label::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow .custom-checkbox .custom-control-label::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow .custom-checkbox .custom-control-label::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedPermissions .ml-form-embedPermissionsOptionsCheckbox .label-description::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-interestGroupsRow .ml-form-interestGroupsRowCheckbox .label-description::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow .label-description::before { border-color: #cccccc!important; background-color: #3dffff!important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow input.custom-control-input[type="checkbox"]{ box-sizing: border-box; padding: 0; position: absolute; z-index: -1; opacity: 0; margin-top: 5px; margin-left: -1.5rem; overflow: visible; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow .custom-checkbox .custom-control-label::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow .custom-checkbox .custom-control-label::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedPermissions .ml-form-embedPermissionsOptionsCheckbox .label-description::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-interestGroupsRow .ml-form-interestGroupsRowCheckbox .label-description::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow .label-description::before { border-radius: 4px!important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow input[type=checkbox]:checked~.label-description::after, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedPermissions .ml-form-embedPermissionsOptionsCheckbox input[type=checkbox]:checked~.label-description::after, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow .custom-checkbox .custom-control-input:checked~.custom-control-label::after, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow .custom-checkbox .custom-control-input:checked~.custom-control-label::after, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-interestGroupsRow .ml-form-interestGroupsRowCheckbox input[type=checkbox]:checked~.label-description::after { background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 8'%3e%3cpath fill='%23fff' d='M6.564.75l-3.59 3.612-1.538-1.55L0 4.26 2.974 7.25 8 2.193z'/%3e%3c/svg%3e"); }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow .custom-radio .custom-control-input:checked~.custom-control-label::after, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow .custom-radio .custom-control-input:checked~.custom-control-label::after { background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='-4 -4 8 8'%3e%3ccircle r='3' fill='%23fff'/%3e%3c/svg%3e"); }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow .custom-radio .custom-control-input:checked~.custom-control-label::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow .custom-radio .custom-control-input:checked~.custom-control-label::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow .custom-checkbox .custom-control-input:checked~.custom-control-label::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow .custom-checkbox .custom-control-input:checked~.custom-control-label::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedPermissions .ml-form-embedPermissionsOptionsCheckbox input[type=checkbox]:checked~.label-description::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-interestGroupsRow .ml-form-interestGroupsRowCheckbox input[type=checkbox]:checked~.label-description::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow input[type=checkbox]:checked~.label-description::before { border-color: #000000!important; background-color: #000000!important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow .custom-radio .custom-control-label::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow .custom-radio .custom-control-label::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow .custom-radio .custom-control-label::after, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow .custom-radio .custom-control-label::after, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow .custom-checkbox .custom-control-label::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow .custom-checkbox .custom-control-label::after, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow .custom-checkbox .custom-control-label::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow .custom-checkbox .custom-control-label::after { top: 2px; box-sizing: border-box; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedPermissions .ml-form-embedPermissionsOptionsCheckbox .label-description::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedPermissions .ml-form-embedPermissionsOptionsCheckbox .label-description::after, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow .label-description::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow .label-description::after { top: 0px!important; box-sizing: border-box!important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow .label-description::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow .label-description::after { top: 0px!important; box-sizing: border-box!important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-interestGroupsRow .ml-form-interestGroupsRowCheckbox .label-description::after { top: 0px!important; box-sizing: border-box!important; position: absolute; left: -1.5rem; display: block; width: 1rem; height: 1rem; content: ""; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-interestGroupsRow .ml-form-interestGroupsRowCheckbox .label-description::before { top: 0px!important; box-sizing: border-box!important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .custom-control-label::before { position: absolute; top: 4px; left: -1.5rem; display: block; width: 16px; height: 16px; pointer-events: none; content: ""; background-color: #ffffff; border: #adb5bd solid 1px; border-radius: 50%; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .custom-control-label::after { position: absolute; top: 2px!important; left: -1.5rem; display: block; width: 1rem; height: 1rem; content: ""; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedPermissions .ml-form-embedPermissionsOptionsCheckbox .label-description::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-interestGroupsRow .ml-form-interestGroupsRowCheckbox .label-description::before, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow .label-description::before { position: absolute; top: 4px; left: -1.5rem; display: block; width: 16px; height: 16px; pointer-events: none; content: ""; background-color: #ffffff; border: #adb5bd solid 1px; border-radius: 50%; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedPermissions .ml-form-embedPermissionsOptionsCheckbox .label-description::after { position: absolute; top: 0px!important; left: -1.5rem; display: block; width: 1rem; height: 1rem; content: ""; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow .label-description::after { position: absolute; top: 0px!important; left: -1.5rem; display: block; width: 1rem; height: 1rem; content: ""; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .custom-radio .custom-control-label::after { background: no-repeat 50%/50% 50%; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .custom-checkbox .custom-control-label::after, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedPermissions .ml-form-embedPermissionsOptionsCheckbox .label-description::after, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-interestGroupsRow .ml-form-interestGroupsRowCheckbox .label-description::after, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow .label-description::after { background: no-repeat 50%/50% 50%; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow .custom-control, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow .custom-control { position: relative; display: block; min-height: 1.5rem; padding-left: 1.5rem; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow .custom-radio .custom-control-input, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow .custom-radio .custom-control-input, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow .custom-checkbox .custom-control-input, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow .custom-checkbox .custom-control-input { position: absolute; z-index: -1; opacity: 0; box-sizing: border-box; padding: 0; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow .custom-radio .custom-control-label, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow .custom-radio .custom-control-label, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow .custom-checkbox .custom-control-label, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow .custom-checkbox .custom-control-label { color: #dc44b5; font-size: 12px!important; font-family: 'Open Sans', Arial, Helvetica, sans-serif; line-height: 22px; margin-bottom: 0; position: relative; vertical-align: top; font-style: normal; font-weight: 700; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow .custom-select, #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow .custom-select { background-color: #3dffff !important; color: #3e0e4a !important; border-color: #cccccc; border-radius: 4px !important; border-style: solid !important; border-width: 1px !important; font-family: 'Open Sans', Arial, Helvetica, sans-serif; font-size: 14px !important; line-height: 20px !important; margin-bottom: 0; margin-top: 0; padding: 10px 28px 10px 12px !important; width: 100% !important; box-sizing: border-box !important; max-width: 100% !important; height: auto; display: inline-block; vertical-align: middle; background: url('https://assets.mlcdn.com/ml/images/default/dropdown.svg') no-repeat right .75rem center/8px 10px; -webkit-appearance: none; -moz-appearance: none; appearance: none; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow { height: auto; width: 100%; float: left; }
            .ml-form-formContent.horozintalForm .ml-form-horizontalRow .ml-input-horizontal { width: 70%; float: left; }
            .ml-form-formContent.horozintalForm .ml-form-horizontalRow .ml-button-horizontal { width: 30%; float: left; }
            .ml-form-formContent.horozintalForm .ml-form-horizontalRow .ml-button-horizontal.labelsOn { padding-top: 25px; }
            .ml-form-formContent.horozintalForm .ml-form-horizontalRow .horizontal-fields { box-sizing: border-box; float: left; padding-right: 10px; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow input { background-color: #3dffff; color: #3e0e4a; border-color: #cccccc; border-radius: 4px; border-style: solid; border-width: 1px; font-family: 'Open Sans', Arial, Helvetica, sans-serif; font-size: 14px; line-height: 20px; margin-bottom: 0; margin-top: 0; padding: 10px 10px; width: 100%; box-sizing: border-box; overflow-y: initial; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow button { background-color: #772fbd !important; border-color: #772fbd; border-style: solid; border-width: 1px; border-radius: 4px; box-shadow: none; color: #ffffff !important; cursor: pointer; font-family: 'Open Sans', Arial, Helvetica, sans-serif; font-size: 14px !important; font-weight: 700; line-height: 20px; margin: 0 !important; padding: 10px !important; width: 100%; height: auto; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow button:hover { background-color: #333333 !important; border-color: #333333 !important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow input[type="checkbox"] { box-sizing: border-box; padding: 0; position: absolute; z-index: -1; opacity: 0; margin-top: 5px; margin-left: -1.5rem; overflow: visible; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow .label-description { color: #000000; display: block; font-family: 'Open Sans', Arial, Helvetica, sans-serif; font-size: 12px; text-align: left; margin-bottom: 0; position: relative; vertical-align: top; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow label { font-weight: normal; margin: 0; padding: 0; position: relative; display: block; min-height: 24px; padding-left: 24px; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow label a { color: #000000; text-decoration: underline; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow label p { color: #000000 !important; font-family: 'Open Sans', Arial, Helvetica, sans-serif !important; font-size: 12px !important; font-weight: normal !important; line-height: 18px !important; padding: 0 !important; margin: 0 5px 0 0 !important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-checkboxRow label p:last-child { margin: 0; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedSubmit { margin: 0 0 20px 0; float: left; width: 100%; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedSubmit button { background-color: #772fbd !important; border: none !important; border-radius: 4px !important; box-shadow: none !important; color: #ffffff !important; cursor: pointer; font-family: 'Open Sans', Arial, Helvetica, sans-serif !important; font-size: 14px !important; font-weight: 700 !important; line-height: 21px !important; height: auto; padding: 10px !important; width: 100% !important; box-sizing: border-box !important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedSubmit button.loading { display: none; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedSubmit button:hover { background-color: #333333 !important; }
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
                            <p><strong><u><span style="font-size: 10px;"></span></u></strong>"Deja tu correo y te enviaremos un video de cómo el Enjambre de Agentes abre operaciones reales."</p>
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

    <div class="social-footer">
        <h3>Síguenos en nuestras redes</h3>
        <div class="social-icons-footer">
            <a href="TU_ENLACE_FACEBOOK_AQUI" target="_blank" title="Facebook"><i class="fab fa-facebook-f"></i></a>
            <a href="TU_ENLACE_WHATSAPP_AQUI" target="_blank" title="WhatsApp"><i class="fab fa-whatsapp"></i></a>
            <a href="TU_ENLACE_YOUTUBE_AQUI" target="_blank" title="YouTube"><i class="fab fa-youtube"></i></a>
            <a href="TU_ENLACE_TIKTOK_AQUI" target="_blank" title="TikTok"><i class="fab fa-tiktok"></i></a>
            <a href="TU_ENLACE_TELEGRAM_AQUI" target="_blank" title="Telegram"><i class="fab fa-telegram-plane"></i></a>
            <a href="TU_ENLACE_INSTAGRAM_AQUI" target="_blank" title="Instagram"><i class="fab fa-instagram"></i></a>
        </div>
    </div>

    <footer>
        <p class="copyright">&copy; 2026 BLENIN.G.77 THE BEST FUTURE FOR YOU. Todos los derechos reservados. Creado por Lenin Benitez.</p>
    </footer>

    <!-- 🤖 INICIO AGENTE IA DE SOPORTE (Chatbase) -->
    <script>
    (function(){if(!window.chatbase||window.chatbase("getState")!=="initialized"){window.chatbase=(...arguments)=>{if(!window.chatbase.q){window.chatbase.q=[]}window.chatbase.q.push(arguments)};window.chatbase=new Proxy(window.chatbase,{get(target,prop){if(prop==="q"){return target.q}return(...args)=>target(prop,...args)}})}const onLoad=function(){const script=document.createElement("script");script.src="https://www.chatbase.co/embed.min.js";script.id="gzEjAzK1VCE72hJ_hBfA4";script.domain="www.chatbase.co";document.body.appendChild(script)};if(document.readyState==="complete"){onLoad()}else{window.addEventListener("load",onLoad)}})();
    </script>
    <!-- 🤖 FIN AGENTE IA DE SOPORTE -->

</body>
</html>"""

    return template.replace("{HERO_TITLE}", c.get('hero_title', '')).replace("{HERO_SUBTITLE}", c.get('hero_subtitle', '')).replace("{HERO_TEXT}", c.get('hero_text', '')).replace("{PUBLICATIONS_HTML}", pubs_html).replace("{PLANS_HTML}", plans_html)

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
