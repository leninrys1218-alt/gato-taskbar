"""
Gato Taskbar v4.0
- 3 colores: Negro/ojos rojos, Blanco/ojos azules, Naranja/ojos verdes
- Gato más grande y visible
- Modo descanso, animaciones múltiples, modo aleatorio
pip install pillow pystray
pyinstaller --noconsole --onefile --icon=cat_icon.ico --name=GatoTaskbar gato_taskbar.py
"""

import threading, time, math, random, os, tempfile
import pystray
from PIL import Image, ImageDraw

# ─────────────────────────────────────────────────────────────
#  PALETAS DE COLOR
# ─────────────────────────────────────────────────────────────

THEMES = {
    "Negro":    {"body": (18,18,18,255),      "eye": (220,40,40,255),   "nose": (200,100,130,255)},
    "Blanco":   {"body": (230,230,235,255),   "eye": (60,140,230,255),  "nose": (220,150,170,255)},
    "Naranja":  {"body": (210,110,20,255),    "eye": (60,200,90,255),   "nose": (200,100,120,255)},
}
THEME_NAMES = list(THEMES.keys())

# Estado del color actual
_color = {"theme": "Negro"}
_color_lock = threading.Lock()

def get_colors():
    with _color_lock:
        return THEMES[_color["theme"]]

# ─────────────────────────────────────────────────────────────
#  RENDER — tamaño interno grande, luego escala a 32
# ─────────────────────────────────────────────────────────────

SIZE = 256   # render interno grande para calidad

def sc(v):
    """Escala coordenada base-64 al SIZE interno."""
    return int(v * SIZE / 64)

def new_img():
    return Image.new("RGBA", (SIZE, SIZE), (0,0,0,0))

def to_tray(img):
    """32x32 para el system tray."""
    return img.resize((32,32), Image.LANCZOS)

# ─────────────────────────────────────────────────────────────
#  PRIMITIVAS
# ─────────────────────────────────────────────────────────────

def ellipse(d, cx, cy, rx, ry, fill):
    d.ellipse([sc(cx-rx), sc(cy-ry), sc(cx+rx), sc(cy+ry)], fill=fill)

def poly(d, pts, fill):
    d.polygon([(sc(x), sc(y)) for x,y in pts], fill=fill)

def thick_line(d, pts, fill, w=4):
    d.line([(sc(x), sc(y)) for x,y in pts], fill=fill, width=max(2, sc(w)))

# ─────────────────────────────────────────────────────────────
#  PARTES DEL GATO
# ─────────────────────────────────────────────────────────────

def draw_head(d, cx, cy, r=15, blink=False):
    C = get_colors()
    B, E, N = C["body"], C["eye"], C["nose"]

    # Cabeza
    ellipse(d, cx, cy, r, r*0.95, B)

    # Orejas exteriores
    poly(d, [(cx-r+3, cy-r+5), (cx-r-6, cy-r-14), (cx-3, cy-r-1)], B)
    poly(d, [(cx+r-3, cy-r+5), (cx+r+6, cy-r-14), (cx+3, cy-r-1)], B)

    # Interior orejas
    ear_inner = tuple(max(0, min(255, int(v*0.6))) for v in B[:3]) + (200,)
    poly(d, [(cx-r+5, cy-r+3), (cx-r-2, cy-r-9), (cx-6, cy-r)],  ear_inner)
    poly(d, [(cx+r-5, cy-r+3), (cx+r+2, cy-r-9), (cx+6, cy-r)],  ear_inner)

    # Ojos
    if blink:
        thick_line(d, [(cx-9, cy-2),(cx-4, cy-5),(cx-1, cy-2)], (30,30,30,255), 2)
        thick_line(d, [(cx+1, cy-2),(cx+4, cy-5),(cx+9, cy-2)], (30,30,30,255), 2)
    else:
        ellipse(d, cx-6, cy-2, 5, 4.5, E)
        ellipse(d, cx+6, cy-2, 5, 4.5, E)
        ellipse(d, cx-6, cy-2, 2.5, 3,   (0,0,0,255))
        ellipse(d, cx+6, cy-2, 2.5, 3,   (0,0,0,255))
        ellipse(d, cx-5, cy-3, 1.5, 1.5, (255,255,255,220))
        ellipse(d, cx+7, cy-3, 1.5, 1.5, (255,255,255,220))

    # Nariz
    ellipse(d, cx, cy+5, 2.5, 2, N)

    # Boca
    thick_line(d, [(cx-3,cy+7),(cx,cy+9),(cx+3,cy+7)], N, 1.5)

    # Bigotes
    whisker = (200,200,200,130)
    thick_line(d, [(cx-3,cy+5),(cx-16,cy+3)],  whisker, 1.2)
    thick_line(d, [(cx-3,cy+6),(cx-16,cy+8)],  whisker, 1.2)
    thick_line(d, [(cx+3,cy+5),(cx+16,cy+3)],  whisker, 1.2)
    thick_line(d, [(cx+3,cy+6),(cx+16,cy+8)],  whisker, 1.2)

def draw_body(d, cx, cy, w=20, h=14):
    B = get_colors()["body"]
    ellipse(d, cx, cy, w, h, B)

def draw_tail(d, pts, thickness=4.5):
    B = get_colors()["body"]
    for i in range(len(pts)-1):
        x1,y1 = sc(pts[i][0]),   sc(pts[i][1])
        x2,y2 = sc(pts[i+1][0]), sc(pts[i+1][1])
        d.line([(x1,y1),(x2,y2)], fill=B, width=max(2, sc(thickness)))

def draw_leg(d, x1,y1, x2,y2, w=4.5):
    B = get_colors()["body"]
    thick_line(d, [(x1,y1),(x2,y2)], B, w)
    ellipse(d, x2, y2, 3.5, 2.5, B)

# ─────────────────────────────────────────────────────────────
#  ANIMACIONES
# ─────────────────────────────────────────────────────────────

def anim_walk(t):
    img=new_img(); d=ImageDraw.Draw(img)
    bob = math.sin(t*math.pi*2)*2.5
    sw  = math.sin(t*math.pi*2)*9
    wv  = math.sin(t*math.pi*2)*5

    draw_body(d, 33, 38+bob)
    draw_head(d, 50, 22+bob)
    draw_tail(d, [(15,38+bob),(10,33+bob+wv),(7,26+bob+wv*1.4),(9,20+bob+wv*0.7)])

    draw_leg(d, 26,45+bob, 20,58+sw*0.5)
    draw_leg(d, 32,45+bob, 30,58-sw*0.4)
    draw_leg(d, 39,45+bob, 41,58+sw*0.3)
    draw_leg(d, 45,45+bob, 50,58-sw*0.5)
    return to_tray(img)

def anim_sit(t):
    img=new_img(); d=ImageDraw.Draw(img)
    blink = (t % 1.0) < 0.87
    ellipse(d, 32,43, 17,15, get_colors()["body"])
    draw_head(d, 32,22, blink=blink)
    draw_tail(d, [(16,46),(12,51),(16,57),(24,59),(33,57),(38,51)])
    draw_leg(d, 22,51, 17,59, 4)
    draw_leg(d, 42,51, 47,59, 4)
    return to_tray(img)

def anim_jump(t):
    img=new_img(); d=ImageDraw.Draw(img)
    arc = -abs(math.sin(t*math.pi))*20
    cy  = 40+arc
    sp  = math.sin(t*math.pi)*7

    draw_body(d, 32, cy)
    draw_head(d, 44, cy-16)
    draw_tail(d, [(15,cy),(10,cy-5),(7,cy-12+sp)])
    draw_leg(d, 25,cy+7, 18,cy+17+sp)
    draw_leg(d, 31,cy+7, 29,cy+17+sp)
    draw_leg(d, 37,cy+7, 41,cy+17+sp)
    draw_leg(d, 43,cy+7, 50,cy+17+sp)
    return to_tray(img)

def anim_stretch(t):
    img=new_img(); d=ImageDraw.Draw(img)
    st = math.sin(t*math.pi)*9

    draw_body(d, 28+st*0.3, 44, 19+st*0.4, 9)
    draw_head(d, 46+st, 38)
    draw_tail(d, [(10,40),(7,35),(5,29),(8,24)])
    ellipse(d, 13, 38, 10, 10, get_colors()["body"])
    draw_leg(d,  9,45,  7,57)
    draw_leg(d, 17,45, 17,57)
    draw_leg(d, 40+st,46, 39+st,57)
    draw_leg(d, 50+st,46, 52+st,57)
    return to_tray(img)

def anim_play(t):
    img=new_img(); d=ImageDraw.Draw(img)
    paw = math.sin(t*math.pi*2)*11

    draw_body(d, 29, 41)
    draw_head(d, 41, 26)
    draw_tail(d, [(13,39),(9,35),(7,29),(9,23)])
    draw_leg(d, 37,43, 53,34+paw, 5)
    draw_leg(d, 29,48, 27,59)
    draw_leg(d, 35,48, 37,59)
    draw_leg(d, 21,46, 17,57)

    by = 32+paw
    ellipse(d, 57, by, 5.5, 5.5, (190,70,70,230))
    ellipse(d, 57, by, 3,   3,   (230,110,110,200))
    return to_tray(img)

def anim_standup(t):
    img=new_img(); d=ImageDraw.Draw(img)
    sw  = math.sin(t*math.pi*2)*2.5
    arm = math.sin(t*math.pi*2)*5

    # cuerpo vertical
    B = get_colors()["body"]
    pts = [(sc(32+sw + 12*math.cos(math.radians(a))), sc(40 + 20*math.sin(math.radians(a)))) for a in range(0,360,6)]
    ImageDraw.Draw(img).polygon(pts, fill=B)

    draw_head(d, 32+sw, 18)
    draw_leg(d, 22+sw,30, 13+sw,22+arm, 3.5)
    draw_leg(d, 42+sw,30, 51+sw,22-arm, 3.5)
    draw_leg(d, 24+sw,53, 19+sw,63)
    draw_leg(d, 40+sw,53, 45+sw,63)
    draw_tail(d, [(32+sw,57),(38+sw,59),(43+sw,55),(43+sw,49)])
    return to_tray(img)

def anim_sneak(t):
    img=new_img(); d=ImageDraw.Draw(img)
    cr = math.sin(t*math.pi*2)*2

    draw_body(d, 31, 49+cr, 21, 9)
    draw_head(d, 48, 43+cr, 12)
    draw_tail(d, [(11,47+cr),(7,43+cr),(5,37+cr),(8,32+cr),(12,30+cr)])
    draw_leg(d, 21,53+cr, 14,60+cr)
    draw_leg(d, 29,53+cr, 27,60+cr)
    draw_leg(d, 37,53+cr, 39,60+cr)
    draw_leg(d, 45,53+cr, 50,60+cr)
    return to_tray(img)

def anim_wash(t):
    img=new_img(); d=ImageDraw.Draw(img)
    lk = abs(math.sin(t*math.pi*2))*12

    ellipse(d, 32,42, 15,14, get_colors()["body"])
    draw_head(d, 32,22)
    draw_tail(d, [(17,46),(13,51),(17,57),(25,59),(33,56)])
    draw_leg(d, 25,38, 27,26-lk, 4.5)
    draw_leg(d, 39,41, 41,57, 4)
    draw_leg(d, 21,50, 17,59, 4)
    return to_tray(img)

# ─────────────────────────────────────────────────────────────
#  CATÁLOGO
# ─────────────────────────────────────────────────────────────

ANIMATIONS = {
    "Caminar":   (anim_walk,    8,  0.10),
    "Sentarse":  (anim_sit,     24, 0.14),
    "Saltar":    (anim_jump,    12, 0.08),
    "Estirarse": (anim_stretch, 10, 0.10),
    "Jugar":     (anim_play,    8,  0.09),
    "Pararse":   (anim_standup, 10, 0.10),
    "Acechar":   (anim_sneak,   10, 0.12),
    "Lavarse":   (anim_wash,    12, 0.12),
}
ANIM_NAMES = list(ANIMATIONS.keys())
REST_TICKS = 30*60*10
PLAY_TICKS = 10*10

# ─────────────────────────────────────────────────────────────
#  ESTADO GLOBAL
# ─────────────────────────────────────────────────────────────

_state = {"anim": None, "frame": 0, "auto": True, "running": True}
_lock  = threading.Lock()
_icon_ref   = [None]
_cache_ref  = [{}]
_rest_ref   = [None]

def _rebuild_cache():
    """Regenera todos los frames con el color actual."""
    cache = {}
    for name,(fn,nf,_) in ANIMATIONS.items():
        cache[name] = [fn(i/nf) for i in range(nf)]
    _cache_ref[0] = cache
    _rest_ref[0]  = anim_sit(0.5)

def set_anim(name):
    with _lock: _state["anim"]=name; _state["frame"]=0; _state["auto"]=False

def do_rest():
    with _lock: _state["anim"]=None; _state["frame"]=0

def toggle_auto():
    with _lock:
        _state["auto"] = not _state["auto"]
        if _state["auto"]: _state["anim"]=None

def set_color(theme):
    with _color_lock: _color["theme"] = theme
    _rebuild_cache()  # regenera frames con nuevo color

def do_quit(icon, item):
    with _lock: _state["running"]=False
    icon.stop()

# Callbacks animaciones
def cb_caminar(i,it):  set_anim("Caminar")
def cb_sentarse(i,it): set_anim("Sentarse")
def cb_saltar(i,it):   set_anim("Saltar")
def cb_estirar(i,it):  set_anim("Estirarse")
def cb_jugar(i,it):    set_anim("Jugar")
def cb_pararse(i,it):  set_anim("Pararse")
def cb_acechar(i,it):  set_anim("Acechar")
def cb_lavarse(i,it):  set_anim("Lavarse")
def cb_rest(i,it):     do_rest()
def cb_auto(i,it):     toggle_auto()

# Callbacks colores
def cb_negro(i,it):   set_color("Negro")
def cb_blanco(i,it):  set_color("Blanco")
def cb_naranja(i,it): set_color("Naranja")

# ─────────────────────────────────────────────────────────────
#  LOOP DE ANIMACIÓN
# ─────────────────────────────────────────────────────────────

def animate_loop():
    ticks=0; resting=True
    while True:
        with _lock:
            if not _state["running"]: break
            auto=_state["auto"]; name=_state["anim"]

        if auto:
            ticks+=1
            if resting and ticks>=REST_TICKS:
                chosen=random.choice(ANIM_NAMES)
                with _lock: _state["anim"]=chosen; _state["frame"]=0
                resting=False; ticks=0
            elif not resting and ticks>=PLAY_TICKS:
                with _lock: _state["anim"]=None; _state["frame"]=0
                resting=True; ticks=0

        with _lock: name=_state["anim"]
        icon=_icon_ref[0]
        if icon is None: time.sleep(0.1); continue

        if name is None:
            rest=_rest_ref[0]
            if rest:
                try: icon.icon=rest
                except: pass
            time.sleep(0.1)
            continue

        cache=_cache_ref[0]
        if name not in cache: time.sleep(0.1); continue

        frames=cache[name]; _,nf,spd=ANIMATIONS[name]
        with _lock:
            fi=_state["frame"]; _state["frame"]=(fi+1)%nf
        try: icon.icon=frames[fi]
        except: pass
        time.sleep(spd)

# ─────────────────────────────────────────────────────────────
#  GENERAR ICO PARA EL EXE
# ─────────────────────────────────────────────────────────────

def make_app_icon():
    img=Image.new("RGBA",(256,256),(0,0,0,0))
    d=ImageDraw.Draw(img)
    C=(15,15,15,255); G=(220,40,40,255); N=(200,100,130,255)

    def e(cx,cy,rx,ry,f): d.ellipse([cx-rx,cy-ry,cx+rx,cy+ry],fill=f)
    def p(pts,f): d.polygon(pts,fill=f)
    def ln(pts,f,w): d.line(pts,fill=f,width=w)

    e(128,175,85,70,C); e(128,78,58,55,C)
    p([(78,40),(52,2),(105,36)],C); p([(178,40),(204,2),(151,36)],C)
    p([(82,38),(62,10),(102,36)],(60,30,40,180))
    p([(174,38),(194,10),(154,36)],(60,30,40,180))
    e(108,74,17,15,G); e(148,74,17,15,G)
    e(108,74,9,12,(0,0,0,255)); e(148,74,9,12,(0,0,0,255))
    e(113,69,5,5,(255,255,255,200)); e(153,69,5,5,(255,255,255,200))
    e(128,100,9,7,N)
    ln([(118,108),(128,116),(138,108)],N,3)
    ln([(78,96),(122,101)],(200,200,200,100),2)
    ln([(78,108),(122,107)],(200,200,200,100),2)
    ln([(134,101),(178,96)],(200,200,200,100),2)
    ln([(134,107),(178,108)],(200,200,200,100),2)
    ln([(65,205),(46,182),(40,150),(50,118),(62,108)],C,16)
    e(92,232,25,16,C); e(164,232,25,16,C)

    path=os.path.join(tempfile.gettempdir(),"cat_icon.ico")
    img.save(path,format="ICO",sizes=[(256,256),(64,64),(32,32),(16,16)])
    return path

# ─────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────

def main():
    print("Cargando...")
    _rebuild_cache()

    menu = pystray.Menu(
        pystray.MenuItem("── Animaciones ──", None, enabled=False),
        pystray.MenuItem("Caminar",   cb_caminar),
        pystray.MenuItem("Sentarse",  cb_sentarse),
        pystray.MenuItem("Saltar",    cb_saltar),
        pystray.MenuItem("Estirarse", cb_estirar),
        pystray.MenuItem("Jugar",     cb_jugar),
        pystray.MenuItem("Pararse",   cb_pararse),
        pystray.MenuItem("Acechar",   cb_acechar),
        pystray.MenuItem("Lavarse",   cb_lavarse),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("── Cambiar color ──", None, enabled=False),
        pystray.MenuItem("Negro  (ojos rojos)",   cb_negro),
        pystray.MenuItem("Blanco (ojos azules)",  cb_blanco),
        pystray.MenuItem("Naranja (ojos verdes)", cb_naranja),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Descansar ahora",        cb_rest),
        pystray.MenuItem("Modo aleatorio ON/OFF",  cb_auto),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Salir", do_quit),
    )

    icon = pystray.Icon("Gato Taskbar", _rest_ref[0], "Gato Taskbar", menu)
    _icon_ref[0] = icon

    threading.Thread(target=animate_loop, daemon=True).start()
    with _lock: _state["anim"]=random.choice(ANIM_NAMES)

    icon.run()

if __name__=="__main__":
    main()
