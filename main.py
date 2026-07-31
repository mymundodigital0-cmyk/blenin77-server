from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from collections import defaultdict
from datetime import datetime, timedelta
import random
import string

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 🌐 PÁGINA WEB DE VENTAS (Landing Page)
# ==========================================
landing_html = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BLENIN.G.77 THE BEST FUTURE FOR YOU</title>
    <style>
        :root { --cyan: #00e5ff; --dark: #0d1b2a; --card: #1b263b; --text: #e0e1dd; }
        body { margin: 0; font-family: 'Segoe UI', sans-serif; background: var(--dark); color: var(--text); scroll-behavior: smooth; }
        nav { background: rgba(13, 27, 42, 0.9); backdrop-filter: blur(10px); padding: 15px 5%; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 100; border-bottom: 1px solid #334155; flex-wrap: wrap; }
        nav .logo { color: var(--cyan); font-size: 1rem; font-weight: bold; text-decoration: none; max-width: 60%; line-height: 1.4; }
        nav ul { list-style: none; display: flex; gap: 20px; }
        nav ul li a { color: var(--text); text-decoration: none; transition: 0.3s; }
        nav ul li a:hover { color: var(--cyan); }
        
        /* Imagen de fondo */
        .hero { text-align: center; padding: 120px 20px; background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(13, 27, 42, 0.9)), url('https://raw.githubusercontent.com/mymundodigital0-cmyk/blenin77-server/main/bienvenida_blenin.png') center/cover no-repeat; color: white; }
        
        .hero h1 { font-size: 2.5rem; color: var(--cyan); margin: 0; text-shadow: 0 0 20px rgba(0, 0, 0, 0.8); }
        .hero h2 { font-size: 1.2rem; color: #fff; margin: 10px 0; text-shadow: 1px 1px 4px rgba(0,0,0,0.8); font-weight: normal; }
        .hero p { font-size: 1.3rem; max-width: 600px; margin: 20px auto; color: #e0e1dd; text-shadow: 1px 1px 4px rgba(0,0,0,0.8); }
        .cta-input { padding: 15px; width: 300px; border-radius: 5px; border: none; background: #fff; color: #000; font-size: 1rem; margin-right: 10px; }
        .btn-primary { background: var(--cyan); color: #000; padding: 15px 30px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; font-size: 1rem; transition: 0.3s; text-decoration: none; display: inline-block; }
        .btn-primary:hover { background: #fff; transform: translateY(-2px); }
        
        .section { padding: 60px 10%; max-width: 1200px; margin: 0 auto; }
        .section h2 { text-align: center; font-size: 2.5rem; color: #fff; margin-bottom: 40px; }
        .grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; }
        .card { background: var(--card); padding: 30px; border-radius: 15px; border: 1px solid #334155; transition: 0.3s; }
        .card:hover { transform: translateY(-5px); border-color: var(--cyan); }
        .card h3 { color: var(--cyan); font-size: 1.5rem; margin-top: 0; }
        
        .video-container { display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; }
        .video-container iframe { width: 560px; height: 315px; border-radius: 10px; border: 2px solid var(--cyan); max-width: 100%; }
        
        .comments-section { background: var(--card); padding: 40px; border-radius: 15px; margin: 40px 10%; max-width: 800px; margin-left: auto; margin-right: auto; }
        
        footer { background: #000; padding: 40px 20px; text-align: center; margin-top: 60px; }
        .social-icons { display: flex; justify-content: center; gap: 20px; margin-bottom: 20px; }
        .social-icons a { color: #94a3b8; font-size: 2rem; transition: 0.3s; }
        .social-icons a:hover { color: var(--cyan); transform: scale(1.2); }
        .copyright { color: #64748b; font-size: 0.9rem; max-width: 800px; margin: 0 auto; }
        
        /* Estilos del formulario MailerLite */
        .ml-form-embedWrapper { margin: 30px auto !important; max-width: 400px !important; }
    </style>
</head>
<body>

    <nav>
        <a href="#" class="logo">BLENIN.G.77 THE BEST FUTURE FOR YOU ܐܠܗܐ ܪܥܐ ܠܝ ܘܠܐ ܐܟܣܪ ܠܝ ܒܟܠ ܫܘܡܐ</a>
        <ul>
            <li><a href="#features">Funciones</a></li>
            <li><a href="#videos">Videos</a></li>
            <li><a href="#pricing">Precios</a></li>
            <li><a href="#community">Comunidad</a></li>
        </ul>
    </nav>

    <div class="hero">
        <h1>BLENIN.G.77</h1>
        <h2>THE BEST FUTURE FOR YOU</h2>
        <h2>ܐܠܗܐ ܪܥܐ ܠܝ ܘܠܐ ܐܟܣܪ ܠܝ ܒܟܠ ܫܘܡܐ</h2>
        <p>IA Predictiva, Enjambre de 500 Agentes y Análisis Global en Tiempo Real. Únete a la revolución cuantitativa.</p>
    </div>

    <div id="features" class="section">
        <h2>Tecnología de Nivel Institucional</h2>
        <div class="grid-3">
            <div class="card">
                <h3>🐟 Enjambre 3D</h3>
                <p>Antes de abrir una operación, 500 agentes virtuales simulan el futuro del mercado en milisegundos basándose en el patrón histórico del activo.</p>
            </div>
            <div class="card">
                <h3>🛡️ Agente Centinela</h3>
                <p>Un guardaespaldas que lee Reuters, CNBC y la Fed en tiempo real. Si detecta un crash, bloquea al bot para proteger tu capital.</p>
            </div>
            <div class="card">
                <h3>🧠 Cerebro Global</h3>
                <p>Red neuronal descentralizada. Tu bot aprende de las operaciones exitosas y fallidas de todos los usuarios a nivel mundial.</p>
            </div>
        </div>
    </div>

    <div id="videos" class="section">
        <h2>Mira al Sistema en Acción</h2>
        <div class="video-container">
            <iframe src="https://www.youtube.com/embed/dQw4w9WgXcQ" title="Video 1" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
        </div>
    </div>

    <div id="pricing" class="section">
        <h2>Planes de Suscripción</h2>
        <div class="grid-3">
            <div class="card">
                <h3>🥉 Bronce</h3>
                <div style="font-size: 2rem; color: var(--cyan); margin: 15px 0;">$49<span style="font-size:1rem; color:#94a3b8;">/mes</span></div>
                <p>✅ 1 Cuenta MT5</p>
                <p>✅ Modo MT5 Puro</p>
                <a href="https://buy.stripe.com/test_4gw3eq8eV6YX7OEdQQ" class="btn-primary" style="margin-top: 20px;">Suscribirme</a>
            </div>
            <div class="card" style="border: 2px solid var(--cyan); transform: scale(1.05);">
                <h3>🥈 Plata</h3>
                <div style="font-size: 2rem; color: var(--cyan); margin: 15px 0;">$99<span style="font-size:1rem; color:#94a3b8;">/mes</span></div>
                <p>✅ 2 Cuentas MT5</p>
                <p>✅ Modo Híbrido + Enjambre</p>
                <a href="https://buy.stripe.com/test_28o5mA4gF2AS5xO000" class="btn-primary" style="margin-top: 20px;">Suscribirme</a>
            </div>
            <div class="card">
                <h3>🥇 Oro</h3>
                <div style="font-size: 2rem; color: var(--cyan); margin: 15px 0;">$199<span style="font-size:1rem; color:#94a3b8;">/mes</span></div>
                <p>✅ Cuentas Ilimitadas</p>
                <p>✅ Deep Learning (PyTorch)</p>
                <a href="https://buy.stripe.com/test_8wM3eqdEj9zC5xO146" class="btn-primary" style="margin-top: 20px;">Suscribirme</a>
            </div>
        </div>
    </div>

    <div id="community" class="comments-section">
        <h2>Comunidad y Testimonios</h2>
        <p style="text-align: center; margin-bottom: 30px;">Comparte tus configuraciones, resultados y aprende de otros traders.</p>
        <div style="text-align: center; margin-bottom: 40px;">
            <a href="https://t.me/tu_canal_de_telegram" class="btn-primary" style="background: #0088cc; color: white;">Únete a nuestro Telegram</a>
        </div>
    </div>

    <!-- INICIO FORMULARIO MAILERLITE (Movido al final) -->
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
            @media only screen and (max-width: 400px){ .ml-form-embedWrapper.embedDefault, .ml-form-embedWrapper.embedPopup { width: 100%!important; } .ml-form-formContent.horozintalForm { float: left!important; } .ml-form-formContent.horozintalForm .ml-form-horizontalRow { height: auto!important; width: 100%!important; float: left!important; } .ml-form-formContent.horozintalForm .ml-form-horizontalRow .ml-input-horizontal { width: 100%!important; } .ml-form-formContent.horozintalForm .ml-form-horizontalRow .ml-input-horizontal > div { padding-right: 0px!important; padding-bottom: 10px; } .ml-form-formContent.horozintalForm .ml-button-horizontal { width: 100%!important; } .ml-form-formContent.horozintalForm .ml-button-horizontal.labelsOn { padding-top: 0px!important; } }
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

    <footer>
        <div class="social-icons">
            <a href="https://t.me/tu_canal">📱</a>
            <a href="https://youtube.com">▶️</a>
            <a href="https://twitter.com">🐦</a>
            <a href="https://instagram.com">📸</a>
        </div>
        <p class="copyright">&copy; 2026 BLENIN.G.77 THE BEST FUTURE FOR YOU ܐܠܗܐ ܪܥܐ ܠܝ ܘܠܐ ܐܟܣܪ ܠܝ ܒܟܠ ܫܘܡܐ. Todos los derechos reservados. Creado por Lenin Benitez.</p>
    </footer>

</body>
</html>
"""

# ==========================================
# 🧠 BASES DE DATOS EN MEMORIA
# ==========================================
db_trades = []
licenses_db = {
    "BLENIN-TEST-1234": {"hwid": None, "expires": datetime.now() + timedelta(days=30), "active": True, "plan": "ORO"}
}

# ==========================================
# 📦 MODELOS DE DATOS (Pydantic)
# ==========================================
class TradeData(BaseModel):
    strategy: str
    symbol: str
    timeframe: str
    outcome: bool
    profit_pips: float
    session: str

class LicenseCheck(BaseModel):
    key: str
    hwid: str

class LicenseCreate(BaseModel):
    plan: str
    duration_days: int = 30

class LicenseAction(BaseModel):
    key: str

def generate_license_key(plan):
    part1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    part2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    plan_name = plan.upper().split()[0]
    return f"BLENIN-{plan_name}-{part1}-{part2}"

# ==========================================
# 🌐 RUTA WEB (Lo que ve el usuario en internet)
# ==========================================
@app.get("/", response_class=HTMLResponse)
def read_root():
    return landing_html

# ==========================================
# 🐟 RUTAS DEL CEREBRO GLOBAL (IA)
# ==========================================
@app.post("/api/sync_intel")
def receive_intel(trade: TradeData):
    db_trades.append(trade)
    return {"status": "received", "total_trades": len(db_trades)}

@app.get("/api/get_global_intel")
def get_intel():
    if not db_trades: return {}
    stats = defaultdict(lambda: {"wins": 0, "total": 0})
    for t in db_trades:
        key = f"{t.strategy}_{t.symbol}_{t.session}"
        stats[key]["total"] += 1
        if t.outcome: stats[key]["wins"] += 1
    result = {}
    for key, val in stats.items():
        if val["total"] > 0:
            result[key] = {"win_rate": val["wins"] / val["total"], "trades": val["total"]}
    return result

# ==========================================
# 🔒 RUTAS DE LICENCIAS (Sistema de Cobros)
# ==========================================
@app.post("/api/validate_license")
def validate_license(data: LicenseCheck):
    key = data.key.upper().strip()
    if key not in licenses_db:
        return {"valid": False, "message": "❌ Licencia no encontrada."}
    
    license_info = licenses_db[key]
    
    if not license_info["active"]:
        return {"valid": False, "message": "🚫 Licencia suspendada por falta de pago."}
        
    if datetime.now() > license_info["expires"]:
        return {"valid": False, "message": "⏳ Tu suscripción ha expirado. Renueva en blenin77.com."}
        
    if license_info["hwid"] is None:
        license_info["hwid"] = data.hwid
    elif license_info["hwid"] != data.hwid:
        return {"valid": False, "message": "🔒 Esta licencia ya está activada en otra PC."}
        
    days_left = (license_info["expires"] - datetime.now()).days
    return {"valid": True, "message": f"✅ Licencia activa. Quedan {days_left} días.", "days_left": days_left}

@app.post("/api/create_license")
def create_license(data: LicenseCreate):
    """Make.com llama esta ruta cuando Stripe confirma un pago"""
    key = generate_license_key(data.plan)
    licenses_db[key] = {
        "hwid": None,
        "expires": datetime.now() + timedelta(days=data.duration_days),
        "active": True,
        "plan": data.plan
    }
    return {"status": "success", "key": key}

@app.post("/api/suspend_license")
def suspend_license(data: LicenseAction):
    """Make.com llama esta ruta cuando Stripe reporta que el pago falló"""
    key = data.key.upper().strip()
    if key in licenses_db:
        licenses_db[key]["active"] = False
        return {"status": "success", "message": "Licencia suspendida."}
    return {"status": "error", "message": "Licencia no encontrada."}

@app.post("/api/renew_license")
def renew_license(data: LicenseAction):
    """Make.com llama esta ruta para renovar 30 días más"""
    key = data.key.upper().strip()
    if key in licenses_db:
        licenses_db[key]["active"] = True
        licenses_db[key]["expires"] = datetime.now() + timedelta(days=30)
        return {"status": "success", "message": "Licencia renovada."}
    return {"status": "error", "message": "Licencia no encontrada."}
