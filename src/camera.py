import pygame
import random
from src.constants import *


class Camera:
    def __init__(self):
        # punto del mundo que queremos ver justo en el centro de la pantalla
        self.focus_x = 640.0
        self.focus_y = 360.0
        self.zoom    = 1.0   # fijo, ver nota de arriba

        # screen shake: intensidad que va bajando sola cada frame
        self.shake_intensity = 0
        self.shake_decay     = 0.85

        # flash de color (rojo al recibir daño)
        self.flash_timer = 0
        self.flash_color = (255, 0, 0)
        self.flash_alpha = 0

    def update(self, player_x, player_y):
        # seguir al jugador suavecito (lerp), no pegado al pixel
        self.focus_x += (player_x - self.focus_x) * 0.15
        self.focus_y += (player_y - self.focus_y) * 0.15

        # el shake decae hasta apagarse
        self.shake_intensity *= self.shake_decay
        if self.shake_intensity < 0.5:
            self.shake_intensity = 0

        # el flash se va desvaneciendo
        if self.flash_timer > 0:
            self.flash_timer -= 1
            self.flash_alpha = int(150 * (self.flash_timer / 12))

    def world_to_screen(self, wx, wy):
        """
        Pasa coordenadas de mundo a pantalla. El focus queda centrado y todo
        se escala desde ese centro, así el zoom nunca empuja al jugador fuera
        de cuadro (cuando lo usábamos, al menos).
        """
        cx = SCREEN_W / 2
        cy = SCREEN_H / 2
        # el shake es solo un offset aleatorio chiquito mientras dura
        shake_x = random.randint(-int(self.shake_intensity), int(self.shake_intensity)) if self.shake_intensity > 0 else 0
        shake_y = random.randint(-int(self.shake_intensity), int(self.shake_intensity)) if self.shake_intensity > 0 else 0
        sx = cx + (wx - self.focus_x) * self.zoom + shake_x
        sy = cy + (wy - self.focus_y) * self.zoom + shake_y
        return int(sx), int(sy)

    def shake(self, intensity):
        # nos quedamos con el shake más fuerte para que no se "pisen"
        self.shake_intensity = max(self.shake_intensity, intensity)

    def flash(self, color=(255, 0, 0), duration=12):
        self.flash_color = color
        self.flash_timer = duration
        self.flash_alpha = 150

    def draw_flash_zone(self, surface, zone_w):
        """Para pintar el flash solo sobre la zona de juego, no sobre el HUD."""
        if self.flash_alpha > 0:
            s = pygame.Surface((zone_w, SCREEN_H), pygame.SRCALPHA)
            s.fill((*self.flash_color, self.flash_alpha))
            surface.blit(s, (0, 0))
