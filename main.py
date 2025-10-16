# A simple Pong game using Pygame
# Controls:
# - Left paddle: W (up), S (down)
# - Right paddle: Up Arrow, Down Arrow
# - Space: restart / serve after score
# - Esc or window close: quit

import pygame
import sys
import random

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

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

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
        pygame.draw.rect(surf, WHITE, self.rect)

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
        if self.rect.bottom >= HEIGHT:
            self.rect.bottom = HEIGHT
            self.vel[1] *= -1

        # Paddle collisions
        if self.rect.colliderect(left_paddle.rect) and self.vel[0] < 0:
            self.rect.left = left_paddle.rect.right
            self._bounce(left_paddle)
        if self.rect.colliderect(right_paddle.rect) and self.vel[0] > 0:
            self.rect.right = right_paddle.rect.left
            self._bounce(right_paddle)

    def _bounce(self, paddle):
        # Increase speed slightly after each hit
        self.vel[0] *= -1.05
        # Adjust vertical velocity based on hit position
        offset = (self.rect.centery - paddle.rect.centery) / (PADDLE_HEIGHT / 2)
        self.vel[1] += offset * 3

    def draw(self, surf):
        pygame.draw.ellipse(surf, WHITE, self.rect)

def draw_center_line(surf):
    for y in range(0, HEIGHT, 20):
        pygame.draw.rect(surf, WHITE, (WIDTH//2 - 1, y + 4, 2, 12))

def render_score(surf, left_score, right_score):
    left_surf = font.render(str(left_score), True, WHITE)
    right_surf = font.render(str(right_score), True, WHITE)
    surf.blit(left_surf, (WIDTH//4 - left_surf.get_width()//2, 20))
    surf.blit(right_surf, (3*WIDTH//4 - right_surf.get_width()//2, 20))

def main():
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
                serving = True
                serve_direction = 1
            elif ball.rect.left > WIDTH:
                left_score += 1
                serving = True
                serve_direction = -1

        # Simple AI for right paddle when no player input (optional)
        # Uncomment the following to have the right paddle controlled by AI:
        # right.ai_move(ball.rect.centery)

        # Draw everything
        screen.fill(BLACK)
        draw_center_line(screen)
        left.draw(screen)
        right.draw(screen)
        ball.draw(screen)
        render_score(screen, left_score, right_score)

        # Small instruction overlay
        instr_font = pygame.font.SysFont(None, 20)
        instr_surf = instr_font.render("W/S and Up/Down to play. Space to serve. Esc to quit.", True, WHITE)
        screen.blit(instr_surf, (WIDTH//2 - instr_surf.get_width()//2, HEIGHT - 30))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()