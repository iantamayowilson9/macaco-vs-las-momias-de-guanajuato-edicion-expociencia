import pygame
import math
import random
from src.constants import *
from src.font import get_font
from src.camera import Camera
from src.effects import FloatingText, BloodParticle
from src.items import Coin
from src.door import Door
from src.bullet import Bullet
from src.enemies import Momia, Zombi, PescadoMutante, EsqueletoRumbero, CthulhuDJ
from src.player import Player
from src.rooms import generate_map
from src.music import MusicPlayer
from src.sound import SoundSystem


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.get_surface() or pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.SCALED | pygame.FULLSCREEN)
        pygame.display.set_caption("Macaco vs. Las Momias de Guanajuato")
        self.clock  = pygame.time.Clock()
        self.music  = MusicPlayer()   # la música arranca en start_game()
        self.sfx    = SoundSystem()

        # fuentes para HUD, títulos
        self.font_sm = get_font(14, bold=True)
        self.font_md = get_font(20, bold=True)
        self.font_lg = get_font(36, bold=True)
        self.font_xl = get_font(64, bold=True)

        self.camera = Camera()
        self.rooms  = []        # se llena al empezar cada run
        self.estado = "MENU"

        # estas listas se vacían/llenan al cargar cada cuarto
        self.enemies        = []
        self.bullets        = []
        self.coins          = []
        self.particles      = []
        self.floating_texts = []
        self.doors          = []
        self.walls          = []

        self.player        = None
        self.current_room  = 0
        self.clear_triggered    = False   
        self._room_enemy_count  = 0       # enemigos al inicio del cuarto

        self.stars = [(random.randint(0, SCREEN_W), random.randint(0, SCREEN_H),
                       random.randint(1, 3), random.random()) for _ in range(120)]

        self.menu_bg_tick = 0
        self.run_number   = 0
        self._disco_tick  = 0
        self._scanline_surf = None
        self._frame_cache   = None

        # frames del GIF de muerte
        self._death_frames      = []
        self._death_frame_idx   = 0
        self._death_frame_timer = 0

        self.tex = self._load_textures()

  
    #  TEXTURAS
    def _load_textures(self):
        """
        Carga todos los PNG
        """
        import os
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        def load(filename):
            try:
                return pygame.image.load(os.path.join(base, "assets", "sprites", filename)).convert_alpha()
            except Exception:
                return None

        t = {}

        # pisos del antro (rotan por cuarto) + fondo
        for i in range(1, 8):
            t[f"floor_antro_{i}"] = load(f"floor_antro_{i}.png")
        t["background_antro"] = load("background_antro.png")

        # paredes y obstáculos (se tesela la imagen dentro del rect)
        t["wall_antro"]     = load("wall_antro.png")
        t["obstacle_antro"] = load("obstacle_antro.png")

        # jugador: 8 direcciones
        for d in ["up", "down", "left", "right", "upleft", "upright", "downleft", "downright"]:
            t[f"player_{d}"] = load(f"player_{d}.png")

        # escudo: PNG apuntando a la derecha, el juego lo rota hacia el mouse
        t["shield"] = load("shield.png")

        # enemigos: mismo sistema de 8 direcciones que el jugador
        for prefix in ["momia", "zombi", "pescado", "esqueleto"]:
            for d in ["up", "down", "left", "right", "upleft", "upright", "downleft", "downright"]:
                t[f"{prefix}_{d}"] = load(f"{prefix}_{d}.png")

        # jefe: un solo sprite
        t["cthulhu"] = load("cthulhu.png")

        # marco decorativo del gameplay
        t["game_frame"] = load("game_frame.png")

        # animación de muerte: todos los PNG dentro de assets/sprites/death/
        import glob
        death_dir = os.path.join(base, "assets", "sprites", "death")
        files = sorted(glob.glob(os.path.join(death_dir, "*.png")) +
                       glob.glob(os.path.join(death_dir, "*.PNG")))
        self._death_frames = []
        for f in files:
            try:
                img = pygame.image.load(f).convert_alpha()
                self._death_frames.append(pygame.transform.scale(img, (SCREEN_W, SCREEN_H)))
            except Exception as e:
                print(f"[Muerte] no pude cargar {f}: {e}")
        print(f"[Muerte] {len(self._death_frames)} frames cargados")

        return t

    def _draw_sprite(self, surface, tex_key, sx, sy, w, h, angle=0):
        """
        Dibuja una textura ya escalada en pantalla.
        """
        img = self.tex.get(tex_key)
        if img is None:
            return False
        scaled = pygame.transform.scale(img, (max(1, w), max(1, h)))
        if angle != 0:
            scaled = pygame.transform.rotate(scaled, -angle)
            surface.blit(scaled, scaled.get_rect(center=(sx, sy)).topleft)
        else:
            surface.blit(scaled, (sx - w // 2, sy - h // 2))
        return True


    #  CARGAR / REINICIAR CUARTOS
    def load_room(self, room_idx, from_door=None):
        room = self.rooms[room_idx]
        self.current_room = room_idx
        self.walls        = room["walls"]
        self.bg_color     = room["bg_color"]

        if self.player is None:
            self.player = Player(room["spawn_x"], room["spawn_y"])
        elif from_door:
            side  = from_door.side
            ox    = room.get("world_ox", 0)
            oy    = room.get("world_oy", 0)
            inset = WALL_T + 200
            if side == 'right':    px, py = ox + inset,      oy + RH // 2
            elif side == 'left':   px, py = ox + RW - inset, oy + RH // 2
            elif side == 'bottom': px, py = ox + RW // 2,    oy + inset
            else:                  px, py = ox + RW // 2,    oy + RH - inset
            self.player.x, self.player.y = float(px), float(py)
            self.player.hp = max(1, self.player.hp)
        else:
            self.player.x = float(room["spawn_x"])
            self.player.y = float(room["spawn_y"])

        self.player.floating_texts = self.floating_texts

        # limpio lo que es por-cuarto
        self.bullets   = []
        self.coins     = []
        self.particles = []

        # si la sala ya estaba limpia (o es el inicio), no se re-spawnean enemigos
        if room.get("cleared", False) or room.get("is_start", False):
            self.enemies = []
            self.clear_triggered = True
        else:
            self.enemies = room["spawn_enemies"](room)
            self.clear_triggered = False

        self._room_enemy_count = len(self.enemies)

        # clono las puertas. Inicio o sala limpia -> ya vienen abiertas.
        self.doors = []
        for d in room["doors"]:
            nd = Door(d.x, d.y, d.side, d.target_room)
            if room.get("is_start", False) or room.get("cleared", False):
                nd.open = True
            self.doors.append(nd)

    def restart_current_room(self):
        """Reinicio (tecla R): cura, re-spawnea enemigos y limpia todo."""
        room = self.rooms[self.current_room]
        self.player.hp   = PLAYER_MAX_HP
        self.player.dead = False
        self.player.invincible_timer = 0
        self.player.x = float(room["spawn_x"])
        self.player.y = float(room["spawn_y"])
        self.enemies        = room["spawn_enemies"](room)
        self.bullets        = []
        self.coins          = []
        self.particles      = []
        self.floating_texts = []
        self.player.floating_texts = self.floating_texts

        self.doors = []
        for d in room["doors"]:
            nd = Door(d.x, d.y, d.side, d.target_room)
            if room.get("is_start", False):
                nd.open = True
            self.doors.append(nd)

        self.clear_triggered   = False
        self._room_enemy_count = len(self.enemies)
        self.camera.shake_intensity = 0
        self.camera.flash_timer     = 0
        self.music.unpause()   # por si veníamos de la pantalla de muerte
        self._go_armed = False
        self._go_was_down = True
        self.estado = "GAMEPLAY"


    #  COORDENADAS
    def screen_to_world(self, sx, sy):
        """Pantalla -> mundo. Es la inversa exacta de world_to_screen"""
        cx, cy = SCREEN_W / 2, SCREEN_H / 2
        wx = (sx - cx) / self.camera.zoom + self.camera.focus_x
        wy = (sy - cy) / self.camera.zoom + self.camera.focus_y
        return wx, wy


    #  DIBUJO DEL FONDO Y PAREDES
    def draw_background(self):
        self.screen.fill(BLACK)

        room   = self.rooms[self.current_room]
        ox     = room.get("world_ox", 0)
        oy     = room.get("world_oy", 0)
        # esquinas del interior (sin contar las paredes exteriores)
        min_wx, max_wx = ox + WALL_T, ox + RW - WALL_T
        min_wy, max_wy = oy + WALL_T, oy + RH - WALL_T
        world_w, world_h = max_wx - min_wx, max_wy - min_wy

        sx1, sy1 = self.camera.world_to_screen(min_wx, min_wy)
        z = self.camera.zoom
        pw, ph = int(world_w * z), int(world_h * z)

        # clipeo a la zona de juego para no pintar encima del HUD
        self.screen.set_clip(pygame.Rect(0, 0, GAME_ZONE_W, SCREEN_H))

        floor_img = self.tex.get(room.get("floor_key"))
        if floor_img:
            cache_key = (room.get("floor_key"), pw, ph)
            if self._floor_cache[0] != cache_key:
                self._floor_cache = (cache_key, pygame.transform.scale(floor_img, (max(1, pw), max(1, ph))))
            self.screen.blit(self._floor_cache[1], (sx1, sy1))
        else:
            # sin textura: piso morado
            v = int(abs(math.sin(self._disco_tick * 0.015)) * 30)
            pygame.draw.rect(self.screen, (5 + v, 0, 20 + v * 2), (sx1, sy1, pw, ph))

        self.screen.set_clip(None)

    def draw_walls(self):
        wall_img = self.tex.get("wall_antro")
        obs_img  = self.tex.get("obstacle_antro")
        z = self.camera.zoom

        # colores de relleno cuando no hay textura
        wall_fill = (28, 18, 48)
        obs_fill  = (35, 22, 58)

        def draw_tiled(img, sx, sy, rw, rh):
            tw, th = img.get_width(), img.get_height()
            self.screen.set_clip(pygame.Rect(sx, sy, rw, rh))
            for ty in range(sy, sy + rh, th):
                for tx in range(sx, sx + rw, tw):
                    self.screen.blit(img, (tx, ty))
            self.screen.set_clip(None)

        def draw_block(sx, sy, rw, rh, img, fill):
            if rw < 2 or rh < 2:
                return
            if img:
                draw_tiled(img, sx, sy, rw, rh)
            else:
                pygame.draw.rect(self.screen, fill, (sx, sy, rw, rh))
            pygame.draw.rect(self.screen, (0, 0, 0), (sx, sy, rw, rh), max(2, int(6 * z)))

        for wall in self.walls:
            sx, sy = self.camera.world_to_screen(wall.x, wall.y)
            rw = max(2, int(wall.w * z))
            rh = max(2, int(wall.h * z))
            # distingo pared exterior (delgada o muy larga) de obstáculo interior
            is_outer = (wall.w == WALL_T or wall.h == WALL_T or
                        wall.w >= int(RW * 0.7) or wall.h >= int(RH * 0.7))
            if is_outer:
                draw_block(sx, sy, rw, rh, wall_img, wall_fill)
            else:
                draw_block(sx, sy, rw, rh, obs_img or wall_img, obs_fill)


    #  BUCLE PRINCIPAL (modo standalone con run())
    def run(self):
        while True:
            self.clock.tick(FPS)
            self._handle_events_internal()

            if self.estado == "MENU":
                self._update_menu(); self._draw_menu()
            elif self.estado == "GAMEPLAY":
                self._update_gameplay(); self._draw_gameplay()
            elif self.estado == "PAUSED":
                self._draw_gameplay(); self._draw_pause()
            elif self.estado == "GAME_OVER":
                self._draw_game_over()
            elif self.estado == "VICTORY":
                self._draw_victory()

            pygame.display.flip()


    #  EVENTOS
    def _process_single_event(self, event):
        """Maneja una sola tecla. Pausa, reinicio, salir de pausa, etc."""
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_ESCAPE, pygame.K_p):
            if self.estado == "GAMEPLAY":
                self.estado = "PAUSED"; self.music.pause()
            elif self.estado == "PAUSED":
                self.estado = "GAMEPLAY"; self.music.unpause()

        if event.key == pygame.K_m and self.estado == "PAUSED":
            self.music.stop()
            self.quit_to_menu = True      # main.py lo detecta y regresa al menú

        if self.estado in ("GAMEPLAY", "PAUSED"):
            if event.key == pygame.K_n:
                self.music.siguiente(); self._radio_toast = 150
            elif event.key == pygame.K_b:
                self.music.anterior();  self._radio_toast = 150
        
        if event.key == pygame.K_r:
            if self.estado in ("GAMEPLAY", "PAUSED", "GAME_OVER"):
                self.restart_current_room()

    def _handle_events_internal(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                import sys; sys.exit()
            self._process_single_event(event)

    def _handle_event(self, event):
        self._process_single_event(event)

    def _tick_external(self, surface):
        """
        Un frame completo (update + draw) llamado desde main.py.
        Devuelve "MENU" cuando la partida termina, o None si sigue.
        """
        self._handle_events_internal()

        if self.estado == "GAMEPLAY":
            self._update_gameplay(); self._draw_gameplay()
        elif self.estado == "PAUSED":
            self._draw_gameplay(); self._draw_pause()
        elif self.estado == "GAME_OVER":
            self._draw_game_over()
        elif self.estado == "VICTORY":
            self._draw_victory()

        
        
        self._draw_radio_toast()

















        keys = pygame.key.get_pressed()
        if getattr(self, "quit_to_menu", False):
            self.quit_to_menu = False
            return "MENU"

        if self.estado == "GAME_OVER" and keys[pygame.K_ESCAPE]:
            return "MENU"
        if self.estado == "VICTORY":
            if not hasattr(self, "_victory_timer"):
                self._victory_timer = 300
            self._victory_timer -= 1
            if self._victory_timer <= 0:
                self._victory_timer = 300
                return "MENU"
        return None

    def start_game(self):
        """Empiezo una run nueva: genera el mapa y resetea todo."""
        self._bg_cache    = (None, None)
        self._floor_cache = (None, None)
        self.rooms        = generate_map()
        self.player       = None
        self.particles      = []
        self.floating_texts = []
        self.run_number  += 1
        self.load_room(0)
        self.music.play()   
        self.estado = "GAMEPLAY"

    #  MENÚ (fallback)
    def _update_menu(self):
        self.menu_bg_tick += 1

    def _draw_menu(self):
        t = self.menu_bg_tick * 0.02
        self.screen.fill(BLACK)
        for i in range(0, SCREEN_W, 80):
            col_r = int(abs(math.sin(t + i * 0.01)) * 60)
            col_b = int(abs(math.cos(t + i * 0.015)) * 120)
            pygame.draw.line(self.screen, (col_r, 0, col_b), (i, 0), (i, SCREEN_H), 2)
        for (sx, sy, sr, phase) in self.stars:
            bright = int(abs(math.sin(t * 2 + phase * 6)) * 200 + 55)
            pygame.draw.circle(self.screen, (bright, bright, bright), (sx, sy), sr)
        cx = SCREEN_W // 2
        title1 = self.font_xl.render("MACACO", True, NEON_ORANGE)
        title2 = self.font_xl.render("vs. LAS MOMIAS", True, NEON_PINK)
        title3 = self.font_lg.render("DE GUANAJUATO", True, NEON_CYAN)
        self.screen.blit(title1, (cx - title1.get_width() // 2, 120))
        self.screen.blit(title2, (cx - title2.get_width() // 2, 210))
        self.screen.blit(title3, (cx - title3.get_width() // 2, 300))
        if int(t * 2) % 2 == 0:
            btn = self.font_lg.render(">> ENTER / ESPACIO para JUGAR <<", True, WHITE)
            self.screen.blit(btn, (cx - btn.get_width() // 2, 460))


    #  GAMEPLAY — UPDATE
    def _update_gameplay(self):
        self._disco_tick += 1
        mouse_wx, mouse_wy = self.screen_to_world(*pygame.mouse.get_pos())

        # tapones en las puertas cerradas, para que ni yo ni los enemigos crucemos una puerta que sigue cerrada
        effective_walls = list(self.walls)
        for door in self.doors:
            if not door.open:
                gap, T = DOOR_GAP, WALL_T
                if door.side in ('left', 'right'):
                    effective_walls.append(pygame.Rect(int(door.x) - T // 2, int(door.y) - gap // 2, T, gap))
                else:
                    effective_walls.append(pygame.Rect(int(door.x) - gap // 2, int(door.y) - T // 2, gap, T))

        self.player.update(mouse_wx, mouse_wy, effective_walls)

        for enemy in self.enemies:
            enemy.update(self.player, self.bullets, effective_walls)

        # daño por contacto: pierdo 1 HP
        if self.player.invincible_timer <= 0:
            for enemy in self.enemies:
                if math.hypot(self.player.x - enemy.x, self.player.y - enemy.y) < self.player.r + enemy.r:
                    self.player.hp -= 1
                    self.player.invincible_timer = int(self.player.defense * 60)
                    self.sfx.play("player_hurt")
                    self.camera.shake(6)
                    self.floating_texts.append(
                        FloatingText("-1", self.player.x, self.player.y - 40, (255, 80, 80), 18, 40))
                    break

        # mover balas 
        for b in self.bullets:
            b.update(self.walls, self.player if b.owner == "enemy" else None)

        # el escudo refleja / el cuerpo recibe
        self.player.check_bullet_collision(self.bullets, self.particles, self.floating_texts, self.camera)

        # balas reflejadas (owner == "player") contra enemigos
        for b in self.bullets:
            if b.dead or b.owner != "player":
                continue
            for enemy in self.enemies:
                if enemy.dead:
                    continue
                if math.hypot(b.x - enemy.x, b.y - enemy.y) < enemy.r + b.r:
                    if b.is_giant:
                        # la bala gigante reflejada explota y daña en área
                        for nearby in self.enemies:
                            if math.hypot(nearby.x - b.x, nearby.y - b.y) < 80:
                                nearby.take_damage(1, self.particles, self.floating_texts, self.camera)
                        self.camera.shake(10)
                    else:
                        enemy.take_damage(1, self.particles, self.floating_texts, self.camera)
                    b.dead = True
                    self.sfx.register_hit(killed=enemy.dead)
                    # XP + monedas al matar
                    if enemy.dead:
                        prev_lv = self.player.level
                        self.player.gain_xp(enemy.xp)
                        if self.player.level > prev_lv:
                            self.sfx.play("levelup")
                        for _ in range(random.randint(1, 4)):
                            self.coins.append(Coin(enemy.x + random.randint(-20, 20),
                                                   enemy.y + random.randint(-20, 20)))
                    break

        for c in self.coins:
            c.update(self.player)

        for door in self.doors:
            if door.player_crosses(self.player):
                opp = {'right': 'left', 'left': 'right', 'top': 'bottom', 'bottom': 'top'}
                fake_door = type('D', (), {'side': opp.get(door.side, door.side)})()
                self.load_room(door.target_room, from_door=fake_door)
                return

        # marco la sala como limpia y abro las puertas
        all_dead = len(self.enemies) == 0 and self._room_enemy_count > 0
        if all_dead and not self.clear_triggered:
            self.clear_triggered = True
            self.rooms[self.current_room]["cleared"] = True
            for door in self.doors:
                door.open = True
                self.floating_texts.append(
                    FloatingText("¡PUERTA ABIERTA!", door.x, door.y - 40, NEON_GREEN, 22, 80))
            self.sfx.play("door_open")

        for ft in self.floating_texts:
            ft.update()

        for p in self.particles:
            p.update()
        # tope de partículas para no acumular sangre infinita
        if len(self.particles) > 300:
            self.particles = self.particles[-300:]

        self.music.update()
        self.sfx.update()
        self.camera.update(self.player.x, self.player.y)

        # tiro lo que ya murió
        self.enemies        = [e for e in self.enemies if not e.dead]
        self.bullets        = [b for b in self.bullets if not b.dead]
        self.coins          = [c for c in self.coins if not c.dead]
        self.floating_texts = [ft for ft in self.floating_texts if not ft.dead]

        # GAME OVER + animacion
        if self.player.dead:
            self.camera.flash_timer = 0
            self.camera.flash_alpha = 0
            self.estado = "GAME_OVER"
            self._death_frame_idx   = 0
            self._death_frame_timer = 0
            self.sfx.play("muerte")
            self.music.pause() 

        # victoria
        if self.rooms:
            last = self.rooms[-1]
            if (self.current_room == len(self.rooms) - 1 and last.get("is_boss", False)
                    and self.clear_triggered and len(self.enemies) == 0):
                self.camera.flash_timer = 0
                self.camera.flash_alpha = 0
                self.estado = "VICTORY"
                self._victory_timer = 300
                self.sfx.play("victoria")

    #  GAMEPLAY — DRAW
    def _draw_gameplay(self):
        self.screen.set_clip(pygame.Rect(0, 0, GAME_ZONE_W, SCREEN_H))
        self.draw_background()
        self.draw_walls()

        for p in self.particles:       # sangre, debajo de todo
            p.draw(self.screen, self.camera)
        for c in self.coins:
            c.draw(self.screen, self.camera)
        for door in self.doors:
            door.draw(self.screen, self.camera)
        for b in self.bullets:
            b.draw(self.screen, self.camera)

        self.camera._game = self
        for e in self.enemies:
            e.draw(self.screen, self.camera)
        self.player.draw(self.screen, self.camera)
        self.camera._game = None

        # contador de combo grande cuando llevo 15+
        if self.sfx.combo >= 15:
            cf = get_font(22, bold=True)
            cs = cf.render(f"{self.sfx.combo}x COMBO!", True, NEON_YELLOW)
            cs.set_alpha(220)
            self.screen.blit(cs, (GAME_ZONE_W // 2 - cs.get_width() // 2, 28))

        for ft in self.floating_texts:
            ft.draw(self.screen, self.camera)

        self.screen.set_clip(None)

        # flash rojo solo en la zona de juego
        self.camera.draw_flash_zone(self.screen, GAME_ZONE_W)

        # filtro scanlines 
        if self._scanline_surf is None:
            self._scanline_surf = pygame.Surface((GAME_ZONE_W, SCREEN_H), pygame.SRCALPHA)
            for scan_y in range(0, SCREEN_H, 3):
                pygame.draw.line(self._scanline_surf, (0, 0, 0, 50), (0, scan_y), (GAME_ZONE_W, scan_y), 1)
        self.screen.blit(self._scanline_surf, (0, 0))

        # marco solo zona de juego
        gf = self.tex.get("game_frame")
        if gf:
            if self._frame_cache is None:
                self._frame_cache = pygame.transform.scale(gf, (GAME_ZONE_W, SCREEN_H))
            self.screen.set_clip(pygame.Rect(0, 0, GAME_ZONE_W, SCREEN_H))
            self.screen.blit(self._frame_cache, (0, 0))
            self.screen.set_clip(None)

        # HUD lateral + minimapa
        room_name = self.rooms[self.current_room].get("name", "")
        self.player.draw_hud(self.screen, self.font_sm, self.font_md,
                             room_name=room_name, acto_name="EL ANTRO", font_lg=self.font_lg)
        self.player.draw_minimap(self.screen, self.rooms, self.current_room, self.font_sm)


    def _draw_game_over_buttons(self):
        """Botones clicables de la pantalla de muerte."""
        pygame.mouse.set_visible(True)
        cx = SCREEN_W // 2
        w, h, gap = 260, 52, 30
        y = 580
        botones = [
            ("REINTENTAR", pygame.Rect(cx - w - gap // 2, y, w, h)),
            ("MENU",       pygame.Rect(cx + gap // 2,     y, w, h)),
        ]

        mx, my = pygame.mouse.get_pos()
        down = pygame.mouse.get_pressed()[0]
        # solo cuenta el clic si el botón se soltó antes (evita clics "arrastrados")
        clicked = down and not getattr(self, "_go_was_down", True) and getattr(self, "_go_armed", False)
        self._go_was_down = down
        if not down:
            self._go_armed = True

        for i, (texto, rect) in enumerate(botones):
            hover = rect.collidepoint(mx, my)
            fondo  = (200, 40, 40) if hover else (60, 10, 15)
            borde  = (255, 255, 0) if hover else (220, 220, 220)
            color  = (255, 255, 0) if hover else WHITE
            pygame.draw.rect(self.screen, fondo, rect, border_radius=8)
            pygame.draw.rect(self.screen, borde, rect, 3, border_radius=8)
            lbl = self.font_md.render(texto, True, color)
            self.screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                                   rect.centery - lbl.get_height() // 2))
            if hover and clicked:
                if i == 0:
                    self.restart_current_room()
                else:
                    self.music.stop()
                    self.quit_to_menu = True

    #  PANTALLAS DE FIN
    def _draw_game_over(self):
        cx = SCREEN_W // 2
        if self._death_frames:
            self._death_frame_timer += 1
            if self._death_frame_timer >= 10:
                self._death_frame_timer = 0
                if self._death_frame_idx < len(self._death_frames) - 1:
                    self._death_frame_idx += 1
            self.screen.blit(self._death_frames[self._death_frame_idx], (0, 0))
            hint = self.font_md.render("ESC = Menu   |   R = Reiniciar", True, WHITE)
            self.screen.blit(hint, (cx - hint.get_width() // 2, 660))
            self._draw_game_over_buttons()        # <-- NUEVO
            return

        # fallback si no hay frames de muerte
        self.screen.fill((90, 5, 15))
        sub  = self.font_lg.render("Las momias te derrotaron...", True, WHITE)
        hint = self.font_md.render("ESC = Menu   |   R = Reiniciar", True, (200, 200, 200))
        self.screen.blit(sub,  (cx - sub.get_width() // 2, 340))
        self.screen.blit(hint, (cx - hint.get_width() // 2, 660))
        self._draw_game_over_buttons()            # <-- NUEVO

    def _draw_victory(self):
        if not hasattr(self, "_victory_timer"):
            self._victory_timer = 300
        self.screen.fill((0, 0, 0))
        t  = pygame.time.get_ticks() * 0.001
        cx = SCREEN_W // 2
        pls = int(abs(math.sin(t * 1.5)) * 20)   # latido del texto
        m1 = self.font_xl.render("ESCENARIO 1 COMPLETADO", True, (220 + pls, 220 + pls, 220 + pls))
        m2 = self.font_lg.render("Entrando a las catacumbas.", True, NEON_GREEN)
        m3 = self.font_lg.render("continuara...", True, (160 + pls, 255, 160 + pls))
        self.screen.blit(m1, (cx - m1.get_width() // 2, 210))
        self.screen.blit(m2, (cx - m2.get_width() // 2, 310))
        self.screen.blit(m3, (cx - m3.get_width() // 2, 380))
        ratio = max(0, 1 - self._victory_timer / 300)
        bw = 400
        pygame.draw.rect(self.screen, (40, 40, 40), (cx - bw // 2, 490, bw, 8))
        pygame.draw.rect(self.screen, NEON_GREEN,  (cx - bw // 2, 490, int(bw * ratio), 8))

    def _draw_radio_toast(self):
        t = getattr(self, "_radio_toast", 0)
        if t <= 0 or self.estado == "PAUSED":   # en pausa ya se ve el nombre arriba
            return
        self._radio_toast = t - 1
        nombre = self.music.current_name.rsplit(".", 1)[0]
        lbl = self.font_sm.render(f"♪  {nombre}", True, (255, 255, 255))
        caja = pygame.Surface((lbl.get_width() + 24, lbl.get_height() + 12), pygame.SRCALPHA)
        caja.fill((0, 0, 0, 170))
        caja.blit(lbl, (12, 6))
        caja.set_alpha(min(255, t * 8))          # se desvanece al final
        self.screen.blit(caja, (20, SCREEN_H - caja.get_height() - 20))

    def _draw_pause(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        cx = SCREEN_W // 2
        t  = pygame.time.get_ticks() * 0.001
        pulse = int(abs(math.sin(t * 2)) * 30)
        title = self.font_xl.render("PAUSA", True, (255, pulse * 2, pulse))
        self.screen.blit(title, (cx - title.get_width() // 2, 130))
        track = self.font_sm.render(f"♪  {self.music.current_name}", True, (160, 160, 200))
        track.set_alpha(180)
        self.screen.blit(track, (cx - track.get_width() // 2, 182))

        # sliders de volumen
        keys = pygame.key.get_pressed()
        if keys[pygame.K_q]: self.music.set_volume(max(0.0, self.music.volume - 0.01))
        if keys[pygame.K_e]: self.music.set_volume(min(1.0, self.music.volume + 0.01))
        if keys[pygame.K_z]: self.sfx.set_volume(max(0.0, self.sfx.volume - 0.01))
        if keys[pygame.K_x]: self.sfx.set_volume(min(1.0, self.sfx.volume + 0.01))

        bw = 300
        def slider(label, val, y_pos, color):
            lbl = self.font_sm.render(label, True, (180, 180, 180))
            self.screen.blit(lbl, (cx - bw // 2, y_pos))
            by = y_pos + lbl.get_height() + 4
            pygame.draw.rect(self.screen, (40, 40, 40), (cx - bw // 2, by, bw, 10), border_radius=5)
            pygame.draw.rect(self.screen, color,        (cx - bw // 2, by, int(bw * val), 10), border_radius=5)
            pct = self.font_sm.render(f"{int(val * 100)}%", True, (200, 200, 200))
            self.screen.blit(pct, (cx + bw // 2 + 8, by))

        slider("MUSICA   [ Q = -   E = + ]", self.music.volume, 250, (0, 200, 255))
        slider("SFX      [ Z = -   X = + ]", self.sfx.volume,   310, (255, 150, 0))

        hint = self.font_sm.render("ESC / P = Continuar  |  R = Reiniciar sala  |  M = Menú principal", True, (140, 140, 160))
        hint2 = self.font_sm.render("N = Siguiente canción  |  B = Anterior", True, (140, 140, 160))
        self.screen.blit(hint2, (cx - hint2.get_width() // 2, 430))
        self.screen.blit(hint, (cx - hint.get_width() // 2, 400))
