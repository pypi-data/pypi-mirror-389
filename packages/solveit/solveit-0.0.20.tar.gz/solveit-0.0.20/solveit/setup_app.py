import os,time
from fasthtml.common import *
from monsterui.all import Theme
from fastcore.utils import *
from json import loads

from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocketDisconnect
from starlette import status

from .kernel import g_dlgs
from .ipynb import write_perms
from .db import cfg_solveit,base_dir,uid,gid
from .ipynb import shutdown_all
from .app_xtras import has_custom_theme, custom_theme_fp, exception_handlers

__all__ = ['base_hdrs', 'hdrs', 'app', 'rt']

base_hdrs = (
    Link(rel="icon", href="assets/favicon.ico"),
    Meta(name="htmx-config", content='{"selfRequestsOnly":false}'),
    Link(rel="stylesheet", href="assets/styles.css"),
    *Theme.blue.headers(katex=False, daisy=False, icons=False),
    Link(rel="stylesheet", href="https://cdn.jsdelivr.net/gh/fastai/fastcore@master/examples/ansi.css"),
    Script(src='assets/monedit.js')
)

hdrs = base_hdrs + (
    Link(rel="preconnect", href='https://cdn.jsdelivr.net/'),
    Link(rel="preconnect", href='https://esm.sh/'),
    Script(src='vendor/ws-2.0.3.js'),
    Script(src='https://cdn.jsdelivr.net/npm/jquery@4.0.0-rc.1/dist/jquery.slim.min.js'),
    # Script(src='vendor/jquery-4.0.0-beta.2.slim.min.js'),
    Script(src='assets/attachment_upload.js'),
    Script(src='assets/jquery-micro-utils.js'),
    #Script(src="https://unpkg.com/idiomorph@0.7.3"),
    #Script(src="https://unpkg.com/idiomorph@0.7.3/dist/idiomorph-ext.min.js"),
    #Script(Path("assets/selection.js").read_text()),
    Script(src='assets/selection.js'),
    *([Link(rel="stylesheet", href=custom_theme_fp, type="text/css")] if has_custom_theme() else [])
)

async def life(app):
    yield
    await shutdown_all()

def ws_decode(msg):
    "If needed -- decode received json"
    data = loads(msg["bytes"].decode("utf-8") if msg.get("text") is None else msg["text"])

async def wsend(ws):
    await ws.accept()
    nm = ws.query_params['dlg_name']
    dlg = g_dlgs.get(nm)
    if not dlg: return
    dlg.conns.add(ws)
    try:
        while True:
            msg = await ws.receive()
            if msg["type"] == "websocket.receive":
                # This isn't really used atm - might be useful for media streams etc?
                for k,v in ws_decode(msg).items():
                    if k=='oob': await dlg.send(nm, v, True)
            elif msg["type"] == "websocket.disconnect":
                close_code = int(msg.get("code") or status.WS_1000_NORMAL_CLOSURE)
                break
    finally: write_perms(dlg)

def bware_f(req, sess):
    if sess.get('is_admin'): return
    elif os.environ.get('IS_INSECURE') == '1': return
    elif req.client.host in ('127.0.0.1', 'localhost', '::1'): return
    auth = sess.get('auth', '')
    ukey = os.environ.get('AAI_USER_KEY',':').split(":")[0]
    if auth!=ukey:
        res = 'no auth' if not auth else f'auth {auth} does not match {ukey}'
        print(res)
        return res

def run_app():
    sess_domain = os.getenv('SOLVE_DOM', None)
    if sess_domain: sess_domain = '.'+sess_domain
    if uid>-1 or gid>-1: os.umask(0o002)
    app = FastHTML(
        routes=[
            Mount('/assets', app=StaticNoCache(directory=base_dir/'assets'),         name="assets"),
            Mount('/vendor', app=StaticFiles  (directory=base_dir/'vendor'),         name="vendor"),
            Mount('/static', app=StaticNoCache(directory=cfg_solveit['static_dir']), name="static"),
            WebSocketRoute('/ws', wsend)
        ],
        hdrs=hdrs, nb_hdrs=False, lifespan=life, sess_domain=sess_domain,
        before = Beforeware(bware_f, skip=['/chk_', '/save_dialog_']) if sess_domain else None,
        exception_handlers=exception_handlers, #exts=['debug'],
        cls='bg-background text-foreground'
    )
    if not cfg_solveit['prod'] and cfg_solveit['debug_delay'] > 0:
        def add_delay(*args, **kws): time.sleep(cfg_solveit['debug_delay'])
        app.before.append(add_delay)
    return app,app.route

app,rt = run_app()
setup_toasts(app)

@rt
def chk_(): return 'ok'

@rt('/favicon.ico')
async def favicon(): return FileResponse('assets/favicon.ico')

