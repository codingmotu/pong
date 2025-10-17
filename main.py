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

# Physics tuning (new)
BALL_MASS = 0.6
PADDLE_MASS = 4.0
BALL_MAX_SPEED = 14.0        # hard cap on ball speed
BALL_DRAG = 0.997            # slight drag each frame
SPIN_FACTOR = 0.28          # how much paddle motion imparts spin
SPIN_DECAY = 0.96           # spin decay per frame
BOUNCE_ELASTICITY = 1.03    # >1 adds slight speed-up on bounce (tweak for arcade feel)
PADDLE_RECOIL = 2.4         # small recoil impulse applied to paddle on hit

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
    # update small trail particles
    for p in particles[:]:
        p['age'] += dt
        p['pos'][0] += p['vel'][0] * 60 * dt
        p['pos'][1] += p['vel'][1] * 60 * dt
        # apply slight gravity-ish or downward bias for style (small)
        p['vel'][1] += 0.08 * dt * 60
        if p['age'] >= p['life']:
            particles.remove(p)
    # update explosion particles with damping
    for p in explosion_particles[:]:
        p['age'] += dt
        p['pos'][0] += p['vel'][0] * 60 * dt
        p['pos'][1] += p['vel'][1] * 60 * dt
        # dampen velocities to simulate air resistance
        p['vel'][0] *= 0.985
        p['vel'][1] *= 0.985
        # gravity pull for explosion bits
        p['vel'][1] += 0.45 * dt * 60
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

# Creative shapes helpers continued (Paddle, Ball, draw, etc.)

# Paddle class with inertia and recoil
class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.speed = PADDLE_SPEED
        self.vel = 0.0
        self._target_vel = 0.0
        self.inertia = 0.6

    def move(self, dy):
        self._target_vel = dy
        self.vel = self.vel * self.inertia + self._target_vel * (1.0 - self.inertia)
        if self.vel < 0:
            self.rect.y = max(self.rect.y + int(self.vel), 0)
        else:
            self.rect.y = min(self.rect.y + int(self.vel), HEIGHT - PADDLE_HEIGHT)

    def apply_recoil(self, impulse):
        self.vel += impulse

    def ai_move(self, target_y):
        center = self.rect.centery
        if center < target_y:
            self.move(self.speed)
        elif center > target_y:
            self.move(-self.speed)
        else:
            self.move(0)

    def draw(self, surf):
        body_color = palette['fg']
        fin_color = palette['accent']
        draw_paddle_shape(surf, self.rect, body_color, fin_color)

# Ball class with spin, drag, momentum transfer
class Ball:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH // 2 - BALL_SIZE // 2, WIDTH // 2 - BALL_SIZE // 2, BALL_SIZE, BALL_SIZE)
        self.reset()
        self.spin = 0.0

    def reset(self, direction=None):
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        vx = BALL_SPEED if direction is None else BALL_SPEED * direction
        vy = random.choice([-1, 1]) * random.uniform(2, 4)
        self.vel = [vx, vy]
        self.spin = 0.0
        if direction is None and random.random() < 0.5:
            self.vel[0] *= -1

    def update(self, left_paddle, right_paddle):
        # Apply spin (Magnus-like effect): spin slightly alters vertical velocity
        if abs(self.spin) > 0.001:
            self.vel[1] += self.spin * 0.12
            self.spin *= SPIN_DECAY

        # move ball
        self.rect.x += int(self.vel[0])
        self.rect.y += int(self.vel[1])

        # Add particle trail with velocity-based spread
        for _ in range(1):
            px = self.rect.centerx + random.uniform(-2, 2)
            py = self.rect.centery + random.uniform(-2, 2)
            pvel = [ -self.vel[0]*0.04 + random.uniform(-0.8,0.8), -self.vel[1]*0.04 + random.uniform(-0.8,0.8)]
            particles.append({'pos':[px,py],'vel':pvel,'life':random.uniform(0.3,0.9),'age':0,'color':palette['ball'],'size':random.uniform(2,4)})

        # Top/bottom collision
        if self.rect.top <= 0:
            self.rect.top = 0
            self.vel[1] *= -1
            self.vel[0] *= 1.01
            self.spin *= 0.6
            play_hit_sound()
        if self.rect.bottom >= HEIGHT:
            self.rect.bottom = HEIGHT
            self.vel[1] *= -1
            self.vel[0] *= 1.01
            self.spin *= 0.6
            play_hit_sound()

        # Paddle collisions with momentum and spin transfer
        if self.rect.colliderect(left_paddle.rect) and self.vel[0] < 0:
            offset = (self.rect.centery - left_paddle.rect.centery) / (PADDLE_HEIGHT / 2)
            spin_from_paddle = left_paddle.vel * SPIN_FACTOR + offset * 1.0
            self._bounce(left_paddle, spin_from_paddle)
            left_paddle.apply_recoil(-PADDLE_RECOIL * math.copysign(1, self.vel[0]))
            play_hit_sound()

        if self.rect.colliderect(right_paddle.rect) and self.vel[0] > 0:
            offset = (self.rect.centery - right_paddle.rect.centery) / (PADDLE_HEIGHT / 2)
            spin_from_paddle = right_paddle.vel * SPIN_FACTOR + offset * 1.0
            self._bounce(right_paddle, spin_from_paddle)
            right_paddle.apply_recoil(PADDLE_RECOIL * math.copysign(1, self.vel[0]))
            play_hit_sound()

        # Apply drag to limit runaway speeds and add small damping
        self.vel[0] *= BALL_DRAG
        self.vel[1] *= BALL_DRAG

        # Cap speed
        spd = math.hypot(self.vel[0], self.vel[1])
        if spd > BALL_MAX_SPEED:
            scale = BALL_MAX_SPEED / spd
            self.vel[0] *= scale
            self.vel[1] *= scale

    def _bounce(self, paddle, spin_input=0.0):
        paddle_vy = paddle.vel
        self.vel[0] = -self.vel[0] * BOUNCE_ELASTICITY
        self.vel[1] += paddle_vy * (PADDLE_MASS / (PADDLE_MASS + BALL_MASS)) * 0.9
        self.spin += spin_input * 0.9
        if self.vel[0] == 0:
            self.vel[0] = BALL_SPEED * (1 if random.random() < 0.5 else -1)

    def draw(self, surf):
        cx, cy = self.rect.center
        glow_surf = pygame.Surface((self.rect.width*6, self.rect.height*6), pygame.SRCALPHA)
        g_radius = int(max(self.rect.width, self.rect.height)*2.5)
        for i in range(g_radius, 0, -4):
            alpha = int(25 * (1 - i / g_radius))
            col = (*palette['ball'], alpha)
            pygame.draw.circle(glow_surf, col, (glow_surf.get_width()//2, glow_surf.get_height()//2), i)
        surf.blit(glow_surf, (cx - glow_surf.get_width()//2, cy - glow_surf.get_height()//2), special_flags=pygame.BLEND_PREMULTIPLIED)
        pts = regular_star_points(cx, cy, self.rect.width, self.rect.width*0.45, 5)
        pygame.draw.polygon(surf, palette['ball'], pts)
        pygame.draw.circle(surf, palette['fg'], (cx, cy), int(self.rect.width*0.25))

# update_particles fixed (removed stray quote)
def update_particles(dt):
    # update small trail particles
    for p in particles[:]:
        p['age'] += dt
        p['pos'][0] += p['vel'][0] * 60 * dt
        p['pos'][1] += p['vel'][1] * 60 * dt
        # apply slight gravity-ish or downward bias for style (small)
        p['vel'][1] += 0.08 * dt * 60
        if p['age'] >= p['life']:
            particles.remove(p)
    # update explosion particles with damping
    for p in explosion_particles[:]:
        p['age'] += dt
        p['pos'][0] += p['vel'][0] * 60 * dt
        p['pos'][1] += p['vel'][1] * 60 * dt
        # dampen velocities to simulate air resistance
        p['vel'][0] *= 0.985
        p['vel'][1] *= 0.985
        # gravity pull for explosion bits
        p['vel'][1] += 0.45 * dt * 60
        if p['age'] >= p['life']:
            explosion_particles.remove(p)

# Remaining game code (drawing, main loop) is unchanged and kept as in previous commit.