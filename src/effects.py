import pygame
import math
import random
from src.constants import *
from src.font import get_font

#  TEXTO NEÓN
class FloatingText:
    def __init__(self, text, x, y, color=NEON_YELLOW, size=22, duration=55):
        self.text     = text
        self.x        = float(x)
        self.y        = float(y)
        self.color    = color
        self.size     = size
        self.duration = duration
        self.timer    = duration
        self.vy       = -1.8
        self.font     = pygame.font.SysFont("consolas", size, bold=True)
        self.dead     = False

    def update(self):
        self.y     += self.vy
        self.timer -= 1
        if self.timer <= 0:
            self.dead = True

    def draw(self, surface, camera):
        alpha = max(0, int(255 * (self.timer / self.duration)))
        sx, sy = camera.world_to_screen(self.x, self.y)
        img = self.font.render(self.text, True, self.color)
        img.set_alpha(alpha)
        surface.blit(img, (sx - img.get_width() // 2, sy))


#  PARTÍCULAS DE SANGRE
class BloodParticle:
    def __init__(self, x, y):
        self.x    = float(x)
        self.y    = float(y)
        angle     = random.uniform(0, math.tau)
        speed     = random.uniform(1.5, 5.0)
        self.vx   = math.cos(angle) * speed
        self.vy   = math.sin(angle) * speed
        self.r    = random.randint(2, 5)
        self.color = random.choice([(220,0,0),(255,30,30),(180,0,0)])
        self.alive= True
        self.static = False  # cuando para, se queda pintado en el suelo

    def update(self):
        if not self.static:
            self.vx *= 0.88
            self.vy *= 0.88
            self.x  += self.vx
            self.y  += self.vy
            if abs(self.vx) < 0.2 and abs(self.vy) < 0.2:
                self.static = True

    def draw(self, surface, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        r = max(1, int(self.r * camera.zoom))
        pygame.draw.circle(surface, (0,0,0), (sx, sy), r+1)
        pygame.draw.circle(surface, self.color, (sx, sy), r)



