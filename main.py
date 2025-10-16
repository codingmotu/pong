# A simple Pong game using Pygame with color palettes and optional sound
# Controls:
# - Left paddle: W (up), S (down)
# - Right paddle: Up Arrow, Down Arrow
# - Space: restart / serve after score
# - C: cycle color palette
# - M: toggle sound on/off
# - Esc or window close: quit

import pygame
import sys
import random
import threading
import platform

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
pygame.display.set_caption("Pong")

# Configuration
WIDTH, HEIGHT = 800, 600
FPS = 60
PADDLE_WIDTH, PADDLE_HEIGHT = 12, 100
BALL_SIZE = 16
PADDLE_SPEED = 6
BALL_SPEED = 5
SCORE_FONT_SIZE = 48

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, SCORE_FONT_SIZE)

# Sound setup
SOUND_ON = True
pygame_mixer_available = False
try:
    # initialize the mixer; allow failure in headless environments
    pygame.mixer.init(frequency=44100, size=-16, channels=2)
    pygame_mixer_available = True
except Exception:
    pygame_mixer_available = False

hit_sound = None
score_sound = None

def make_sine_sound(freq=440, duration_ms=120, volume=0.3, sample_rate=44100):
    """Generate a pygame Sound using numpy sine wave. Returns None if numpy or mixer unavailable."""
    if not NUMPY_AVAILABLE or not pygame_mixer_available:
        return None
    samples = int(sample_rate * (duration_ms / 1000.0))
    t = np.linspace(0, duration_ms/1000.0, samples, False)
    wave = 0.5 * np.sin(2 * np.pi * freq * t)
    # stereo
    audio = np.zeros((samples, 2), dtype=np.int16)
    max_amp = np.iinfo(np.int16).max
    audio[:, 0] = (wave * max_amp * volume).astype(np.int16)
    audio[:, 1] = (wave * max_amp * volume).astype(np.int16)
    try:
        sound = pygame.sndarray.make_sound(audio)
        return sound
    except Exception:
        return None

if pygame_mixer_available and NUMPY_AVAILABLE:
    # Create two simple sounds
    hit_sound = make_sine_sound(freq=700, duration_ms=80, volume=0.25)
    score_sound = make_sine_sound(freq=360, duration_ms=300, volume=0.35)

# If mixer not available but winsound is, we'll use winsound.Beep in a thread
def _winsound_beep(freq, duration_ms):
    try:
        winsound.Beep(int(freq), int(duration_ms))
    except Exception:
        pass

def play_hit_sound():
    if not SOUND_ON:
        return
    if pygame_mixer_available and hit_sound:
        try:
            hit_sound.play()
            return
        except Exception:
            pass
    if WINSOUND_AVAILABLE:
        threading.Thread(target=_winsound_beep, args=(800, 80), daemon=True).start()

def play_score_sound():
    if not SOUND_ON:
        return
    if pygame_mixer_available and score_sound:
        try:
            score_sound.play()
            return
        except Exception:
            pass
    if WINSOUND_AVAILABLE:
        threading.Thread(target=_winsound_beep, args=(400, 300), daemon=True).start()

# Color palettes
PALETTES = [
    {
        'name': 'Classic',
        'bg': (0, 0, 0),
        'fg': (255, 255, 255),
        'accent': (200, 200, 200),
        'ball': (255, 255, 255)
    },
    {
        'name': 'Neon',
        'bg': (10, 0, 30),
        'fg': (0, 255, 200),
        'accent': (255, 0, 200),
        'ball': (0, 255, 200)
    },
    {
        'name': 'Retro',
        'bg': (12, 24, 60),
        'fg': (255, 200, 0),
        'accent': (255, 120, 10),
        'ball': (255, 120, 10)
    }
]
palette_index = 0
palette = PALETTES[palette_index]

class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.speed = PADDLE_SPEED

    def move(self, dy):
        if dy < 0:
            self.rect.y = max(self.rect.y + dy, 0)
        else:
            self.rect.y = min(self.rect.y + dy, HEIGHT - PADDLE_HEIGHT)

    def ai_move(self, target_y):
        # simple AI to follow the ball center
        center = self.rect.centery
        if center < target_y:
            self.move(self.speed)
        elif center > target_y:
            self.move(-self.speed)

    def draw(self, surf):
        pygame.draw.rect(surf, palette['fg'], self.rect)

class Ball:
    def __init__(self):
        self.rect = pygame.Rect(
            WIDTH // 2 - BALL_SIZE // 2,
            HEIGHT // 2 - BALL_SIZE // 2,
            BALL_SIZE, BALL_SIZE
        )
        self.reset()

    def reset(self, direction=None):
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        # Choose random vertical velocity and direction
        vx = BALL_SPEED if direction is None else BALL_SPEED * direction
        vy = random.choice([-1, 1]) * random.uniform(2, 4)
        self.vel = [vx, vy]
        # Slight random horizontal flip if direction not specified
        if direction is None and random.random() < 0.5:
            self.vel[0] *= -1

    def update(self, left_paddle, right_paddle):
        self.rect.x += int(self.vel[0])
        self.rect.y += int(self.vel[1])

        # Top/bottom collision
        if self.rect.top <= 0:
            self.rect.top = 0
            self.vel[1] *= -1
            play_hit_sound()
        if self.rect.bottom >= HEIGHT:
            self.rect.bottom = HEIGHT
            self.vel[1] *= -1
            play_hit_sound()

        # Paddle collisions
        if self.rect.colliderect(left_paddle.rect) and self.vel[0] < 0:
            self.rect.left = left_paddle.rect.right
            self._bounce(left_paddle)
            play_hit_sound()
        if self.rect.colliderect(right_paddle.rect) and self.vel[0] > 0:
            self.rect.right = right_paddle.rect.left
            self._bounce(right_paddle)
            play_hit_sound()

    def _bounce(self, paddle):
        # Increase speed slightly after each hit
        self.vel[0] *= -1.05
        # Adjust vertical velocity based on hit position
        offset = (self.rect.centery - paddle.rect.centery) / (PADDLE_HEIGHT / 2)
        self.vel[1] += offset * 3

    def draw(self, surf):
        pygame.draw.ellipse(surf, palette['ball'], self.rect)


def draw_center_line(surf):
    for y in range(0, HEIGHT, 20):
        pygame.draw.rect(surf, palette['accent'], (WIDTH//2 - 1, y + 4, 2, 12))

def render_score(surf, left_score, right_score):
    left_surf = font.render(str(left_score), True, palette['fg'])
    right_surf = font.render(str(right_score), True, palette['fg'])
    surf.blit(left_surf, (WIDTH//4 - left_surf.get_width()//2, 20))
    surf.blit(right_surf, (3*WIDTH//4 - right_surf.get_width()//2, 20))


def main():
    global palette_index, palette, SOUND_ON
    left = Paddle(20, HEIGHT//2 - PADDLE_HEIGHT//2)
    right = Paddle(WIDTH - 20 - PADDLE_WIDTH, HEIGHT//2 - PADDLE_HEIGHT//2)
    ball = Ball()

    left_score = 0
    right_score = 0
    serving = True
    serve_direction = random.choice([-1, 1])  # -1 left, 1 right

    running = True
    while running:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    if serving:
                        ball.reset(direction=serve_direction)
                        serving = False
                    else:
                        # restart serve state
                        serving = True
                        ball.reset(direction=serve_direction)
                elif event.key == pygame.K_c:
                    # cycle palette
                    palette_index = (palette_index + 1) % len(PALETTES)
                    palette = PALETTES[palette_index]
                elif event.key == pygame.K_m:
                    SOUND_ON = not SOUND_ON

        keys = pygame.key.get_pressed()
        # Left paddle controls (W/S)
        if keys[pygame.K_w]:
            left.move(-left.speed)
        if keys[pygame.K_s]:
            left.move(left.speed)
        # Right paddle controls (Up/Down)
        if keys[pygame.K_UP]:
            right.move(-right.speed)
        if keys[pygame.K_DOWN]:
            right.move(right.speed)

        # If serving, place ball beside the serving paddle
        if serving:
            if serve_direction < 0:
                ball.rect.right = left.rect.right + 10
                ball.rect.centery = left.rect.centery
            else:
                ball.rect.left = right.rect.left - 10 - BALL_SIZE
                ball.rect.centery = right.rect.centery

        # Update ball and check scoring
        if not serving:
            ball.update(left, right)

            if ball.rect.right < 0:
                right_score += 1
                play_score_sound()
                serving = True
                serve_direction = 1
            elif ball.rect.left > WIDTH:
                left_score += 1
                play_score_sound()
                serving = True
                serve_direction = -1

        # Draw everything
        screen.fill(palette['bg'])
        draw_center_line(screen)
        left.draw(screen)
        right.draw(screen)
        ball.draw(screen)
        render_score(screen, left_score, right_score)

        # Small instruction overlay
        instr_font = pygame.font.SysFont(None, 20)
        instr_surf = instr_font.render("W/S and Up/Down to play. Space to serve. C: change color. M: toggle sound. Esc to quit.", True, palette['fg'])
        screen.blit(instr_surf, (WIDTH//2 - instr_surf.get_width()//2, HEIGHT - 30))

        # Palette name & sound status
        status_font = pygame.font.SysFont(None, 18)
        status_surf = status_font.render(f"Palette: {palette['name']} | Sound: {'On' if SOUND_ON else 'Off'}", True, palette['accent'])
        screen.blit(status_surf, (10, HEIGHT - 24))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()