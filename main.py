landing_html = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BLENIN77 - Plataforma de Trading Cuantitativo</title>
    <style>
        :root { --cyan: #00e5ff; --dark: #0d1b2a; --card: #1b263b; --text: #e0e1dd; }
        body { margin: 0; font-family: 'Segoe UI', sans-serif; background: var(--dark); color: var(--text); scroll-behavior: smooth; }
        nav { background: rgba(13, 27, 42, 0.9); backdrop-filter: blur(10px); padding: 15px 5%; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 100; border-bottom: 1px solid #334155; }
        nav .logo { color: var(--cyan); font-size: 1.5rem; font-weight: bold; text-decoration: none; }
        nav ul { list-style: none; display: flex; gap: 20px; }
        nav ul li a { color: var(--text); text-decoration: none; transition: 0.3s; }
        nav ul li a:hover { color: var(--cyan); }
        .hero { text-align: center; padding: 80px 20px; background: radial-gradient(circle at 50% 50%, #1b263b 0%, var(--dark) 100%); }
        .hero h1 { font-size: 3.5rem; color: var(--cyan); margin: 0; text-shadow: 0 0 20px rgba(0, 229, 255, 0.5); }
        .hero p { font-size: 1.3rem; max-width: 600px; margin: 20px auto; color: #94a3b8; }
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
        .copyright { color: #64748b; font-size: 0.9rem; }
    </style>
</head>
<body>

    <nav>
        <a href="#" class="logo">BLENIN77</a>
        <ul>
            <li><a href="#features">Funciones</a></li>
            <li><a href="#videos">Videos</a></li>
            <li><a href="#pricing">Precios</a></li>
            <li><a href="#community">Comunidad</a></li>
        </ul>
    </nav>

    <div class="hero">
        <h1>El Futuro del Trading Algorítmico</h1>
        <p>IA Predictiva, Enjambre de 500 Agentes y Análisis Global en Tiempo Real. Únete a la revolución cuantitativa.</p>
        <!-- EMBUDO DE VENTAS: Registro de correo -->
        <form action="https://TU_URL_DE_MAILERLITE.com" method="post" style="margin-top: 30px;">
            <input type="email" class="cta-input" name="email" placeholder="Ingresa tu correo para ver el bot en acción..." required>
            <button type="submit" class="btn-primary">Quiero Acceso</button>
        </form>
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
            <!-- Reemplaza este link por el ID de tu video de YouTube -->
            <iframe src="https://www.youtube.com/embed/dQw4w9WgXcQ" title="Video 1" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
            <iframe src="https://www.youtube.com/embed/dQw4w9WgXcQ" title="Video 2" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
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
        
        <!-- BOTÓN PARA UNIRSE A TELEGRAM/DISCORD -->
        <div style="text-align: center; margin-bottom: 40px;">
            <a href="https://t.me/tu_canal_de_telegram" class="btn-primary" style="background: #0088cc; color: white;">Únete a nuestro Telegram</a>
        </div>

        <!-- SISTEMA DE COMENTARIOS DISQUS -->
        <div id="disqus_thread"></div>
        <script>
            var disqus_config = function () {
                this.page.url = "https://blenin77-server.onrender.com"; // Pon tu URL real
                this.page.identifier = "blenin77-home";
            };
            (function() {
                var d = document, s = d.createElement('script');
                s.src = 'https://TU_SITIO_DISQUS.disqus.com/embed.js'; // Pon tu sitio de Disqus
                s.setAttribute('data-timestamp', +new Date());
                (d.head || d.body).appendChild(s);
            })();
        </script>
    </div>

    <footer>
        <div class="social-icons">
            <!-- Íconos de redes sociales (usando texto/emoji por simplicidad, puedes cambiar a SVG) -->
            <a href="https://t.me/tu_canal">📱</a>
            <a href="https://youtube.com">▶️</a>
            <a href="https://twitter.com">🐦</a>
            <a href="https://instagram.com">📸</a>
        </div>
        <p class="copyright">&copy; 2026 BLENIN77. Todos los derechos reservados. Creado por Lenin Benitez.</p>
    </footer>

</body>
</html>
"""
