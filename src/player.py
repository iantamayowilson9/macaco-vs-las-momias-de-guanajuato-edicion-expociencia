import pygame
import math
import random
from src.constants import *
from src.font import get_font
from src.bullet import Bullet
from src.effects import FloatingText, BloodParticle

#  JUGADOR: MACACO
class Player:
    def __init__(self, x, y):
        self.x      = float(x)
        self.y      = float(y)
        self.hp     = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.speed  = PLAYER_BASE_SPEED
        self.coins  = 0
        self.xp     = 0
        self.xp_to_level = 100
        self.level  = 1

        self.shield_radius = SHIELD_BASE_RADIUS
        self.shield_angle  = 0.0
        self.shield_arc    = math.radians(SHIELD_ARC_DEG)

        self.damage  = 1      # daño por bala reflejada (base 1)
        self.defense = 1.0    # segundos de invencibilidad al recibir daño (base=1s)

        self.invincible_timer = 0
        self.r = 12

        self.floating_texts = []
        self.dead = False

    def gain_xp(self, amount):
        self.xp += amount
        if self.xp >= self.xp_to_level:
            self.xp -= self.xp_to_level
            self.xp_to_level = int(self.xp_to_level * 1.4)
            self.level += 1
            self.floating_texts.append(
                FloatingText("SUBISTE DE NIVEL!", self.x, self.y - 60, NEON_YELLOW, 28, 90))

    def update(self, mouse_world_x, mouse_world_y, walls):
        # Seguir al mouse
        dx = mouse_world_x - self.x
        dy = mouse_world_y - self.y
        d  = math.hypot(dx, dy)
        if d > 2:
            move = min(self.speed, d)
            self.x += (dx / d) * move
            self.y += (dy / d) * move

        # Colision con paredes
        for wall in walls:
            # Empuje
            nearest_x = max(wall.left, min(self.x, wall.right))
            nearest_y = max(wall.top,  min(self.y, wall.bottom))
            ddx = self.x - nearest_x
            ddy = self.y - nearest_y
            dist = math.hypot(ddx, ddy)
            if dist < self.r and dist > 0:
                self.x += (ddx / dist) * (self.r - dist)
                self.y += (ddy / dist) * (self.r - dist)

        # Ángulo del escudo = hacia el mouse
        self.shield_angle = math.atan2(
            mouse_world_y - self.y,
            mouse_world_x - self.x)

        if self.invincible_timer > 0:
            self.invincible_timer -= 1

    def check_bullet_collision(self, bullets, particles, floating_texts, camera):
        for b in bullets:
            if b.dead or b.owner != "enemy":
                continue
            dx = b.x - self.x
            dy = b.y - self.y
            dist = math.hypot(dx, dy)

            if dist < self.shield_radius + b.r:
                bullet_angle = math.atan2(b.y - self.y, b.x - self.x)
                angle_diff   = abs(((bullet_angle - self.shield_angle + math.pi) % math.tau) - math.pi)

                if angle_diff < self.shield_arc / 2:
                    b.vx *= -1
                    b.vy *= -1
                    b.owner = "player"
                    b.color = NEON_YELLOW
                    camera.shake(3)
                    if hasattr(camera, '_game') and camera._game:
                        camera._game.sfx.play('shield_reflect')
                    continue

            if dist < self.r + b.r:
                if self.invincible_timer <= 0:
                    self.hp -= 1
                    self.invincible_timer = int(self.defense * 60)
                    if hasattr(camera, '_game') and camera._game:
                        camera._game.sfx.play('player_hurt')
                    camera.shake(14)
                    camera.flash((255, 0, 0), 14)
                    if b.is_giant:
                        # Explosión al recibir proyectil de zombie
                        for _ in range(8):
                            particles.append(BloodParticle(b.x, b.y))
                    if self.hp <= 0:
                        self.dead = True
                b.dead = True

    def draw(self, surface, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        z = camera.zoom
        r = max(4, int(self.r * z))

        # Parpadeo de invencibilidad
        if self.invincible_timer > 0 and (self.invincible_timer // 5) % 2 == 0:
            return
        
        drawn = False
        if hasattr(camera, '_game') and camera._game:
            g = camera._game
            spr_size = max(24, int(48 * z))

            # Normalizar ángulo a [0, 360)
            ang = math.degrees(self.shield_angle) % 360

            if   ang < 22.5  or ang >= 337.5: tex_key = "player_right"
            elif ang < 67.5:                  tex_key = "player_downright"
            elif ang < 112.5:                 tex_key = "player_down"
            elif ang < 157.5:                 tex_key = "player_downleft"
            elif ang < 202.5:                 tex_key = "player_left"
            elif ang < 247.5:                 tex_key = "player_upleft"
            elif ang < 292.5:                 tex_key = "player_up"
            else:                             tex_key = "player_upright"

            drawn = g._draw_sprite(surface, tex_key, sx, sy, spr_size, spr_size, 0)
        if not drawn:
            pygame.draw.circle(surface, NEON_ORANGE, (sx, sy), r)
            pygame.draw.circle(surface, WHITE, (sx, sy), r, 2)

        sr       = max(6, int(self.shield_radius * z))
        thickness = max(3, int(8 * z))
        node_r   = max(3, int(5 * z))
        # Ángulo del escudo 
        shield_deg = math.degrees(self.shield_angle)

        shield_drawn = False
        if hasattr(camera, '_game') and camera._game:
            g = camera._game
            img = g.tex.get("shield")
            if img:
                canvas = sr * 2
                scaled = pygame.transform.scale(img, (canvas, canvas))
                rotated = pygame.transform.rotate(scaled, -shield_deg)
                # Re-centrar tras la rotación
                rect = rotated.get_rect(center=(sx, sy))
                surface.blit(rotated, rect.topleft)
                shield_drawn = True

        if not shield_drawn:
            arc_start = -(self.shield_angle + self.shield_arc / 2)
            arc_end   = -(self.shield_angle - self.shield_arc / 2)
            arc_rect  = pygame.Rect(sx - sr, sy - sr, sr * 2, sr * 2)
            pygame.draw.arc(surface, NEON_CYAN, arc_rect, arc_start, arc_end, thickness)


    def draw_hud(self, surface, font_sm, font_md, room_name="", acto_name="", font_lg=None):
        """
        HUD lateral derecho (220px) con todas las stats del jugador.
        """
        hx = HUD_X      # 1060
        hw = HUD_W      # 220
        hs = SCREEN_H   # 720
        pad = 12

        pygame.draw.rect(surface, (8, 8, 18), (hx, 0, hw, hs))
        pygame.draw.line(surface, NEON_PURPLE, (hx, 0), (hx, hs), 2)

        y = pad

        title = font_md.render("MACACO", True, NEON_ORANGE)
        surface.blit(title, (hx + hw//2 - title.get_width()//2, y))
        y += title.get_height() + 4
        sep_col = (50, 0, 80)

        def sep():
            nonlocal y
            pygame.draw.line(surface, sep_col, (hx+pad, y), (hx+hw-pad, y), 1)
            y += 6

        sep()

        hp_lbl = font_sm.render("VIDA", True, (180,180,180))
        surface.blit(hp_lbl, (hx+pad, y))
        y += hp_lbl.get_height() + 2
        heart_size = 16
        hearts_per_row = 5
        for i in range(self.max_hp):
            col = (220,20,60) if i < self.hp else (60,0,15)
            bx  = hx + pad + (i % hearts_per_row) * (heart_size + 4)
            by  = y + (i // hearts_per_row) * (heart_size + 4)
            pygame.draw.rect(surface, col, (bx, by, heart_size, heart_size))
            pygame.draw.rect(surface, WHITE, (bx, by, heart_size, heart_size), 1)
        rows = math.ceil(self.max_hp / hearts_per_row)
        y += rows * (heart_size + 4) + 4
        hp_num = font_sm.render(f"{self.hp} / {self.max_hp}", True, (220,20,60))
        surface.blit(hp_num, (hx + hw//2 - hp_num.get_width()//2, y))
        y += hp_num.get_height() + 6
        sep()

        lv_txt = font_md.render(f"NIVEL  {self.level}", True, NEON_YELLOW)
        surface.blit(lv_txt, (hx + hw//2 - lv_txt.get_width()//2, y))
        y += lv_txt.get_height() + 4

        # Barra XP
        bw = hw - pad*2
        xp_ratio = self.xp / max(1, self.xp_to_level)
        pygame.draw.rect(surface, (20,20,60),   (hx+pad, y, bw, 10))
        pygame.draw.rect(surface, NEON_BLUE,    (hx+pad, y, int(bw*xp_ratio), 10))
        pygame.draw.rect(surface, WHITE,         (hx+pad, y, bw, 10), 1)
        y += 14
        xp_lbl = font_sm.render(f"XP {self.xp}/{self.xp_to_level}", True, NEON_BLUE)
        surface.blit(xp_lbl, (hx + hw//2 - xp_lbl.get_width()//2, y))
        y += xp_lbl.get_height() + 6
        sep()

        coin_lbl = font_sm.render("MONEDAS", True, (180,180,180))
        surface.blit(coin_lbl, (hx+pad, y))
        y += coin_lbl.get_height() + 2
        coin_val = font_md.render(f"$ {self.coins}", True, NEON_YELLOW)
        surface.blit(coin_val, (hx + hw//2 - coin_val.get_width()//2, y))
        y += coin_val.get_height() + 6
        sep()


        dmg_lbl = font_sm.render("DAÑO", True, (180,180,180))
        surface.blit(dmg_lbl, (hx+pad, y))
        y += dmg_lbl.get_height() + 2
        # Barra de daño (base 1 → max ~3 con items)
        dmg_ratio = min(1.0, self.damage / 3.0)
        bw = hw - pad*2
        pygame.draw.rect(surface, (40,0,0),    (hx+pad, y, bw, 10))
        pygame.draw.rect(surface, NEON_PINK,   (hx+pad, y, int(bw*dmg_ratio), 10))
        pygame.draw.rect(surface, WHITE,        (hx+pad, y, bw, 10), 1)
        y += 12
        dmg_val = font_sm.render(f"{self.damage:.2f}x  (1 hit/bala)", True, NEON_PINK)
        surface.blit(dmg_val, (hx + hw//2 - dmg_val.get_width()//2, y))
        y += dmg_val.get_height() + 6
        sep()

        def_lbl = font_sm.render("DEFENSA", True, (180,180,180))
        surface.blit(def_lbl, (hx+pad, y))
        y += def_lbl.get_height() + 2
        # Barra de defensa (base 1s → max ~3s)
        def_ratio = min(1.0, self.defense / 3.0)
        pygame.draw.rect(surface, (0,20,60),   (hx+pad, y, bw, 10))
        pygame.draw.rect(surface, NEON_BLUE,   (hx+pad, y, int(bw*def_ratio), 10))
        pygame.draw.rect(surface, WHITE,        (hx+pad, y, bw, 10), 1)
        y += 12
        inv_frames = int(self.defense * 60)
        def_val = font_sm.render(f"{self.defense:.2f}s  ({inv_frames}f inv.)", True, NEON_BLUE)
        surface.blit(def_val, (hx + hw//2 - def_val.get_width()//2, y))
        y += def_val.get_height() + 6
        sep()

        if acto_name:
            at = font_sm.render(acto_name, True, NEON_ORANGE)
            surface.blit(at, (hx + hw//2 - at.get_width()//2, y))
            y += at.get_height() + 4
        room_lbl = font_sm.render("SALA", True, (180,180,180))
        surface.blit(room_lbl, (hx+pad, y))
        y += room_lbl.get_height() + 2
        clean = room_name.split("–")[-1].strip() if "–" in room_name else room_name
        rt = font_sm.render(clean, True, (120,120,200))
        surface.blit(rt, (hx + hw//2 - rt.get_width()//2, y))
        y += rt.get_height() + 4
        sep()

        controls = [("MOUSE","Mover + Escudo"),("R","Reiniciar"),("ESC","Salir")]
        return y

    def draw_minimap(self, surface, rooms, current_room_idx, font_sm, start_y=None):
        hx, hw, pad = HUD_X, HUD_W, 12
        mm_y = (start_y + 8) if start_y is not None else SCREEN_H - 130
        if mm_y + 80 > SCREEN_H:
            return
        lbl = font_sm.render("MAPA RUN", True, (180, 180, 180))
        surface.blit(lbl, (hx + pad, mm_y))
        mm_y += lbl.get_height() + 4
        pygame.draw.line(surface, (50, 0, 80),
                         (hx + pad, mm_y), (hx + hw - pad, mm_y), 1)
        mm_y += 4
        if not rooms:
            return
        cell, gap = 14, 3
        positions = [r["grid_pos"] for r in rooms]
        min_gx = min(pos[0] for pos in positions)
        min_gy = min(pos[1] for pos in positions)
        for i, room in enumerate(rooms):
            gx, gy = room["grid_pos"]
            rx = hx + pad + (gx - min_gx) * (cell + gap)
            ry = mm_y    + (gy - min_gy) * (cell + gap)
            if ry + cell > SCREEN_H - 4:
                continue
            is_boss    = room.get("is_boss", False)
            is_current = (i == current_room_idx)
            is_cleared = room.get("cleared", False)
            if is_current:
                col = (255, 200, 0)
            elif is_cleared:
                col = (0, 180, 80)
            elif is_boss:
                col = (200, 0, 80)
            else:
                col = (80, 80, 120)
            pygame.draw.rect(surface, col, (rx, ry, cell, cell), border_radius=2)
            pygame.draw.rect(surface, (0, 0, 0), (rx, ry, cell, cell), 1, border_radius=2)

