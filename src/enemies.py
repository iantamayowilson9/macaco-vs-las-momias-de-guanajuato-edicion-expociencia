import pygame
import math
import random
from src.constants import *
from src.font import get_font
from src.bullet import Bullet
from src.effects import BloodParticle


class EnemyBase:
    NAME = "Enemigo"   # cada subclase pone el suyo

    def __init__(self, x, y, hp, speed, xp, color, r=14):
        self.x      = float(x)
        self.y      = float(y)
        self.hp     = hp
        self.max_hp = hp
        self.speed  = speed
        self.xp     = xp           # cuánta XP suelta al morir
        self.color  = color
        self.r      = r
        self.dead   = False
        self.shoot_timer = 0
        self.shoot_cd    = 120     # frames entre disparos
        self.stun_timer  = 0

    def _dir_key(self, tex_prefix, target_x, target_y):
        """
        Devuelve la clave del sprite según el ángulo hacia el objetivo.
        Es el mismo truco de las 8 direcciones que uso para el jugador:
        parto el círculo en 8 sectores de 45° y elijo el que toca.
        """
        ang = math.degrees(math.atan2(target_y - self.y, target_x - self.x)) % 360
        if   ang < 22.5  or ang >= 337.5: suffix = "_right"
        elif ang < 67.5:                  suffix = "_downright"
        elif ang < 112.5:                 suffix = "_down"
        elif ang < 157.5:                 suffix = "_downleft"
        elif ang < 202.5:                 suffix = "_left"
        elif ang < 247.5:                 suffix = "_upleft"
        elif ang < 292.5:                 suffix = "_up"
        else:                             suffix = "_upright"
        return tex_prefix + suffix

    def _draw_tex_or_circle(self, surface, camera, tex_prefix, color, r_world,
                            target_x=None, target_y=None):
        """
        Dibuja el sprite del enemigo mirando hacia el jugador
        Devuelve (sx, sy, r) por si el caller quiere dibujar algo encima
        """
        sx, sy = camera.world_to_screen(self.x, self.y)
        z = camera.zoom
        r = max(4, int(r_world * z))
        spr = max(r * 2, int(60 * z))
        drawn = False

        if hasattr(camera, '_game') and camera._game:
            g = camera._game
            if target_x is not None and target_y is not None:
                key = self._dir_key(tex_prefix, target_x, target_y)
            else:
                key = tex_prefix + "_down"
            img = g.tex.get(key) or g.tex.get(tex_prefix)
            if img:
                scaled = pygame.transform.scale(img, (spr, spr))
                surface.blit(scaled, (sx - spr // 2, sy - spr // 2))
                drawn = True

        if not drawn:
            pygame.draw.circle(surface, color, (sx, sy), r)
            pygame.draw.circle(surface, WHITE, (sx, sy), r, 2)
        return sx, sy, r

    def take_damage(self, dmg, particles, floating_texts, camera):
        self.hp -= dmg
        camera.shake(5)
        # chorrito de sangre
        for _ in range(random.randint(10, 15)):
            particles.append(BloodParticle(self.x, self.y))
        if self.hp <= 0:
            self.dead = True

    def _collide_walls(self, walls):
        """Lo empuja fuera de cualquier pared. Mismo metodo que usamos con el jugador."""
        for wall in walls:
            nearest_x = max(wall.left, min(self.x, wall.right))
            nearest_y = max(wall.top,  min(self.y, wall.bottom))
            ddx = self.x - nearest_x
            ddy = self.y - nearest_y
            dist = math.hypot(ddx, ddy)
            if 0 < dist < self.r:
                self.x += (ddx / dist) * (self.r - dist + 1)
                self.y += (ddy / dist) * (self.r - dist + 1)

    def _draw_hp_bar(self, surface, camera):
        """Texto de Nombre + barrita de vida encima del enemigo."""
        sx, sy = camera.world_to_screen(self.x, self.y)
        z   = camera.zoom
        r_s = max(4, int(self.r * z))
        bw  = max(18, int(self.r * 1.8 * z))
        bh  = max(2, int(3 * z))
        ratio = max(0, self.hp / self.max_hp)

        nf  = get_font(max(7, int(10 * z)))
        lbl = nf.render(self.NAME, True, self.color)

        name_y = sy - r_s - lbl.get_height() - bh - 30
        bar_y  = name_y + lbl.get_height() + 2

        surface.blit(lbl, (sx - lbl.get_width() // 2, name_y))
        pygame.draw.rect(surface, DARK_RED,   (sx - bw // 2, bar_y, bw, bh))
        pygame.draw.rect(surface, NEON_GREEN, (sx - bw // 2, bar_y, int(bw * ratio), bh))


class Momia(EnemyBase):
    """Lenta, aguanta 3 golpes y tira rafagas de balas rectas."""
    NAME = "Momia de Guanajuato"

    def __init__(self, x, y):
        super().__init__(x, y, hp=3, speed=1.2, xp=10, color=NEON_GREEN, r=13)
        self.shoot_cd   = 180
        self.move_timer = 90   # avanza un rato, descansa otro rato

    def update(self, player, bullets, walls):
        if self.stun_timer > 0:
            self.stun_timer -= 1
            return

        # camina hacia el jugador a tirones (avanza 90 frames, se detiene, repite)
        self.move_timer -= 1
        if self.move_timer > 0:
            dx = player.x - self.x
            dy = player.y - self.y
            d  = math.hypot(dx, dy) or 1
            self.x += (dx / d) * self.speed
            self.y += (dy / d) * self.speed
        elif self.move_timer < -60:
            self.move_timer = 90

        # dispara hacia el jugador
        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_cd:
            self.shoot_timer = 0
            dx = player.x - self.x
            dy = player.y - self.y
            d  = math.hypot(dx, dy) or 1
            speed = 5.5
            for _ in range(3):
                bullets.append(Bullet(self.x, self.y,
                                      dx / d * speed, dy / d * speed,
                                      r=6, color=NEON_GREEN))
        self._collide_walls(walls)

    def draw(self, surface, camera):
        px = camera._game.player.x if (hasattr(camera, '_game') and camera._game) else self.x
        py = camera._game.player.y if (hasattr(camera, '_game') and camera._game) else self.y
        sx, sy, r = self._draw_tex_or_circle(surface, camera, "momia", self.color, self.r, px, py)
        z = camera.zoom
        
        for i in range(3):
            a  = i * (math.pi / 1.5)
            ex = sx + int(math.cos(a) * r * 0.8)
            ey = sy + int(math.sin(a) * r * 0.8)
            pygame.draw.line(surface, (200, 200, 180), (sx, sy), (ex, ey), max(1, int(2 * z)))
        self._draw_hp_bar(surface, camera)


class Zombi(EnemyBase):
    """
    Lanza una bala grande con homing que te persigue. Pero si la reflejas, esa misma bala explota y daña a todo
    enemigo cercano
    """
    NAME = "Zombi"

    def __init__(self, x, y):
        super().__init__(x, y, hp=2, speed=2.5, xp=15, color=NEON_PINK, r=13)
        self.shoot_cd = 200
        self.angle    = random.uniform(0, math.tau)
        self.erratic  = random.uniform(0.04, 0.1)  

    def update(self, player, bullets, walls):
        if self.stun_timer > 0:
            self.stun_timer -= 1
            return

        dx = player.x - self.x
        dy = player.y - self.y
        target_angle = math.atan2(dy, dx)
        self.angle += (target_angle - self.angle) * 0.08
        self.angle += random.uniform(-self.erratic, self.erratic)
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_cd:
            self.shoot_timer = 0
            dx = player.x - self.x
            dy = player.y - self.y
            d  = math.hypot(dx, dy) or 1
            # bala lenta, grande, con homing y que explota
            bullets.append(Bullet(self.x, self.y, dx / d * 2.5, dy / d * 2.5,
                                  r=14, color=NEON_PINK, homing=True, is_giant=True))
        self._collide_walls(walls)

    def draw(self, surface, camera):
        px = camera._game.player.x if (hasattr(camera, '_game') and camera._game) else self.x
        py = camera._game.player.y if (hasattr(camera, '_game') and camera._game) else self.y
        self._draw_tex_or_circle(surface, camera, "zombi", self.color, self.r, px, py)
        self._draw_hp_bar(surface, camera)


class PescadoMutante(EnemyBase):
    """Tira un abanico de 3 balas que rebotan 2 veces en las paredes"""
    NAME = "Pescado Mutante"

    def __init__(self, x, y):
        super().__init__(x, y, hp=2, speed=1.8, xp=20, color=NEON_CYAN, r=14)
        self.shoot_cd = 150

    def update(self, player, bullets, walls):
        if self.stun_timer > 0:
            self.stun_timer -= 1
            return

        # te persigue de frente
        dx = player.x - self.x
        dy = player.y - self.y
        d  = math.hypot(dx, dy) or 1
        self.x += (dx / d) * self.speed
        self.y += (dy / d) * self.speed

        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_cd:
            self.shoot_timer = 0
            base = math.atan2(player.y - self.y, player.x - self.x)
            for spread in (-0.25, 0, 0.25):
                a = base + spread
                bullets.append(Bullet(self.x, self.y,
                                      math.cos(a) * 4.5, math.sin(a) * 4.5,
                                      r=7, color=NEON_CYAN, bounces=2))
        self._collide_walls(walls)

    def draw(self, surface, camera):
        px = camera._game.player.x if (hasattr(camera, '_game') and camera._game) else self.x
        py = camera._game.player.y if (hasattr(camera, '_game') and camera._game) else self.y
        self._draw_tex_or_circle(surface, camera, "pescado", self.color, self.r, px, py)
        self._draw_hp_bar(surface, camera)


class EsqueletoRumbero(EnemyBase):
    """
    desde lejos te suelta escopetazos de 5 balas y aguanta 4 golpes
    """
    NAME = "Esqueleto Rumbero"

    def __init__(self, x, y):
        super().__init__(x, y, hp=4, speed=1.0, xp=25, color=NEON_ORANGE, r=14)
        self.shoot_cd     = 140
        self.retreat_dist = 260   # distancia a la que intenta quedarse

    def update(self, player, bullets, walls):
        if self.stun_timer > 0:
            self.stun_timer -= 1
            return

        dx = player.x - self.x
        dy = player.y - self.y
        d  = math.hypot(dx, dy) or 1
        # demasiado cerca -> huye; si no, se acerca lento
        if d < self.retreat_dist:
            self.x -= (dx / d) * self.speed
            self.y -= (dy / d) * self.speed
        else:
            self.x += (dx / d) * self.speed * 0.5
            self.y += (dy / d) * self.speed * 0.5

        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_cd:
            self.shoot_timer = 0
            base = math.atan2(dy, dx)
            for i in range(5):
                a = base + (i - 2) * 0.18   # escopetazo centrado
                bullets.append(Bullet(self.x, self.y,
                                      math.cos(a) * 5.5, math.sin(a) * 5.5,
                                      r=6, color=NEON_ORANGE))
        self._collide_walls(walls)

    def draw(self, surface, camera):
        px = camera._game.player.x if (hasattr(camera, '_game') and camera._game) else self.x
        py = camera._game.player.y if (hasattr(camera, '_game') and camera._game) else self.y
        self._draw_tex_or_circle(surface, camera, "esqueleto", self.color, self.r, px, py)
        self._draw_hp_bar(surface, camera)


class CthulhuDJ(EnemyBase):
    """
    Jefe final. Tiene 40 de vida. Orbita mientras tira balas en patrón circular.
    Tiene dos fases: al bajar del 50% de vida dispara más
    seguido y suma una espiral rosa encima del círculo morado
    """
    NAME = "Cthulhu DJ Sonidero"

    def __init__(self, x, y):
        super().__init__(x, y, hp=40, speed=1.0, xp=200, color=NEON_PURPLE, r=60)
        self.phase      = 1
        self.angle      = 0.0   # rotación del patrón circular
        self.spiral_arm = 0.0   # rotación de la espiral de fase 2

    def update(self, player, bullets, walls):
        if self.stun_timer > 0:
            self.stun_timer -= 1
            return

        # se acerca un poco pero da vueltas (componente perpendicular)
        dx = player.x - self.x
        dy = player.y - self.y
        d  = math.hypot(dx, dy) or 1
        perp_x, perp_y = -dy / d, dx / d
        self.x += (dx / d) * self.speed * 0.4 + perp_x * 0.6
        self.y += (dy / d) * self.speed * 0.4 + perp_y * 0.6
        self._collide_walls(walls)

        # cambio de fase cuando le baja la vida
        if self.hp < self.max_hp * 0.5:
            self.phase = 2

        self.shoot_timer += 1
        cd = 30 if self.phase == 2 else 50
        if self.shoot_timer >= cd:
            self.shoot_timer = 0
            # patrón circular: N balas repartidas en 360°
            num = 16 if self.phase == 2 else 10
            for i in range(num):
                a = self.angle + (math.tau / num) * i
                bullets.append(Bullet(self.x, self.y,
                                      math.cos(a) * 3.5, math.sin(a) * 3.5,
                                      r=8, color=NEON_PURPLE))
            self.angle += 0.3   # giro un poco el patrón cada vez

            # fase 2: espiral rosa extra
            if self.phase == 2:
                for i in range(8):
                    a = self.spiral_arm + (math.tau / 8) * i
                    bullets.append(Bullet(self.x, self.y,
                                          math.cos(a) * 4.5, math.sin(a) * 4.5,
                                          r=7, color=NEON_PINK))
                self.spiral_arm += 0.18

    def draw(self, surface, camera):
        z = camera.zoom
        r = max(8, int(self.r * z))
        px = camera._game.player.x if (hasattr(camera, '_game') and camera._game) else self.x
        py = camera._game.player.y if (hasattr(camera, '_game') and camera._game) else self.y
        sx, sy, r2 = self._draw_tex_or_circle(surface, camera, "cthulhu", NEON_PURPLE, self.r, px, py)

        # barra de vida gorda con su nombre
        bw = max(40, int(r2 * 3 * z))
        bh = max(6, int(8 * z))
        ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(surface, DARK_RED,    (sx - bw // 2, sy - r2 - bh - 6, bw, bh))
        pygame.draw.rect(surface, NEON_PURPLE, (sx - bw // 2, sy - r2 - bh - 6, int(bw * ratio), bh))
        font = get_font(max(8, int(13 * z)), bold=True)
        lbl  = font.render("CTHULHU DJ SONIDERO", True, NEON_YELLOW)
        surface.blit(lbl, (sx - lbl.get_width() // 2, sy - r2 - bh - 22))
