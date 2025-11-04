from wsgiref.simple_server import make_server
import os

def jg_answer_back(start_response):
    def answer_back(status='200 OK', body=''):
        start_response(status, [('Content-Type', 'text/html')])
        return [body.encode('utf-8')]
    return answer_back

def jg_handle_error(code, message='Erreur inconnue'):
    error_file = os.path.join('jg_templates', 'error.html')
    if os.path.exists(error_file):
        with open(error_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return content.replace('{{code}}', str(code)).replace('{{message}}', str(message))
    return f"<h1>Erreur {code}</h1><p>{message}</p>"

def jg_load_html(filename):
    path = os.path.join('jg_templates', filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return jg_handle_error('404', f'{filename} introuvable')

def jg_render_html(template_path, output_path, context=None):
    if context is None:
        context = {}
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    for k, v in context.items():
        content = content.replace(f'{{{{{k}}}}}', str(v))
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

def jg_get(environ, start_response):
    answer_back = jg_answer_back(start_response)
    return answer_back(body=jg_load_html('home.html'))

def jg_post(environ, start_response):
    answer_back = jg_answer_back(start_response)
    return answer_back(body=jg_load_html('post.html'))

def jg_web_app(environ, start_response):
    method = environ.get('REQUEST_METHOD', 'GET')
    answer_back = jg_answer_back(start_response)
    try:
        if method == 'GET':
            return jg_get(environ, start_response)
        elif method == 'POST':
            return jg_post(environ, start_response)
        else:
            return answer_back('405 Method Not Allowed', jg_handle_error('405', 'Méthode non autorisée'))
    except Exception as e:
        return answer_back('500 Internal Server Error', jg_handle_error('500', str(e)))

def jg_start_server(port=8080):
    http = make_server('0.0.0.0', port, jg_web_app)
    print(f"🚀 Serveur JugoPy actif sur http://0.0.0.0:{port}")
    http.serve_forever()

def jg_create_app(app_name):
    if not app_name:
        print("Nom d'application requis.")
        return

    folders = [
        f"{app_name}/src",
        f"{app_name}/jg_templates",
        f"{app_name}/jg_static/css",
        f"{app_name}/jg_static/js",
        f"{app_name}/jg_static/images"
    ]
    for d in folders:
        os.makedirs(d, exist_ok=True)

    error_html = """<!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Erreur {{code}}</title>
        </head>
        <body>
            <h1>Erreur {{code}}</h1>
            <p>{{message}}</p>
        </body>
        </html>
    """

    home_html = """<!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Accueil</title>
        </head>
        <body>
            <h1>Bienvenue sur JugoPy</h1>
        </body>
        </html>
    """

    post_html = """<!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>POST</title>
        </head>
        <body>
            <h1>Page POST - Données reçues !</h1>
        </body>
        </html>
    """

    templates = {
        'error.html': error_html,
        'home.html': home_html,
        'post.html': post_html
    }

    for name, content in templates.items():
        jg_render_html(template_path=os.path.join(app_name, 'jg_templates', name),
                       output_path=os.path.join(app_name, 'jg_templates', name),
                       context={})

    main_file = os.path.join(app_name, "app.py")
    if not os.path.exists(main_file):
        jg_render_html(
            template_path=None,
            output_path=main_file,
            context={}
        )
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write("from jugopy import jg_start_server\n\njg_start_server(8080)\n")

    print(f"✅ Projet '{app_name}' créé avec succès.")
    print(f"Structure :")
    for f in folders + [main_file]:
        print(f" - {f}")
