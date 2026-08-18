# ==========================================
# 🌐 PÁGINA WEB DE VENTAS (LANDING PAGE)
# ==========================================
@app.get("/", response_class=HTMLResponse)
def read_root():
    c = get_content()
    
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

    # Mantenemos el código de MailerLite intacto en esta variable
    mailerlite_html = """
    <div class="section max-w-600px mx-auto mb-20">
        <style type="text/css">
            /* Forzar Dark Mode en el formulario MailerLite */
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper.embedForm { background-color: #0f172a !important; border: 1px solid #334155 !important; border-radius: 8px !important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedContent h4 { color: #00e5ff !important; font-family: 'Inter', sans-serif !important; font-weight: 700 !important; font-size: 20px !important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedContent p { color: #94a3b8 !important; font-family: 'Inter', sans-serif !important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedSubmit button { background-color: #00e5ff !important; color: #000 !important; font-family: 'Inter', sans-serif !important; font-weight: 700 !important; border-radius: 6px !important; }
            #mlb2-44360624.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-horizontalRow input { background-color: #1e293b !important; color: #fff !important; border-color: #334155 !important; border-radius: 6px !important; font-family: 'Inter', sans-serif !important; }
        </style>
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
    """

    return f"""
    <!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BLENIN.G.77 - Institutional Trading AI</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body {{ font-family: 'Inter', sans-serif; background-color: #020617; }}
        .glow {{ text-shadow: 0 0 10px rgba(6, 182, 212, 0.5); }}
        .bg-grid {{ background-image: linear-gradient(rgba(15, 23, 42, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(15, 23, 42, 0.1) 1px, transparent 1px); background-size: 40px 40px; }}
    </style>
</head>
<body class="text-slate-300 bg-grid">

    <!-- Navbar -->
    <nav class="bg-slate-950/80 backdrop-blur-md sticky top-0 z-50 border-b border-slate-800">
        <div class="container mx-auto px-6 py-4 flex justify-between items-center">
            <a href="#" class="text-xl font-extrabold text-cyan-400 glow">BLENIN.G.77</a>
            <div class="hidden md:flex space-x-6 text-sm font-medium">
                <a href="#features" class="hover:text-cyan-400 transition">Tecnología</a>
                <a href="#videos" class="hover:text-cyan-400 transition">Galería</a>
                <a href="#pricing" class="hover:text-cyan-400 transition">Precios</a>
            </div>
            <a href="#pricing" class="bg-cyan-500 text-slate-900 px-4 py-2 rounded text-sm font-bold hover:bg-cyan-400 transition">Comprar Ahora</a>
        </div>
    </nav>

    <!-- Hero Section con la Imagen Original de Fondo -->
    <header class="relative overflow-hidden py-32 md:py-40" style="background-image: url('https://raw.githubusercontent.com/mymundodigital0-cmyk/blenin77-server/main/bienvenida_blenin.png'); background-size: cover; background-position: center;">
        <div class="absolute inset-0 bg-gradient-to-b from-slate-950/80 via-slate-950/70 to-slate-950"></div>
        <div class="container mx-auto px-6 text-center relative z-10">
            <div class="inline-block bg-slate-800/50 border border-slate-700 px-4 py-1 rounded-full text-xs font-medium text-cyan-400 mb-6">🚀 SISTEMA INSTITUCIONAL ACTIVO</div>
            <h1 class="text-4xl md:text-6xl font-extrabold text-white mb-4 glow">{c.get('hero_title', '')}</h1>
            <h2 class="text-lg md:text-xl text-slate-300 font-light mb-6 tracking-wider uppercase">{c.get('hero_subtitle', '')}</h2>
            <p class="text-md md:text-lg text-slate-300 max-w-2xl mx-auto mb-10">{c.get('hero_text', '')}</p>
            <div class="flex justify-center gap-4">
                <a href="#pricing" class="bg-cyan-500 text-slate-900 font-bold py-3 px-8 rounded hover:bg-cyan-400 transition transform hover:-translate-y-1 shadow-lg shadow-cyan-500/20">Ver Planes</a>
                <a href="#videos" class="border border-slate-600 bg-slate-900/50 backdrop-blur text-white font-bold py-3 px-8 rounded hover:bg-slate-800 transition">Ver Demo</a>
            </div>
        </div>
    </header>

    <!-- Features -->
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

    <!-- Videos / Gallery -->
    <section id="videos" class="py-20 bg-slate-950">
        <div class="container mx-auto px-6">
            <h2 class="text-3xl font-bold text-center text-white mb-12">Mira al Sistema en Acción</h2>
            {pubs_html}
        </div>
    </section>

    <!-- Pricing -->
    <section id="pricing" class="py-20 container mx-auto px-6">
        <h2 class="text-3xl font-bold text-center text-white mb-4">Planes de Suscripción</h2>
        <p class="text-slate-400 text-center mb-12">Elige el plan que se adapte a tu capital y estilo de trading.</p>
        <div class="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {plans_html}
        </div>
    </section>

    <!-- MAILERLITE FORMULARIO -->
    {mailerlite_html}

    <!-- Social Footer -->
    <section class="py-12 border-t border-slate-800">
        <div class="container mx-auto px-6 text-center">
            <h3 class="text-xl font-bold text-white mb-6">Síguenos en nuestras redes</h3>
            <div class="flex justify-center space-x-4 text-xl">
                {social_html}
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-slate-950 py-10 border-t border-slate-800">
        <div class="container mx-auto px-6 text-center">
            <p class="text-slate-500 text-sm mb-4 max-w-3xl mx-auto">
                <strong>Aviso de Riesgo:</strong> El trading de divisas y CFDs implica un riesgo sustancial y no es adecuado para todos los inversores. El rendimiento pasado no es indicativo de resultados futuros. Operar con apalancamiento puede resultar en la pérdida de su capital.
            </p>
            <p class="text-slate-600 text-xs">&copy; 2024 BLENIN.G.77 THE BEST FUTURE FOR YOU. Creado por Lenin Benitez.</p>
        </div>
    </footer>

    <!-- CHATBASE BOT -->
    <script>
    (function(){{if(!window.chatbase||window.chatbase("getState")!=="initialized"){{window.chatbase=(...arguments)=>{{if(!window.chatbase.q){{window.chatbase.q=[]}}window.chatbase.q.push(arguments)}};window.chatbase=new Proxy(window.chatbase,{{get(target,prop){{if(prop==="q"){{return target.q}}return(...args)=>target(prop,...args)}}}})}}const onLoad=function(){{const script=document.createElement("script");script.src="https://www.chatbase.co/embed.min.js";script.id="gzEjAzK1VCE72hJ_hBfA4";script.domain="www.chatbase.co";document.body.appendChild(script)}};if(document.readyState==="complete"){{onLoad()}}else{{window.addEventListener("load",onLoad)}}}})();
    </script>
</body>
</html>
    """
