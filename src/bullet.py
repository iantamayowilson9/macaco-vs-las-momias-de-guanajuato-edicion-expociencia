import pygame
import math
import random
from src.constants import *
from src.font import get_font

#  PROYECTIL
class Bullet:
    def __init__(self, x, y, vx, vy, r=6, color=NEON_GREEN,
                 owner="enemy", bounces=0, homing=False, is_giant=False):
        self.x       = float(x)
        self.y       = float(y)
        self.vx      = float(vx)
        self.vy      = float(vy)
        self.r       = r
        self.color   = color
        self.owner   = owner   # "enemy" o "player"
        self.bounces_left = bounces
        self.homing  = homing
        self.is_giant= is_giant
        self.dead    = False
        self.trail   = []

    def update(self, walls, player=None):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 6:
            self.trail.pop(0)

        if self.homing and player:
            dx = player.x - self.x
            dy = player.y - self.y
            d  = math.hypot(dx, dy) or 1
            self.vx += (dx/d) * 0.04
            self.vy += (dy/d) * 0.04
            sp = math.hypot(self.vx, self.vy)
            if sp > 3.5:
                self.vx = self.vx/sp * 3.5
                self.vy = self.vy/sp * 3.5

        self.x += self.vx
        self.y += self.vy

        # Rebote en paredes del mapa
        for wall in walls:
            if wall.collidepoint(self.x, self.y):
                if self.bounces_left > 0:
                    # Determinar rebote eje X o Y
                    if (abs(self.x - wall.left) < 8 or abs(self.x - wall.right) < 8):
                        self.vx *= -1
                    else:
                        self.vy *= -1
                    self.bounces_left -= 1
                    self.x += self.vx
                    self.y += self.vy
                else:
                    self.dead = True

    def draw(self, surface, camera):
        # Trail
        for i, (tx, ty) in enumerate(self.trail):
            alpha_r = max(1, int(self.r * (i/len(self.trail)) * camera.zoom * 0.7))
            tsx, tsy = camera.world_to_screen(tx, ty)
            pygame.draw.circle(surface, self.color, (tsx, tsy), alpha_r)
        sx, sy = camera.world_to_screen(self.x, self.y)
        r = max(2, int(self.r * camera.zoom))
        
        try:
            pygame.gfxdraw.aacircle(surface, sx, sy, r+3, (0,0,0))
            pygame.gfxdraw.filled_circle(surface, sx, sy, r+3, (0,0,0))
            pygame.gfxdraw.aacircle(surface, sx, sy, r, self.color)
            pygame.gfxdraw.filled_circle(surface, sx, sy, r, self.color)
        except Exception:
            pygame.draw.circle(surface, (0,0,0), (sx, sy), r+3)
            pygame.draw.circle(surface, self.color, (sx, sy), r)



