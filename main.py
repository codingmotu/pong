# Pong with realistic sounds (tennis hit + final explosion) and enhanced visuals.
# Place realistic WAV files in assets/sounds/tennis_hit.wav and assets/sounds/explosion.wav
#
# Controls:
# - Left paddle: W (up), S (down)
# - Right paddle: Up Arrow, Down Arrow
# - Space: restart / serve after score
# - C: cycle color palette
# - M: toggle sound on/off
# - Esc or window close: quit
#
# Notes:
# - If the WAV files are present they will be used (recommended).
# - If WAVs are missing, the code falls back to generated tones or system beep.
# - The game triggers an "explosion" and final effect when a player reaches WIN_SCORE.

import pygame
import sys
import random
import threading
import platform
import math
import os
import time

# Optional numpy for generated sounds
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except Exception:
    NUMPY_AVAILABLE = False

# Try winsound on Windows as a fallback
try:
    if platform.system() == "Windows":
        import winsound
        WINSOUND_AVAILABLE = True
    else:
        WINSOUND_AVAILABLE = False
except Exception:
    WINSOUND_AVAILABLE = False

pygame.init()
pygame.display.set_caption("Pong - Vibrant (With Realistic Sounds)")

# Configuration
WIDTH, HEIGHT = 900, 600
FPS = 60
PADDLE_WIDTH, PADDLE_HEIGHT = 16, 110
BALL_SIZE = 18
PADDLE_SPEED = 7
BALL_SPEED = 5
SCORE_FONT_SIZE = 56
WIN_SCORE = 7  # Score to trigger final explosion & win

ASSETS_SOUNDS_DIR = os.path.join("assets", "sounds")
HIT_WAV = os.path.join(ASSETS_SOUNDS_DIR, "tennis_hit.wav")
EXPLOSION_WAV = os.path.join(ASSETS_SOUNDS_DIR, "explosion.wav")
SCORE_WAV = os.path.join(ASSETS_SOUNDS_DIR, "score.wav")  # optional lighter score sound

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, SCORE_FONT_SIZE)

# Sound setup (uses pygame.mixer if available)
SOUND_ON = True
pygame_mixer_available = False
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2)
    pygame_mixer_available = True
except Exception:
    pygame_mixer_available = False

hit_sound = None
score_sound = None
explosion_sound = None

def make_sine_sound(freq=440, duration_ms=120, volume=0.3, sample_rate=44100):
    """Generate a pygame Sound using numpy sine wave. Returns None if numpy or mixer unavailable."""
    if not NUMPY_AVAILABLE or not pygame_mixer_available:
        return None
    samples = int(sample_rate * (duration_ms / 1000.0))
    t = np.linspace(0, duration_ms/1000.0, samples, False)
    # Add a slight attack/decay envelope for more natural tone
    env = np.minimum(1.0, 10 * t) * np.exp(-3 * t)
    wave = 0.5 * env * np.sin(2 * math.pi * freq * t)
    audio = np.zeros((samples, 2), dtype=np.int16)
    max_amp = np.iinfo(np.int16).max
    audio[:, 0] = (wave * max_amp * volume).astype(np.int16)
    audio[:, 1] = (wave * max_amp * volume).astype(np.int16)
    try:
        sound = pygame.sndarray.make_sound(audio)
        return sound
    except Exception:
        return None

def try_load_sound(path):
    """Try to load a WAV file via pygame mixer; return Sound or None."""
    if not pygame_mixer_available:
        return None
    try:
        if os.path.isfile(path):
            return pygame.mixer.Sound(path)
    except Exception:
        pass
    return None

# Attempt to load realistic WAVs first
if pygame_mixer_available:
    hit_sound = try_load_sound(HIT_WAV)
    explosion_sound = try_load_sound(EXPLOSION_WAV)
    score_sound = try_load_sound(SCORE_WAV)

# If no WAVs, prepare fallback tones
if hit_sound is None and pygame_mixer_available and NUMPY_AVAILABLE:
    # short, sharp tone for hit (higher frequency, short)
    hit_sound = make_sine_sound(freq=800, duration_ms=60, volume=0.25)
if score_sound is None and pygame_mixer_available and NUMPY_AVAILABLE:
    score_sound = make_sine_sound(freq=360, duration_ms=220, volume=0.32)
if explosion_sound is None and pygame_mixer_available and NUMPY_AVAILABLE:
    # explosion fallback: layered low rumble (created when playing)
    explosion_sound = None  # we'll synthesize a short rumble via threads if needed

def _winsound_beep(freq, duration_ms):
    try:
        winsound.Beep(int(freq), int(duration_ms))
    except Exception:
        pass

def play_sound_obj(sound):
    try:
        if sound and SOUND_ON:
            sound.play()
    except Exception:
        pass

def play_hit_sound():
    if not SOUND_ON:
        return
    if pygame_mixer_available and hit_sound:
        play_sound_obj(hit_sound)
        return
    if WINSOUND_AVAILABLE:
        threading.Thread(target=_winsound_beep, args=(1200, 60), daemon=True).start()

def play_score_sound():
    if not SOUND_ON:
        return
    if pygame_mixer_available and score_sound:
        play_sound_obj(score_sound)
        return
    if WINSOUND_AVAILABLE:
        threading.Thread(target=_winsound_beep, args=(480, 200), daemon=True).start()

def play_explosion_sound():
    if not SOUND_ON:
        return
    if pygame_mixer_available and explosion_sound:
        # if a real WAV is provided
        play_sound_obj(explosion_sound)
        return
    if pygame_mixer_available and NUMPY_AVAILABLE:
        # generate a multi-layered rumble (non-blocking)
        def rumble():
            base = make_sine_sound(freq=120, duration_ms=900, volume=0.6)
            mid = make_sine_sound(freq=220, duration_ms=700, volume=0.45)
            snap = make_sine_sound(freq=1000, duration_ms=120, volume=0.35)
            if base: base.play()
            time.sleep(0.06)
            if mid: mid.play()
            time.sleep(0.12)
            if snap: snap.play()
        threading.Thread(target=rumble, daemon=True).start()
        return
    if WINSOUND_AVAILABLE:
        # fallback beeps for Windows
        threading.Thread(target=_winsound_beep, args=(300, 600), daemon=True).start()
        threading.Thread(target=_winsound_beep, args=(150, 900), daemon=True).start()

# Enhanced color palettes with gradients
PALETTES = [
    {
        'name': 'Aurora',
        'bg_top': (12, 7, 50),
        'bg_bottom': (5, 80, 120),
        'fg': (255, 245, 230),
        'accent': (120, 255, 200),
        'ball': (255, 200, 100)
    },
    {
        'name': 'Sunset Pop',
        'bg_top': (25, 10, 40),
        'bg_bottom': (255, 100, 60),
        'fg': (250, 250, 250),
        'accent': (255, 40, 120),
        'ball': (255, 255, 100)
    },
    {
        'name': 'Cyber',
        'bg_top': (2, 8, 20),
        'bg_bottom': (10, 40, 70),
        'fg': (180, 255, 255),
        'accent': (255, 0, 200),
        'ball': (120, 255, 200)
    }
]
palette_index = 0
palette = PALETTES[palette_index]

# Particles for ball trail and explosion
particles = []
explosion_particles = []

def add_particle(x, y, color, size=None, vel=None, life=None):
    p = {
        'pos': [x, y],
        'vel': vel if vel is not None else [random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6)],
        'life': life if life is not None else random.uniform(0.35, 0.9),
        'age': 0,
        'color': color,
        'size': size if size is not None else random.uniform(2, 5)
    }
    particles.append(p)

def add_explosion(cx, cy, color, count=60):
    explosion_particles.clear()
    for _ in range(count):
        angle = random.uniform(0, math.pi*2)
        speed = random.uniform(2.5, 8.5)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        explosion_particles.append({'pos': [cx, cy], 'vel':[vx, vy], 'life': random.uniform(0.9, 1.6), 'age':0, 'color': color, 'size': random.uniform(3.5, 9.0)})

def update_particles(dt):
    for p in particles[:]:
        p['age'] += dt
        p['pos'][0] += p['vel'][0] * 60 * dt
        p['pos'][1] += p['vel'][1] * 60 * dt
        if p['age'] >= p['life']:
            particles.remove(p)
    for p in explosion_particles[:]:
        p['age'] += dt
        p['pos'][0] += p['vel'][0] * 60 * dt
        p['pos'][1] += p['vel'][1] * 60 * dt
        # slow down
        p['vel'][0] *= 0.98
        p['vel'][1'] *= 0.98 if False else p['vel'][1]  # harmless no-op to keep formatting safe
        if p['age'] >= p['life']:
            explosion_particles.remove(p)

# Utility: vertical gradient
def draw_vertical_gradient(surf, top_col, bottom_col):
    height = surf.get_height()
    for y in range(height):
        ratio = y / height
        r = int(top_col[0] * (1 - ratio) + bottom_col[0] * ratio)
        g = int(top_col[1] * (1 - ratio) + bottom_col[1] * ratio)
        b = int(top_col[2] * (1 - ratio) + bottom_col[2] * ratio)
        pygame.draw.line(surf, (r, g, b), (0, y), (surf.get_width(), y))

# Creative shapes drawing helpers
def draw_paddle_shape(surf, rect, color, fin_color):
    # rounded rect body
    pygame.draw.rect(surf, color, rect, border_radius=int(rect.width/2))
    # triangular fin pointing outward depending on side
    if rect.centerx < WIDTH//2:
        tri = [(rect.left, rect.centery), (rect.left + int(rect.width*0.6), rect.top), (rect.left + int(rect.width*0.6), rect.bottom)]
    else:
        tri = [(rect.right, rect.centery), (rect.right - int(rect.width*0.6), rect.top), (rect.right - int(rect.width*0.6), rect.bottom)]
    pygame.draw.polygon(surf, fin_color, tri)
    # subtle inner highlight
    inner = rect.inflate(-6, -20)
    try:
        highlight = tuple(min(255, c+30) for c in color)
    except Exception:
        highlight = color
    pygame.draw.rect(surf, highlight, inner, border_radius=int(inner.width/2))

# ... (file continues with rest of content)
