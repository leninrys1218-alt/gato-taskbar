"""
Gato Taskbar v3.0
- Gato negro detallado
- Icono .ico generado y embebido
- Siempre visible en taskbar (no oculto en ^)
pip install pillow pystray
pyinstaller --noconsole --onefile --icon=cat_icon.ico gato_taskbar.py
"""

import threading, time, math, random, os, sys, tempfile
import pystray
from PIL import Image, ImageDraw

# ── Tamaño de render interno (se escala a 32 para tray) ───────────────────
SIZE = 128
BLACK_CAT = (15, 15, 15, 255)
EYE_COLOR = (80, 200, 120, 255)   # ojos verdes brillantes
NOSE_COLOR = (200, 120, 150, 255)

def s(v):
    return int(v * SIZE / 64)

def new_img(bg=(0,0,0,0)):
    return Image.new("RGBA", (SIZE, SIZE), bg)

# ── Primitivas ─────────────────────────────────────────────────────────────

def ellipse(d, cx, cy, rx, ry, fill):
    d.ellipse([s(cx-rx), s(cy-ry), s(cx+rx), s(cy+ry)], fill=fill)

def poly(d, pts, fill):
    d.polygon([(s(x), s(y)) for x,y in pts], fill=fill)

def line(d, pts, fill, w=3):
    d.line([(s(x), s(y)) for x,y in pts], fill=fill, width=max(2, s(w)))

# ── Partes del gato ─────────────────────────────────────────────────────────

def draw_cat_head(d, cx, cy, r=14, blink=False):
    # Cabeza redonda
    ellipse(d, cx, cy, r, r*0.92, BLACK_CAT)
    # Orejas puntiagudas
    poly(d, [(cx-r+2, cy-r+4), (cx-r-5, cy-r-12), (cx-4, cy-r-2)], BLACK_CAT)
    poly(d, [(cx+r-2, cy-r+4), (cx+r+5, cy-r-12), (cx+4, cy-r-2)], BLACK_CAT)
    # Interior orejas (rosa oscuro)
    poly(d, [(cx-r+4, cy-r+2), (cx-r-2, cy-r-8), (cx-6, cy-r)], (80, 40, 50, 180))
    poly(d, [(cx+r-4, cy-r+2), (cx+r+2, cy-r-8), (cx+6, cy-r)], (80, 40, 50, 180))
    # Ojos
    if blink:
        # ojos cerrados = línea curva
        line(d, [(cx-8, cy-2), (cx-4, cy-4), (cx-1, cy-2)], (30,30,30,255), 2)
        line(d, [(cx+1, cy-2), (cx+4, cy-4), (cx+8, cy-2)], (30,30,30,255), 2)
    else:
        ellipse(d, cx-5, cy-2, 4, 3.5, EYE_COLOR)
        ellipse(d, cx+5, cy-2, 4, 3.5, EYE_COLOR)
        ellipse(d, cx-5, cy-2, 2, 2.5, (0,0,0,255))
        ellipse(d, cx+5, cy-2, 2, 2.5, (0,0,0,255))
        # brillo ojo
        ellipse(d, cx-4, cy-3, 1, 1, (255,255,255,200))
        ellipse(d, cx+6, cy-3, 1, 1, (255,255,255,200))
    # Nariz
    ellipse(d, cx, cy+4, 2, 1.5, NOSE_COLOR)
    # Bigotes
    line(d, [(cx-2, cy+4), (cx-14, cy+2)], (200,200,200,120), 1)
    line(d, [(cx-2, cy+5), (cx-14, cy+6)], (200,200,200,120), 1)
    line(d, [(cx+2, cy+4), (cx+14, cy+2)], (200,200,200,120), 1)
    line(d, [(cx+2, cy+5), (cx+14, cy+6)], (200,200,200,120), 1)

def draw_cat_body(d, cx, cy, w=18, h=13):
    ellipse(d, cx, cy, w, h, BLACK_CAT)

def draw_cat_tail(d, pts, thickness=4):
    for i in range(len(pts)-1):
        x1,y1 = s(pts[i][0]), s(pts[i][1])
        x2,y2 = s(pts[i+1][0]), s(pts[i+1][1])
        d.line([(x1,y1),(x2,y2)], fill=BLACK_CAT, width=max(2,s(thickness)))

def draw_cat_leg(d, x1, y1, x2, y2, thickness=4):
    line(d, [(x1,y1),(x2,y2)], BLACK_CAT, thickness)
    ellipse(d, x2, y2, 3, 2, BLACK_CAT)

def to32(img):
    return img.resize((32,32), Image.LANCZOS)

def to_tray_size(img):
    """Resize a tamaño óptimo para el tray (32x32)."""
    return img.resize((32,32), Image.LANCZOS)

# ── ANIMACIONES ─────────────────────────────────────────────────────────────

def anim_walk(t):
    img = new_img(); d = ImageDraw.Draw(img)
    bob = math.sin(t*math.pi*2) * 2
    sw  = math.sin(t*math.pi*2) * 8

    draw_cat_body(d, 34, 38+bob)
    draw_cat_head(d, 50, 24+bob)
    wv = math.sin(t*math.pi*2)*4
    draw_cat_tail(d, [(16,38+bob),(10,34+bob+wv),(7,27+bob+wv*1.3),(9,22+bob+wv*0.6)])

    draw_cat_leg(d, 27,46+bob, 22,58+sw*0.5)
    draw_cat_leg(d, 33,46+bob, 30,58-sw*0.4)
    draw_cat_leg(d, 40,46+bob, 42,58+sw*0.3)
    draw_cat_leg(d, 46,46+bob, 50,58-sw*0.5)
    return to_tray_size(img)

def anim_sit(t):
    img = new_img(); d = ImageDraw.Draw(img)
    blink = (t % 1.0) < 0.87

    # cuerpo redondo sentado
    ellipse(d, 32, 42, 16, 14, BLACK_CAT)
    draw_cat_head(d, 32, 22, blink=blink)
    draw_cat_tail(d, [(18,45),(14,50),(18,56),(26,58),(34,56),(38,50)])
    # patas dobladas
    draw_cat_leg(d, 22,50, 18,58, 4)
    draw_cat_leg(d, 42,50, 46,58, 4)
    return to_tray_size(img)

def anim_jump(t):
    img = new_img(); d = ImageDraw.Draw(img)
    arc = -abs(math.sin(t*math.pi))*18
    cy  = 42+arc
    sp  = math.sin(t*math.pi)*6

    draw_cat_body(d, 32, cy)
    draw_cat_head(d, 44, cy-14)
    draw_cat_tail(d, [(16,cy),(11,cy-4),(8,cy-10+sp)])
    draw_cat_leg(d, 26,cy+6, 20,cy+14+sp)
    draw_cat_leg(d, 32,cy+6, 30,cy+14+sp)
    draw_cat_leg(d, 38,cy+6, 42,cy+14+sp)
    draw_cat_leg(d, 44,cy+6, 50,cy+14+sp)
    return to_tray_size(img)

def anim_stretch(t):
    img = new_img(); d = ImageDraw.Draw(img)
    st = math.sin(t*math.pi)*8

    ellipse(d, 30+st*0.3, 44, 18+st*0.4, 9, BLACK_CAT)
    draw_cat_head(d, 46+st, 38)
    draw_cat_tail(d, [(12,40),(8,36),(6,30),(9,25)])
    ellipse(d, 14,38, 9,9, BLACK_CAT)  # trasero
    draw_cat_leg(d, 10,44, 8,56)
    draw_cat_leg(d, 18,44, 18,56)
    draw_cat_leg(d, 40+st,46, 40+st,56)
    draw_cat_leg(d, 50+st,46, 52+st,56)
    return to_tray_size(img)

def anim_play(t):
    img = new_img(); d = ImageDraw.Draw(img)
    paw = math.sin(t*math.pi*2)*10

    draw_cat_body(d, 30, 42)
    draw_cat_head(d, 42, 28)
    draw_cat_tail(d, [(14,40),(10,36),(8,30),(10,24)])
    # pata extendida jugando
    draw_cat_leg(d, 38,44, 52,36+paw, 5)
    draw_cat_leg(d, 30,48, 28,58)
    draw_cat_leg(d, 36,48, 38,58)
    draw_cat_leg(d, 22,46, 18,56)
    # pelotita
    by = 34+paw
    ellipse(d, 56, by, 5, 5, (180,80,80,230))
    ellipse(d, 56, by, 3, 3, (220,120,120,200))
    return to_tray_size(img)

def anim_standup(t):
    img = new_img(); d = ImageDraw.Draw(img)
    sw  = math.sin(t*math.pi*2)*2
    arm = math.sin(t*math.pi*2)*4

    # cuerpo vertical
    ellipse(d, 32+sw, 40, 11, 18, BLACK_CAT)
    draw_cat_head(d, 32+sw, 18)
    # bracitos arriba
    draw_cat_leg(d, 22+sw,30, 14+sw,22+arm, 3)
    draw_cat_leg(d, 42+sw,30, 50+sw,22-arm, 3)
    # patas traseras
    draw_cat_leg(d, 24+sw,52, 20+sw,62)
    draw_cat_leg(d, 40+sw,52, 44+sw,62)
    draw_cat_tail(d, [(32+sw,56),(38+sw,58),(42+sw,54),(42+sw,48)])
    return to_tray_size(img)

def anim_sneak(t):
    img = new_img(); d = ImageDraw.Draw(img)
    cr = math.sin(t*math.pi*2)*1.5

    ellipse(d, 32, 50+cr, 20, 8, BLACK_CAT)
    draw_cat_head(d, 48, 44+cr, 11)
    draw_cat_tail(d, [(12,48+cr),(8,44+cr),(6,38+cr),(9,33+cr),(12,32+cr)])
    draw_cat_leg(d, 22,54+cr, 16,60+cr)
    draw_cat_leg(d, 30,54+cr, 28,60+cr)
    draw_cat_leg(d, 38,54+cr, 40,60+cr)
    draw_cat_leg(d, 46,54+cr, 50,60+cr)
    return to_tray_size(img)

def anim_wash(t):
    img = new_img(); d = ImageDraw.Draw(img)
    lk = abs(math.sin(t*math.pi*2))*10

    ellipse(d, 32, 42, 14, 13, BLACK_CAT)
    draw_cat_head(d, 32, 22)
    draw_cat_tail(d, [(18,46),(14,50),(18,56),(26,58),(34,55)])
    # pata sube a lamer
    draw_cat_leg(d, 26,38, 28,28-lk, 4)
    draw_cat_leg(d, 38,40, 40,56, 4)
    draw_cat_leg(d, 22,50, 18,58, 4)
    return to_tray_size(img)

# ── Catálogo ───────────────────────────────────────────────────────────────

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
ANIM_NAMES  = list(ANIMATIONS.keys())
REST_TICKS  = 30 * 60 * 10
PLAY_TICKS  = 10 * 10

# ── Estado global ──────────────────────────────────────────────────────────

_state = {"anim": None, "frame": 0, "auto": True, "running": True}
_lock  = threading.Lock()
_icon_ref = [None]

def set_anim(name):
    with _lock: _state["anim"]=name; _state["frame"]=0; _state["auto"]=False

def do_rest():
    with _lock: _state["anim"]=None; _state["frame"]=0

def toggle_auto():
    with _lock:
        _state["auto"] = not _state["auto"]
        if _state["auto"]: _state["anim"]=None

def do_quit(icon, item):
    with _lock: _state["running"]=False
    icon.stop()

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

# ── Loop de animación ──────────────────────────────────────────────────────

def animate_loop(cache, rest_icon):
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
            try: icon.icon=rest_icon
            except: pass
            time.sleep(0.1)
            continue

        frames=cache[name]; _,nf,spd=ANIMATIONS[name]
        with _lock:
            fi=_state["frame"]; _state["frame"]=(fi+1)%nf
        try: icon.icon=frames[fi]
        except: pass
        time.sleep(spd)

# ── Generar .ico para el ejecutable ───────────────────────────────────────

def make_app_icon():
    """Crea un .ico con silueta de gato negro para el ejecutable."""
    img = Image.new("RGBA", (256,256), (0,0,0,0))
    d   = ImageDraw.Draw(img)
    C   = (15,15,15,255)
    G   = (80,200,120,255)

    def e(cx,cy,rx,ry,f): d.ellipse([cx-rx,cy-ry,cx+rx,cy+ry],fill=f)
    def p(pts,f): d.polygon(pts,fill=f)
    def ln(pts,f,w): d.line(pts,fill=f,width=w)

    # cuerpo
    e(128,170, 80,65, C)
    # cabeza
    e(128,80, 55,52, C)
    # orejas
    p([(80,42),(55,5),(102,38)], C)
    p([(176,42),(201,5),(154,38)], C)
    p([(83,40),(63,12),(100,38)], (80,40,50,180))
    p([(173,40),(193,12),(156,38)], (80,40,50,180))
    # ojos
    e(108,76, 16,14, G)
    e(148,76, 16,14, G)
    e(108,76, 9,11, (0,0,0,255))
    e(148,76, 9,11, (0,0,0,255))
    e(112,71, 4,4, (255,255,255,200))
    e(152,71, 4,4, (255,255,255,200))
    # nariz
    e(128,100, 8,6, (200,120,150,255))
    # boca
    ln([(120,106),(128,112),(136,106)], (200,120,150,200), 3)
    # bigotes
    ln([(80,98),(122,102)], (200,200,200,100), 2)
    ln([(80,108),(122,106)], (200,200,200,100), 2)
    ln([(134,102),(176,98)], (200,200,200,100), 2)
    ln([(134,106),(176,108)], (200,200,200,100), 2)
    # cola
    ln([(68,200),(50,180),(44,150),(52,120),(62,110)], C, 14)
    # patas
    e(95,228, 22,14, C)
    e(161,228, 22,14, C)

    ico_path = os.path.join(tempfile.gettempdir(), "cat_icon.ico")
    img.save(ico_path, format="ICO", sizes=[(256,256),(64,64),(32,32),(16,16)])
    return ico_path

# ── Main ───────────────────────────────────────────────────────────────────

def main():
    print("Precargando animaciones...")
    cache = {}
    for name,(fn,nf,_) in ANIMATIONS.items():
        cache[name] = [fn(i/nf) for i in range(nf)]
    rest_icon = anim_sit(0.5)
    print("Listo.")

    menu = pystray.Menu(
        pystray.MenuItem("=== Animaciones ===", None, enabled=False),
        pystray.MenuItem("Caminar",   cb_caminar),
        pystray.MenuItem("Sentarse",  cb_sentarse),
        pystray.MenuItem("Saltar",    cb_saltar),
        pystray.MenuItem("Estirarse", cb_estirar),
        pystray.MenuItem("Jugar",     cb_jugar),
        pystray.MenuItem("Pararse",   cb_pararse),
        pystray.MenuItem("Acechar",   cb_acechar),
        pystray.MenuItem("Lavarse",   cb_lavarse),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Descansar ahora",      cb_rest),
        pystray.MenuItem("Modo aleatorio ON/OFF", cb_auto),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Salir", do_quit),
    )

    icon = pystray.Icon("Gato Taskbar", rest_icon, "Gato Taskbar", menu)
    _icon_ref[0] = icon

    threading.Thread(target=animate_loop, args=(cache, rest_icon), daemon=True).start()

    with _lock: _state["anim"] = random.choice(ANIM_NAMES)

    icon.run()

if __name__ == "__main__":
    main()
