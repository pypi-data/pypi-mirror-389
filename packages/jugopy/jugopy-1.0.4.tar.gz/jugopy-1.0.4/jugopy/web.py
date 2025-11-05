import os, re, mimetypes, urllib.parse, http.cookies
from wsgiref.simple_server import make_server

class Colors:
    OK = '\033[92m'; INFO = '\033[94m'; WARN = '\033[93m'; ERROR = '\033[91m'; BOLD = '\033[1m'; END = '\033[0m'

def cprint(msg, color=Colors.INFO):
    print(f"{color}{msg}{Colors.END}")

BASE_DIR = os.path.dirname(__file__)
TEMPLATES_DIR = os.path.join(BASE_DIR, 'jg_templates')
STATIC_ROOT = os.path.join(BASE_DIR, 'jg_static')

STATIC_MAP = {
    'css': 'css', 'js': 'js',
    'png': 'images', 'jpg': 'images', 'jpeg': 'images', 'gif': 'images',
    'svg': 'images', 'webp': 'images', 'ico': 'images',
    'json': 'json', 'mp3': 'audios', 'wav': 'audios',
    'pdf': 'documents', 'txt': 'documents',
}

DEFAULT_TEMPLATES = {
    'error.html': """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Erreur {{code}}</title></head><body><h1>Erreur {{code}}</h1><p>{{message}}</p></body></html>""",
}

def load_template(name, context=None):
    context = context or {}
    path = os.path.join(TEMPLATES_DIR, name)
    cprint(f"[TEMPLATE] Chargement: {name}", Colors.INFO)
    if not os.path.exists(path):
        cprint(f"[TEMPLATE] Fichier manquant → défaut", Colors.WARN)
        content = DEFAULT_TEMPLATES.get(name, "<h1>Erreur</h1>")
    else:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        cprint(f"[TEMPLATE] Chargé depuis disque", Colors.OK)
    for k, v in context.items():
        placeholder = f'{{{{{k}}}}}'
        if placeholder in content:
            cprint(f"[TEMPLATE] {{ {{{k}}} }} → {str(v)[:50]}", Colors.INFO)
        content = content.replace(placeholder, str(v))
    return content

def render_error(code, message="Erreur inconnue"):
    cprint(f"[ERROR] {code} → {message}", Colors.ERROR)
    return load_template('error.html', {'code': code, 'message': message})

def response(start_response, status='200 OK', body='', content_type='text/html', headers=None):
    headers = headers or []
    headers.append(('Content-Type', content_type))
    size = len(body) if isinstance(body, (str, bytes)) else 0
    cprint(f"[RESPONSE] {status} | {content_type} | {size} octets", Colors.OK)
    start_response(status, headers)
    return [body.encode('utf-8') if isinstance(body, str) else body]

_routes = []

def jg_get(path, template, context=None):
    if context is None: context = {}
    _routes.append(('GET', path, template, context))
    cprint(f"[ROUTE] GET {path} → {template} | context: {context}", Colors.OK)

def jg_post(path, template, context=None):
    if context is None: context = {}
    _routes.append(('POST', path, template, context))
    cprint(f"[ROUTE] POST {path} → {template} | context: {context}", Colors.OK)

def get_static_path(requested_path):
    if not requested_path or '/' not in requested_path: return None
    clean_path = requested_path.lstrip('/')
    parts = clean_path.split('/', 1)
    if len(parts) != 2: return None
    prefix, filename = parts
    if '.' not in filename: return None
    ext = filename.rsplit('.', 1)[-1].lower()
    subdir = STATIC_MAP.get(ext)
    if not subdir: return None
    full_path = os.path.join(STATIC_ROOT, subdir, filename)
    cprint(f"[STATIC] {requested_path} → {full_path}", Colors.INFO)
    return full_path

def serve_static_file(requested_path, environ, start_response):
    file_path = get_static_path(requested_path)
    if not file_path or not os.path.exists(file_path):
        cprint(f"[STATIC] Introuvable: {requested_path}", Colors.ERROR)
        return response(start_response, '404 Not Found', render_error(404, "Fichier manquant"))
    mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
    cprint(f"[STATIC] Envoi: {file_path} | {mime_type}", Colors.OK)
    mode = 'rb' if mime_type.startswith(('image/', 'audio/', 'video/')) else 'r'
    with open(file_path, mode) as f:
        content = f.read()
        if mode == 'r': content = content.encode('utf-8')
        start_response('200 OK', [('Content-Type', mime_type)])
        return [content]

def jg_web_app(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ['REQUEST_METHOD']
    ip = environ.get('REMOTE_ADDR', 'unknown')
    cprint(f"\n{'='*70}", Colors.BOLD)
    cprint(f"[REQUEST] {method} {path} | IP: {ip}", Colors.BOLD)

    if path.startswith(('/css/', '/js/', '/img/', '/audio/', '/data/', '/doc/')):
        return serve_static_file(path, environ, start_response)

    for r_method, r_path, r_template, r_context in _routes:
        if method == r_method and path == r_path:
            cprint(f"[ROUTE] Match: {method} {path} → {r_template}", Colors.OK)
            return response(start_response, body=load_template(r_template, r_context))

    cprint(f"[404] Aucune route: {method} {path}", Colors.ERROR)
    return response(start_response, '404 Not Found', render_error(404, "Page non trouvée"))

def jg_start_server(port=8080):
    if not any(r[1] == '/' and r[0] == 'GET' for r in _routes):
        cprint("[WARNING] Aucune route '/' définie ! Ajoute: jg_get('/', 'home.html', {'user': 'Toi'})", Colors.WARN)
    cprint(f"\n[SERVER] Démarrage → http://localhost:{port}", Colors.OK)
    server = make_server('0.0.0.0', port, jg_web_app)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        cprint("\n[SERVER] Arrêté.", Colors.WARN)

def jg_create_app(app_name):
    if not app_name or os.path.exists(app_name):
        cprint("Nom invalide ou projet existant.", Colors.ERROR)
        return
    cprint(f"[CREATE] Projet: {app_name}", Colors.OK)

    for d in ['css', 'js', 'images', 'json', 'audios', 'documents']:
        os.makedirs(os.path.join(app_name, 'jg_static', d), exist_ok=True)
        cprint(f"[CREATE] Dossier: jg_static/{d}", Colors.INFO)

    os.makedirs(os.path.join(app_name, 'jg_templates'), exist_ok=True)

    with open(os.path.join(app_name, 'jg_templates', 'error.html'), 'w', encoding='utf-8') as f:
        f.write(DEFAULT_TEMPLATES['error.html'])
    with open(os.path.join(app_name, 'jg_templates', 'home.html'), 'w', encoding='utf-8') as f:
        f.write("<!DOCTYPE html><html><head><meta charset='utf-8'><title>Accueil</title></head><body><h1>Bienvenue {{user}} !</h1></body></html>")
    with open(os.path.join(app_name, 'jg_templates', 'login.html'), 'w', encoding='utf-8') as f:
        f.write("<!DOCTYPE html><html><head><meta charset='utf-8'><title>Login</title></head><body><form method='POST' action='/login'><input name='email' placeholder='Email'><input name='password' type='password'><button>Login</button></form><p>{{error}}</p></body></html>")

    app_py = os.path.join(app_name, 'app.py')
    with open(app_py, 'w', encoding='utf-8') as f:
        f.write("""# app.py - Ultra-simple avec jg_get()
            from jugopy import jg_get, jg_post, jg_start_server

            # OBLIGATOIRE : page d'accueil
            jg_get('/', 'home.html', {'user': 'Logbo'})

            # Ajoute tes pages ici :
            jg_get('/about', 'home.html', {'user': 'À propos'})
            jg_get('/contact', 'home.html', {'user': 'Contact'})

            # Exemple POST
            jg_post('/login', 'login.html', {'error': 'Identifiants incorrects'})

            # Démarrage
            jg_start_server(8080)
        """)
    cprint(f"[CREATE] Fichier: app.py", Colors.INFO)
    cprint(f"\nProjet '{app_name}' prêt !", Colors.OK)
    cprint(f"→ cd {app_name} && python app.py", Colors.INFO)