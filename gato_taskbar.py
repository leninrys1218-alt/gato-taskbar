"""
🐱 Gato Corriendo - Taskbar Pet
Coloca una silueta de gato animado en tu barra de tareas.
Requiere: pip install pillow pystray
Para compilar a .exe: pyinstaller --noconsole --onefile gato_taskbar.py
"""

import tkinter as tk
from PIL import Image, ImageDraw
import pystray
import threading
import time
import sys
import math

# ── Frames del gato corriendo (pixel art 32x32 en coordenadas) ──────────────
# Cada frame es una lista de polígonos que forman la silueta del gato

def draw_cat_frame(frame_index, size=32):
    """Dibuja un frame del gato corriendo como imagen RGBA."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    s = size / 32  # escala
    color = (255, 255, 255, 255)

    # Animación cíclica: 8 frames
    f = frame_index % 8
    t = f / 8.0  # 0.0 .. 0.875

    # Movimiento de rebote del cuerpo
    body_y = math.sin(t * math.pi * 2) * 1.5 * s

    # ── Cuerpo ────────────────────────────────────────────────────────────────
    body = [
        (8*s,  14*s + body_y),
        (22*s, 13*s + body_y),
        (24*s, 18*s + body_y),
        (20*s, 20*s + body_y),
        (10*s, 21*s + body_y),
        (6*s,  18*s + body_y),
    ]
    draw.polygon(body, fill=color)

    # ── Cabeza ────────────────────────────────────────────────────────────────
    head_x = 22*s
    head_y = 10*s + body_y
    draw.ellipse([head_x-4*s, head_y-4*s, head_x+4*s, head_y+4*s], fill=color)

    # Orejas
    draw.polygon([
        (head_x-3*s, head_y-3*s),
        (head_x-5*s, head_y-7*s),
        (head_x-1*s, head_y-4*s),
    ], fill=color)
    draw.polygon([
        (head_x+1*s, head_y-3*s),
        (head_x+3*s, head_y-7*s),
        (head_x+4*s, head_y-4*s),
    ], fill=color)

    # Ojo (pequeño hueco negro)
    draw.ellipse([head_x+1*s, head_y-1.5*s, head_x+2.5*s, head_y+0.5*s], fill=(0,0,0,255))

    # Hocico / nariz
    draw.ellipse([head_x-1.5*s, head_y+1*s, head_x+0.5*s, head_y+2.5*s], fill=(200,150,150,200))

    # ── Cola (ondulante) ──────────────────────────────────────────────────────
    tail_wave = math.sin(t * math.pi * 2 + 1) * 4 * s
    tail_pts = [
        (8*s,  17*s + body_y),
        (5*s,  15*s + body_y + tail_wave * 0.3),
        (2*s,  11*s + body_y + tail_wave * 0.7),
        (4*s,   8*s + body_y + tail_wave),
        (6*s,   9*s + body_y + tail_wave),
        (4.5*s,11*s + body_y + tail_wave * 0.7),
        (7*s,  14*s + body_y + tail_wave * 0.3),
        (9*s,  16*s + body_y),
    ]
    draw.polygon(tail_pts, fill=color)

    # ── Patas (4 patas con movimiento alterno) ────────────────────────────────
    # Fase de cada pata
    phases = [0, 0.5, 0.25, 0.75]
    paw_x_bases = [12*s, 18*s, 10*s, 16*s]
    for i, (px, ph) in enumerate(zip(paw_x_bases, phases)):
        paw_t = (t + ph) % 1.0
        # Pata arriba a la mitad del ciclo
        swing = math.sin(paw_t * math.pi * 2) * 5 * s
        py_top = 20*s + body_y
        py_bot = 27*s + body_y - abs(swing) * 0.6

        # Pata: rectángulo pequeño
        pw = 2.5 * s
        draw.rectangle([px - pw/2, py_top, px + pw/2, py_bot - abs(swing)*0.4], fill=color)
        # Patita redondeada abajo
        draw.ellipse([px - pw, py_bot - 2*s, px + pw, py_bot + 1.5*s], fill=color)

    return img


def make_icon_frames(size=32, n_frames=8):
    frames = []
    for i in range(n_frames):
        img = draw_cat_frame(i, size)
        frames.append(img)
    return frames


# ── Sistema de tray ───────────────────────────────────────────────────────────

class GatoTray:
    def __init__(self):
        self.frames = make_icon_frames(32, 8)
        self.current = 0
        self.running = True
        self.speed = 0.12  # segundos entre frames

        # Crear menú
        menu = pystray.Menu(
            pystray.MenuItem("🐱 Gato Corriendo", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Más rápido ⚡", self.faster),
            pystray.MenuItem("Más lento 🐢", self.slower),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Salir ✕", self.quit),
        )

        self.icon = pystray.Icon(
            "gato",
            self.frames[0],
            "🐱 Gato Corriendo",
            menu,
        )

    def faster(self, icon, item):
        self.speed = max(0.04, self.speed - 0.02)

    def slower(self, icon, item):
        self.speed = min(0.5, self.speed + 0.04)

    def animate(self):
        while self.running:
            time.sleep(self.speed)
            self.current = (self.current + 1) % len(self.frames)
            try:
                self.icon.icon = self.frames[self.current]
            except Exception:
                break

    def quit(self, icon, item):
        self.running = False
        icon.stop()

    def run(self):
        t = threading.Thread(target=self.animate, daemon=True)
        t.start()
        self.icon.run()


if __name__ == "__main__":
    app = GatoTray()
    app.run()