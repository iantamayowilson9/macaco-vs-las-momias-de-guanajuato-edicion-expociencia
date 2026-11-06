import pygame
import math
import random
from src.constants import *


class Coin:
    """
    Moneda que sueltan los enemigos al morir. Si nadie la junta,
    se borra sola
    """
    def __init__(self, x, y, value=1):
        self.x     = float(x)
        self.y     = float(y)
        self.vx    = random.uniform(-2, 2)
        self.vy    = random.uniform(-3, -1)
        self.value = value
        self.r     = 7
        self.dead  = False
        self.timer = 300   # ~5 seg a 60fps antes de desaparecer

    def update(self, player):
        # cae y va frenando en horizontal
        self.vy += 0.15
        self.vx *= 0.95
        self.x  += self.vx
        self.y  += self.vy

        # tope para que no se caiga al infinito
        if self.y > player.y + 500:
            self.y = player.y + 500

        self.timer -= 1
        if self.timer <= 0:
            self.dead = True

        # si el jugador esta cerca, la recoge
        dx = player.x - self.x
        dy = player.y - self.y
        if math.hypot(dx, dy) < 30:
            player.coins += self.value
            self.dead = True

    def draw(self, surface, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        r = max(3, int(self.r * camera.zoom))
        pygame.draw.circle(surface, NEON_YELLOW, (sx, sy), r)
        pygame.draw.circle(surface, WHITE, (sx, sy), r, 1)   # borde blanco
