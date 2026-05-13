"""
Gato Taskbar v1.1 - Fix menu pystray
pip install pillow pystray
pyinstaller --noconsole --onefile gato_taskbar.py
"""

import threading, time, math, random
import pystray
from PIL import Image, ImageDraw

SIZE = 64

def s(v):
    return v * SIZE / 32

W = (220, 220, 220, 255)

def new_img():
    return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

def draw_body(d, cx, cy, w=10, h=6):
    pts = [(s(cx + w*math.cos(math.radians(a))), s(cy + h*math.sin(math.radians(a)))) for a in range(0,360,8)]
    d.polygon(pts, fill=W)

def draw_head(d, cx, cy, r=5):
    d.ellipse([s(cx-r), s(cy-r), s(cx+r), s(cy+r)], fill=W)

def draw_ear(d, tx, ty, b1x, b1y, b2x, b2y):
    d.polygon([(s(tx),s(ty)),(s(b1x),s(b1y)),(s(b2x),s(b2y))], fill=W)

def draw_tail(d, pts, w=2):
    for i in range(len(pts)-1):
        d.line([(s(pts[i][0]),s(pts[i][1])),(s(pts[i+1][0]),s(pts[i+1][1]))], fill=W, width=max(1,int(s(w))))

def draw_leg(d, x1, y1, x2, y2, w=2.5):
    d.line([(s(x1),s(y1)),(s(x2),s(y2))], fill=W, width=max(1,int(s(w))))
    d.ellipse([s(x2)-s(1.5),s(y2)-s(1),s(x2)+s(1.5),s(y2)+s(1)], fill=W)

def draw_eye(d, cx, cy):
    d.ellipse([s(cx-.8),s(cy-.8),s(cx+.8),s(cy+.8)], fill=(20,20,20,255))

def to32(img):
    return img.resize((32,32), Image.LANCZOS)

def anim_walk(t):
    img=new_img(); d=ImageDraw.Draw(img)
    bob=math.sin(t*math.pi*2)*.7
    draw_body(d,15,19+bob); draw_head(d,23,13+bob)
    draw_ear(d,21,8+bob,20,12+bob,23,12+bob); draw_ear(d,25,8+bob,24,12+bob,27,12+bob)
    draw_eye(d,24,13+bob)
    sw=math.sin(t*math.pi*2)*3
    draw_leg(d,12,23+bob,10,29+sw*.5); draw_leg(d,16,23+bob,17,29-sw*.5)
    draw_leg(d,20,23+bob,19,29+sw*.3); draw_leg(d,23,23+bob,24,29-sw*.3)
    wv=math.sin(t*math.pi*2)*2
    draw_tail(d,[(7,19+bob),(4,17+bob+wv),(3,13+bob+wv*1.5),(5,10+bob+wv*.5)])
    return to32(img)

def anim_sit(t):
    img=new_img(); d=ImageDraw.Draw(img)
    blink=t%1.0<0.88
    draw_body(d,16,22,7,6); draw_head(d,16,13,5)
    draw_ear(d,13,7,12,11,15,11); draw_ear(d,19,7,17,11,20,11)
    if blink:
        draw_eye(d,14,13); draw_eye(d,18,13)
    else:
        d.line([(s(13),s(13)),(s(15),s(13))],fill=(20,20,20,255),width=2)
        d.line([(s(17),s(13)),(s(19),s(13))],fill=(20,20,20,255),width=2)
    draw_tail(d,[(10,24),(8,27),(12,29),(17,28),(20,25)])
    draw_leg(d,12,25,10,28,2); draw_leg(d,20,25,22,28,2)
    return to32(img)

def anim_jump(t):
    img=new_img(); d=ImageDraw.Draw(img)
    arc=-abs(math.sin(t*math.pi))*9
    cy=21+arc
    draw_body(d,15,cy); draw_head(d,22,cy-5)
    draw_ear(d,20,cy-10,19,cy-6,22,cy-6); draw_ear(d,24,cy-10,23,cy-6,26,cy-6)
    draw_eye(d,23,cy-5)
    sp=math.sin(t*math.pi)*4
    draw_leg(d,11,cy+2,8,cy+7+sp); draw_leg(d,14,cy+2,12,cy+7+sp)
    draw_leg(d,18,cy+2,20,cy+7+sp); draw_leg(d,21,cy+2,24,cy+7+sp)
    draw_tail(d,[(8,cy),(5,cy-2),(3,cy-5+sp)])
    return to32(img)

def anim_stretch(t):
    img=new_img(); d=ImageDraw.Draw(img)
    st=math.sin(t*math.pi)*4
    draw_body(d,15,23,10+st*.4,4); draw_head(d,23+st,20,4)
    draw_ear(d,21+st,15,20+st,19,23+st,19); draw_ear(d,25+st,15,24+st,19,27+st,19)
    draw_eye(d,24+st,20); draw_body(d,7,20,5,5)
    draw_leg(d,5,22,4,28); draw_leg(d,9,22,10,28)
    draw_leg(d,20+st,22,19+st,28); draw_leg(d,24+st,22,25+st,28)
    draw_tail(d,[(5,19),(3,16),(2,12),(4,9)])
    return to32(img)

def anim_play(t):
    img=new_img(); d=ImageDraw.Draw(img)
    paw=math.sin(t*math.pi*2)*5
    draw_body(d,14,21,8,5); draw_head(d,21,14,4.5)
    draw_ear(d,19,9,18,13,21,13); draw_ear(d,23,9,22,13,25,13)
    draw_eye(d,22,14)
    draw_leg(d,19,22,25,18+paw,3)
    draw_leg(d,16,23,15,29); draw_leg(d,20,23,21,29); draw_leg(d,11,22,10,29)
    draw_tail(d,[(7,20),(4,18),(3,14),(5,11)])
    by=17+paw; d.ellipse([s(26),s(by),s(29),s(by+3)],fill=(200,100,100,220))
    return to32(img)

def anim_standup(t):
    img=new_img(); d=ImageDraw.Draw(img)
    sw=math.sin(t*math.pi*2)*1.5
    pts=[(s(16+sw+5*math.cos(math.radians(a))),s(19+9*math.sin(math.radians(a)))) for a in range(0,360,8)]
    ImageDraw.Draw(img).polygon(pts,fill=W)
    draw_head(d,16+sw,10,4.5)
    draw_ear(d,13+sw,5,12+sw,9,15+sw,9); draw_ear(d,19+sw,5,18+sw,9,21+sw,9)
    draw_eye(d,15+sw,10); draw_eye(d,18+sw,10)
    arm=math.sin(t*math.pi*2)*2
    draw_leg(d,12+sw,17,9+sw,14+arm,2); draw_leg(d,20+sw,17,23+sw,14-arm,2)
    draw_leg(d,13+sw,25,11+sw,30); draw_leg(d,19+sw,25,21+sw,30)
    draw_tail(d,[(16+sw,26),(20+sw,28),(22+sw,25),(21+sw,21)])
    return to32(img)

def anim_sneak(t):
    img=new_img(); d=ImageDraw.Draw(img)
    cr=math.sin(t*math.pi*2)
    draw_body(d,15,25+cr,10,3.5); draw_head(d,23,22+cr,4)
    draw_ear(d,21,17+cr,20,21+cr,23,21+cr); draw_ear(d,25,17+cr,24,21+cr,27,21+cr)
    draw_eye(d,24,22+cr)
    draw_leg(d,11,27+cr,8,30+cr); draw_leg(d,15,27+cr,14,30+cr)
    draw_leg(d,19,27+cr,20,30+cr); draw_leg(d,22,27+cr,24,30+cr)
    draw_tail(d,[(7,25+cr),(5,23+cr),(4,19+cr),(6,16+cr),(8,15+cr)])
    return to32(img)

def anim_wash(t):
    img=new_img(); d=ImageDraw.Draw(img)
    lk=abs(math.sin(t*math.pi*2))*3
    draw_body(d,16,22,7,6); draw_head(d,16,13,5)
    draw_ear(d,13,7,12,11,15,11); draw_ear(d,19,7,17,11,20,11)
    draw_eye(d,14,13); draw_eye(d,18,13)
    draw_leg(d,13,20,15,15-lk,2.5)
    draw_leg(d,19,21,21,29,2); draw_leg(d,12,25,10,29,2)
    draw_tail(d,[(10,24),(8,27),(12,29),(17,28),(20,25)])
    return to32(img)

ANIMATIONS = {
    "Caminar":   (anim_walk,    8,  0.10),
    "Sentarse":  (anim_sit,     20, 0.15),
    "Saltar":    (anim_jump,    12, 0.08),
    "Estirarse": (anim_stretch, 10, 0.10),
    "Jugar":     (anim_play,    8,  0.09),
    "Pararse":   (anim_standup, 10, 0.10),
    "Acechar":   (anim_sneak,   10, 0.12),
    "Lavarse":   (anim_wash,    12, 0.12),
}
ANIM_NAMES = list(ANIMATIONS.keys())
REST_TICKS  = 30 * 60 * 10   # 30 min a 10 ticks/s
PLAY_TICKS  = 10 * 10        # 10 segundos

# Estado global (evita lambdas con closures problemáticas en pystray)
_state = {
    "anim":  None,
    "frame": 0,
    "auto":  True,
    "running": True,
}
_lock = threading.Lock()
_icon_ref = [None]

def set_anim(name):
    with _lock:
        _state["anim"]  = name
        _state["frame"] = 0
        _state["auto"]  = False

def do_rest():
    with _lock:
        _state["anim"]  = None
        _state["frame"] = 0

def toggle_auto():
    with _lock:
        _state["auto"] = not _state["auto"]
        if _state["auto"]:
            _state["anim"] = None

def do_quit(icon, item):
    with _lock:
        _state["running"] = False
    icon.stop()

# Callbacks del menú — funciones normales, sin lambdas con argumento extra
def cb_caminar(icon, item):  set_anim("Caminar")
def cb_sentarse(icon, item): set_anim("Sentarse")
def cb_saltar(icon, item):   set_anim("Saltar")
def cb_estirar(icon, item):  set_anim("Estirarse")
def cb_jugar(icon, item):    set_anim("Jugar")
def cb_pararse(icon, item):  set_anim("Pararse")
def cb_acechar(icon, item):  set_anim("Acechar")
def cb_lavarse(icon, item):  set_anim("Lavarse")
def cb_rest(icon, item):     do_rest()
def cb_auto(icon, item):     toggle_auto()

def animate_loop(cache, rest_icon):
    ticks = 0
    resting = True

    while True:
        with _lock:
            running = _state["running"]
            auto    = _state["auto"]
            name    = _state["anim"]

        if not running:
            break

        # Lógica automática
        if auto:
            ticks += 1
            if resting and ticks >= REST_TICKS:
                chosen = random.choice(ANIM_NAMES)
                with _lock:
                    _state["anim"]  = chosen
                    _state["frame"] = 0
                resting = False
                ticks   = 0
            elif not resting and ticks >= PLAY_TICKS:
                with _lock:
                    _state["anim"]  = None
                    _state["frame"] = 0
                resting = True
                ticks   = 0

        with _lock:
            name = _state["anim"]

        icon = _icon_ref[0]
        if icon is None:
            time.sleep(0.1)
            continue

        if name is None:
            try: icon.icon = rest_icon
            except: pass
            time.sleep(0.1)
            continue

        frames = cache[name]
        _, nf, spd = ANIMATIONS[name]

        with _lock:
            fi = _state["frame"]
            _state["frame"] = (fi + 1) % nf

        try: icon.icon = frames[fi]
        except: pass
        time.sleep(spd)


def main():
    print("Precargando animaciones...")
    cache = {}
    for name, (fn, nf, _) in ANIMATIONS.items():
        cache[name] = [fn(i / nf) for i in range(nf)]
    rest_icon = anim_sit(0.5)
    print("Listo.")

    menu = pystray.Menu(
        pystray.MenuItem("Caminar",   cb_caminar),
        pystray.MenuItem("Sentarse",  cb_sentarse),
        pystray.MenuItem("Saltar",    cb_saltar),
        pystray.MenuItem("Estirarse", cb_estirar),
        pystray.MenuItem("Jugar",     cb_jugar),
        pystray.MenuItem("Pararse",   cb_pararse),
        pystray.MenuItem("Acechar",   cb_acechar),
        pystray.MenuItem("Lavarse",   cb_lavarse),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Descansar ahora", cb_rest),
        pystray.MenuItem("Modo aleatorio ON/OFF", cb_auto),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Salir", do_quit),
    )

    icon = pystray.Icon("gato", rest_icon, "Gato Taskbar", menu)
    _icon_ref[0] = icon

    t = threading.Thread(target=animate_loop, args=(cache, rest_icon), daemon=True)
    t.start()

    # Arrancar con animación aleatoria
    with _lock:
        _state["anim"] = random.choice(ANIM_NAMES)

    icon.run()


if __name__ == "__main__":
    main()
